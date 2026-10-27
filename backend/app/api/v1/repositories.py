import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from app.core.config import settings
from app.core.security import parse_github_url
from app.database.connection import get_db
from app.models.repository import Repository, RepositoryFile, CodeEntity, Dependency
from app.schemas.repository import (
    RepositoryCreateRequest,
    RepositoryResponse,
    RepositoryDetailResponse,
    FileTreeItem,
    FileContentResponse
)
from app.repository.git_service import GitService
from app.repository.file_scanner import FileScanner
from app.code_intelligence.ast_parser import PythonASTParser
from app.code_intelligence.generic_parser import GenericCodeParser
from app.rag.chunker import CodeAwareChunker
from app.rag.vector_store import VectorStore
from app.core.logging import logger

router = APIRouter(prefix="/repositories", tags=["Repositories"])

git_service = GitService()
file_scanner = FileScanner()
ast_parser = PythonASTParser()
generic_parser = GenericCodeParser()
chunker = CodeAwareChunker()
vector_store = VectorStore()

@router.post("", response_model=RepositoryResponse)
async def connect_repository(req: RepositoryCreateRequest, db: AsyncSession = Depends(get_db)):
    """
    Connects and clones a GitHub repository, computes file stats, and records it in the database.
    """
    owner, repo_name = parse_github_url(req.url)
    
    # Check if repo already registered
    result = await db.execute(select(Repository).where(Repository.url == req.url))
    existing_repo = result.scalars().first()
    
    repo_id = existing_repo.id if existing_repo else str(uuid.uuid4())
    
    # Clone repository
    try:
        local_path, default_branch = git_service.clone_repository(req.url, repo_id, branch=req.branch)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to clone repository: {str(e)}")

    # Initial file scan
    files_data, language_stats, total_files, total_lines = file_scanner.scan_repository(local_path)

    if existing_repo:
        existing_repo.local_path = str(local_path)
        existing_repo.default_branch = default_branch
        existing_repo.status = "cloned"
        existing_repo.languages = language_stats
        existing_repo.total_files = total_files
        existing_repo.total_lines = total_lines
        repo_obj = existing_repo
    else:
        repo_obj = Repository(
            id=repo_id,
            name=repo_name,
            owner=owner,
            url=req.url,
            local_path=str(local_path),
            default_branch=default_branch,
            status="cloned",
            languages=language_stats,
            total_files=total_files,
            total_lines=total_lines,
            description=f"GitHub repository {owner}/{repo_name}"
        )
        db.add(repo_obj)

    await db.commit()
    await db.refresh(repo_obj)
    
    # Proactively index repository in background or sync
    try:
        await index_repository_internal(repo_obj.id, local_path, files_data, db)
    except Exception as idx_err:
        logger.error(f"Indexing error: {idx_err}")

    await db.refresh(repo_obj)
    return repo_obj

@router.get("", response_model=List[RepositoryResponse])
async def list_repositories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repository).order_by(Repository.updated_at.desc()))
    return result.scalars().all()

@router.get("/{repository_id}", response_model=RepositoryResponse)
async def get_repository(repository_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repository).where(Repository.id == repository_id))
    repo = result.scalars().first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo

@router.get("/{repository_id}/files/tree", response_model=List[dict])
async def get_repository_file_tree(repository_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repository).where(Repository.id == repository_id))
    repo = result.scalars().first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    tree = file_scanner.build_file_tree(Path(repo.local_path))
    return tree

@router.get("/{repository_id}/file-content", response_model=FileContentResponse)
async def get_file_content(repository_id: str, path: str = Query(..., description="Relative file path"), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repository).where(Repository.id == repository_id))
    repo = result.scalars().first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    target_file = Path(repo.local_path) / path
    if not target_file.exists() or not target_file.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    content = file_scanner.read_file_safe(target_file)
    if content is None:
        raise HTTPException(status_code=400, detail="File cannot be read (binary or too large)")

    return FileContentResponse(
        path=path,
        filename=target_file.name,
        language=file_scanner.detect_language(target_file),
        size_bytes=target_file.stat().st_size,
        line_count=len(content.splitlines()),
        content=content
    )

@router.post("/{repository_id}/index")
async def index_repository_endpoint(repository_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repository).where(Repository.id == repository_id))
    repo = result.scalars().first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    files_data, _, _, _ = file_scanner.scan_repository(Path(repo.local_path))
    count = await index_repository_internal(repo.id, Path(repo.local_path), files_data, db)
    return {"status": "success", "indexed_chunks": count}

async def index_repository_internal(repo_id: str, repo_dir: Path, files_data: List[dict], db: AsyncSession) -> int:
    """Internal helper to parse AST, extract dependencies, chunk, and index into vector store."""
    all_chunks = []

    # Clean existing data for this repo before reindexing
    await db.execute(delete(CodeEntity).where(CodeEntity.repository_id == repo_id))
    await db.execute(delete(Dependency).where(Dependency.repository_id == repo_id))
    await db.execute(delete(RepositoryFile).where(RepositoryFile.repository_id == repo_id))
    await db.commit()

    for f in files_data:
        file_id = str(uuid.uuid4())
        content = f.get("content")
        if not content:
            continue

        file_path = f["path"]
        lang = f["language"]
        
        # Parse entities
        entities = []
        if lang == "Python":
            parse_res = ast_parser.parse_source(content, file_path)
            entities = parse_res.get("entities", [])
        elif lang in ["JavaScript", "TypeScript", "JavaScript (React)", "TypeScript (React)", "Go", "Rust"]:
            parse_res = generic_parser.parse_source(content, file_path, lang)
            entities = parse_res.get("entities", [])

        # Parse dependencies
        manifest_deps = generic_parser.parse_manifest_dependencies(f["filename"], content)
        for dep in manifest_deps:
            dep_obj = Dependency(
                id=str(uuid.uuid4()),
                repository_id=repo_id,
                name=dep["name"],
                version=dep.get("version"),
                ecosystem=dep["ecosystem"],
                source_file=file_path
            )
            db.add(dep_obj)

        # Create file DB entry
        file_obj = RepositoryFile(
            id=file_id,
            repository_id=repo_id,
            path=file_path,
            filename=f["filename"],
            extension=f["extension"],
            language=lang,
            size_bytes=f["size_bytes"],
            line_count=f["line_count"],
            is_indexed=True
        )
        db.add(file_obj)

        for ent in entities:
            ent_obj = CodeEntity(
                id=str(uuid.uuid4()),
                repository_id=repo_id,
                file_id=file_id,
                file_path=file_path,
                name=ent["name"],
                entity_type=ent["entity_type"],
                start_line=ent["start_line"],
                end_line=ent["end_line"],
                signature=ent.get("signature"),
                docstring=ent.get("docstring"),
                decorators=ent.get("decorators", []),
                calls=ent.get("calls", [])
            )
            db.add(ent_obj)

        # Chunk file
        file_chunks = chunker.chunk_file(file_path, content, language=lang, entities=entities)
        all_chunks.extend(file_chunks)

    # Index into vector database
    indexed_count = vector_store.index_chunks(repo_id, all_chunks)
    
    # Update repo status
    res = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = res.scalars().first()
    if repo:
        repo.status = "indexed"

    await db.commit()
    return indexed_count
