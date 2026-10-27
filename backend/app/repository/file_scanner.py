import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Ignored directories
IGNORED_DIRS: Set[str] = {
    ".git",
    ".github",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target", # Rust / Java
    "bin",
    "obj",
    ".tox",
    ".eggs",
    "coverage",
    ".coverage",
}

# Ignored file extensions (binaries, lockfiles, images, media, compiled)
IGNORED_EXTENSIONS: Set[str] = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib", ".exe",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".mp4", ".mov", ".avi", ".mp3", ".wav",
    ".zip", ".tar", ".gz", ".7z", ".rar",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".lock", ".wasm", ".class", ".jar",
    ".min.js", ".min.css", ".map",
    ".db", ".sqlite", ".sqlite3"
}

# Sensitive / credential files to never index
SECRET_PATTERNS: Set[str] = {
    ".env", ".env.local", ".env.production", ".env.development",
    "id_rsa", "id_rsa.pub", "id_ed25519", "id_ed25519.pub",
    "credentials.json", "service_account.json", "secrets.yaml"
}

# Language mapping
LANGUAGE_MAP: Dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".cs": "C#",
    ".php": "PHP",
    ".rb": "Ruby",
    ".sh": "Shell",
    ".bash": "Shell",
    ".ps1": "PowerShell",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".md": "Markdown",
    ".sql": "SQL",
    ".dockerfile": "Dockerfile",
}

SPECIAL_FILENAMES: Dict[str, str] = {
    "Dockerfile": "Dockerfile",
    "Makefile": "Makefile",
    "package.json": "JSON",
    "Cargo.toml": "TOML",
    "go.mod": "Go Module",
    "requirements.txt": "Python Requirements",
    "pyproject.toml": "TOML",
}

class FileScanner:
    def __init__(self, max_file_size_bytes: int = 1_000_000):
        self.max_file_size_bytes = max_file_size_bytes

    def should_ignore(self, path: Path, rel_path: Path) -> bool:
        # Check directories in path
        for part in rel_path.parts[:-1]:
            if part in IGNORED_DIRS or part.startswith('.'):
                return True

        filename = path.name
        if filename in IGNORED_DIRS:
            return True

        if filename in SECRET_PATTERNS or filename.startswith(".env"):
            return True

        ext = path.suffix.lower()
        if ext in IGNORED_EXTENSIONS:
            return True

        return False

    def detect_language(self, path: Path) -> Optional[str]:
        if path.name in SPECIAL_FILENAMES:
            return SPECIAL_FILENAMES[path.name]
        return LANGUAGE_MAP.get(path.suffix.lower())

    def read_file_safe(self, path: Path) -> Optional[str]:
        if not path.is_file():
            return None
        if path.stat().st_size > self.max_file_size_bytes:
            return None
        
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                with open(path, "r", encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception:
                return None
        return None

    def scan_repository(self, repo_dir: Path) -> Tuple[List[Dict], Dict[str, int], int, int]:
        """
        Scans repository and returns:
        (files_list, language_stats, total_files, total_lines)
        """
        files_data = []
        language_stats: Dict[str, int] = {}
        total_files = 0
        total_lines = 0

        for root, dirs, files in os.walk(repo_dir):
            # Modify dirs in-place to avoid descending into ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith('.')]

            for f in files:
                full_path = Path(root) / f
                rel_path = full_path.relative_to(repo_dir)

                if self.should_ignore(full_path, rel_path):
                    continue

                lang = self.detect_language(full_path)
                size_bytes = full_path.stat().st_size
                content = self.read_file_safe(full_path)
                
                line_count = 0
                if content is not None:
                    line_count = len(content.splitlines())

                total_files += 1
                total_lines += line_count

                if lang:
                    language_stats[lang] = language_stats.get(lang, 0) + line_count

                files_data.append({
                    "path": str(rel_path).replace("\\", "/"),
                    "filename": f,
                    "extension": full_path.suffix.lower(),
                    "language": lang,
                    "size_bytes": size_bytes,
                    "line_count": line_count,
                    "content": content,
                })

        return files_data, language_stats, total_files, total_lines

    def build_file_tree(self, repo_dir: Path) -> List[Dict]:
        """Builds a hierarchical tree structure of the repository."""
        def get_tree_node(current_path: Path) -> Dict:
            rel_path = current_path.relative_to(repo_dir)
            if current_path.is_file():
                return {
                    "name": current_path.name,
                    "path": str(rel_path).replace("\\", "/"),
                    "type": "file",
                    "size": current_path.stat().st_size,
                    "language": self.detect_language(current_path),
                }
            
            children = []
            try:
                for entry in sorted(current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                    entry_rel = entry.relative_to(repo_dir)
                    if self.should_ignore(entry, entry_rel):
                        continue
                    node = get_tree_node(entry)
                    if node:
                        children.append(node)
            except Exception:
                pass

            return {
                "name": current_path.name if current_path != repo_dir else repo_dir.name,
                "path": str(rel_path).replace("\\", "/") if current_path != repo_dir else "",
                "type": "directory",
                "children": children
            }

        tree = get_tree_node(repo_dir)
        return tree.get("children", [])
