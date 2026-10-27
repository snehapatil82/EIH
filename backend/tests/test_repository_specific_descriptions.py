"""
Tests for repository-specific diagram description generation.

Covers:
- Multi-diagram-type coverage for all 9 types
- Two different repositories producing divergent descriptions (Acceptance Criterion 1)
- Missing evidence fallback for ER diagram on DB-less repo (Acceptance Criterion 5)
- View mode switching (code vs workflow)
- Description regeneration freshness
"""

import pytest
from app.code_intelligence.diagram_description_generator import DiagramDescriptionGenerator


# ─────────────────────────────────────────────────────────────────
# Test fixtures: two synthetic repositories with distinct structures
# ─────────────────────────────────────────────────────────────────

def _make_web_api_repo():
    """A Python web API repo with routes, models, and services."""
    nodes = {
        "f1": {"type": "file", "label": "app.py", "path": "app.py", "language": "python", "line_count": 120},
        "f2": {"type": "file", "label": "routes.py", "path": "api/routes.py", "language": "python", "line_count": 80},
        "f3": {"type": "file", "label": "models.py", "path": "db/models.py", "language": "python", "line_count": 60},
        "f4": {"type": "file", "label": "service.py", "path": "services/service.py", "language": "python", "line_count": 90},
        "f5": {"type": "file", "label": "requirements.txt", "path": "requirements.txt", "language": "text", "line_count": 10},
        "c1": {"type": "class", "label": "UserModel", "file_path": "db/models.py", "start_line": 5, "end_line": 30, "signature": "class UserModel(Base)"},
        "c2": {"type": "class", "label": "OrderModel", "file_path": "db/models.py", "start_line": 32, "end_line": 55, "signature": "class OrderModel(Base)"},
        "c3": {"type": "class", "label": "AuthService", "file_path": "services/service.py", "start_line": 1, "end_line": 45, "signature": "class AuthService"},
        "fn1": {"type": "function", "label": "create_user", "file_path": "api/routes.py", "start_line": 10, "end_line": 25, "signature": "def create_user(request)"},
        "fn2": {"type": "function", "label": "login", "file_path": "api/routes.py", "start_line": 27, "end_line": 50, "signature": "def login(request)"},
        "fn3": {"type": "function", "label": "main", "file_path": "app.py", "start_line": 1, "end_line": 10, "signature": "def main()"},
        "d1": {"type": "dependency", "label": "fastapi", "version": "0.100.0", "ecosystem": "pip"},
        "d2": {"type": "dependency", "label": "sqlalchemy", "version": "2.0.0", "ecosystem": "pip"},
    }
    edges = [
        {"source": "fn1", "target": "c1", "type": "calls"},
        {"source": "fn2", "target": "c3", "type": "calls"},
        {"source": "c3", "target": "c1", "type": "dependency"},
        {"source": "f1", "target": "f2", "type": "imports"},
    ]
    endpoints = [
        {"method": "POST", "path": "/api/users", "handler": "create_user", "file": "api/routes.py"},
        {"method": "POST", "path": "/api/login", "handler": "login", "file": "api/routes.py"},
    ]
    file_to_entities = {
        "api/routes.py": ["create_user", "login"],
        "db/models.py": ["UserModel", "OrderModel"],
        "services/service.py": ["AuthService"],
    }
    return nodes, edges, endpoints, file_to_entities


def _make_data_script_repo():
    """A minimal data processing script repo with no classes or DB models."""
    nodes = {
        "f1": {"type": "file", "label": "process.py", "path": "process.py", "language": "python", "line_count": 50},
        "f2": {"type": "file", "label": "config.yaml", "path": "config.yaml", "language": "yaml", "line_count": 15},
        "f3": {"type": "file", "label": "README.md", "path": "README.md", "language": "markdown", "line_count": 20},
        "fn1": {"type": "function", "label": "run_pipeline", "file_path": "process.py", "start_line": 1, "end_line": 30, "signature": "def run_pipeline(config)"},
        "fn2": {"type": "function", "label": "load_data", "file_path": "process.py", "start_line": 32, "end_line": 50, "signature": "def load_data(path)"},
        "d1": {"type": "dependency", "label": "pandas", "version": "2.0.0", "ecosystem": "pip"},
    }
    edges = [
        {"source": "fn1", "target": "fn2", "type": "calls"},
    ]
    return nodes, edges, [], {"process.py": ["run_pipeline", "load_data"]}


ALL_DIAGRAM_TYPES = [
    "architecture", "sequence", "flowchart", "uml", "dependency", "er",
    "usecase", "state", "dfd"
]


# ─────────────────────────────────────────────────────────────────
# Test 1: All 9 diagram types produce non-empty structured output
# ─────────────────────────────────────────────────────────────────

