from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.connection import get_db
from app.models.repository import Repository, RepositoryFile, CodeEntity, Dependency
from app.schemas.repository import (
    CodeEntityResponse,
    DependencyResponse,
    FrameworkResponse,
    DirectorySummary,
    RepositoryOverviewResponse,
    DiagramResponse,
    CallGraphFunctionSummary,
    CallGraphResponse,
    CallGraphNodeItem,
    CallGraphEdgeItem
)
from app.code_intelligence.graph_builder import RepositoryGraph
from app.code_intelligence.framework_detector import detect_frameworks
from app.code_intelligence.call_graph_engine import (
    get_or_build_repository_call_graph,
    get_call_graph_service,
    invalidate_repository_call_graph
)
from app.repository.file_scanner import FileScanner

router = APIRouter(prefix="/repositories/{repository_id}", tags=["Code Intelligence"])
file_scanner = FileScanner()

@router.get("/entities", response_model=List[CodeEntityResponse])
async def get_repository_entities(repository_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CodeEntity).where(CodeEntity.repository_id == repository_id)
    )
    return result.scalars().all()

@router.get("/dependencies", response_model=List[DependencyResponse])
async def get_repository_dependencies(repository_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Dependency).where(Dependency.repository_id == repository_id)
    )
    return result.scalars().all()

@router.get("/frameworks", response_model=List[FrameworkResponse])
async def get_repository_frameworks(repository_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repository).where(Repository.id == repository_id))
    repo = result.scalars().first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    deps_res = await db.execute(select(Dependency).where(Dependency.repository_id == repository_id))
    deps = [{"name": d.name, "version": d.version, "ecosystem": d.ecosystem, "source_file": d.source_file} for d in deps_res.scalars().all()]

    files_res = await db.execute(select(RepositoryFile).where(RepositoryFile.repository_id == repository_id))
    file_paths = [f.path for f in files_res.scalars().all()]
    if not file_paths and repo.local_path and Path(repo.local_path).exists():
        files_data, _, _, _ = file_scanner.scan_repository(Path(repo.local_path))
        file_paths = [f["path"] for f in files_data]

    detected = detect_frameworks(deps, file_paths, repo.languages)
    return detected

