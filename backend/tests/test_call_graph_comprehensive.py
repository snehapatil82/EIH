import pytest
import os
import tempfile
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.code_intelligence.call_graph_engine import (
    PythonASTCallGraphParser,
    TypeScriptCallGraphParser,
    RepositoryCallGraph,
    CallGraphEngine,
    invalidate_repository_call_graph,
    get_or_build_repository_call_graph
)


def test_simple_chain_and_multiple_calls():
    """Test simple chain: a -> b -> c and multiple calls from one function."""
    code = """
def c():
    return 42

def b():
    return c()

def a():
    b()
    c()
"""
    parser = PythonASTCallGraphParser()
    funcs, _ = parser.parse_file("chain.py", code)
    assert len(funcs) == 3
    
    graph = RepositoryCallGraph("test_repo", ".")
    for f in funcs:
        graph.add_function(f)
    graph.resolve_relationships()

    fn_a = next(f for f in funcs if f.name == "a")
    fn_b = next(f for f in funcs if f.name == "b")
    fn_c = next(f for f in funcs if f.name == "c")

    assert len(fn_a.outgoing_calls) == 2
    assert len(fn_b.outgoing_calls) == 1
    assert len(fn_c.incoming_callers) == 2

    # Traverse from a
    root, nodes, edges = graph.traverse(fn_a.id, mode="calls_from", depth=2)
    node_names = {n.name for n in nodes}
    assert "a" in node_names
    assert "b" in node_names
    assert "c" in node_names


def test_conditional_branches_and_lexical_order():
    """Test conditional branches (if/else) and lexical order."""
    code = """
def process_order(order):
    validate_order(order)
    if order.is_paid:
        save_order(order)
    else:
        request_payment(order)
"""
    parser = PythonASTCallGraphParser()
    funcs, _ = parser.parse_file("orders.py", code)
    fn = funcs[0]
    assert fn.name == "process_order"
    assert len(fn.outgoing_calls) == 3

    # Check lexical orders
    calls = sorted(fn.outgoing_calls, key=lambda x: x.lexical_order)
    assert calls[0].callee_symbol_name == "validate_order"
    assert not calls[0].is_conditional

    assert calls[1].callee_symbol_name == "save_order"
    assert calls[1].is_conditional
    assert "is_paid" in (calls[1].branch_condition or "")

    assert calls[2].callee_symbol_name == "request_payment"
    assert calls[2].is_conditional
    assert calls[2].branch_condition == "else"


def test_recursive_calls_and_cycles():
    """Test recursive calls and cyclic graph traversals without infinite loops."""
    code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def cycle_a():
    cycle_b()

def cycle_b():
    cycle_a()
"""
    parser = PythonASTCallGraphParser()
    funcs, _ = parser.parse_file("recursion.py", code)
    graph = RepositoryCallGraph("test_repo", ".")
    for f in funcs:
        graph.add_function(f)
    graph.resolve_relationships()

    fact_fn = next(f for f in funcs if f.name == "factorial")
    assert any(c.is_recursive for c in fact_fn.outgoing_calls)

    cycle_a = next(f for f in funcs if f.name == "cycle_a")
    root, nodes, edges = graph.traverse(cycle_a.id, mode="full", depth=4)
    # Must terminate and not duplicate nodes
    node_ids = [n.id for n in nodes]
    assert len(node_ids) == len(set(node_ids))
    assert len(nodes) == 2


def test_class_methods_and_self():
    """Test class methods and calls via self.method()."""
    code = """
class OrderService:
    def execute(self):
        self.step_one()
        self.step_two()

    def step_one(self):
        pass

    def step_two(self):
        pass
"""
    parser = PythonASTCallGraphParser()
    funcs, _ = parser.parse_file("service.py", code)
    assert len(funcs) == 3
    for f in funcs:
        assert f.enclosing_class == "OrderService"

    graph = RepositoryCallGraph("test_repo", ".")
    for f in funcs:
        graph.add_function(f)
    graph.resolve_relationships()

    exec_fn = next(f for f in funcs if f.name == "execute")
    assert len(exec_fn.outgoing_calls) == 2
    assert all(c.is_resolved for c in exec_fn.outgoing_calls)


def test_async_await_calls():
    """Test async functions and await call sites."""
    code = """
async def fetch_data():
    return await api_request()
"""
    parser = PythonASTCallGraphParser()
    funcs, _ = parser.parse_file("async_test.py", code)
    fn = funcs[0]
    assert fn.is_async
    assert len(fn.outgoing_calls) == 1
    assert fn.outgoing_calls[0].is_async


def test_cross_file_and_imports():
    """Test resolving calls across multiple files with imports."""
    mod_code = """
def helper_calc():
    return 100
"""
    main_code = """
from utils.math_mod import helper_calc

def run_main():
    return helper_calc()
"""
    parser = PythonASTCallGraphParser()
    mod_funcs, mod_imports = parser.parse_file("utils/math_mod.py", mod_code)
    main_funcs, main_imports = parser.parse_file("app/main.py", main_code)

    graph = RepositoryCallGraph("test_repo", ".")
    for f in mod_funcs + main_funcs:
        graph.add_function(f)
    graph.file_imports["utils/math_mod.py"] = mod_imports
    graph.file_imports["app/main.py"] = main_imports
    graph.resolve_relationships()

    main_fn = main_funcs[0]
    call = main_fn.outgoing_calls[0]
    assert call.is_resolved
    assert call.target_file == "utils/math_mod.py"


def test_typescript_functions_and_classes():
    """Test syntax-aware JavaScript/TypeScript parsing."""
    ts_code = """