class TestAllDiagramTypes:
    """Verify every diagram type returns non-empty summary, components, and relationships."""

    @pytest.fixture
    def web_gen(self):
        nodes, edges, endpoints, fte = _make_web_api_repo()
        return DiagramDescriptionGenerator(
            repo_name="web-api-project",
            nodes=nodes,
            edges=edges,
            endpoints=endpoints,
            file_to_entities=fte,
        )

    @pytest.mark.parametrize("diagram_type", ALL_DIAGRAM_TYPES)
    def test_code_view_returns_structured_output(self, web_gen, diagram_type):
        result = web_gen.generate(diagram_type, view_mode="code", mermaid_code="graph TD\n  A-->B")
        assert "summary" in result, f"Missing summary for {diagram_type}"
        assert "components_involved" in result, f"Missing components_involved for {diagram_type}"
        assert "key_relationships" in result, f"Missing key_relationships for {diagram_type}"
        assert "source_references" in result, f"Missing source_references for {diagram_type}"
        assert "evidence_status" in result, f"Missing evidence_status for {diagram_type}"
        assert "description" in result, f"Missing description for {diagram_type}"
        # Summary must not be empty for a repo with real entities
        assert len(result["summary"]) > 10, f"Summary too short for {diagram_type}: '{result['summary']}'"

    @pytest.mark.parametrize("diagram_type", ALL_DIAGRAM_TYPES)
    def test_workflow_view_returns_structured_output(self, web_gen, diagram_type):
        result = web_gen.generate(diagram_type, view_mode="workflow", mermaid_code="graph TD\n  A-->B")
        assert "summary" in result
        assert "description" in result
        assert isinstance(result.get("components_involved", []), list)
        assert isinstance(result.get("key_relationships", []), list)


# ─────────────────────────────────────────────────────────────────
# Test 2: Two different repos produce different descriptions
# (Acceptance Criterion 1)
# ─────────────────────────────────────────────────────────────────

class TestMultiRepoDivergence:
    """Two repos with different structure must yield different descriptions."""

    def test_architecture_descriptions_differ(self):
        nodes_a, edges_a, ep_a, fte_a = _make_web_api_repo()
        gen_a = DiagramDescriptionGenerator(
            repo_name="web-api-project", nodes=nodes_a, edges=edges_a,
            endpoints=ep_a, file_to_entities=fte_a,
        )
        nodes_b, edges_b, ep_b, fte_b = _make_data_script_repo()
        gen_b = DiagramDescriptionGenerator(
            repo_name="data-pipeline", nodes=nodes_b, edges=edges_b,
            endpoints=ep_b, file_to_entities=fte_b,
        )

        desc_a = gen_a.generate("architecture", view_mode="code")
        desc_b = gen_b.generate("architecture", view_mode="code")

        assert desc_a["summary"] != desc_b["summary"], (
            "Two different repos must produce different architecture summaries"
        )
        assert desc_a["components_involved"] != desc_b["components_involved"], (
            "Components must differ between repos"
        )

    def test_uml_descriptions_differ(self):
        nodes_a, edges_a, ep_a, fte_a = _make_web_api_repo()
        gen_a = DiagramDescriptionGenerator(
            repo_name="web-api-project", nodes=nodes_a, edges=edges_a,
            endpoints=ep_a, file_to_entities=fte_a,
        )
        nodes_b, edges_b, ep_b, fte_b = _make_data_script_repo()
        gen_b = DiagramDescriptionGenerator(
            repo_name="data-pipeline", nodes=nodes_b, edges=edges_b,
            endpoints=ep_b, file_to_entities=fte_b,
        )

        desc_a = gen_a.generate("uml", view_mode="code")
        desc_b = gen_b.generate("uml", view_mode="code")

        assert desc_a["summary"] != desc_b["summary"], (
            "UML descriptions must differ for repos with/without classes"
        )

    def test_dependency_descriptions_differ(self):
        nodes_a, edges_a, ep_a, fte_a = _make_web_api_repo()
        gen_a = DiagramDescriptionGenerator(
            repo_name="web-api-project", nodes=nodes_a, edges=edges_a,
            endpoints=ep_a, file_to_entities=fte_a,
        )
        nodes_b, edges_b, ep_b, fte_b = _make_data_script_repo()
        gen_b = DiagramDescriptionGenerator(
            repo_name="data-pipeline", nodes=nodes_b, edges=edges_b,
            endpoints=ep_b, file_to_entities=fte_b,
        )

        desc_a = gen_a.generate("dependency", view_mode="code")
        desc_b = gen_b.generate("dependency", view_mode="code")

        assert desc_a["summary"] != desc_b["summary"], (
            "Dependency descriptions must differ between repos with different packages"
        )


# ─────────────────────────────────────────────────────────────────
# Test 3: ER diagram on DB-less repo returns unverified evidence
# (Acceptance Criterion 5)
# ─────────────────────────────────────────────────────────────────

