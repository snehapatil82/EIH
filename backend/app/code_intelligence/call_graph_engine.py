"""
Repository-Aware Call Graph Engine for Engineering Intelligence Hub (EIH).
Extracts static function-call relationships, call sites, parameters, control-flow
branch conditions, and generates interactive graphs & grounded explanations.
"""

import ast
import re
import os
import html
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, deque

from app.core.logging import logger


class FunctionParameter:
    def __init__(self, name: str, type_annotation: Optional[str] = None, default_value: Optional[str] = None):
        self.name = name
        self.type_annotation = type_annotation
        self.default_value = default_value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type_annotation": self.type_annotation,
            "default_value": self.default_value
        }


class CallSite:
    def __init__(
        self,
        caller_id: str,
        caller_name: str,
        callee_raw_name: str,
        callee_symbol_name: str,
        call_site_line: int,
        lexical_order: int = 0,
        source_file: str = "",
        is_conditional: bool = False,
        branch_condition: Optional[str] = None,
        is_loop: bool = False,
        is_exception: bool = False,
        is_async: bool = False,
        is_recursive: bool = False,
        is_dynamic: bool = False,
        is_external: bool = False,
        is_resolved: bool = False,
        callee_id: Optional[str] = None,
        target_file: Optional[str] = None
    ):
        self.caller_id = caller_id
        self.caller_name = caller_name
        self.callee_raw_name = callee_raw_name
        self.callee_symbol_name = callee_symbol_name
        self.call_site_line = call_site_line
        self.lexical_order = lexical_order
        self.source_file = source_file
        self.is_conditional = is_conditional
        self.branch_condition = branch_condition
        self.is_loop = is_loop
        self.is_exception = is_exception
        self.is_async = is_async
        self.is_recursive = is_recursive
        self.is_dynamic = is_dynamic
        self.is_external = is_external
        self.is_resolved = is_resolved
        self.callee_id = callee_id
        self.target_file = target_file

    def to_dict(self) -> Dict[str, Any]:
        return {
            "caller_id": self.caller_id,
            "caller_name": self.caller_name,
            "callee_raw_name": self.callee_raw_name,
            "callee_symbol_name": self.callee_symbol_name,
            "call_site_line": self.call_site_line,
            "lexical_order": self.lexical_order,
            "source_file": self.source_file,
            "is_conditional": self.is_conditional,
            "branch_condition": self.branch_condition,
            "is_loop": self.is_loop,
            "is_exception": self.is_exception,
            "is_async": self.is_async,
            "is_recursive": self.is_recursive,
            "is_dynamic": self.is_dynamic,
            "is_external": self.is_external,
            "is_resolved": self.is_resolved,
            "callee_id": self.callee_id,
            "target_file": self.target_file
        }


class FunctionNode:
    def __init__(
        self,
        node_id: str,
        name: str,
        full_name: str,
        file_path: str,
        start_line: int,
        end_line: int,
        enclosing_class: Optional[str] = None,
        enclosing_module: str = "",
        parameters: Optional[List[FunctionParameter]] = None,
        is_async: bool = False,
        docstring: Optional[str] = None,
        decorators: Optional[List[str]] = None,
        language: str = "Python",
        source_code_snippet: Optional[str] = None
    ):
        self.id = node_id
        self.name = name
        self.full_name = full_name
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.enclosing_class = enclosing_class
        self.enclosing_module = enclosing_module
        self.parameters = parameters or []
        self.is_async = is_async
        self.docstring = docstring
        self.decorators = decorators or []
        self.language = language
        self.source_code_snippet = source_code_snippet

        # Relationships
        self.outgoing_calls: List[CallSite] = []
        self.incoming_callers: List[CallSite] = []

    def to_dict(self, include_calls: bool = True) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "name": self.name,
            "full_name": self.full_name,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "enclosing_class": self.enclosing_class,
            "enclosing_module": self.enclosing_module,
            "parameters": [p.to_dict() for p in self.parameters],
            "is_async": self.is_async,
            "docstring": self.docstring,
            "decorators": self.decorators,
            "language": self.language,
            "caller_count": len(self.incoming_callers),
            "callee_count": len(self.outgoing_calls)
        }
        if include_calls:
            data["outgoing_calls"] = [c.to_dict() for c in self.outgoing_calls]
            data["incoming_callers"] = [c.to_dict() for c in self.incoming_callers]
        return data


# Standard library & common built-ins for external classification
PYTHON_BUILTINS_AND_STDLIB = {
    "print", "len", "range", "str", "int", "float", "bool", "dict", "list", "set", "tuple",
    "isinstance", "issubclass", "hasattr", "getattr", "setattr", "delattr", "callable",
    "open", "super", "enumerate", "zip", "map", "filter", "any", "all", "min", "max",
    "sum", "sorted", "reversed", "iter", "next", "type", "id", "hash", "repr", "format",
    "os", "sys", "path", "join", "split", "exists", "abspath", "dirname", "basename",
    "json", "loads", "dumps", "dump", "load", "re", "match", "search", "findall", "sub",
    "time", "sleep", "datetime", "now", "utcnow", "timedelta", "date", "asyncio", "run",
    "gather", "sleep", "create_task", "logging", "getLogger", "info", "warning", "error",
    "debug", "Path", "uuid", "uuid4", "pytest", "fixture", "mark", "raises", "skip"
}


