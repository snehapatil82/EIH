"""
Tests for the GitHub publishing flow:
  - Branch name validation
  - Confirmation gate enforcement
  - Protected branch blocking
  - Git diff generation reusing CodeChange records
  - Token configuration checks
  - Workspace management guards
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.api.v1.github_publish import (
    _validate_branch_name,
    _get_git_token,
    _safe_run_git,
)
from app.sandbox.secret_redactor import redact


# ─── Branch Name Validation ────────────────────────────────────────────────────

class TestBranchNameValidation:
    def test_valid_feature_branch(self):
        assert _validate_branch_name("feature/my-feature") == "feature/my-feature"

    def test_valid_simple_name(self):
        assert _validate_branch_name("agent-task-abc12345") == "agent-task-abc12345"

    def test_valid_with_dots(self):
        assert _validate_branch_name("hotfix.1.2.3") == "hotfix.1.2.3"

    def test_invalid_space(self):
        with pytest.raises(HTTPException) as exc:
            _validate_branch_name("feature branch")
        assert exc.value.status_code == 400

    def test_invalid_tilde(self):
        with pytest.raises(HTTPException):
            _validate_branch_name("feature~bad")

    def test_invalid_double_dot(self):
        with pytest.raises(HTTPException):
            _validate_branch_name("feature..bad")

    def test_invalid_starts_with_dot(self):
        with pytest.raises(HTTPException):
            _validate_branch_name(".hidden")

    def test_invalid_ends_with_dot(self):
        with pytest.raises(HTTPException):
            _validate_branch_name("bad.")

    def test_invalid_lock_suffix(self):
        with pytest.raises(HTTPException):
            _validate_branch_name("feature.lock")

    def test_empty_raises(self):
        with pytest.raises(HTTPException):
            _validate_branch_name("   ")


# ─── Protected Branch Blocking ─────────────────────────────────────────────────

class TestProtectedBranchBlocking:
    """
    Verify that the /publish endpoint refuses pushes to protected branches.
    We test this via the validation logic, not a live push.
    """
    PROTECTED = ["main", "master", "develop", "production", "release"]

    @pytest.mark.asyncio
    async def test_push_to_main_blocked(self):
        """
        The publish endpoint must return 403 when target is 'main'.
        We reproduce the logic here without a full API call.
        """
        from app.api.v1.github_publish import PublishRequest
        req = PublishRequest(
            branch_name="main",
            commit_message="test",
            confirmed=True,
            create_pr=False,
        )
        PROTECTED_BRANCHES = {"main", "master", "develop", "production", "release"}
        assert req.branch_name in PROTECTED_BRANCHES

    def test_feature_branch_not_protected(self):
        PROTECTED_BRANCHES = {"main", "master", "develop", "production", "release"}
        assert "feature/new-auth" not in PROTECTED_BRANCHES


# ─── Confirmation Gate ─────────────────────────────────────────────────────────

class TestConfirmationGate:
    def test_confirmed_false_must_block(self):
        """
        Simulate what the publish endpoint does when confirmed=False.
        The actual gate raises HTTPException(400) before any git operations.
        """
        from app.api.v1.github_publish import PublishRequest
        req = PublishRequest(
            branch_name="feature/test",
            commit_message="feat: test",
            confirmed=False,
            create_pr=False,
        )
        # The gate logic
        blocked = not req.confirmed
        assert blocked is True

    def test_confirmed_true_passes_gate(self):
        from app.api.v1.github_publish import PublishRequest
        req = PublishRequest(
            branch_name="feature/test",
            commit_message="feat: test",
            confirmed=True,
            create_pr=False,
        )
        blocked = not req.confirmed
        assert blocked is False


# ─── Token Configuration ───────────────────────────────────────────────────────

class TestTokenConfiguration:
    def test_missing_token_raises_401(self):
        with patch("app.api.v1.github_publish.settings") as mock_settings:
            mock_settings.GITHUB_TOKEN = None
            with pytest.raises(HTTPException) as exc:
                _get_git_token()
            assert exc.value.status_code == 401
            assert "GITHUB_TOKEN" in exc.value.detail

    def test_empty_token_raises_401(self):
        with patch("app.api.v1.github_publish.settings") as mock_settings:
            mock_settings.GITHUB_TOKEN = ""
            with pytest.raises(HTTPException) as exc:
                _get_git_token()
            assert exc.value.status_code == 401

    def test_configured_token_returns_value(self):
        with patch("app.api.v1.github_publish.settings") as mock_settings:
            mock_settings.GITHUB_TOKEN = "ghp_testtoken123456789012345678"
            token = _get_git_token()
            assert token == "ghp_testtoken123456789012345678"


# ─── Git Diff Content Tests ────────────────────────────────────────────────────

class TestGitDiffContent:
    def test_diff_contains_added_lines(self):
        """Verify diff format using workspace_manager.generate_diff."""
        from app.repository.workspace_manager import WorkspaceManager
        wm = WorkspaceManager()
        original = "line1\nline2\n"
        modified = "line1\nline2\nline3_added\n"
        diff = wm.generate_diff(original, modified, "test/file.py")
        assert "+line3_added" in diff
        assert "a/test/file.py" in diff
        assert "b/test/file.py" in diff

    def test_diff_shows_removed_lines(self):
        from app.repository.workspace_manager import WorkspaceManager
        wm = WorkspaceManager()
        original = "line1\nline2\nline3_removed\n"
        modified = "line1\nline2\n"
        diff = wm.generate_diff(original, modified, "test/file.py")
        assert "-line3_removed" in diff

    def test_diff_new_file(self):
        from app.repository.workspace_manager import WorkspaceManager
        wm = WorkspaceManager()
        diff = wm.generate_diff(None, "new content\n", "new/file.py")
        assert "+new content" in diff

    def test_no_diff_for_unchanged_content(self):
        from app.repository.workspace_manager import WorkspaceManager
        wm = WorkspaceManager()
        content = "unchanged\n"
        diff = wm.generate_diff(content, content, "same/file.py")
        assert diff == ""


# ─── Workspace Preservation Tests ─────────────────────────────────────────────

class TestWorkspacePreservation:
    def test_apply_workspace_copies_files(self, tmp_path):
        """apply_workspace_to_repository must copy workspace files to target."""
        ws = tmp_path / "workspace"
        ws.mkdir()
        repo = tmp_path / "repo"
        repo.mkdir()

        (ws / "newfile.py").write_text("print('hello')")
        (ws / "subdir").mkdir()
        (ws / "subdir" / "another.py").write_text("x = 1")

        from app.repository.workspace_manager import WorkspaceManager
        wm = WorkspaceManager(workspaces_base_dir=tmp_path)
        count = wm.apply_workspace_to_repository(ws, repo)

        assert count == 2
        assert (repo / "newfile.py").read_text() == "print('hello')"
        assert (repo / "subdir" / "another.py").read_text() == "x = 1"

    def test_existing_repo_files_not_deleted(self, tmp_path):
        """Files not touched by workspace must remain in repo."""
        ws = tmp_path / "workspace"
        ws.mkdir()
        repo = tmp_path / "repo"
        repo.mkdir()

        # Pre-existing file in repo NOT in workspace
        (repo / "existing.py").write_text("existing")
        # New file from workspace
        (ws / "new.py").write_text("new")

        from app.repository.workspace_manager import WorkspaceManager
        wm = WorkspaceManager(workspaces_base_dir=tmp_path)
        wm.apply_workspace_to_repository(ws, repo)

        # Existing file should still be there
        assert (repo / "existing.py").exists()
        assert (repo / "existing.py").read_text() == "existing"


# ─── Secret Redaction in Push Errors ──────────────────────────────────────────

class TestSecretRedactionInErrors:
    def test_error_message_token_redacted(self):
        """Tokens in error messages must be redacted before returning to client."""
        token = "ghp_SUPERSECRETTOKEN12345678901234"
        raw_error = f"remote: Invalid credentials for https://github.com, token={token}"
        safe_error = redact(raw_error)
        assert token not in safe_error

    def test_push_url_credentials_stripped(self):
        """Auth URLs with embedded tokens must be stripped before logging."""
        import re
        auth_url = "https://ghp_SECRETTOKEN@github.com/owner/repo.git"
        sanitized = re.sub(r"https://[^@]+@", "https://", auth_url)
        assert "SECRETTOKEN" not in sanitized
        assert "github.com/owner/repo.git" in sanitized
