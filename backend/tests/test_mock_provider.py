"""
Comprehensive tests for HighFidelityMockProvider — verifies that the provider
generates DISTINCT, question-specific answers (not generic templates) from
real retrieved code chunks.
"""
import asyncio
import pytest
from app.llm.mock_provider import HighFidelityMockProvider

# ──────────────────────────── shared fixtures ───────────────────────────────

AUTH_CHUNK = {
    "file_path": "backend/app/api/v1/auth.py",
    "start_line": 1,
    "end_line": 45,
    "content": """
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

SECRET_KEY = "super-secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
""",
    "entity_name": "create_access_token",
    "entity_type": "function",
    "language": "Python",
    "score": 0.95,
}

DB_CHUNK = {
    "file_path": "backend/app/models/repository.py",
    "start_line": 1,
    "end_line": 40,
    "content": """
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from app.database.base import Base
import datetime

class Repository(Base):
    \"\"\"SQLAlchemy ORM model for a GitHub/GitLab repository.\"\"\"
    __tablename__ = "repositories"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    owner = Column(String(255), nullable=False)
    url = Column(String(512), unique=True, index=True)
    status = Column(String(50), default="pending")
    languages = Column(JSON, default=dict)
    total_files = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    files = relationship("RepositoryFile", back_populates="repository", cascade="all, delete-orphan")
""",
    "entity_name": "Repository",
    "entity_type": "class",
    "language": "Python",
    "score": 0.90,
}

API_CHUNK = {
    "file_path": "backend/app/api/v1/repositories.py",
    "start_line": 10,
    "end_line": 60,
    "content": """
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.models.repository import Repository

router = APIRouter(tags=["Repositories"])

@router.get("/repositories", response_model=List[RepositoryResponse])
async def list_repositories(db: AsyncSession = Depends(get_db)):
    \"\"\"Return all tracked repositories.\"\"\"
    result = await db.execute(select(Repository))
    return result.scalars().all()

@router.post("/repositories", response_model=RepositoryResponse, status_code=201)
async def create_repository(payload: CreateRepositoryRequest, db: AsyncSession = Depends(get_db)):
    \"\"\"Clone and index a new repository.\"\"\"
    repo = Repository(id=str(uuid4()), name=payload.name, url=payload.url, owner=payload.owner)
    db.add(repo)
    await db.commit()
    return repo

@router.delete("/repositories/{repo_id}", status_code=204)
async def delete_repository(repo_id: str, db: AsyncSession = Depends(get_db)):
    \"\"\"Remove a repository and all its indexed data.\"\"\"
    ...
""",
    "entity_name": "list_repositories",
    "entity_type": "function",
    "language": "Python",
    "score": 0.88,
}

TEST_CHUNK = {
    "file_path": "backend/tests/test_api_endpoints.py",
    "start_line": 1,
    "end_line": 30,
    "content": """
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_list_repositories_empty():
    response = client.get("/api/v1/repositories")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_repository():
    payload = {"name": "my-repo", "url": "https://github.com/x/y", "owner": "x"}
    response = client.post("/api/v1/repositories", json=payload)
    assert response.status_code == 201
""",
    "entity_name": "test_health_check",
    "entity_type": "function",
    "language": "Python",
    "score": 0.82,
}

MAIN_CHUNK = {
    "file_path": "backend/app/main.py",
    "start_line": 1,
    "end_line": 35,
    "content": """
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.connection import init_db
from app.api.v1.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="Engineering Intelligence Hub", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(api_router, prefix="/api/v1")
""",
    "entity_name": "lifespan",
    "entity_type": "function",
    "language": "Python",
    "score": 0.80,
}

ALL_CHUNKS = [AUTH_CHUNK, DB_CHUNK, API_CHUNK, TEST_CHUNK, MAIN_CHUNK]


# ──────────────────────────── helper ────────────────────────────────────────

def run(coro):
    return asyncio.run(coro)


provider = HighFidelityMockProvider()


# ──────────────────────────── answer uniqueness tests ───────────────────────