class BaseCallGraphParser(ABC):
    """
    Extensible interface for language-specific call graph parsers.
    New language parsers can be registered with the CallGraphParserRegistry.
    """
    @abstractmethod
    def parse_file(self, file_path: str, source_code: str) -> Tuple[List[FunctionNode], Dict[str, str]]:
        """Parses a file and returns (functions, imports_map)."""
        pass


class PythonASTCallGraphParser(BaseCallGraphParser):
    """
    Syntax-aware call graph parser for Python using the built-in `ast` module.
    Tracks scopes, imports, calls, lexical ordering, await calls, and control-flow branches.
    """

    def parse_file(self, file_path: str, source_code: str) -> Tuple[List[FunctionNode], Dict[str, str]]:
        functions: List[FunctionNode] = []
        imports_map: Dict[str, str] = {}  # alias/symbol -> source module or full path

        try:
            tree = ast.parse(source_code)
        except Exception as e:
            logger.warning(f"PythonASTCallGraphParser: Failed to parse {file_path}: {e}")
            return functions, imports_map

        module_name = Path(file_path).stem

        # 1. First pass: Collect imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local_name = alias.asname or alias.name
                    imports_map[local_name] = alias.name
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    local_name = alias.asname or alias.name
                    target = f"{mod}.{alias.name}" if mod else alias.name
                    imports_map[local_name] = target

        # 2. Extract class and function definitions with scope
        lines = source_code.splitlines()

        class FunctionVisitor(ast.NodeVisitor):
            def __init__(self):
                self.class_stack: List[str] = []
                self.current_function: Optional[FunctionNode] = None
                self.branch_stack: List[str] = []
                self.loop_depth = 0
                self.exception_depth = 0
                self.is_inside_await = False
                self.call_order_counter = 0

            def visit_ClassDef(self, node: ast.ClassDef):
                self.class_stack.append(node.name)
                self.generic_visit(node)
                self.class_stack.pop()

            def visit_FunctionDef(self, node: ast.FunctionDef):
                self._handle_function(node, is_async=False)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
                self._handle_function(node, is_async=True)

            def _handle_function(self, node: Any, is_async: bool):
                enclosing_class = self.class_stack[-1] if self.class_stack else None
                full_name = f"{enclosing_class}.{node.name}" if enclosing_class else node.name
                node_id = f"{file_path}:{full_name}:{node.lineno}"

                # Extract parameters with defaults and type annotations
                params: List[FunctionParameter] = []
                arg_count = len(node.args.args)
                default_count = len(node.args.defaults)
                defaults = [None] * (arg_count - default_count) + list(node.args.defaults)

                for arg, def_node in zip(node.args.args, defaults):
                    arg_name = arg.arg
                    type_ann = ast.unparse(arg.annotation) if getattr(arg, "annotation", None) else None
                    def_val = ast.unparse(def_node) if def_node is not None else None
                    params.append(FunctionParameter(name=arg_name, type_annotation=type_ann, default_value=def_val))

                # Extract docstring
                docstring = ast.get_docstring(node)

                # Extract decorators
                decorators = []
                for d in node.decorator_list:
                    try:
                        decorators.append(ast.unparse(d))
                    except Exception:
                        pass

                # Snippet
                start = max(1, node.lineno)
                end = getattr(node, "end_lineno", node.lineno)
                snippet_lines = lines[start - 1 : min(len(lines), end)]
                snippet = "\n".join(snippet_lines) if snippet_lines else None

                fn_node = FunctionNode(
                    node_id=node_id,
                    name=node.name,
                    full_name=full_name,
                    file_path=file_path,
                    start_line=node.lineno,
                    end_line=end,
                    enclosing_class=enclosing_class,
                    enclosing_module=module_name,
                    parameters=params,
                    is_async=is_async,
                    docstring=docstring,
                    decorators=decorators,
                    language="Python",
                    source_code_snippet=snippet
                )

                previous_function = self.current_function
                previous_order = self.call_order_counter
                self.current_function = fn_node
                self.call_order_counter = 0

                # Visit statements in function body
                for stmt in node.body:
                    self.visit(stmt)

                functions.append(fn_node)
                self.current_function = previous_function
                self.call_order_counter = previous_order

            def visit_If(self, node: ast.If):
                # Unparse test condition
                try:
                    cond_str = ast.unparse(node.test)
                except Exception:
                    cond_str = "condition"

                # Then branch
                self.branch_stack.append(f"if {cond_str}")
                for stmt in node.body:
                    self.visit(stmt)
                self.branch_stack.pop()

                # Else / Elif branch
                if node.orelse:
                    self.branch_stack.append("else")
                    for stmt in node.orelse:
                        self.visit(stmt)
                    self.branch_stack.pop()

            def visit_IfExp(self, node: ast.IfExp):
                try:
                    cond_str = ast.unparse(node.test)
                except Exception:
                    cond_str = "condition"
                self.branch_stack.append(f"if {cond_str}")
                self.visit(node.body)
                self.branch_stack.pop()
                self.branch_stack.append("else")
                self.visit(node.orelse)
                self.branch_stack.pop()

            def visit_For(self, node: ast.For):
                self.loop_depth += 1
                self.generic_visit(node)
                self.loop_depth -= 1

            def visit_While(self, node: ast.While):
                self.loop_depth += 1
                self.generic_visit(node)
                self.loop_depth -= 1

            def visit_Try(self, node: ast.Try):
                for stmt in node.body:
                    self.visit(stmt)

                self.exception_depth += 1
                for handler in node.handlers:
                    for stmt in handler.body:
                        self.visit(stmt)
                for stmt in node.finalbody:
                    self.visit(stmt)
                self.exception_depth -= 1

            def visit_Await(self, node: ast.Await):
                prev_await = self.is_inside_await
                self.is_inside_await = True
                self.generic_visit(node)
                self.is_inside_await = prev_await

            def visit_Call(self, node: ast.Call):
                if not self.current_function:
                    self.generic_visit(node)
                    return

                self.call_order_counter += 1
                call_line = getattr(node, "lineno", self.current_function.start_line)

                # Determine raw name & base symbol
                raw_name = ""
                symbol_name = ""
                is_dynamic = False

                if isinstance(node.func, ast.Name):
                    raw_name = node.func.id
                    symbol_name = node.func.id
                    if symbol_name in ("getattr", "eval", "exec", "locals", "globals"):
                        is_dynamic = True
                elif isinstance(node.func, ast.Attribute):
                    try:
                        raw_name = ast.unparse(node.func)
                    except Exception:
                        raw_name = node.func.attr
                    symbol_name = node.func.attr
                elif isinstance(node.func, ast.Subscript):
                    try:
                        raw_name = ast.unparse(node.func)
                    except Exception:
                        raw_name = "subscript_call"
                    symbol_name = "dynamic_dispatch"
                    is_dynamic = True
                else:
                    try:
                        raw_name = ast.unparse(node.func)
                    except Exception:
                        raw_name = "call"
                    symbol_name = raw_name

                # Check if call is recursive (callee is this function)
                is_recursive = (
                    symbol_name == self.current_function.name
                    or raw_name == self.current_function.name
                    or raw_name == f"self.{self.current_function.name}"
                    or raw_name == f"cls.{self.current_function.name}"
                )

                # Check if call is awaited or in async context
                is_async_call = self.is_inside_await or (self.current_function and self.current_function.is_async)

                # Check if conditional
                is_cond = len(self.branch_stack) > 0
                branch_cond = self.branch_stack[-1] if is_cond else None

                call_site = CallSite(
                    caller_id=self.current_function.id,
                    caller_name=self.current_function.name,
                    callee_raw_name=raw_name,
                    callee_symbol_name=symbol_name,
                    call_site_line=call_line,
                    lexical_order=self.call_order_counter,
                    source_file=file_path,
                    is_conditional=is_cond,
                    branch_condition=branch_cond,
                    is_loop=(self.loop_depth > 0),
                    is_exception=(self.exception_depth > 0),
                    is_async=is_async_call,
                    is_recursive=is_recursive,
                    is_dynamic=is_dynamic
                )
                self.current_function.outgoing_calls.append(call_site)
                self.generic_visit(node)

        # Handle match/case if Python >= 3.10
        if hasattr(ast, "Match"):
            def visit_Match(self, node: Any):
                for case in getattr(node, "cases", []):
                    try:
                        pat_str = ast.unparse(case.pattern)
                    except Exception:
                        pat_str = "case"
                    self.branch_stack.append(f"case {pat_str}")
                    for stmt in case.body:
                        self.visit(stmt)
                    self.branch_stack.pop()
            FunctionVisitor.visit_Match = visit_Match

        visitor = FunctionVisitor()
        visitor.visit(tree)
        return functions, imports_map