@router.get("/overview", response_model=RepositoryOverviewResponse)
async def get_repository_overview(repository_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repository).where(Repository.id == repository_id))
    repo = result.scalars().first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # 1. Files
    files_res = await db.execute(select(RepositoryFile).where(RepositoryFile.repository_id == repository_id))
    files = files_res.scalars().all()
    file_paths = [f.path for f in files]
    
    if not files and repo.local_path and Path(repo.local_path).exists():
        files_data, lang_stats, total_files, total_lines = file_scanner.scan_repository(Path(repo.local_path))
        file_paths = [f["path"] for f in files_data]
    else:
        files_data = [{"path": f.path, "filename": f.filename, "language": f.language, "line_count": f.line_count, "size_bytes": f.size_bytes} for f in files]

    # 2. Dependencies
    deps_res = await db.execute(select(Dependency).where(Dependency.repository_id == repository_id))
    deps = deps_res.scalars().all()
    deps_dicts = [{"name": d.name, "version": d.version, "ecosystem": d.ecosystem, "source_file": d.source_file} for d in deps]

    # 3. Entities
    entities_res = await db.execute(select(CodeEntity).where(CodeEntity.repository_id == repository_id))
    entities = entities_res.scalars().all()

    # Entity counts by type
    entity_counts: Dict[str, int] = defaultdict(int)
    for ent in entities:
        entity_counts[ent.entity_type] += 1

    # 4. Detected Frameworks
    frameworks = detect_frameworks(deps_dicts, file_paths, repo.languages or {})

    # 5. Language percentages
    total_lang_lines = sum((repo.languages or {}).values())
    lang_percentages: Dict[str, float] = {}
    if total_lang_lines > 0:
        for lang, count in (repo.languages or {}).items():
            lang_percentages[lang] = round((count / total_lang_lines) * 100, 1)
    elif repo.languages:
        equal_pct = round(100.0 / len(repo.languages), 1)
        for lang in repo.languages:
            lang_percentages[lang] = equal_pct

    # 6. Directories breakdown
    dir_stats = defaultdict(lambda: {"file_count": 0, "line_count": 0, "languages": set()})
    unique_dirs = set()
    manifest_files = []
    key_entrypoints = []

    ENTRYPOINT_NAMES = {
        "server.js", "app.js", "index.js", "main.js", "main.py", "app.py", "wsgi.py",
        "asgi.py", "main.go", "main.rs", "index.ts", "main.tsx", "App.tsx", "App.jsx"
    }
    MANIFEST_NAMES = {
        "package.json", "requirements.txt", "pyproject.toml", "Cargo.toml", "go.mod",
        "pom.xml", "build.gradle", "Dockerfile", "docker-compose.yml", "tsconfig.json"
    }

    for f in files_data:
        p = f["path"]
        parts = p.split("/")
        if len(parts) > 1:
            root_dir = parts[0]
            dir_stats[root_dir]["file_count"] += 1
            dir_stats[root_dir]["line_count"] += f.get("line_count", 0)
            if f.get("language"):
                dir_stats[root_dir]["languages"].add(f["language"])
            for i in range(len(parts) - 1):
                unique_dirs.add("/".join(parts[:i + 1]))

        fname = parts[-1]
        if fname in MANIFEST_NAMES:
            manifest_files.append(p)
        if fname in ENTRYPOINT_NAMES or ("server" in fname.lower() and fname.endswith((".js", ".ts", ".py"))):
            key_entrypoints.append(p)

    root_directories = [
        DirectorySummary(
            name=name,
            path=name,
            file_count=data["file_count"],
            line_count=data["line_count"],
            languages=sorted(list(data["languages"]))
        )
        for name, data in sorted(dir_stats.items(), key=lambda x: x[1]["file_count"], reverse=True)
    ]

    return RepositoryOverviewResponse(
        repository_id=repo.id,
        name=repo.name,
        owner=repo.owner,
        url=repo.url,
        default_branch=repo.default_branch,
        status=repo.status,
        total_files=repo.total_files or len(files_data),
        total_lines=repo.total_lines or sum(f.get("line_count", 0) for f in files_data),
        total_directories=len(unique_dirs) or len(root_directories),
        languages=repo.languages or {},
        language_percentages=lang_percentages,
        frameworks=[FrameworkResponse(**fw) for fw in frameworks],
        dependencies_count=len(deps),
        dependencies=[DependencyResponse.model_validate(d) for d in deps],
        entities_count=len(entities),
        entity_counts_by_type=dict(entity_counts),
        root_directories=root_directories,
        manifest_files=manifest_files,
        key_entrypoints=key_entrypoints
    )

async def _build_graph(repository_id: str, db: AsyncSession) -> tuple:
    """Helper: fetch files, entities, deps and build RepositoryGraph."""
    from sqlalchemy.future import select as sa_select
    result = await db.execute(sa_select(Repository).where(Repository.id == repository_id))
    repo = result.scalars().first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    files_res = await db.execute(sa_select(RepositoryFile).where(RepositoryFile.repository_id == repository_id))
    files = [
        {"id": f.id, "path": f.path, "filename": f.filename, "language": f.language, "line_count": f.line_count}
        for f in files_res.scalars().all()
    ]

    entities_res = await db.execute(sa_select(CodeEntity).where(CodeEntity.repository_id == repository_id))
    entities = [
        {
            "id": e.id, "name": e.name, "entity_type": e.entity_type,
            "file_path": e.file_path, "start_line": e.start_line,
            "end_line": e.end_line, "signature": e.signature, "calls": e.calls or [],
        }
        for e in entities_res.scalars().all()
    ]

    deps_res = await db.execute(sa_select(Dependency).where(Dependency.repository_id == repository_id))
    deps = [
        {"id": d.id, "name": d.name, "version": d.version, "ecosystem": d.ecosystem, "source_file": d.source_file}
        for d in deps_res.scalars().all()
    ]

    graph = RepositoryGraph()
    graph.build_from_metadata(files, entities, deps)
    return repo, graph


