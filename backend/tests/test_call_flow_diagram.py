import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_call_flow_diagram_and_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Fetch repositories
        res = await client.get("/api/v1/repositories")
        assert res.status_code == 200, res.text
        repos = res.json()
        assert len(repos) > 0
        repo_id = repos[0]["id"]

        # 2. Test diagrams/callflow endpoint (Diagram Studio standard compatibility)
        res_cf = await client.get(f"/api/v1/repositories/{repo_id}/diagrams/callflow?view_mode=code")
        assert res_cf.status_code == 200, res_cf.text
        cf_data = res_cf.json()
        assert cf_data["diagram_type"] == "callflow"
        assert cf_data["view_mode"] == "code"
        assert "flowchart" in cf_data["mermaid_code"]
        assert "description" in cf_data
        assert "nodes_evidence" in cf_data
        assert isinstance(cf_data["nodes_evidence"], list)

        # 3. Test list functions endpoint
        res_fns = await client.get(f"/api/v1/repositories/{repo_id}/call-graph/functions")
        assert res_fns.status_code == 200, res_fns.text
        fns = res_fns.json()
        assert isinstance(fns, list)

        # 4. Test call-graph endpoint with defaults
        res_cg = await client.get(f"/api/v1/repositories/{repo_id}/call-graph?mode=calls_from&depth=2")
        assert res_cg.status_code == 200, res_cg.text
        cg_data = res_cg.json()
        assert cg_data["repository_id"] == repo_id
        assert cg_data["mode"] == "calls_from"
        assert cg_data["depth"] == 2
        assert "flowchart" in cg_data["mermaid_code"]
        assert "nodes" in cg_data
        assert "edges" in cg_data
        assert "explanation" in cg_data
        assert "stats" in cg_data

        # 5. Test called_by and full modes
        res_caller = await client.get(f"/api/v1/repositories/{repo_id}/call-graph?mode=called_by&depth=1")
        assert res_caller.status_code == 200

        res_full = await client.get(f"/api/v1/repositories/{repo_id}/call-graph?mode=full&depth=2")
        assert res_full.status_code == 200