def test_auth_question_mentions_jwt():
    answer = run(provider.generate_response(
        "How does authentication work in this project?",
        context_chunks=[AUTH_CHUNK, DB_CHUNK]
    ))
    answer_lower = answer.lower()
    # Must reference something auth-specific from the actual chunk
    assert any(kw in answer_lower for kw in ["jwt", "token", "oauth", "verify_password", "create_access_token",
                                               "bearer", "bcrypt", "hs256"]), \
        f"Auth answer should mention JWT/token keywords; got:\n{answer[:500]}"


def test_db_question_mentions_model_class():
    answer = run(provider.generate_response(
        "How is the database model structured?",
        context_chunks=[DB_CHUNK, MAIN_CHUNK]
    ))
    answer_lower = answer.lower()
    assert any(kw in answer_lower for kw in ["repository", "column", "sqlalchemy", "orm", "table",
                                               "relationship", "base"]), \
        f"DB answer should mention ORM/model keywords; got:\n{answer[:500]}"


def test_api_question_mentions_routes():
    answer = run(provider.generate_response(
        "Which API endpoints are defined?",
        context_chunks=[API_CHUNK, MAIN_CHUNK]
    ))
    answer_lower = answer.lower()
    assert any(kw in answer_lower for kw in ["router", "endpoint", "get", "post", "delete",
                                               "repositories", "fastapi"]), \
        f"API answer should mention routes; got:\n{answer[:500]}"


def test_test_question_mentions_test_functions():
    answer = run(provider.generate_response(
        "How are the tests organized in this project?",
        context_chunks=[TEST_CHUNK, MAIN_CHUNK]
    ))
    answer_lower = answer.lower()
    assert any(kw in answer_lower for kw in ["test", "pytest", "assert", "testclient", "fixture"]), \
        f"Test answer should mention pytest/test functions; got:\n{answer[:500]}"


def test_answers_are_different_for_different_questions():
    """The core test: two different questions must NOT produce the same answer."""
    auth_answer = run(provider.generate_response(
        "How does authentication work?",
        context_chunks=ALL_CHUNKS
    ))
    db_answer = run(provider.generate_response(
        "Where is the database connection initialized?",
        context_chunks=ALL_CHUNKS
    ))
    # Answers must differ substantially (not just header)
    assert auth_answer != db_answer, "Two different questions must not return identical answers"
    # The auth answer should be more about auth, not DB
    assert auth_answer.count("jwt") + auth_answer.count("token") + auth_answer.count("oauth") > \
           db_answer.count("jwt") + db_answer.count("token") + db_answer.count("oauth"), \
        "Auth answer should mention JWT/tokens more than DB answer"


def test_code_snippet_included_in_answer():
    """Every answer must include actual code from the chunks (a code block)."""
    answer = run(provider.generate_response(
        "Explain the repository model",
        context_chunks=[DB_CHUNK]
    ))
    assert "```" in answer, "Answer must include a fenced code block with real source code"


def test_newcomer_section_always_present():
    """All answers should contain a newcomer-friendly explanation."""
    answer = run(provider.generate_response(
        "What does the main entrypoint do?",
        context_chunks=[MAIN_CHUNK]
    ))
    assert any(kw in answer.lower() for kw in ["newcomer", "new user", "for new", "💡"]), \
        f"Answer should contain a newcomer section; got:\n{answer[:500]}"


def test_no_context_gives_helpful_message():
    """When no chunks are provided, the user should get actionable guidance."""
    answer = run(provider.generate_response("What is this codebase?", context_chunks=[]))
    assert any(kw in answer.lower() for kw in ["index", "analyse", "no indexed", "vector store", "repository explorer"]), \
        f"No-context answer should guide user to index repo; got:\n{answer}"


def test_file_path_cited_in_answer():
    """The answer must reference the actual file path from chunks."""
    answer = run(provider.generate_response(
        "How does JWT token creation work?",
        context_chunks=[AUTH_CHUNK]
    ))
    assert "auth.py" in answer.lower() or "api/v1/auth" in answer.lower(), \
        f"Answer should cite the auth.py file path; got:\n{answer[:500]}"