class TypeScriptCallGraphParser(BaseCallGraphParser):
    """
    Extensible syntax-aware parser for JavaScript and TypeScript.
    Extracts functions, classes, methods, parameters, and invocation call sites.
    """
    JS_FUNC_PATTERN = re.compile(
        r"(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_$]+)\s*\(([^)]*)\)",
        re.MULTILINE
    )
    JS_ARROW_PATTERN = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*(?::\s*[^=]+)?\s*=>",
        re.MULTILINE
    )
    JS_CLASS_PATTERN = re.compile(
        r"class\s+([a-zA-Z0-9_$]+)(?:\s+extends\s+[a-zA-Z0-9_$]+)?\s*\{",
        re.MULTILINE
    )
    JS_CLASS_METHOD_PATTERN = re.compile(
        r"^\s*(?:public|private|protected|async|static|\s)*([a-zA-Z0-9_$]+)\s*\(([^)]*)\)\s*(?::\s*[^{]+)?\s*\{",
        re.MULTILINE
    )
    JS_CALL_PATTERN = re.compile(
        r"(?:await\s+)?\b([a-zA-Z0-9_$]+(?:\.[a-zA-Z0-9_$]+)?)\s*\(",
        re.MULTILINE
    )

    def parse_file(self, file_path: str, source_code: str) -> Tuple[List[FunctionNode], Dict[str, str]]:
        functions: List[FunctionNode] = []
        imports_map: Dict[str, str] = {}
        lines = source_code.splitlines()

        # Parse imports
        for line in lines:
            m = re.search(r"import\s+(?:\{([^}]+)\}|([a-zA-Z0-9_$]+))\s+from\s+['\"]([^'\"]+)['\"]", line)
            if m:
                named = m.group(1)
                default_name = m.group(2)
                src = m.group(3)
                if named:
                    for s in named.split(","):
                        s_clean = s.strip()
                        if s_clean:
                            imports_map[s_clean] = src
                if default_name:
                    imports_map[default_name.strip()] = src

        found_funcs: List[Tuple[str, str, int, str, Optional[str], bool]] = [] # name, params_str, line, kind, enclosing_class, is_async

        # 1. Standard functions
        for m in self.JS_FUNC_PATTERN.finditer(source_code):
            line_no = source_code[:m.start()].count("\n") + 1
            is_async = "async " in m.group(0)
            found_funcs.append((m.group(1), m.group(2), line_no, "function", None, is_async))

        # 2. Arrow functions
        for m in self.JS_ARROW_PATTERN.finditer(source_code):
            line_no = source_code[:m.start()].count("\n") + 1
            is_async = "async" in m.group(0)
            found_funcs.append((m.group(1), m.group(2), line_no, "arrow", None, is_async))

        # 3. Class methods
        # Identify classes
        class_spans = []
        for cm in self.JS_CLASS_PATTERN.finditer(source_code):
            cname = cm.group(1)
            cstart = cm.start()
            class_spans.append((cname, cstart))

        for idx, line in enumerate(lines):
            line_num = idx + 1
            method_m = self.JS_CLASS_METHOD_PATTERN.match(line)
            if method_m:
                mname = method_m.group(1)
                if mname not in ("constructor", "if", "for", "while", "switch", "catch", "function"):
                    # Find which class this belongs to
                    line_char_pos = sum(len(l) + 1 for l in lines[:idx])
                    enclosing_cls = None
                    for cname, cstart in reversed(class_spans):
                        if line_char_pos > cstart:
                            enclosing_cls = cname
                            break
                    is_async = "async" in line
                    found_funcs.append((mname, method_m.group(2), line_num, "method", enclosing_cls, is_async))

        # Sort functions by start line
        found_funcs.sort(key=lambda x: x[2])

        for i, (fname, pstr, sline, kind, encl_cls, is_async_fn) in enumerate(found_funcs):
            eline = found_funcs[i + 1][2] - 1 if i + 1 < len(found_funcs) else len(lines)
            full_fn_name = f"{encl_cls}.{fname}" if encl_cls else fname
            node_id = f"{file_path}:{full_fn_name}:{sline}"

            params = [
                FunctionParameter(name=p.strip().split(":")[0].strip())
                for p in pstr.split(",") if p.strip()
            ]

            fn_node = FunctionNode(
                node_id=node_id,
                name=fname,
                full_name=full_fn_name,
                file_path=file_path,
                start_line=sline,
                end_line=eline,
                enclosing_class=encl_cls,
                enclosing_module=Path(file_path).stem,
                parameters=params,
                is_async=is_async_fn,
                language="TypeScript" if file_path.endswith((".ts", ".tsx")) else "JavaScript"
            )

            # Find calls inside function boundary
            fn_code = "\n".join(lines[sline - 1 : eline])
            order = 0
            for call_m in self.JS_CALL_PATTERN.finditer(fn_code):
                raw = call_m.group(1)
                if raw in ("function", "if", "for", "while", "switch", "catch", "return", "import"):
                    continue
                order += 1
                call_line = sline + fn_code[:call_m.start()].count("\n")
                symbol = raw.split(".")[-1]
                call_text = call_m.group(0)
                is_await = "await " in call_text
                preceding_text = fn_code[:call_m.start()]
                last_line = preceding_text.splitlines()[-1] if preceding_text.splitlines() else ""
                is_cond = "if " in last_line or "else " in last_line or "?" in last_line

                call_site = CallSite(
                    caller_id=node_id,
                    caller_name=fname,
                    callee_raw_name=raw,
                    callee_symbol_name=symbol,
                    call_site_line=call_line,
                    lexical_order=order,
                    source_file=file_path,
                    is_recursive=(symbol == fname or raw == f"this.{fname}"),
                    is_async=is_await or is_async_fn,
                    is_conditional=is_cond,
                    branch_condition="if branch" if is_cond else None
                )
                fn_node.outgoing_calls.append(call_site)

            functions.append(fn_node)

        return functions, imports_map


