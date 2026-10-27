import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database.connection import AsyncSessionLocal
from app.models.repository import Repository
from sqlalchemy.future import select

@pytest.mark.asyncio
async def test_documentation_dashboard_and_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get existing repos
        repo_res = await client.get("/api/v1/repositories")
        assert repo_res.status_code == 200
        repos = repo_res.json()
        assert len(repos) > 0
        repo_id = repos[0]["id"]

        # 1. Fetch dashboard
        dash_res = await client.get(f"/api/v1/repositories/{repo_id}/documentation/dashboard")
        assert dash_res.status_code == 200
        dash_data = dash_res.json()
        assert "repository_name" in dash_data
        assert "coverage_score" in dash_data
        assert dash_data["total_documents"] >= 13

        # 2. List all documentation items
        list_res = await client.get(f"/api/v1/repositories/{repo_id}/documentation")
        assert list_res.status_code == 200
        items = list_res.json()
        assert len(items) >= 13
        doc_types = [i["doc_type"] for i in items]
        assert "readme" in doc_types
        assert "api_documentation" in doc_types
        assert "architecture_documentation" in doc_types
        assert "database_documentation" in doc_types

@pytest.mark.asyncio
async def test_generate_and_validate_documentation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        repo_res = await client.get("/api/v1/repositories")
        repo_id = repo_res.json()[0]["id"]

        # Generate README
        gen_res = await client.post(
            f"/api/v1/repositories/{repo_id}/documentation/generate",
            json={"doc_type": "readme", "custom_instructions": "Focus on production deployment"}
        )
        assert gen_res.status_code == 200
        gen_data = gen_res.json()
        assert gen_data["status"] == "up_to_date"
        assert len(gen_data["content"]) > 50
        assert "Ground Truth & Source References" in gen_data["content"]
        assert len(gen_data["citations"]) > 0

        # Validate documentation
        doc_id = gen_data["id"]
        val_res = await client.post(f"/api/v1/repositories/{repo_id}/documentation/{doc_id}/validate")
        assert val_res.status_code == 200
        val_data = val_res.json()
        assert "verified_claims" in val_data

        # Check versions
        v_res = await client.get(f"/api/v1/repositories/{repo_id}/documentation/{doc_id}/versions")
        assert v_res.status_code == 200
        versions = v_res.json()
        assert len(versions) >= 1

@pytest.mark.asyncio
async def test_documentation_gaps_and_coverage():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        repo_res = await client.get("/api/v1/repositories")
        repo_id = repo_res.json()[0]["id"]

        # Coverage
        cov_res = await client.get(f"/api/v1/repositories/{repo_id}/documentation/coverage")
        assert cov_res.status_code == 200
        cov_data = cov_res.json()
        assert "coverage_percentage" in cov_data
        assert "total_modules" in cov_data

        # Gaps
        gap_res = await client.get(f"/api/v1/repositories/{repo_id}/documentation/gaps")
        assert gap_res.status_code == 200
        gaps = gap_res.json()
        assert isinstance(gaps, list)

@pytest.mark.asyncio
async def test_documentation_ai_action_and_search_and_change_sync():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        repo_res = await client.get("/api/v1/repositories")
        repo_id = repo_res.json()[0]["id"]

        items_res = await client.get(f"/api/v1/repositories/{repo_id}/documentation")
        doc_id = items_res.json()[0]["id"]

        # AI Action
        ai_res = await client.post(
            f"/api/v1/repositories/{repo_id}/documentation/{doc_id}/ai-action",
            json={"action": "simplify", "selected_text": "This module enforces cryptographic boundaries."}
        )
        assert ai_res.status_code == 200
        ai_data = ai_res.json()
        assert "result" in ai_data

        # Search
        search_res = await client.post(
            f"/api/v1/repositories/{repo_id}/documentation/search?query=overview"
        )
        assert search_res.status_code == 200
        search_data = search_res.json()
        assert "results" in search_data

        # Change Impact Sync
        sync_res = await client.post(
            f"/api/v1/repositories/{repo_id}/documentation/sync-impact",
            json={"changed_files": ["backend/app/api/v1/routes.py", "backend/app/models/user.py"]}
        )
        assert sync_res.status_code == 200
        sync_data = sync_res.json()
        assert sync_data["affected_documents_count"] >= 1
