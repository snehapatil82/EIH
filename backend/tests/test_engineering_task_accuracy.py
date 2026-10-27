import pytest
import asyncio
from pathlib import Path
from app.agents.state import AgentState
from app.agents.orchestrator import OrchestratorAgent
from app.agents.code_agent import CodeGenerationAgent
from app.agents.test_agent import TestGenerationAgent
from app.agents.diagram_agent import DiagramAgent
from app.agents.documentation_agent import DocumentationAgent
from app.agents.validation_agent import ValidationAgent
from app.repository.workspace_manager import WorkspaceManager

@pytest.mark.asyncio
async def test_user_registration_task_accuracy(tmp_path):
    """
    Verifies that when given a user registration requirement:
    1. CodeGenerationAgent creates password hashing and user registration services
    2. TestGenerationAgent creates passing unit tests for registration and auth
    3. DiagramAgent creates sequence and architecture diagrams matching user registration
    4. DocumentationAgent creates user registration API documentation
    5. ValidationAgent validates syntax and executes the sandbox tests successfully
    """
    ws_manager = WorkspaceManager(workspaces_base_dir=tmp_path)
    state = AgentState(
        task_id="test-accuracy-task-1",
        repository_id="test-repo-1",
        repository_path=str(tmp_path),
        workspace_path=str(tmp_path),
        user_requirement="Create user registration API endpoint with password hashing.",
        workflow_type="multi_agent"
    )

    # 1. Code Generation
    code_agent = CodeGenerationAgent()
    code_res = await code_agent.execute(state)
    assert code_res["status"] == "success"
    assert len(state.proposed_changes) >= 2
    
    file_paths = [c["file_path"] for c in state.proposed_changes]
    assert any("auth_service" in f for f in file_paths)
    assert any("user_service" in f for f in file_paths)

    # Verify password hashing in auth_service
    auth_change = next(c for c in state.proposed_changes if "auth_service" in c["file_path"])
    assert "hash_password" in auth_change["modified_content"]
    assert "verify_password" in auth_change["modified_content"]
    assert "create_access_token" in auth_change["modified_content"]

    # Verify user registration logic in user_service
    user_change = next(c for c in state.proposed_changes if "user_service" in c["file_path"])
    assert "register_user" in user_change["modified_content"]
    assert "login_user" in user_change["modified_content"]
    assert "already exists" in user_change["modified_content"]

    # 2. Test Generation
    test_agent = TestGenerationAgent()
    test_res = await test_agent.execute(state)
    assert test_res["status"] == "success"
    assert len(state.generated_tests) >= 1
    test_change = state.generated_tests[0]
    assert "test_password_hashing_and_verification" in test_change["modified_content"]
    assert "test_user_registration_flow" in test_change["modified_content"]
    assert "test_registration_duplicate_email_fails" in test_change["modified_content"]

    # 3. Diagram Generation
    diagram_agent = DiagramAgent()
    diag_res = await diagram_agent.execute(state)
    assert diag_res["status"] == "success"
    assert len(state.diagrams) >= 2
    types = [d["type"] for d in state.diagrams]
    assert "sequence" in types
    assert "architecture" in types
    seq_diag = next(d for d in state.diagrams if d["type"] == "sequence")
    assert "register" in seq_diag["mermaid_code"]

    # 4. Documentation Generation
    doc_agent = DocumentationAgent()
    doc_res = await doc_agent.execute(state)
    assert doc_res["status"] == "success"
    doc_change = state.generated_documentation[0]
    assert "User Registration" in doc_change["modified_content"]
    assert "register_user" in doc_change["modified_content"]

    # 5. Validation Agent
    val_agent = ValidationAgent()
    val_res = await val_agent.execute(state)
    assert val_res["status"] == "passed"
    assert val_res["syntax_passed"] is True
    assert val_res["tests_passed"] is True


@pytest.mark.asyncio
async def test_full_orchestrator_execution_with_progress_callback(tmp_path):
    """
    Verifies that the orchestrator executes the full multi-agent workflow
    and triggers the real-time progress callback at each stage.
    """
    ws_manager = WorkspaceManager(workspaces_base_dir=tmp_path)
    state = AgentState(
        task_id="test-accuracy-task-2",
        repository_id="test-repo-2",
        repository_path=str(tmp_path),
        workspace_path=str(tmp_path),
        user_requirement="Create user registration API endpoint with password hashing.",
        workflow_type="multi_agent"
    )

    logged_stages = []

    async def mock_callback(current_state, agent_name, level, message):
        logged_stages.append((agent_name, level))

    orchestrator = OrchestratorAgent()
    result_state = await orchestrator.execute_task_workflow(state, progress_callback=mock_callback)

    assert result_state.status == "waiting_approval"
    assert len(result_state.proposed_changes) >= 3 # auth, user_service, doc, test
    assert len(result_state.diagrams) >= 2
    assert len(logged_stages) >= 8

    agent_names_logged = {agent for agent, _ in logged_stages}
    assert "requirement_agent" in agent_names_logged
    assert "code_agent" in agent_names_logged
    assert "test_agent" in agent_names_logged
    assert "validation_agent" in agent_names_logged
    assert "review_agent" in agent_names_logged