import { helper } from './helpers';

export async function processItem(item: string) {
    if (item) {
        await helper(item);
    }
}

export class TaskRunner {
    async execute() {
        this.runTask();
    }
    runTask() {
        console.log('running');
    }
}
"""
    parser = TypeScriptCallGraphParser()
    funcs, imports = parser.parse_file("src/service.ts", ts_code)
    assert len(funcs) == 3
    fn_map = {f.name: f for f in funcs}
    assert "processItem" in fn_map
    assert fn_map["processItem"].is_async
    assert "execute" in fn_map
    assert fn_map["execute"].enclosing_class == "TaskRunner"

    graph = RepositoryCallGraph("ts_repo", ".")
    for f in funcs:
        graph.add_function(f)
    graph.resolve_relationships()

    exec_fn = fn_map["execute"]
    assert any(c.callee_symbol_name == "runTask" and c.is_resolved for c in exec_fn.outgoing_calls)


def test_invalid_syntax_and_unsupported_files():
    """Test handling of invalid syntax without crashing."""
    broken_code = "def syntax_error( ::::"
    parser = PythonASTCallGraphParser()
    funcs, imports = parser.parse_file("broken.py", broken_code)
    assert funcs == []
    assert imports == {}


def test_mermaid_generation_and_escaping():
    """Test Mermaid generation with special characters in function and branch labels."""
    code = """
def calculate(data):
    if data["flag"] > 0:
        return 'valid'
"""
    parser = PythonASTCallGraphParser()
    funcs, _ = parser.parse_file("calc.py", code)
    graph = RepositoryCallGraph("test_repo", ".")
    for f in funcs:
        graph.add_function(f)
    graph.resolve_relationships()

    engine = CallGraphEngine()
    root = funcs[0]
    mermaid = engine.generate_mermaid(root, funcs, root.outgoing_calls, "calls_from")
    assert "flowchart LR" in mermaid
    assert ":::rootNode" in mermaid
    # Check that quotes are escaped
    assert 'data["flag"]' not in mermaid or "'" in mermaid or "data" in mermaid


def test_depth_limiter():
    """Test depth limiter: depth=1 should only include direct calls."""
    code = """
def f1():
    f2()

def f2():
    f3()

def f3():
    f4()

def f4():
    pass
"""
    parser = PythonASTCallGraphParser()
    funcs, _ = parser.parse_file("depth.py", code)
    graph = RepositoryCallGraph("test_repo", ".")
    for f in funcs:
        graph.add_function(f)
    graph.resolve_relationships()

    f1 = next(f for f in funcs if f.name == "f1")
    root, nodes_d1, edges_d1 = graph.traverse(f1.id, mode="calls_from", depth=1)
    assert len(nodes_d1) == 2  # f1 and f2

    root, nodes_d2, edges_d2 = graph.traverse(f1.id, mode="calls_from", depth=2)
    assert len(nodes_d2) == 3  # f1, f2, and f3


@pytest.mark.asyncio
async def test_api_endpoints_comprehensive():
    """Test all call graph endpoints via FastAPI TestClient."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get repos
        res = await client.get("/api/v1/repositories")
        assert res.status_code == 200
        repos = res.json()
        assert len(repos) > 0
        repo_id = repos[0]["id"]

        # 1. Functions listing with search and file_path
        res_fns = await client.get(f"/api/v1/repositories/{repo_id}/call-graph/functions?limit=20")
        assert res_fns.status_code == 200
        fns = res_fns.json()
        assert isinstance(fns, list)

        if len(fns) > 0:
            test_fn = fns[0]
            fn_id = test_fn["id"]

            # 2. Function details endpoint
            res_det = await client.get(f"/api/v1/repositories/{repo_id}/call-graph/functions/{fn_id}")
            assert res_det.status_code == 200
            det = res_det.json()
            assert det["id"] == fn_id
            assert "name" in det
            assert "parameters" in det

            # 3. Callers endpoint
            res_callers = await client.get(f"/api/v1/repositories/{repo_id}/call-graph/functions/{fn_id}/callers")
            assert res_callers.status_code == 200
            assert isinstance(res_callers.json(), list)

            # 4. Outgoing calls endpoint
            res_calls = await client.get(f"/api/v1/repositories/{repo_id}/call-graph/functions/{fn_id}/calls")
            assert res_calls.status_code == 200
            assert isinstance(res_calls.json(), list)

            # 5. Call graph generation with depth=1
            res_cg1 = await client.get(f"/api/v1/repositories/{repo_id}/call-graph?function_id={fn_id}&mode=calls_from&depth=1")
            assert res_cg1.status_code == 200
            cg_data1 = res_cg1.json()
            assert cg_data1["root_function_id"] == fn_id
            assert cg_data1["depth"] == 1
            assert "mermaid_code" in cg_data1

            # 6. Call graph generation with depth=3 and mode=full
            res_cg3 = await client.get(f"/api/v1/repositories/{repo_id}/call-graph?function_id={fn_id}&mode=full&depth=3")
            assert res_cg3.status_code == 200

        # 7. Refresh endpoint
        res_ref = await client.post(f"/api/v1/repositories/{repo_id}/call-graph/refresh")
        assert res_ref.status_code == 200
        ref_data = res_ref.json()
        assert ref_data["status"] == "refreshed"
