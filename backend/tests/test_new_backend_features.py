import pytest
import uuid
from pathlib import Path
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.provider import get_llm_provider
from app.models.changes import TaskDiagram
from app.agents.state import AgentState
from app.agents.orchestrator import OrchestratorAgent

@pytest.mark.asyncio
async def test_anthropic_provider_initialization():
    provider = AnthropicProvider(api_key="test-key")
    assert provider.api_key == "test-key"
    assert "messages" in provider.base_url or "api.anthropic.com" in provider.base_url

@pytest.mark.asyncio
async def test_diagram_agent_and_orchestrator_diagrams(tmp_path):
    orchestrator = OrchestratorAgent()
    
    # Create mock repo
    repo_dir = tmp_path / "mock_repo"
    repo_dir.mkdir()
    (repo_dir / "main.py").write_text("def hello(): return 'world'")

    state = AgentState(
        task_id=str(uuid.uuid4()),
        repository_id="repo-test",
        repository_path=str(repo_dir),
        workspace_path=str(repo_dir),
        user_requirement="Implement JWT login and token authentication"
    )

    completed_state = await orchestrator.execute_task_workflow(state)
    assert len(completed_state.diagrams) >= 1
    assert any(d.get("type") in ["sequence", "architecture"] for d in completed_state.diagrams)
