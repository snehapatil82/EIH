"""
Project Type Detector — identifies a project's ecosystem from manifest files
found inside a workspace directory. Used by the terminal to suggest relevant commands.
"""
import os
from pathlib import Path
from typing import Dict, List, Optional


class ProjectInfo:
    def __init__(
        self,
        project_type: str,
        manifests: List[str],
        allowed_commands: List[str],
        suggested_commands: List[Dict[str, str]],
    ):
        self.project_type = project_type
        self.manifests = manifests
        self.allowed_commands = allowed_commands
        self.suggested_commands = suggested_commands


# Ordered from most specific to most generic
_DETECTORS = [
    {
        "type": "node",
        "marker_files": ["package.json"],
        "suggested": [
            {"label": "Install Dependencies", "cmd": "npm install"},
            {"label": "Run Dev Server", "cmd": "npm run dev"},
            {"label": "Run Tests", "cmd": "npm test"},
            {"label": "Build", "cmd": "npm run build"},
            {"label": "Lint", "cmd": "npm run lint"},
        ],
        "allowed": ["npm", "npx", "node", "yarn", "pnpm", "tsc"],
    },
    {
        "type": "python_pyproject",
        "marker_files": ["pyproject.toml"],
        "suggested": [
            {"label": "Install (pip)", "cmd": "pip install -e ."},
            {"label": "Run Tests", "cmd": "pytest"},
            {"label": "Lint (ruff)", "cmd": "ruff check ."},
            {"label": "Format (black)", "cmd": "black ."},
            {"label": "Type Check", "cmd": "mypy ."},
        ],
        "allowed": ["pip", "pip3", "python", "python3", "pytest", "ruff", "black", "mypy", "poetry"],
    },
    {
        "type": "python_requirements",
        "marker_files": ["requirements.txt"],
        "suggested": [
            {"label": "Install Dependencies", "cmd": "pip install -r requirements.txt"},
            {"label": "Run Tests", "cmd": "pytest"},
            {"label": "Lint (flake8)", "cmd": "flake8 ."},
            {"label": "Format (black)", "cmd": "black ."},
        ],
        "allowed": ["pip", "pip3", "python", "python3", "pytest", "flake8", "black", "mypy"],
    },
    {
        "type": "go",
        "marker_files": ["go.mod"],
        "suggested": [
            {"label": "Download Deps", "cmd": "go mod download"},
            {"label": "Build", "cmd": "go build ./..."},
            {"label": "Run Tests", "cmd": "go test ./..."},
            {"label": "Vet", "cmd": "go vet ./..."},
        ],
        "allowed": ["go"],
    },
    {
        "type": "rust",
        "marker_files": ["Cargo.toml"],
        "suggested": [
            {"label": "Build", "cmd": "cargo build"},
            {"label": "Run Tests", "cmd": "cargo test"},
            {"label": "Clippy", "cmd": "cargo clippy"},
            {"label": "Format", "cmd": "cargo fmt"},
        ],
        "allowed": ["cargo"],
    },
    {
        "type": "java_maven",
        "marker_files": ["pom.xml"],
        "suggested": [
            {"label": "Install", "cmd": "mvn install -DskipTests"},
            {"label": "Run Tests", "cmd": "mvn test"},
            {"label": "Build", "cmd": "mvn package"},
        ],
        "allowed": ["mvn", "mvnw"],
    },
    {
        "type": "java_gradle",
        "marker_files": ["build.gradle", "build.gradle.kts"],
        "suggested": [
            {"label": "Build", "cmd": "./gradlew build"},
            {"label": "Run Tests", "cmd": "./gradlew test"},
        ],
        "allowed": ["gradle", "./gradlew", "gradlew"],
    },
]

# Always-allowed commands regardless of project type
_UNIVERSAL_ALLOWED = ["ls", "dir", "echo", "cat", "pwd", "which", "find", "grep"]


def detect_project(workspace_path: Path) -> ProjectInfo:
    """
    Scan workspace_path for manifest files and return a ProjectInfo.
    Falls back to a generic profile if no manifest is found.
    """
    found_manifests = []
    matched_detector = None

    for detector in _DETECTORS:
        for marker in detector["marker_files"]:
            if (workspace_path / marker).exists():
                found_manifests.append(marker)
                if matched_detector is None:
                    matched_detector = detector
                break

    if matched_detector:
        return ProjectInfo(
            project_type=matched_detector["type"],
            manifests=found_manifests,
            allowed_commands=matched_detector["allowed"] + _UNIVERSAL_ALLOWED,
            suggested_commands=matched_detector["suggested"],
        )

    # Generic fallback
    return ProjectInfo(
        project_type="generic",
        manifests=[],
        allowed_commands=_UNIVERSAL_ALLOWED,
        suggested_commands=[
            {"label": "List Files", "cmd": "ls -la"},
        ],
    )


def is_command_allowed(command: str, allowed_commands: List[str]) -> bool:
    """
    Check the executable (first token) of a command string against the allowlist.
    """
    if not command or not command.strip():
        return False

    parts = command.strip().split()
    if not parts:
        return False

    executable = parts[0]

    # Strip path prefixes: ./gradlew → gradlew, /usr/bin/python → python
    executable_basename = os.path.basename(executable)

    return executable_basename in allowed_commands or executable in allowed_commands
