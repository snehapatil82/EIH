import ast
from typing import Dict, List, Optional, Any
from app.core.logging import logger

class PythonASTParser:
    """
    Parses Python source code and extracts functions, classes, methods,
    decorators, docstrings, imports, and calls with line numbers.
    """

    def parse_source(self, source_code: str, file_path: str) -> Dict[str, Any]:
        result = {
            "entities": [],
            "imports": [],
            "endpoints": [],
            "has_syntax_error": False,
            "error_message": None
        }

        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            result["has_syntax_error"] = True
            result["error_message"] = f"Syntax error at line {e.lineno}, col {e.offset}: {e.msg}"
            return result
        except Exception as e:
            result["has_syntax_error"] = True
            result["error_message"] = str(e)
            return result

        for node in ast.walk(tree):
            # Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result["imports"].append({
                        "module": alias.name,
                        "alias": alias.asname,
                        "line": getattr(node, "lineno", 0)
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    result["imports"].append({
                        "module": f"{module}.{alias.name}" if module else alias.name,
                        "alias": alias.asname,
                        "line": getattr(node, "lineno", 0)
                    })

        # Top-level and nested classes and functions
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                self._extract_class(node, file_path, result)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._extract_function(node, file_path, result)

        return result

    def _extract_class(self, node: ast.ClassDef, file_path: str, result: Dict[str, Any]):
        docstring = ast.get_docstring(node)
        bases = [self._format_node(base) for base in node.bases]
        decorators = [self._format_node(d) for d in node.decorator_list]

        class_entity = {
            "name": node.name,
            "entity_type": "class",
            "file_path": file_path,
            "start_line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno),
            "signature": f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}",
            "docstring": docstring,
            "decorators": decorators,
            "calls": []
        }
        result["entities"].append(class_entity)

        # Extract methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._extract_function(item, file_path, result, parent_class=node.name)

    def _extract_function(self, node: Any, file_path: str, result: Dict[str, Any], parent_class: Optional[str] = None):
        docstring = ast.get_docstring(node)
        decorators = [self._format_node(d) for d in node.decorator_list]
        args_str = self._format_arguments(node.args)
        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        
        full_name = f"{parent_class}.{node.name}" if parent_class else node.name
        entity_type = "method" if parent_class else "function"

        # Check for API endpoint decorators (e.g. @app.get, @router.post)
        is_endpoint = False
        endpoint_method = None
        endpoint_path = None

        for dec in decorators:
            for http_m in ["get", "post", "put", "delete", "patch", "options"]:
                if f".{http_m}" in dec.lower() or f"route(" in dec.lower() or f"api_view" in dec.lower():
                    is_endpoint = True
                    endpoint_method = http_m.upper()
                    endpoint_path = dec
                    break

        if is_endpoint:
            result["endpoints"].append({
                "name": full_name,
                "file_path": file_path,
                "method": endpoint_method or "GET",
                "decorator": endpoint_path,
                "start_line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno)
            })

        # Collect function calls inside this function
        calls = []
        for inner in ast.walk(node):
            if isinstance(inner, ast.Call):
                call_name = self._format_node(inner.func)
                if call_name and call_name not in calls:
                    calls.append(call_name)

        result["entities"].append({
            "name": full_name,
            "entity_type": "endpoint" if is_endpoint else entity_type,
            "file_path": file_path,
            "start_line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno),
            "signature": f"{prefix} {node.name}({args_str})",
            "docstring": docstring,
            "decorators": decorators,
            "calls": calls[:20] # Top calls
        })

    def _format_arguments(self, args_node: ast.arguments) -> str:
        args = []
        for arg in args_node.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {self._format_node(arg.annotation)}"
            args.append(arg_str)
        return ", ".join(args)

    def _format_node(self, node: Any) -> str:
        try:
            return ast.unparse(node)
        except Exception:
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                return f"{self._format_node(node.value)}.{node.attr}"
            elif isinstance(node, ast.Call):
                return f"{self._format_node(node.func)}(...)"
            elif isinstance(node, ast.Constant):
                return str(node.value)
            return ""
