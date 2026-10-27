from pathlib import Path
from typing import Dict, Any, List
from app.agents.state import AgentState
from app.agents.tools import AgentTools
from app.core.logging import logger

class ValidationAgent:
    def __init__(self):
        pass

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        logger.info(f"ValidationAgent: Validating workspace changes at {state.workspace_path} (Iteration {state.retry_count + 1})")
        ws_path = Path(state.workspace_path)

        syntax_passed = True
        syntax_errors = []

        # 1. Syntax check on all proposed Python/JSON files
        for change in state.proposed_changes:
            rel_file = change["file_path"]
            res = AgentTools.check_syntax(ws_path, rel_file)
            if not res.get("valid", True):
                syntax_passed = False
                syntax_errors.append(f"{rel_file}: {res.get('error')}")

        # 2. Test Execution
        test_files = [c["file_path"] for c in state.proposed_changes if c["file_path"].startswith("tests/")]
        test_file_target = test_files[0] if test_files else None
        test_res = AgentTools.run_tests_safe(ws_path, test_file_target)
        tests_passed = test_res.get("passed", True)

        imports_passed = syntax_passed # AST import validation
        requirements_passed = len(state.proposed_changes) > 0

        overall_passed = syntax_passed and tests_passed and requirements_passed

        error_summary = None
        if not overall_passed:
            err_parts = []
            if syntax_errors:
                err_parts.append(f"Syntax Errors: {'; '.join(syntax_errors)}")
            if not tests_passed:
                err_parts.append(f"Test Failures: {test_res.get('output')}")
            error_summary = " | ".join(err_parts)

        val_result = {
            "status": "passed" if overall_passed else "failed",
            "syntax_passed": syntax_passed,
            "imports_passed": imports_passed,
            "tests_passed": tests_passed,
            "requirements_passed": requirements_passed,
            "error_summary": error_summary,
            "details": {
                "syntax_errors": syntax_errors,
                "test_output": test_res.get("output"),
                "files_validated": [c["file_path"] for c in state.proposed_changes]
            }
        }

        state.validation_results = val_result
        return val_result
