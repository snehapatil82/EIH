import re
from pathlib import Path
from typing import Tuple
from urllib.parse import urlparse
from fastapi import HTTPException

# Regex for valid GitHub URLs: https://github.com/owner/repo or git@github.com:owner/repo.git
GITHUB_URL_REGEX = re.compile(
    r"^(https:\/\/github\.com\/|git@github\.com:)([a-zA-Z0-9_\-\.]+)\/([a-zA-Z0-9_\-\.]+?)(\.git)?(\/)?$"
)

def parse_github_url(url: str) -> Tuple[str, str]:
    """
    Validates a GitHub repository URL and extracts owner and repository name.
    """
    clean_url = url.strip()
    match = GITHUB_URL_REGEX.match(clean_url)
    if not match:
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub repository URL. Must be formatted like https://github.com/owner/repository",
        )
    owner = match.group(2)
    repo = match.group(3)
    return owner, repo

def validate_safe_path(target_path: Path, base_dir: Path) -> Path:
    """
    Prevents path traversal attacks by ensuring the target path is strictly
    within the allowed base directory.
    """
    resolved_base = base_dir.resolve()
    resolved_target = target_path.resolve()

    try:
        resolved_target.relative_to(resolved_base)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Security violation: Access denied for path outside sandbox ({resolved_target})",
        )
    return resolved_target
