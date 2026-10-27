import pytest
import tempfile
from pathlib import Path
from app.agents.state import AgentState
from app.agents.code_agent import CodeGenerationAgent
from app.agents.test_agent import TestGenerationAgent
from app.agents.validation_agent import ValidationAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.tools import AgentTools

def test_parse_llm_code_files_multi_file():
    llm_output = """
Here is the code:

# file: src/services/calculator.py
```python
class Calculator:
    def add(self, a, b):
        return a + b
```

// file: src/utils/formatter.ts
```typescript
export function formatValue(val: number): string {
    return val.toFixed(2);
}
```
"""
    files = AgentTools.parse_llm_code_files(llm_output)
    assert len(files) == 2
    assert files[0]["file_path"] == "src/services/calculator.py"
    assert "class Calculator" in files[0]["code"]
    assert files[1]["file_path"] == "src/utils/formatter.ts"
    assert "export function formatValue" in files[1]["code"]

@pytest.mark.asyncio
async def test_code_and_test_agents_custom_requirement():
    with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as ws_dir:
        state = AgentState(
            task_id="test-custom-1",
            repository_id="test-repo-custom",
            repository_path=str(repo_dir),
            workspace_path=str(ws_dir),
            user_requirement="Create a DataProcessor class with clean methods for transform and summarize",
            workflow_type="multi_agent"
        )

        code_agent = CodeGenerationAgent()
        code_res = await code_agent.execute(state)
        assert code_res["status"] == "success"
        assert len(state.proposed_changes) >= 1

        test_agent = TestGenerationAgent()
        test_res = await test_agent.execute(state)
        assert test_res["status"] == "success"
        assert len(state.generated_tests) >= 1

        val_agent = ValidationAgent()
        val_res = await val_agent.execute(state)
        assert val_res["syntax_passed"] is True
        assert val_res["tests_passed"] is True
        assert val_res["status"] == "passed"

@pytest.mark.asyncio
async def test_orchestrator_custom_non_auth_requirement():
    orchestrator = OrchestratorAgent()

    with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as ws_dir:
        state = AgentState(
            task_id="test-custom-2",
            repository_id="test-repo-custom2",
            repository_path=str(repo_dir),
            workspace_path=str(ws_dir),
            user_requirement="Build a metrics collector service",
            workflow_type="multi_agent"
        )

        final_state = await orchestrator.execute_task_workflow(state)
        assert final_state.status == "waiting_approval"
        assert final_state.validation_results["status"] == "passed"
        assert len(final_state.proposed_changes) >= 2
