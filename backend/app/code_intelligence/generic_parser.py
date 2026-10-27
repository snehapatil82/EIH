import re
from typing import Dict, List, Any

# Regex patterns for JavaScript/TypeScript
JS_FUNCTION_REGEX = re.compile(r"(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_$]+)\s*\(([^)]*)\)", re.MULTILINE)
JS_ARROW_REGEX = re.compile(r"(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*(?::\s*[^=]+)?\s*=>", re.MULTILINE)
JS_CLASS_REGEX = re.compile(r"(?:export\s+)?class\s+([a-zA-Z0-9_$]+)(?:\s+extends\s+([a-zA-Z0-9_$]+))?", re.MULTILINE)
JS_IMPORT_REGEX = re.compile(r"import\s+(?:\{([^}]+)\}|([a-zA-Z0-9_$]+))\s+from\s+['\"]([^'\"]+)['\"]", re.MULTILINE)

# Regex patterns for Go
GO_FUNC_REGEX = re.compile(r"func\s+(?:\((?:[a-zA-Z0-9_*]+\s+)?([a-zA-Z0-9_*]+)\)\s+)?([a-zA-Z0-9_]+)\s*\(([^)]*)\)", re.MULTILINE)
GO_TYPE_REGEX = re.compile(r"type\s+([a-zA-Z0-9_]+)\s+(struct|interface)", re.MULTILINE)

# Regex patterns for Rust
RUST_FN_REGEX = re.compile(r"(?:pub\s+)?(?:async\s+)?fn\s+([a-zA-Z0-9_]+)\s*(?:<[^>]+>)?\s*\(([^)]*)\)", re.MULTILINE)
RUST_STRUCT_REGEX = re.compile(r"(?:pub\s+)?(?:struct|enum|trait)\s+([a-zA-Z0-9_]+)", re.MULTILINE)

# Dependency parsers for package.json, requirements.txt, pyproject.toml, go.mod, Cargo.toml
class GenericCodeParser:
    def parse_source(self, source_code: str, file_path: str, language: str) -> Dict[str, Any]:
        result = {
            "entities": [],
            "imports": [],
            "endpoints": [],
            "has_syntax_error": False,
            "error_message": None
        }

        lines = source_code.splitlines()

        if language in ["JavaScript", "TypeScript", "JavaScript (React)", "TypeScript (React)"]:
            # Functions
            for match in JS_FUNCTION_REGEX.finditer(source_code):
                start_line = source_code[:match.start()].count("\n") + 1
                name = match.group(1)
                args = match.group(2).strip()
                result["entities"].append({
                    "name": name,
                    "entity_type": "function",
                    "file_path": file_path,
                    "start_line": start_line,
                    "end_line": start_line + 5, # approx
                    "signature": f"function {name}({args})",
                    "docstring": None,
                    "decorators": [],
                    "calls": []
                })

            # Arrow Functions
            for match in JS_ARROW_REGEX.finditer(source_code):
                start_line = source_code[:match.start()].count("\n") + 1
                name = match.group(1)
                args = match.group(2).strip()
                result["entities"].append({
                    "name": name,
                    "entity_type": "function",
                    "file_path": file_path,
                    "start_line": start_line,
                    "end_line": start_line + 5,
                    "signature": f"const {name} = ({args}) =>",
                    "docstring": None,
                    "decorators": [],
                    "calls": []
                })

            # Classes
            for match in JS_CLASS_REGEX.finditer(source_code):
                start_line = source_code[:match.start()].count("\n") + 1
                name = match.group(1)
                extends_cls = match.group(2)
                result["entities"].append({
                    "name": name,
                    "entity_type": "class",
                    "file_path": file_path,
                    "start_line": start_line,
                    "end_line": start_line + 10,
                    "signature": f"class {name}{f' extends {extends_cls}' if extends_cls else ''}",
                    "docstring": None,
                    "decorators": [],
                    "calls": []
                })

            # Imports
            for match in JS_IMPORT_REGEX.finditer(source_code):
                start_line = source_code[:match.start()].count("\n") + 1
                named_imports = match.group(1)
                default_import = match.group(2)
                module_source = match.group(3)
                result["imports"].append({
                    "module": module_source,
                    "symbols": named_imports.split(",") if named_imports else [default_import],
                    "line": start_line
                })

        elif language == "Go":
            for match in GO_FUNC_REGEX.finditer(source_code):
                start_line = source_code[:match.start()].count("\n") + 1
                receiver = match.group(1)
                name = match.group(2)
                args = match.group(3).strip()
                full_name = f"({receiver}).{name}" if receiver else name
                result["entities"].append({
                    "name": full_name,
                    "entity_type": "method" if receiver else "function",
                    "file_path": file_path,
                    "start_line": start_line,
                    "end_line": start_line + 5,
                    "signature": f"func {full_name}({args})",
                    "docstring": None,
                    "decorators": [],
                    "calls": []
                })

        elif language == "Rust":
            for match in RUST_FN_REGEX.finditer(source_code):
                start_line = source_code[:match.start()].count("\n") + 1
                name = match.group(1)
                args = match.group(2).strip()
                result["entities"].append({
                    "name": name,
                    "entity_type": "function",
                    "file_path": file_path,
                    "start_line": start_line,
                    "end_line": start_line + 5,
                    "signature": f"fn {name}({args})",
                    "docstring": None,
                    "decorators": [],
                    "calls": []
                })

        return result

    def parse_manifest_dependencies(self, filename: str, content: str) -> List[Dict[str, str]]:
        """Extracts dependencies from package manifests."""
        deps = []
        if filename == "requirements.txt":
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-"):
                    parts = re.split(r"[><=~]=", line)
                    name = parts[0].strip()
                    version = parts[1].strip() if len(parts) > 1 else None
                    deps.append({"name": name, "version": version, "ecosystem": "pip", "source_file": filename})

        elif filename == "package.json":
            try:
                import json
                data = json.loads(content)
                for dep_type in ["dependencies", "devDependencies"]:
                    for pkg, ver in data.get(dep_type, {}).items():
                        deps.append({"name": pkg, "version": ver, "ecosystem": "npm", "source_file": filename})
            except Exception:
                pass

        elif filename == "Cargo.toml":
            in_deps = False
            for line in content.splitlines():
                line = line.strip()
                if line == "[dependencies]":
                    in_deps = True
                elif line.startswith("[") and in_deps:
                    in_deps = False
                elif in_deps and "=" in line:
                    parts = line.split("=", 1)
                    name = parts[0].strip()
                    version = parts[1].strip().strip('"\'')
                    deps.append({"name": name, "version": version, "ecosystem": "cargo", "source_file": filename})

        elif filename == "pyproject.toml":
            in_deps = False
            for line in content.splitlines():
                line = line.strip()
                if line in ["[project.dependencies]", "[tool.poetry.dependencies]"]:
                    in_deps = True
                elif line.startswith("[") and in_deps:
                    in_deps = False
                elif in_deps and "=" in line and not line.startswith("#"):
                    parts = line.split("=", 1)
                    name = parts[0].strip().strip('"\'')
                    version = parts[1].strip().strip('"\'')
                    if name and name.lower() != "python":
                        deps.append({"name": name, "version": version, "ecosystem": "pip", "source_file": filename})

        return deps
