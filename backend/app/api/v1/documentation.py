from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.connection import get_db
from app.models.repository import Repository
from app.models.documentation import DocumentationItem, DocumentationVersion, DocumentationGap
from app.schemas.documentation import (
    DocumentationItemResponse,
    DocumentationVersionResponse,
    DocumentationGapResponse,
    DocumentationDashboardResponse,
    DocumentationCoverageResponse,
    DocumentationValidationResponse,
    DocumentationGenerateRequest,
    DocumentationUpdateRequest,
    DocumentationAIActionRequest,
    DocumentationAIActionResponse,
    DocumentationSearchResponse,
    ChangeImpactSyncRequest,
    ChangeImpactSyncResponse
)
from app.services.documentation_service import DocumentationIntelligenceService

router = APIRouter(prefix="/repositories/{repository_id}/documentation", tags=["Documentation Intelligence"])
doc_service = DocumentationIntelligenceService()


async def _get_repository(repository_id: str, db: AsyncSession) -> Repository:
    stmt = select(Repository).where(Repository.id == repository_id)
    res = await db.execute(stmt)
    repo = res.scalars().first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.get("/dashboard", response_model=DocumentationDashboardResponse)
async def get_documentation_dashboard(repository_id: str, db: AsyncSession = Depends(get_db)):
    repo = await _get_repository(repository_id, db)
    return await doc_service.get_dashboard_summary(repo, db)


@router.get("", response_model=List[DocumentationItemResponse])
async def list_documentation_items(repository_id: str, db: AsyncSession = Depends(get_db)):
    repo = await _get_repository(repository_id, db)
    items = await doc_service.get_or_create_doc_items(repo, db)
    return items


@router.get("/coverage", response_model=DocumentationCoverageResponse)
async def get_documentation_coverage(repository_id: str, db: AsyncSession = Depends(get_db)):
    repo = await _get_repository(repository_id, db)
    return await doc_service.calculate_coverage(repo, db)


@router.get("/gaps", response_model=List[DocumentationGapResponse])
async def get_documentation_gaps(repository_id: str, db: AsyncSession = Depends(get_db)):
    repo = await _get_repository(repository_id, db)
    stmt = select(DocumentationGap).where(DocumentationGap.repository_id == repository_id)
    res = await db.execute(stmt)
    gaps = res.scalars().all()
    if not gaps:
        gaps = await doc_service.scan_documentation_gaps(repo, db)
    return gaps


@router.post("/gaps/scan", response_model=List[DocumentationGapResponse])
async def scan_documentation_gaps_endpoint(repository_id: str, db: AsyncSession = Depends(get_db)):
    repo = await _get_repository(repository_id, db)
    return await doc_service.scan_documentation_gaps(repo, db)


@router.post("/gaps/{gap_id}/resolve", response_model=DocumentationItemResponse)
async def resolve_documentation_gap_endpoint(
    repository_id: str,
    gap_id: str,
    db: AsyncSession = Depends(get_db)
):
    repo = await _get_repository(repository_id, db)
    return await doc_service.resolve_gap(repo, gap_id, db)


@router.get("/item/{doc_type}", response_model=DocumentationItemResponse)
async def get_documentation_by_type(repository_id: str, doc_type: str, db: AsyncSession = Depends(get_db)):
    repo = await _get_repository(repository_id, db)
    stmt = select(DocumentationItem).where(
        DocumentationItem.repository_id == repo.id,
        DocumentationItem.doc_type == doc_type
    )
    res = await db.execute(stmt)
    item = res.scalars().first()
    if not item:
        items = await doc_service.get_or_create_doc_items(repo, db)
        item = next((i for i in items if i.doc_type == doc_type), None)
    if not item:
        raise HTTPException(status_code=404, detail=f"Documentation type '{doc_type}' not found")
    return item


@router.post("/generate", response_model=DocumentationItemResponse)
async def generate_documentation(
    repository_id: str,
    req: DocumentationGenerateRequest,
    db: AsyncSession = Depends(get_db)
):
    repo = await _get_repository(repository_id, db)
    return await doc_service.generate_document(
        repo=repo,
        doc_type=req.doc_type,
        custom_instructions=req.custom_instructions,
        db=db
    )