class CallGraphParserRegistry:
    """
    Registry for language parsers enabling extensible language additions.
    """
    def __init__(self):
        self._parsers: Dict[str, BaseCallGraphParser] = {}

    def register(self, extensions: List[str], parser: BaseCallGraphParser):
        for ext in extensions:
            self._parsers[ext.lower()] = parser

    def get_parser(self, extension: str) -> Optional[BaseCallGraphParser]:
        return self._parsers.get(extension.lower())


class RepositoryCallGraph:
    """
    Main call graph container. Indexes all function nodes, resolves call sites
    across files and classes, and supports depth-controlled traversal.
    """

    def __init__(self, repository_id: str, repo_path: str):
        self.repository_id = repository_id
        self.repo_path = repo_path
        self.functions: Dict[str, FunctionNode] = {}  # id -> FunctionNode
        self.functions_by_name: Dict[str, List[FunctionNode]] = defaultdict(list)
        self.functions_by_file: Dict[str, List[FunctionNode]] = defaultdict(list)
        self.functions_by_class: Dict[Tuple[str, str], FunctionNode] = {}  # (class_name, method_name) -> node
        self.file_imports: Dict[str, Dict[str, str]] = {}  # file_path -> {symbol: source}
        self.built_at: Optional[float] = None

    def add_function(self, fn: FunctionNode):
        self.functions[fn.id] = fn
        self.functions_by_name[fn.name].append(fn)
        self.functions_by_file[fn.file_path].append(fn)
        if fn.enclosing_class:
            self.functions_by_class[(fn.enclosing_class, fn.name)] = fn

    def populate_from_entities(self, entities: List[Dict[str, Any]]):
        """
        Fallback builder using CodeEntity records from database when disk files are unavailable.
        """
        for ent in entities:
            if ent.get("entity_type") in ("function", "method"):
                fpath = ent.get("file_path") or "main.py"
                name = ent.get("name") or "func"
                node_id = ent.get("id") or f"{fpath}:{name}:{ent.get('start_line', 1)}"
                fn = FunctionNode(
                    node_id=node_id,
                    name=name,
                    full_name=name,
                    file_path=fpath,
                    start_line=ent.get("start_line", 1),
                    end_line=ent.get("end_line", 1),
                    enclosing_class=None,
                    enclosing_module=Path(fpath).stem,
                    is_async=False,
                    docstring=None,
                    language="Python"
                )
                calls = ent.get("calls") or []
                for idx, cname in enumerate(calls):
                    call_site = CallSite(
                        caller_id=node_id,
                        caller_name=name,
                        callee_raw_name=cname,
                        callee_symbol_name=cname.split(".")[-1],
                        call_site_line=ent.get("start_line", 1) + idx,
                        lexical_order=idx + 1,
                        source_file=fpath
                    )
                    fn.outgoing_calls.append(call_site)
                self.add_function(fn)
        self.resolve_relationships()

    def resolve_relationships(self):
        """
        Resolves callee_id and target_file for each call site using:
        1. Local class methods (self.method)
        2. Same-file function definitions
        3. Explicit module / file imports
        4. Global unique repository functions
        5. Marks external / standard library calls honestly.
        """
        for caller_id, caller in self.functions.items():
            for call in caller.outgoing_calls:
                target_node: Optional[FunctionNode] = None

                # A. Recursive call
                if call.callee_symbol_name == caller.name:
                    target_node = caller
                    call.is_recursive = True

                # B. Class method call: self.method(), cls.method(), or this.method()
                elif (
                    caller.enclosing_class
                    and (
                        call.callee_raw_name.startswith("self.")
                        or call.callee_raw_name.startswith("cls.")
                        or call.callee_raw_name.startswith("this.")
                    )
                ):
                    method_target = self.functions_by_class.get((caller.enclosing_class, call.callee_symbol_name))
                    if method_target:
                        target_node = method_target

                # B2. Sibling method in same class called directly
                if not target_node and caller.enclosing_class:
                    method_target = self.functions_by_class.get((caller.enclosing_class, call.callee_symbol_name))
                    if method_target and method_target.id != caller.id:
                        target_node = method_target

                # C. Same file function call
                if not target_node:
                    same_file_matches = [
                        f for f in self.functions_by_file.get(caller.file_path, [])
                        if f.name == call.callee_symbol_name and f.id != caller.id
                    ]
                    if same_file_matches:
                        target_node = same_file_matches[0]

                # D. Imported symbol resolution
                if not target_node and caller.file_path in self.file_imports:
                    imports = self.file_imports[caller.file_path]
                    imported_source = imports.get(call.callee_symbol_name) or imports.get(call.callee_raw_name.split(".")[0])
                    if imported_source:
                        # Match imported module to files in repo
                        for fpath, file_funcs in self.functions_by_file.items():
                            mod_name = Path(fpath).stem
                            if mod_name in imported_source or imported_source.replace(".", "/") in fpath:
                                for f in file_funcs:
                                    if f.name == call.callee_symbol_name:
                                        target_node = f
                                        break
                            if target_node:
                                break

                # E. Global unique repository function
                if not target_node:
                    global_matches = self.functions_by_name.get(call.callee_symbol_name, [])
                    if len(global_matches) == 1:
                        target_node = global_matches[0]
                    elif len(global_matches) > 1:
                        # Disambiguate by module path similarity
                        caller_parts = set(caller.file_path.split("/"))
                        best_match = None
                        best_overlap = -1
                        for cand in global_matches:
                            cand_parts = set(cand.file_path.split("/"))
                            overlap = len(caller_parts.intersection(cand_parts))
                            if overlap > best_overlap:
                                best_overlap = overlap
                                best_match = cand
                        target_node = best_match

                # F. Apply resolution or mark external / unresolved
                if target_node:
                    call.callee_id = target_node.id
                    call.target_file = target_node.file_path
                    call.is_resolved = True
                    call.is_external = False
                    # Cross-link incoming caller
                    target_node.incoming_callers.append(call)
                else:
                    call.is_resolved = False
                    raw_base = call.callee_raw_name.split(".")[0]
                    if raw_base in PYTHON_BUILTINS_AND_STDLIB or call.callee_symbol_name in PYTHON_BUILTINS_AND_STDLIB:
                        call.is_external = True
                    else:
                        call.is_external = False

    def traverse(
        self,
        root_function_id: str,
        mode: str = "calls_from",
        depth: int = 2,
        max_nodes: int = 40
    ) -> Tuple[FunctionNode, List[FunctionNode], List[CallSite]]:
        """
        Traverses call graph with cycle detection, depth limiter, and node deduplication.
        Modes: 'calls_from' (callees), 'called_by' (callers), 'full' (both directions).
        """
        root = self.functions.get(root_function_id) if root_function_id else None
        if not root:
            if self.functions:
                # Pick function with highest connections or first entrypoint
                root = max(self.functions.values(), key=lambda f: len(f.outgoing_calls) + len(f.incoming_callers))
            else:
                root = FunctionNode("root", "entrypoint", "entrypoint", "main.py", 1, 10)
                return root, [root], []

        nodes_map: Dict[str, FunctionNode] = {root.id: root}
        included_edges: List[CallSite] = []
        edge_keys: Set[Tuple[str, str, int]] = set()

        # Queue items: (function_id, current_depth, direction: 'outgoing' | 'incoming' | 'both')
        queue: deque = deque()
        queue.append((root.id, 0, mode))

        visited_expanded: Set[Tuple[str, str]] = set()

        while queue and len(nodes_map) < max_nodes:
            curr_id, curr_depth, curr_direction = queue.popleft()
            state_key = (curr_id, curr_direction)
            if state_key in visited_expanded:
                continue
            visited_expanded.add(state_key)

            curr_node = self.functions.get(curr_id)
            if not curr_node:
                continue

            if curr_depth >= depth:
                continue

            # 1. Outgoing calls (callees)
            if curr_direction in ("calls_from", "full"):
                for edge in curr_node.outgoing_calls:
                    edge_key = (edge.caller_id, edge.callee_id or edge.callee_raw_name, edge.call_site_line)
                    if edge_key not in edge_keys:
                        edge_keys.add(edge_key)
                        included_edges.append(edge)

                    if edge.callee_id and edge.callee_id in self.functions:
                        target = self.functions[edge.callee_id]
                        if target.id not in nodes_map:
                            nodes_map[target.id] = target
                            # Recursion / cycle prevention: only queue if not visited
                            if (target.id, "calls_from") not in visited_expanded:
                                queue.append((target.id, curr_depth + 1, "calls_from"))

            # 2. Incoming calls (callers)
            if curr_direction in ("called_by", "full"):
                for edge in curr_node.incoming_callers:
                    edge_key = (edge.caller_id, edge.callee_id or edge.callee_raw_name, edge.call_site_line)
                    if edge_key not in edge_keys:
                        edge_keys.add(edge_key)
                        included_edges.append(edge)

                    if edge.caller_id in self.functions:
                        caller_fn = self.functions[edge.caller_id]
                        if caller_fn.id not in nodes_map:
                            nodes_map[caller_fn.id] = caller_fn
                            if (caller_fn.id, "called_by") not in visited_expanded:
                                queue.append((caller_fn.id, curr_depth + 1, "called_by"))

        return root, list(nodes_map.values()), included_edges


