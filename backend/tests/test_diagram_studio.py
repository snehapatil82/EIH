import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_diagram_studio_dual_view_all_types():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get repos
        res = await client.get("/api/v1/repositories")
        assert res.status_code == 200, res.text
        repos = res.json()
        assert len(repos) > 0
        repo_id = repos[0]["id"]

        diagram_types = ["architecture", "sequence", "flowchart", "uml", "dependency", "er", "usecase", "state", "dfd"]

        for diag_type in diagram_types:
            # 1. Backward compatibility: default request (should default to code view)
            url_default = (
                f"/api/v1/repositories/{repo_id}/architecture"
                if diag_type == "architecture"
                else f"/api/v1/repositories/{repo_id}/diagrams/{diag_type}"
            )
            res_default = await client.get(url_default)
            assert res_default.status_code == 200, f"Default {diag_type} failed: {res_default.text}"
            data_default = res_default.json()
            assert data_default["diagram_type"] == diag_type
            assert data_default["view_mode"] == "code"
            assert len(data_default["mermaid_code"]) > 0
            assert "description" in data_default
            assert "nodes_evidence" in data_default
            assert isinstance(data_default["nodes_evidence"], list)

            # 2. Explicit Code View
            res_code = await client.get(f"{url_default}?view_mode=code")
            assert res_code.status_code == 200
            data_code = res_code.json()
            assert data_code["view_mode"] == "code"
            assert len(data_code["mermaid_code"]) > 0

            # 3. User Workflow View
            res_wf = await client.get(f"{url_default}?view_mode=workflow&workflow_description=User+authentication+and+task+execution")
            assert res_wf.status_code == 200, f"Workflow {diag_type} failed: {res_wf.text}"
            data_wf = res_wf.json()
            assert data_wf["diagram_type"] == diag_type
            assert data_wf["view_mode"] == "workflow"
            assert len(data_wf["mermaid_code"]) > 0
            assert "evidence_limitations" in data_wf
            assert len(data_wf["nodes_evidence"]) > 0

            # Check that evidence nodes contain required fields
            for ev in data_wf["nodes_evidence"]:
                assert "id" in ev
                assert "label" in ev
                assert "evidence_type" in ev
                assert ev["confidence"] in ("verified", "inferred")

@pytest.mark.asyncio
async def test_diagram_studio_invalid_mode_handling():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/repositories")
        repo_id = res.json()[0]["id"]

        # Invalid view mode should return 422 Unprocessable Entity
        res_invalid = await client.get(f"/api/v1/repositories/{repo_id}/diagrams/sequence?view_mode=unknown_mode")
        assert res_invalid.status_code == 422