@router.put("/{doc_id}", response_model=DocumentationItemResponse)
async def update_documentation_content(
    repository_id: str,
    doc_id: str,
    req: DocumentationUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    repo = await _get_repository(repository_id, db)
    stmt = select(DocumentationItem).where(
        DocumentationItem.id == doc_id,
        DocumentationItem.repository_id == repo.id
    )
    res = await db.execute(stmt)
    item = res.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Documentation item not found")

    import uuid, datetime
    # Save a revision version
    v_stmt = select(DocumentationVersion).where(DocumentationVersion.documentation_id == item.id)
    v_res = await db.execute(v_stmt)
    v_count = len(v_res.scalars().all())

    new_version = DocumentationVersion(
        id=str(uuid.uuid4()),
        documentation_id=item.id,
        version_tag=f"v1.{v_count}",
        content=req.content,
        change_summary=req.change_summary or "Manual user edit",
        validation_status="unvalidated"
    )
    db.add(new_version)

    # Validate updated content
    val_res = await doc_service.validate_content(repo, req.content, db)

    item.content = req.content
    item.validation_status = val_res.status
    item.validation_details = {
        "verified_claims": val_res.verified_claims,
        "verified_files": val_res.verified_files,
        "verified_apis": val_res.verified_apis,
        "outdated_references": val_res.outdated_references,
        "unsupported_claims": val_res.unsupported_claims,
        "warnings": val_res.warnings,
        "claims": val_res.claims
    }
    item.status = "up_to_date" if val_res.passed else "update_recommended"
    item.updated_at = datetime.datetime.utcnow()

    await db.commit()
    await db.refresh(item)
    return item


@router.post("/{doc_id}/validate", response_model=DocumentationValidationResponse)
async def validate_documentation(
    repository_id: str,
    doc_id: str,
    db: AsyncSession = Depends(get_db)
):
    repo = await _get_repository(repository_id, db)
    stmt = select(DocumentationItem).where(
        DocumentationItem.id == doc_id,
        DocumentationItem.repository_id == repo.id
    )
    res = await db.execute(stmt)
    item = res.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Documentation item not found")

    val_res = await doc_service.validate_content(repo, item.content, db)
    item.validation_status = val_res.status
    item.validation_details = {
        "verified_claims": val_res.verified_claims,
        "verified_files": val_res.verified_files,
        "verified_apis": val_res.verified_apis,
        "outdated_references": val_res.outdated_references,
        "unsupported_claims": val_res.unsupported_claims,
        "warnings": val_res.warnings,
        "claims": val_res.claims
    }
    await db.commit()
    return val_res


@router.post("/{doc_id}/regenerate", response_model=DocumentationItemResponse)
async def regenerate_documentation(
    repository_id: str,
    doc_id: str,
    db: AsyncSession = Depends(get_db)
):
    repo = await _get_repository(repository_id, db)
    stmt = select(DocumentationItem).where(
        DocumentationItem.id == doc_id,
        DocumentationItem.repository_id == repo.id
    )
    res = await db.execute(stmt)
    item = res.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Documentation item not found")

    return await doc_service.generate_document(
        repo=repo,
        doc_type=item.doc_type,
        custom_instructions=None,
        db=db
    )


@router.get("/{doc_id}/versions", response_model=List[DocumentationVersionResponse])
async def get_documentation_versions(
    repository_id: str,
    doc_id: str,
    db: AsyncSession = Depends(get_db)
):
    repo = await _get_repository(repository_id, db)
    stmt = select(DocumentationVersion).where(
        DocumentationVersion.documentation_id == doc_id
    ).order_by(DocumentationVersion.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/{doc_id}/revert/{version_id}", response_model=DocumentationItemResponse)
async def revert_documentation_version(
    repository_id: str,
    doc_id: str,
    version_id: str,
    db: AsyncSession = Depends(get_db)
):
    repo = await _get_repository(repository_id, db)
    stmt = select(DocumentationItem).where(
        DocumentationItem.id == doc_id,
        DocumentationItem.repository_id == repo.id
    )
    res = await db.execute(stmt)
    item = res.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Documentation item not found")

    v_stmt = select(DocumentationVersion).where(
        DocumentationVersion.id == version_id,
        DocumentationVersion.documentation_id == doc_id
    )
    v_res = await db.execute(v_stmt)
    version = v_res.scalars().first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    item.content = version.content
    item.validation_status = version.validation_status
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/{doc_id}/ai-action", response_model=DocumentationAIActionResponse)
async def handle_documentation_ai_action(
    repository_id: str,
    doc_id: str,
    req: DocumentationAIActionRequest,
    db: AsyncSession = Depends(get_db)
):
    repo = await _get_repository(repository_id, db)
    stmt = select(DocumentationItem).where(
        DocumentationItem.id == doc_id,
        DocumentationItem.repository_id == repo.id
    )
    res = await db.execute(stmt)
    item = res.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Documentation item not found")

    return await doc_service.execute_ai_action(
        doc_item=item,
        action=req.action,
        selected_text=req.selected_text,
        instruction=req.instruction
    )


@router.post("/search", response_model=DocumentationSearchResponse)
async def search_documentation_endpoint(
    repository_id: str,
    query: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db)
):
    repo = await _get_repository(repository_id, db)
    return await doc_service.search_documentation(repo, query, db)


@router.post("/sync-impact", response_model=ChangeImpactSyncResponse)
async def sync_change_impact_endpoint(
    repository_id: str,
    req: ChangeImpactSyncRequest,
    db: AsyncSession = Depends(get_db)
):
    repo = await _get_repository(repository_id, db)
    changed = req.changed_files or ["backend/main.py"]
    return await doc_service.sync_change_impact(repo, changed, db)