class TestMissingEvidenceFallback:
    """Repos without database models should have unverified ER evidence."""

    def test_er_on_repo_without_db_models(self):
        nodes, edges, ep, fte = _make_data_script_repo()
        gen = DiagramDescriptionGenerator(
            repo_name="data-pipeline", nodes=nodes, edges=edges,
            endpoints=ep, file_to_entities=fte,
        )
        result = gen.generate("er", view_mode="code")

        assert result["evidence_status"] == "unverified", (
            f"ER diagram on DB-less repo should be 'unverified', got '{result['evidence_status']}'"
        )
        # Must not silently fall back to generic text
        assert "could not" in result["summary"].lower() or "no database" in result["summary"].lower() or "no model" in result["summary"].lower() or "unverified" in result.get("evidence_limitations", "").lower(), (
            f"ER description for DB-less repo must explicitly mention missing evidence. Got: {result['summary']}"
        )

    def test_uml_on_repo_without_classes(self):
        nodes, edges, ep, fte = _make_data_script_repo()
        gen = DiagramDescriptionGenerator(
            repo_name="data-pipeline", nodes=nodes, edges=edges,
            endpoints=ep, file_to_entities=fte,
        )
        result = gen.generate("uml", view_mode="code")

        # The repo has no classes, so evidence should be partial or unverified
        assert result["evidence_status"] in ("partial", "unverified"), (
            f"UML for repo without classes should be partial/unverified, got '{result['evidence_status']}'"
        )


# ─────────────────────────────────────────────────────────────────
# Test 4: Descriptions reference real project identifiers
# (Acceptance Criterion 3)
# ─────────────────────────────────────────────────────────────────

class TestDescriptionsReferenceRealEntities:
    """Descriptions must name real files and code entities."""

    def test_architecture_references_repo_name(self):
        nodes, edges, ep, fte = _make_web_api_repo()
        gen = DiagramDescriptionGenerator(
            repo_name="web-api-project", nodes=nodes, edges=edges,
            endpoints=ep, file_to_entities=fte,
        )
        result = gen.generate("architecture", view_mode="code")
        summary = result["summary"].lower()
        desc = result["description"].lower()
        combined = summary + " " + desc

        assert "web-api-project" in combined, (
            f"Architecture description must reference repo name 'web-api-project'. Got: {result['summary']}"
        )

    def test_source_references_contain_real_file_paths(self):
        nodes, edges, ep, fte = _make_web_api_repo()
        gen = DiagramDescriptionGenerator(
            repo_name="web-api-project", nodes=nodes, edges=edges,
            endpoints=ep, file_to_entities=fte,
        )
        result = gen.generate("architecture", view_mode="code")
        refs = result.get("source_references", [])
        # Should reference actual files from the repo
        all_paths = {f["path"] for f in gen.files}
        if refs:
            # At least one reference should match an actual file
            matched = any(
                any(fp in ref for fp in all_paths)
                for ref in refs
            )
            assert matched, f"Source references {refs} should contain actual file paths from {all_paths}"

    def test_components_involved_contain_real_identifiers(self):
        nodes, edges, ep, fte = _make_web_api_repo()
        gen = DiagramDescriptionGenerator(
            repo_name="web-api-project", nodes=nodes, edges=edges,
            endpoints=ep, file_to_entities=fte,
        )
        result = gen.generate("uml", view_mode="code")
        components = result.get("components_involved", [])
        if components:
            all_names = {n.get("label", "") for n in nodes.values()}
            all_paths = {f["path"] for f in gen.files}
            combined = all_names | all_paths
            # At least one component must reference something real
            matched = any(
                any(real in comp for real in combined)
                for comp in components
            )
            assert matched, f"Components {components} should reference real entities from {combined}"


# ─────────────────────────────────────────────────────────────────
# Test 5: View mode switching produces distinct descriptions
# ─────────────────────────────────────────────────────────────────

class TestViewModeSwitching:
    """Code view and workflow view must produce different descriptions."""

    def test_code_vs_workflow_architecture(self):
        nodes, edges, ep, fte = _make_web_api_repo()
        gen = DiagramDescriptionGenerator(
            repo_name="web-api-project", nodes=nodes, edges=edges,
            endpoints=ep, file_to_entities=fte,
        )
        code_result = gen.generate("architecture", view_mode="code")
        workflow_result = gen.generate("architecture", view_mode="workflow")

        # At minimum, the summaries should differ since code view vs workflow view
        # describe different perspectives
        assert code_result["summary"] != workflow_result["summary"], (
            "Code view and workflow view must produce different summaries"
        )


# ─────────────────────────────────────────────────────────────────
# Test 6: Regeneration freshness - same inputs same output (deterministic)
# ─────────────────────────────────────────────────────────────────

class TestRegenerationDeterminism:
    """Calling generate twice with same inputs should produce identical descriptions."""

    def test_same_input_same_output(self):
        nodes, edges, ep, fte = _make_web_api_repo()
        gen = DiagramDescriptionGenerator(
            repo_name="web-api-project", nodes=nodes, edges=edges,
            endpoints=ep, file_to_entities=fte,
        )
        result1 = gen.generate("architecture", view_mode="code", mermaid_code="graph TD\n  A-->B")
        result2 = gen.generate("architecture", view_mode="code", mermaid_code="graph TD\n  A-->B")

        assert result1["summary"] == result2["summary"]
        assert result1["description"] == result2["description"]
        assert result1["components_involved"] == result2["components_involved"]
        assert result1["key_relationships"] == result2["key_relationships"]
        assert result1["evidence_status"] == result2["evidence_status"]