class CallGraphEngine:
    """
    High-level service managing repository call graph indexing,
    Mermaid flowchart generation, and grounded explanations.
    """

    def __init__(self):
        self.py_parser = PythonASTCallGraphParser()
        self.ts_parser = TypeScriptCallGraphParser()
        self.registry = CallGraphParserRegistry()
        self.registry.register([".py"], self.py_parser)
        self.registry.register([".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"], self.ts_parser)

    def build_graph_for_repository(self, repository_id: str, repo_path: Path) -> RepositoryCallGraph:
        """
        Builds a full repository call graph from files on disk using registered language parsers.
        """
        graph = RepositoryCallGraph(repository_id, str(repo_path))

        # Scan code files
        code_extensions = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
        for root, _, files in os.walk(repo_path):
            # Skip hidden, virtualenv, node_modules, cache dirs
            if any(part.startswith(".") or part in ("node_modules", ".venv", "venv", "__pycache__", "dist", "build") for part in Path(root).parts):
                continue

            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                parser = self.registry.get_parser(ext)
                if parser:
                    full_p = Path(root) / fname
                    rel_p = str(full_p.relative_to(repo_path)).replace("\\", "/")

                    try:
                        with open(full_p, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read()

                        nodes, imports = parser.parse_file(rel_p, content)
                        for n in nodes:
                            graph.add_function(n)
                        graph.file_imports[rel_p] = imports
                    except Exception as e:
                        logger.warning(f"CallGraphEngine: Error parsing {rel_p}: {e}")

        # Resolve references
        graph.resolve_relationships()
        graph.built_at = os.path.getmtime(repo_path) if repo_path.exists() else 0
        return graph

    def generate_mermaid(
        self,
        root: FunctionNode,
        nodes: List[FunctionNode],
        edges: List[CallSite],
        mode: str
    ) -> str:
        """
        Generates robust, syntax-safe Mermaid flowchart code.
        """
        lines = ["flowchart LR"]
        lines.append("  %% Style Classes")
        lines.append("  classDef rootNode fill:#0284c7,stroke:#38bdf8,stroke-width:2px,color:#ffffff,font-weight:bold;")
        lines.append("  classDef normalNode fill:#0f172a,stroke:#334155,stroke-width:1px,color:#f1f5f9;")
        lines.append("  classDef externalNode fill:#1e293b,stroke:#64748b,stroke-width:1px,stroke-dasharray: 4 4,color:#94a3b8;")

        node_id_map: Dict[str, str] = {}
        for idx, n in enumerate(nodes):
            safe_id = f"fn_{idx}"
            node_id_map[n.id] = safe_id

            short_path = "/".join(n.file_path.split("/")[-2:]) if "/" in n.file_path else n.file_path
            loc_label = f"{short_path}:L{n.start_line}"
            fn_title = f"{n.enclosing_class}.{n.name}()" if n.enclosing_class else f"{n.name}()"
            escaped_title = html.escape(fn_title).replace('"', "'")

            label = f'["<b>{escaped_title}</b><br/><span style=\'font-size:10px; color:#94a3b8;\'>{loc_label}</span>"]'
            css_class = ":::rootNode" if n.id == root.id else ":::normalNode"
            lines.append(f"  {safe_id}{label}{css_class}")

        # External or unresolved target nodes
        external_count = 0
        external_id_map: Dict[str, str] = {}
        for e in edges:
            if not e.callee_id or e.callee_id not in node_id_map:
                ext_name = e.callee_symbol_name
                if ext_name not in external_id_map:
                    external_count += 1
                    ext_id = f"ext_{external_count}"
                    external_id_map[ext_name] = ext_id
                    tag = "external" if e.is_external else "unresolved"
                    lines.append(f'  {ext_id}["<i>{html.escape(ext_name)}()</i><br/><span style=\'font-size:9px; color:#64748b;\'>[{tag}]</span>"]:::externalNode')

        # Add directed edges
        for e in edges:
            source_id = node_id_map.get(e.caller_id)
            if not source_id:
                continue

            target_id = node_id_map.get(e.callee_id) if e.callee_id else external_id_map.get(e.callee_symbol_name)
            if not target_id:
                continue

            # Edge label with line and conditions
            edge_parts = [f"L{e.call_site_line}"]
            if e.branch_condition:
                cond_clean = e.branch_condition.replace('"', "'")[:25]
                edge_parts.append(f"[{cond_clean}]")
            elif e.is_conditional:
                edge_parts.append("[branch]")
            if e.is_loop:
                edge_parts.append("[loop]")
            if e.is_async:
                edge_parts.append("[await]")
            if e.is_recursive:
                edge_parts.append("[recursive]")

            edge_text = " ".join(edge_parts)

            if e.is_async:
                lines.append(f'  {source_id} -. "{edge_text}" .-> {target_id}')
            else:
                lines.append(f'  {source_id} -->|"{edge_text}"| {target_id}')

        return "\n".join(lines)

    def generate_explanation(
        self,
        root: FunctionNode,
        nodes: List[FunctionNode],
        edges: List[CallSite],
        mode: str
    ) -> Dict[str, Any]:
        """
        Generates a repository-specific, grounded explanation of the call flow.
        """
        short_file = "/".join(root.file_path.split("/")[-2:]) if "/" in root.file_path else root.file_path
        func_display = f"{root.enclosing_class}.{root.name}()" if root.enclosing_class else f"{root.name}()"

        # 1. Summary
        summary = (
            f"Static call flow analysis for `{func_display}` defined in `{root.file_path}` "
            f"(lines {root.start_line}-{root.end_line})."
        )
        if root.docstring:
            summary += f" Description: {root.docstring.strip().splitlines()[0]}"

        # 2. Outgoing calls breakdown
        outgoing = sorted(root.outgoing_calls, key=lambda x: x.lexical_order)
        outgoing_breakdown = []
        for c in outgoing:
            cond_info = f" inside branch `{c.branch_condition}`" if c.branch_condition else (" inside condition" if c.is_conditional else " unconditionally")
            loop_info = " within loop" if c.is_loop else ""
            async_info = " via await" if c.is_async else ""
            res_info = f" resolved to `{c.target_file}`" if c.is_resolved and c.target_file else (" (external library)" if c.is_external else " (unresolved)")
            outgoing_breakdown.append({
                "callee": c.callee_raw_name,
                "line": c.call_site_line,
                "order": c.lexical_order,
                "execution_nature": f"Called{cond_info}{loop_info}{async_info}{res_info}."
            })

        # 3. Incoming callers
        incoming_callers = []
        for inc in root.incoming_callers:
            incoming_callers.append({
                "caller": inc.caller_name,
                "file": inc.source_file,
                "line": inc.call_site_line,
                "condition": inc.branch_condition or ("conditional" if inc.is_conditional else "direct")
            })

        # 4. Control flow & branching narrative
        conditional_calls = [c for c in outgoing if c.is_conditional]
        loop_calls = [c for c in outgoing if c.is_loop]
        control_flow_narrative = (
            f"The function executes {len(outgoing)} call expressions. "
        )
        if conditional_calls:
            control_flow_narrative += (
                f"It contains {len(conditional_calls)} conditional call(s) governed by branches "
                "(e.g., if/else paths), meaning not all targets execute in every invocation. "
            )
        else:
            control_flow_narrative += "All outgoing calls execute in sequential lexical order without branching. "

        if loop_calls:
            control_flow_narrative += f"Additionally, {len(loop_calls)} call(s) occur within iterative loops."

        # 5. Limitations & Evidence notice
        unresolved_count = sum(1 for e in edges if not e.is_resolved and not e.is_external)
        external_count = sum(1 for e in edges if e.is_external)
        limitations = (
            "This graph is statically inferred from source code AST syntax. Runtime execution follows specific branches "
            f"based on input parameters. Dynamic dispatches or runtime reflection cannot be statically guaranteed. "
            f"({external_count} external libraries detected, {unresolved_count} targets unresolved)."
        )

        return {
            "summary": summary,
            "function_name": root.name,
            "full_name": func_display,
            "file_path": root.file_path,
            "line_range": f"L{root.start_line}-L{root.end_line}",
            "parameters": [p.to_dict() for p in root.parameters],
            "docstring": root.docstring,
            "outgoing_calls_breakdown": outgoing_breakdown,
            "incoming_callers": incoming_callers,
            "control_flow_narrative": control_flow_narrative,
            "static_limitations": limitations,
            "components_involved": list(set([n.file_path for n in nodes])),
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }


# Global in-memory cache for call graphs per repository
_call_graph_cache: Dict[str, Tuple[float, RepositoryCallGraph]] = {}
_call_graph_engine = CallGraphEngine()


def get_call_graph_service() -> CallGraphEngine:
    return _call_graph_engine


def get_or_build_repository_call_graph(repository_id: str, repo_path: Path) -> RepositoryCallGraph:
    """
    Returns cached repository call graph or builds a new one if not cached / modified.
    """
    mtime = os.path.getmtime(repo_path) if repo_path.exists() else 0
    cached = _call_graph_cache.get(repository_id)

    if cached and cached[0] == mtime:
        return cached[1]

    logger.info(f"Building call graph for repository {repository_id} at {repo_path}")
    graph = _call_graph_engine.build_graph_for_repository(repository_id, repo_path)
    _call_graph_cache[repository_id] = (mtime, graph)
    return graph


def invalidate_repository_call_graph(repository_id: str):
    """Invalidates the in-memory cache when a repository is re-indexed or modified."""
    if repository_id in _call_graph_cache:
        del _call_graph_cache[repository_id]
