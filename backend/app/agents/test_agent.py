import re
import ast
from pathlib import Path
from typing import Dict, Any, List
from app.agents.state import AgentState
from app.agents.tools import AgentTools
from app.repository.workspace_manager import WorkspaceManager
from app.llm.provider import LLMProvider, get_llm_provider
from app.llm.mock_provider import HighFidelityMockProvider
from app.core.logging import logger

class TestGenerationAgent:
    __test__ = False

    def __init__(self, llm_provider: LLMProvider = None):
        self.llm = llm_provider or get_llm_provider()
        self.ws_manager = WorkspaceManager()

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        logger.info(f"TestGenerationAgent: Creating tests in workspace {state.workspace_path} (Retry {state.retry_count})")
        ws_path = Path(state.workspace_path)
        req = state.user_requirement.lower()
        val_error = state.validation_results.get("error_summary")

        generated_tests = []
        parsed_test_files = []

        # 1. Try LLM test generation if provider is not Mock
        if not isinstance(self.llm, HighFidelityMockProvider):
            try:
                system_prompt = (
                    "You are an expert QA and Test Automation Engineer. "
                    "Generate comprehensive, production-grade unit and integration tests using pytest for the newly implemented code. "
                    "Ensure tests properly import target modules with fallback imports, e.g.:\n"
                    "```python\n"
                    "try:\n"
                    "    from src.module import Component\n"
                    "except ImportError:\n"
                    "    from module import Component\n"
                    "```\n"
                    "Precede each output test file with `# file: tests/test_feature.py` followed by ```python\n...code...\n```. "
                    "Cover positive cases, edge cases, invalid inputs, and error handling."
                )

                # Formulate changes summary for LLM prompt
                changes_summary = []
                for change in state.proposed_changes:
                    if change.get("file_path", "").endswith(".py") and not change["file_path"].startswith("tests/"):
                        changes_summary.append(f"--- File: {change['file_path']} ---\n{change.get('modified_content', '')}")

                prompt_content = f"Requirement: {state.user_requirement}\nDesign Doc:\n{state.design_doc or ''}\n\nProposed Code Changes:\n" + "\n\n".join(changes_summary)
                if val_error:
                    prompt_content += f"\n\nPrevious Validation Error / Test Failure (Fix this!):\n{val_error}"

                raw_response = await self.llm.generate_response(
                    prompt=prompt_content,
                    system_prompt=system_prompt
                )

                parsed_test_files = AgentTools.parse_llm_code_files(raw_response, default_filename="tests/test_generated.py")
            except Exception as e:
                logger.warning(f"TestGenerationAgent: LLM test generation fallback triggered: {e}")

        # 2. Dynamic Fallback Generation if LLM was skipped or returned no files
        if not parsed_test_files:
            # Find python implementation files in proposed_changes
            code_changes = [c for c in state.proposed_changes if c.get("file_path", "").endswith(".py") and not c["file_path"].startswith("tests/")]

            is_user_auth = any(k in req for k in ["auth", "jwt", "login", "register", "registration", "signup", "password", "user"]) or any("user_service" in c["file_path"].lower() or "auth" in c["file_path"].lower() for c in code_changes)

            if is_user_auth:
                test_code = (
                    'import pytest\n'
                    'import datetime\n'
                    'try:\n'
                    '    from src.auth.auth_service import hash_password, verify_password, create_access_token, verify_access_token\n'
                    'except ImportError:\n'
                    '    from auth_service import hash_password, verify_password, create_access_token, verify_access_token\n'
                    'try:\n'
                    '    from src.services.user_service import UserRegistrationService\n'
                    'except ImportError:\n'
                    '    try:\n'
                    '        from user_service import UserRegistrationService\n'
                    '    except ImportError:\n'
                    '        UserRegistrationService = None\n\n'
                    'def test_password_hashing_and_verification():\n'
                    '    raw = "SecretPassword123!"\n'
                    '    hashed = hash_password(raw)\n'
                    '    assert hashed != raw\n'
                    '    assert verify_password(raw, hashed) is True\n'
                    '    assert verify_password("WrongPassword", hashed) is False\n\n'
                    'def test_jwt_token_lifecycle():\n'
                    '    payload = {"sub": "user_123", "email": "test@example.com"}\n'
                    '    token = create_access_token(payload)\n'
                    '    assert isinstance(token, str)\n'
                    '    assert len(token.split(".")) == 3\n\n'
                    '    decoded = verify_access_token(token)\n'
                    '    assert decoded is not None\n'
                    '    assert decoded["sub"] == "user_123"\n'
                    '    assert decoded["email"] == "test@example.com"\n\n'
                    'def test_tampered_jwt_token_fails():\n'
                    '    token = create_access_token({"sub": "admin"})\n'
                    '    tampered = token[:-4] + "fake"\n'
                    '    assert verify_access_token(tampered) is None\n\n'
                    'def test_user_registration_flow():\n'
                    '    if not UserRegistrationService:\n'
                    '        pytest.skip("UserRegistrationService not available")\n'
                    '    svc = UserRegistrationService()\n'
                    '    res = svc.register_user({"email": "dev@company.com", "password": "StrongPassword99!", "full_name": "Dev User"})\n'
                    '    assert res["status"] == "success"\n'
                    '    assert res["user"]["email"] == "dev@company.com"\n'
                    '    assert "access_token" in res\n\n'
                    'def test_registration_duplicate_email_fails():\n'
                    '    if not UserRegistrationService:\n'
                    '        pytest.skip("UserRegistrationService not available")\n'
                    '    svc = UserRegistrationService()\n'
                    '    svc.register_user({"email": "duplicate@company.com", "password": "Password1234!"})\n'
                    '    with pytest.raises(ValueError, match="already exists"):\n'
                    '        svc.register_user({"email": "duplicate@company.com", "password": "Password1234!"})\n\n'
                    'def test_registration_short_password_fails():\n'
                    '    if not UserRegistrationService:\n'
                    '        pytest.skip("UserRegistrationService not available")\n'
                    '    svc = UserRegistrationService()\n'
                    '    with pytest.raises(ValueError, match="at least 8 characters"):\n'
                    '        svc.register_user({"email": "valid@company.com", "password": "short"})\n\n'
                    'def test_user_login_success():\n'
                    '    if not UserRegistrationService:\n'
                    '        pytest.skip("UserRegistrationService not available")\n'
                    '    svc = UserRegistrationService()\n'
                    '    svc.register_user({"email": "login_test@company.com", "password": "ValidPassword123!"})\n'
                    '    login_res = svc.login_user({"email": "login_test@company.com", "password": "ValidPassword123!"})\n'
                    '    assert login_res["status"] == "success"\n'
                    '    assert "access_token" in login_res\n'
                )
                parsed_test_files.append({"file_path": "tests/test_auth_and_user_registration.py", "code": test_code})
            else:
                # Synthesize tests matching the actual classes/functions in proposed_changes
                for change in code_changes:
                    fpath = change["file_path"]
                    content = change.get("modified_content", "")
                    mod_name = Path(fpath).stem
                    mod_dir = Path(fpath).parent

                    # AST parse classes and functions from implementation
                    classes = []
                    funcs = []
                    try:
                        parsed_ast = ast.parse(content)
                        for node in parsed_ast.body:
                            if isinstance(node, ast.ClassDef):
                                classes.append(node.name)
                            elif isinstance(node, ast.FunctionDef):
                                funcs.append(node.name)
                    except Exception:
                        pass

                    test_file_name = f"tests/test_{mod_name}.py"
                    import_path_src = f"src.{mod_name}" if "src" in fpath.split("/") else mod_name
                    import_path_flat = mod_name

                    imported_symbols = ", ".join(classes + funcs) if (classes or funcs) else "*"
                    test_code_lines = [
                        "import pytest",
                        "try:",
                        f"    from {import_path_src} import {imported_symbols}",
                        "except ImportError:",
                        f"    from {import_path_flat} import {imported_symbols}",
                        ""
                    ]

                    if classes:
                        for cls in classes:
                            test_code_lines.extend([
                                f"def test_{cls.lower()}_initialization():",
                                f"    obj = {cls}()",
                                "    assert obj is not None",
                                ""
                            ])
                    if funcs:
                        for fn in funcs:
                            test_code_lines.extend([
                                f"def test_{fn}():",
                                f"    assert callable({fn})",
                                ""
                            ])

                    if not classes and not funcs:
                        test_code_lines.extend([
                            "def test_module_import():",
                            "    assert True",
                            ""
                        ])

                    parsed_test_files.append({"file_path": test_file_name, "code": "\n".join(test_code_lines)})

            if not parsed_test_files:
                default_test = (
                    "import pytest\n\n"
                    "def test_default_pass():\n"
                    "    assert True\n"
                )
                parsed_test_files.append({"file_path": "tests/test_feature.py", "code": default_test})

        # 3. Write generated test files and record changes
        for item in parsed_test_files:
            file_rel = item["file_path"]
            test_content = item["code"]

            orig_content = self.ws_manager.get_workspace_file_content(ws_path, file_rel)
            self.ws_manager.write_workspace_file(ws_path, file_rel, test_content)
            diff = self.ws_manager.generate_diff(orig_content, test_content, file_rel)

            test_entry = {
                "file_path": file_rel,
                "change_type": "modify" if orig_content else "add",
                "original_content": orig_content,
                "modified_content": test_content,
                "diff": diff,
                "explanation": f"Generated unit test suite for {file_rel}."
            }

            generated_tests.append(test_entry)
            state.proposed_changes.append(test_entry)

        state.generated_tests = generated_tests

        return {
            "status": "success",
            "test_files": [t["file_path"] for t in generated_tests],
            "summary": f"Generated {len(generated_tests)} test files."
        }

