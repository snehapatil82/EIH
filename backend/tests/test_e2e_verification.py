import pytest
import tempfile
import uuid
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database.connection import init_db
from app.models.repository import Repository
from app.models.task import EngineeringTask
from app.agents.state import AgentState
from app.agents.orchestrator import OrchestratorAgent
from app.repository.workspace_manager import WorkspaceManager

@pytest.mark.asyncio
async def test_full_end_to_end_platform_lifecycle():
    await init_db()

    with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as ws_tmp:
        repo_dir = Path(repo_tmp)
        # 1. Create realistic sample repository
        (repo_dir / "src").mkdir()
        (repo_dir / "src" / "main.py").write_text(
            'from fastapi import FastAPI\napp = FastAPI()\n\n@app.get("/")\ndef root(): return {"message": "hello"}\n',
            encoding="utf-8"
        )
        (repo_dir / "requirements.txt").write_text("fastapi>=0.100.0\nuvicorn>=0.20.0\n", encoding="utf-8")
        (repo_dir / "README.md").write_text("# Core Sample API\n\nFastAPI backend service.\n", encoding="utf-8")

        # 2. Test RAG Q&A through API transport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Connect local repo as mock or through service
            from app.api.v1.repositories import index_repository_internal
            from app.repository.file_scanner import FileScanner
            from app.database.connection import AsyncSessionLocal
            
            scanner = FileScanner()
            files_data, lang_stats, total_f, total_l = scanner.scan_repository(repo_dir)

            repo_id = f"test-e2e-repo-{uuid.uuid4()}"
            repo_url = f"https://github.com/testorg/core-api-{uuid.uuid4()}"
            async with AsyncSessionLocal() as db:
                repo_obj = Repository(
                    id=repo_id,
                    name="core-api",
                    owner="testorg",
                    url=repo_url,
                    local_path=str(repo_dir),
                    default_branch="main",
                    status="indexed",
                    languages=lang_stats,
                    total_files=total_f,
                    total_lines=total_l
                )
                db.add(repo_obj)
                await db.commit()
                await index_repository_internal(repo_id, repo_dir, files_data, db)

            try:
                # 3. Test Grounded RAG Ask Endpoint
                chat_resp = await client.post(
                    f"/api/v1/repositories/{repo_id}/ask",
                    json={"question": "Explain the architecture of this project"}
                )
                assert chat_resp.status_code == 200
                chat_data = chat_resp.json()
                assert "answer" in chat_data
                assert len(chat_data["citations"]) > 0
                assert "src/main.py" in chat_data["citations"][0]["file_path"] or "README.md" in chat_data["citations"][0]["file_path"]

                # 4. Test Autonomous Multi-Agent Engineering Task
                ws_manager = WorkspaceManager()
                task_ws = ws_manager.create_task_workspace("task-e2e-1", repo_dir)

                state = AgentState(
                    task_id="task-e2e-1",
                    repository_id=repo_id,
                    repository_path=str(repo_dir),
                    workspace_path=str(task_ws),
                    user_requirement="Add JWT authentication and generate tests",
                    workflow_type="multi_agent"
                )

                orchestrator = OrchestratorAgent()
                final_state = await orchestrator.execute_task_workflow(state)

                assert final_state.status == "waiting_approval"
                assert final_state.complexity == "COMPLEX"
                assert len(final_state.proposed_changes) >= 2 # auth_service + test_auth + doc
                assert len(final_state.diagrams) >= 1 # Sequence and architecture diagrams
                assert final_state.validation_results["status"] == "passed"
                assert final_state.review_results["status"] == "approved"

                # 5. Test Human-in-the-Loop Change Application
                applied_count = ws_manager.apply_workspace_to_repository(task_ws, repo_dir)
                assert applied_count >= 2
                assert (repo_dir / "auth_service.py").exists() or (repo_dir / "src" / "auth" / "auth_service.py").exists() or (repo_dir / "tests" / "test_auth.py").exists()
            finally:
                async with AsyncSessionLocal() as db_cleanup:
                    from sqlalchemy import delete
                    from app.models.repository import RepositoryFile, CodeEntity, Dependency
                    await db_cleanup.execute(delete(CodeEntity).where(CodeEntity.repository_id == repo_id))
                    await db_cleanup.execute(delete(Dependency).where(Dependency.repository_id == repo_id))
                    await db_cleanup.execute(delete(RepositoryFile).where(RepositoryFile.repository_id == repo_id))
                    await db_cleanup.execute(delete(Repository).where(Repository.id == repo_id))
                    await db_cleanup.commit()
