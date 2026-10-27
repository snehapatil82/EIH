import pytest
import tempfile
from pathlib import Path
from app.agents.state import AgentState
from app.agents.orchestrator import OrchestratorAgent
from app.agents.tools import AgentTools

def test_orchestrator_complexity_classification():
    orchestrator = OrchestratorAgent()
    assert orchestrator.classify_complexity("Explain how authentication works") == "SIMPLE"
    assert orchestrator.classify_complexity("Generate tests for auth") == "MEDIUM"
    assert orchestrator.classify_complexity("Add JWT authentication, create tests and update documentation") == "COMPLEX"

@pytest.mark.asyncio
async def test_agent_orchestrator_full_workflow():
    orchestrator = OrchestratorAgent()
    
    with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as ws_dir:
        # Create minimal repository structure
        r_path = Path(repo_dir)
        (r_path / "main.py").write_text("def run(): pass\n", encoding="utf-8")
        
        state = AgentState(
            task_id="test-task-1",
            repository_id="test-repo-1",
            repository_path=str(repo_dir),
            workspace_path=str(ws_dir),
            user_requirement="Add JWT authentication and generate tests",
            workflow_type="multi_agent"
        )

        final_state = await orchestrator.execute_task_workflow(state)
        
        assert final_state.status == "waiting_approval"
        assert len(final_state.task_plan) > 0
        assert len(final_state.proposed_changes) >= 2 # code + test + doc
        assert len(final_state.diagrams) > 0
        assert final_state.validation_results["status"] == "passed"
        assert final_state.review_results["quality_score"] > 80