@router.get("/architecture", response_model=DiagramResponse)
async def get_repository_architecture_diagram(
    repository_id: str,
    view_mode: str = Query("code", pattern="^(code|workflow)$"),
    workflow_description: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    repo, graph = await _build_graph(repository_id, db)
    return graph.generate_diagram(
        "architecture",
        view_mode=view_mode,
        repo_name=repo.name,
        workflow_description=workflow_description
    )


@router.get("/diagrams/sequence", response_model=DiagramResponse)
async def get_sequence_diagram(
    repository_id: str,
    view_mode: str = Query("code", pattern="^(code|workflow)$"),
    workflow_description: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    repo, graph = await _build_graph(repository_id, db)
    return graph.generate_diagram(
        "sequence",
        view_mode=view_mode,
        repo_name=repo.name,
        workflow_description=workflow_description
    )


@router.get("/diagrams/flowchart", response_model=DiagramResponse)
async def get_flowchart_diagram(
    repository_id: str,
    view_mode: str = Query("code", pattern="^(code|workflow)$"),
    workflow_description: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    repo, graph = await _build_graph(repository_id, db)
    return graph.generate_diagram(
        "flowchart",
        view_mode=view_mode,
        repo_name=repo.name,
        workflow_description=workflow_description
    )


@router.get("/diagrams/uml", response_model=DiagramResponse)
async def get_uml_diagram(
    repository_id: str,
    view_mode: str = Query("code", pattern="^(code|workflow)$"),
    workflow_description: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    repo, graph = await _build_graph(repository_id, db)
    return graph.generate_diagram(
        "uml",
        view_mode=view_mode,
        repo_name=repo.name,
        workflow_description=workflow_description
    )


@router.get("/diagrams/dependency", response_model=DiagramResponse)
async def get_dependency_diagram(
    repository_id: str,
    view_mode: str = Query("code", pattern="^(code|workflow)$"),
    workflow_description: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    repo, graph = await _build_graph(repository_id, db)
    return graph.generate_diagram(
        "dependency",
        view_mode=view_mode,
        repo_name=repo.name,
        workflow_description=workflow_description
    )


@router.get("/diagrams/er", response_model=DiagramResponse)
async def get_er_diagram(
    repository_id: str,
    view_mode: str = Query("code", pattern="^(code|workflow)$"),
    workflow_description: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    repo, graph = await _build_graph(repository_id, db)
    return graph.generate_diagram(
        "er",
        view_mode=view_mode,
        repo_name=repo.name,
        workflow_description=workflow_description
    )


@router.get("/diagrams/usecase", response_model=DiagramResponse)
async def get_usecase_diagram(
    repository_id: str,
    view_mode: str = Query("code", pattern="^(code|workflow)$"),
    workflow_description: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    repo, graph = await _build_graph(repository_id, db)
    return graph.generate_diagram(
        "usecase",
        view_mode=view_mode,
        repo_name=repo.name,
        workflow_description=workflow_description
    )


@router.get("/diagrams/state", response_model=DiagramResponse)
async def get_state_diagram(
    repository_id: str,
    view_mode: str = Query("code", pattern="^(code|workflow)$"),
    workflow_description: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    repo, graph = await _build_graph(repository_id, db)
    return graph.generate_diagram(
        "state",
        view_mode=view_mode,
        repo_name=repo.name,
        workflow_description=workflow_description
    )


@router.get("/diagrams/dfd", response_model=DiagramResponse)
async def get_dfd_diagram(
    repository_id: str,
    view_mode: str = Query("code", pattern="^(code|workflow)$"),
    workflow_description: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    repo, graph = await _build_graph(repository_id, db)
    return graph.generate_diagram(
        "dfd",
        view_mode=view_mode,
        repo_name=repo.name,
        workflow_description=workflow_description
    )


@router.get("/diagrams/callflow", response_model=DiagramResponse)
async def get_callflow_diagram(
    repository_id: str,
    view_mode: str = Query("code", pattern="^(code|workflow)$"),
    workflow_description: Optional[str] = Query(None),
    function_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    repo, graph = await _build_graph(repository_id, db)
    cg = await _get_call_graph_for_repo(repo, db)
    if cg and cg.functions:
        root_id = function_id if (function_id and function_id in cg.functions) else None
        root, nodes, edges = cg.traverse(root_id, mode="calls_from", depth=2)
        svc = get_call_graph_service()
        mermaid = svc.generate_mermaid(root, nodes, edges, "calls_from")
        explanation = svc.generate_explanation(root, nodes, edges, "calls_from")
        nodes_evidence = [
            {
                "id": n.id,
                "label": f"{n.enclosing_class}.{n.name}()" if n.enclosing_class else f"{n.name}()",
                "evidence_type": "function",
                "source_file": n.file_path,
                "line_range": f"{n.start_line}-{n.end_line}",
                "confidence": "verified",
                "details": f"Signature: {n.name}({', '.join([p.name for p in n.parameters])}), {len(n.outgoing_calls)} calls, {len(n.incoming_callers)} callers."
            }
            for n in nodes
        ]
        return DiagramResponse(
            diagram_type="callflow",
            view_mode=view_mode,
            mermaid_code=mermaid,
            description=explanation["summary"],
            summary=explanation["control_flow_narrative"],
            components_involved=explanation["components_involved"],
            key_relationships=[f"{e.caller_name} -> {e.callee_raw_name} (L{e.call_site_line})" for e in edges[:15]],
            source_references=[f"{n.file_path}:L{n.start_line}-L{n.end_line}" for n in nodes[:15]],
            evidence_status="verified",
            evidence_limitations=explanation["static_limitations"],
            nodes_evidence=nodes_evidence
        )

    return graph.generate_diagram(
        "callflow",
        view_mode=view_mode,
        repo_name=repo.name,
        workflow_description=workflow_description
    )


@router.get("/call-graph/functions", response_model=List[CallGraphFunctionSummary])
@router.get("/functions", response_model=List[CallGraphFunctionSummary])
async def list_call_graph_functions(
    repository_id: str,
    search: Optional[str] = Query(None),
    file_path: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    repo, _ = await _build_graph(repository_id, db)
    cg = await _get_call_graph_for_repo(repo, db)

    results: List[CallGraphFunctionSummary] = []
    if cg and cg.functions:
        for fn in cg.functions.values():
            if file_path and fn.file_path != file_path and not fn.file_path.endswith(file_path):
                continue
            if search:
                s = search.lower()
                if s not in fn.name.lower() and s not in fn.file_path.lower() and s not in (fn.enclosing_class or "").lower():
                    continue
            results.append(
                CallGraphFunctionSummary(
                    id=fn.id,
                    name=fn.name,
                    full_name=fn.full_name,
                    file_path=fn.file_path,
                    start_line=fn.start_line,
                    end_line=fn.end_line,
                    enclosing_class=fn.enclosing_class,
                    signature=f"{fn.name}({', '.join([p.name for p in fn.parameters])})",
                    caller_count=len(fn.incoming_callers),
                    callee_count=len(fn.outgoing_calls),
                    is_async=fn.is_async
                )
            )

    results.sort(key=lambda x: (x.callee_count + x.caller_count), reverse=True)
    return results[:limit]


@router.get("/call-graph", response_model=CallGraphResponse)
async def get_call_graph_endpoint(
    repository_id: str,
    function_id: Optional[str] = Query(None),
    mode: str = Query("calls_from", pattern="^(calls_from|called_by|full)$"),
    depth: int = Query(2, ge=1, le=5),
    db: AsyncSession = Depends(get_db)
):
    repo, _ = await _build_graph(repository_id, db)
    cg = await _get_call_graph_for_repo(repo, db)

    if not cg or not cg.functions:
        raise HTTPException(status_code=404, detail="No code functions found in repository.")

    root_id = function_id
    if not root_id or root_id not in cg.functions:
        top_fn = max(cg.functions.values(), key=lambda f: len(f.outgoing_calls) + len(f.incoming_callers))
        root_id = top_fn.id

    root, nodes, edges = cg.traverse(root_id, mode=mode, depth=depth)
    svc = get_call_graph_service()
    mermaid_code = svc.generate_mermaid(root, nodes, edges, mode)
    explanation = svc.generate_explanation(root, nodes, edges, mode)

    node_items = [
        CallGraphNodeItem(
            id=n.id,
            name=n.name,
            full_name=n.full_name,
            file_path=n.file_path,
            start_line=n.start_line,
            end_line=n.end_line,
            enclosing_class=n.enclosing_class,
            enclosing_module=n.enclosing_module,
            parameters=[p.to_dict() for p in n.parameters],
            is_async=n.is_async,
            docstring=n.docstring,
            decorators=n.decorators,
            language=n.language,
            caller_count=len(n.incoming_callers),
            callee_count=len(n.outgoing_calls)
        )
        for n in nodes
    ]

    edge_items = [
        CallGraphEdgeItem(
            caller_id=e.caller_id,
            caller_name=e.caller_name,
            callee_raw_name=e.callee_raw_name,
            callee_symbol_name=e.callee_symbol_name,
            callee_id=e.callee_id,
            call_site_line=e.call_site_line,
            lexical_order=e.lexical_order,
            source_file=e.source_file,
            target_file=e.target_file,
            is_conditional=e.is_conditional,
            branch_condition=e.branch_condition,
            is_loop=e.is_loop,
            is_exception=e.is_exception,
            is_async=e.is_async,
            is_recursive=e.is_recursive,
            is_dynamic=e.is_dynamic,
            is_external=e.is_external,
            is_resolved=e.is_resolved
        )
        for e in edges
    ]

    stats = {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "external_calls": sum(1 for e in edges if e.is_external),
        "conditional_calls": sum(1 for e in edges if e.is_conditional),
        "async_calls": sum(1 for e in edges if e.is_async),
        "loop_calls": sum(1 for e in edges if e.is_loop)
    }

    return CallGraphResponse(
        repository_id=repository_id,
        root_function_id=root.id,
        root_function_name=root.full_name,
        mode=mode,
        depth=depth,
        mermaid_code=mermaid_code,
        nodes=node_items,
        edges=edge_items,
        explanation=explanation,
        stats=stats
    )


@router.get("/call-graph/functions/{function_id:path}/callers", response_model=List[CallGraphEdgeItem])
async def get_function_callers(
    repository_id: str,
    function_id: str,
    db: AsyncSession = Depends(get_db)
):
    repo, _ = await _build_graph(repository_id, db)
    cg = await _get_call_graph_for_repo(repo, db)
    if not cg or function_id not in cg.functions:
        raise HTTPException(status_code=404, detail="Function not found in repository call graph")
    fn = cg.functions[function_id]
    return [
        CallGraphEdgeItem(
            caller_id=e.caller_id,
            caller_name=e.caller_name,
            callee_raw_name=e.callee_raw_name,
            callee_symbol_name=e.callee_symbol_name,
            callee_id=e.callee_id,
            call_site_line=e.call_site_line,
            lexical_order=e.lexical_order,
            source_file=e.source_file,
            target_file=e.target_file,
            is_conditional=e.is_conditional,
            branch_condition=e.branch_condition,
            is_loop=e.is_loop,
            is_exception=e.is_exception,
            is_async=e.is_async,
            is_recursive=e.is_recursive,
            is_dynamic=e.is_dynamic,
            is_external=e.is_external,
            is_resolved=e.is_resolved
        )
        for e in fn.incoming_callers
    ]


@router.get("/call-graph/functions/{function_id:path}/calls", response_model=List[CallGraphEdgeItem])
async def get_function_outgoing_calls(
    repository_id: str,
    function_id: str,
    db: AsyncSession = Depends(get_db)
):
    repo, _ = await _build_graph(repository_id, db)
    cg = await _get_call_graph_for_repo(repo, db)
    if not cg or function_id not in cg.functions:
        raise HTTPException(status_code=404, detail="Function not found in repository call graph")
    fn = cg.functions[function_id]
    return [
        CallGraphEdgeItem(
            caller_id=e.caller_id,
            caller_name=e.caller_name,
            callee_raw_name=e.callee_raw_name,
            callee_symbol_name=e.callee_symbol_name,
            callee_id=e.callee_id,
            call_site_line=e.call_site_line,
            lexical_order=e.lexical_order,
            source_file=e.source_file,
            target_file=e.target_file,
            is_conditional=e.is_conditional,
            branch_condition=e.branch_condition,
            is_loop=e.is_loop,
            is_exception=e.is_exception,
            is_async=e.is_async,
            is_recursive=e.is_recursive,
            is_dynamic=e.is_dynamic,
            is_external=e.is_external,
            is_resolved=e.is_resolved
        )
        for e in fn.outgoing_calls
    ]


@router.get("/call-graph/functions/{function_id:path}", response_model=CallGraphNodeItem)
async def get_function_details(
    repository_id: str,
    function_id: str,
    db: AsyncSession = Depends(get_db)
):
    repo, _ = await _build_graph(repository_id, db)
    cg = await _get_call_graph_for_repo(repo, db)
    if not cg or function_id not in cg.functions:
        raise HTTPException(status_code=404, detail="Function not found in repository call graph")
    fn = cg.functions[function_id]
    return CallGraphNodeItem(
        id=fn.id,
        name=fn.name,
        full_name=fn.full_name,
        file_path=fn.file_path,
        start_line=fn.start_line,
        end_line=fn.end_line,
        enclosing_class=fn.enclosing_class,
        enclosing_module=fn.enclosing_module,
        parameters=[p.to_dict() for p in fn.parameters],
        is_async=fn.is_async,
        docstring=fn.docstring,
        decorators=fn.decorators,
        language=fn.language,
        caller_count=len(fn.incoming_callers),
        callee_count=len(fn.outgoing_calls)
    )


@router.post("/call-graph/refresh")
async def refresh_call_graph_endpoint(
    repository_id: str,
    db: AsyncSession = Depends(get_db)
):
    repo, _ = await _build_graph(repository_id, db)
    invalidate_repository_call_graph(repository_id)
    cg = await _get_call_graph_for_repo(repo, db)
    return {
        "status": "refreshed",
        "repository_id": repository_id,
        "function_count": len(cg.functions) if cg else 0
    }


def _resolve_repo_path(repo: Repository) -> Optional[Path]:
    if repo.local_path:
        p = Path(repo.local_path)
        if p.exists():
            return p
        p2 = Path("backend") / repo.local_path
        if p2.exists():
            return p2
        for base in ["backend/cloned_repos", "backend/workspaces", "cloned_repos", "workspaces"]:
            p3 = Path(base) / repo.id
            if p3.exists():
                return p3
    return None


async def _get_call_graph_for_repo(repo: Repository, db: AsyncSession):
    repo_path = _resolve_repo_path(repo)
    cg = None
    if repo_path and repo_path.exists():
        cg = get_or_build_repository_call_graph(repo.id, repo_path)
    if not cg or not cg.functions:
        entities_res = await db.execute(select(CodeEntity).where(CodeEntity.repository_id == repo.id))
        entities = [
            {
                "id": e.id, "name": e.name, "entity_type": e.entity_type,
                "file_path": e.file_path, "start_line": e.start_line,
                "end_line": e.end_line, "signature": e.signature, "calls": e.calls or [],
            }
            for e in entities_res.scalars().all()
        ]
        cg = get_or_build_repository_call_graph(repo.id, repo_path or Path("."))
        if entities:
            cg.populate_from_entities(entities)
    return cg


@router.get("/diagrams/{diagram_type}", response_model=DiagramResponse)
async def get_generic_diagram(
    repository_id: str,
    diagram_type: str,
    view_mode: str = Query("code", pattern="^(code|workflow)$"),
    workflow_description: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    if diagram_type in ("callflow", "callgraph", "call_graph"):
        return await get_callflow_diagram(
            repository_id=repository_id,
            view_mode=view_mode,
            workflow_description=workflow_description,
            db=db
        )
    repo, graph = await _build_graph(repository_id, db)
    return graph.generate_diagram(
        diagram_type,
        view_mode=view_mode,
        repo_name=repo.name,
        workflow_description=workflow_description
    )

