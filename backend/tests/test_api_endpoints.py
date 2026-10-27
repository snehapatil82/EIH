import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database.connection import init_db

@pytest.mark.asyncio
async def test_health_check_endpoint():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "Engineering Intelligence Hub" in data["service"]

@pytest.mark.asyncio
async def test_research_benchmarks_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/research/benchmarks")
        assert response.status_code == 200
        data = response.json()
        assert "single_agent_metrics" in data
        assert "multi_agent_metrics" in data
