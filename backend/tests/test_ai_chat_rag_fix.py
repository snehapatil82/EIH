"""
Regression and verification test suite for AI Chat and RAG Fix:
Ensures distinct, question-specific responses for queries with shared keywords (e.g. 'database'),
verifies granular retrieval boosting, multi-turn follow-up context resolution, and honest fallbacks.
"""
import asyncio
import pytest
from app.llm.mock_provider import HighFidelityMockProvider
from app.rag.retriever import RepositoryRetriever
from app.rag.vector_store import VectorStore

def run(coro):
    return asyncio.run(coro)

# Sample rich codebase context chunks mirroring real repository files
CONN_CHUNK = {
    "file_path": "backend/app/database/connection.py",
    "start_line": 1,
    "end_line": 42,
    "content": """
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.database.base import Base

async_engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    import app.models.repository
    import app.models.chat
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
""",
    "entity_name": "create_async_engine",
    "entity_type": "function",
    "language": "Python",
    "score": 0.88,
}

CONFIG_CHUNK = {
    "file_path": "backend/app/core/config.py",
    "start_line": 35,
    "end_line": 55,
    "content": """
    PORT: int = 8000
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR / 'eih_data.db'}"
    SYNC_DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'eih_data.db'}"
    CHROMA_PERSIST_DIR: Path = BASE_DIR / "chroma_db"
    LLM_PROVIDER: str = "mock"
""",
    "entity_name": "Settings",
    "entity_type": "class",
    "language": "Python",
    "score": 0.85,
}

MODEL_CHUNK = {
    "file_path": "backend/app/models/repository.py",
    "start_line": 1,
    "end_line": 35,
    "content": """
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base

class Repository(Base):
    __tablename__ = "repositories"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(String(512), unique=True, index=True)
    files = relationship("RepositoryFile", back_populates="repository", cascade="all, delete-orphan")

class RepositoryFile(Base):
    __tablename__ = "repository_files"
    id = Column(String(36), primary_key=True)
    repository_id = Column(String(36), ForeignKey("repositories.id"), nullable=False)
    repository = relationship("Repository", back_populates="files")
""",
    "entity_name": "Repository",
    "entity_type": "class",
    "language": "Python",
    "score": 0.87,
}

CHAT_API_CHUNK = {
    "file_path": "backend/app/api/v1/chat.py",
    "start_line": 20,
    "end_line": 70,
    "content": """
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.database.connection import get_db

@router.get("/repositories/{repository_id}/conversations")
async def list_conversations(repository_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.repository_id == repository_id)
        .options(selectinload(Conversation.messages))
        .order_by(Conversation.updated_at.desc())
    )
    return result.scalars().all()
""",
    "entity_name": "list_conversations",
    "entity_type": "function",
    "language": "Python",
    "score": 0.86,
}

ALL_TEST_CHUNKS = [CONN_CHUNK, CONFIG_CHUNK, MODEL_CHUNK, CHAT_API_CHUNK]
provider = HighFidelityMockProvider()

# ────────────────────────── Distinct Answers for Database Questions ──────────────────────────

def test_database_questions_produce_distinct_answers():
    """Verify that different database questions do NOT produce identical boilerplate answers."""
    questions = [
        "Where is the database connection initialized?",
        "Which database does the project use?",
        "What tables exist?",
        "How are database migrations handled?",
        "How are database errors handled?",
        "What relationships exist between models?",
        "How do I optimize database queries?",
        "Why can't I connect to the database?",
    ]

    answers = {}
    for q in questions:
        ans = run(provider.generate_response(q, context_chunks=ALL_TEST_CHUNKS))
        answers[q] = ans

    # Pairwise comparison: ensure every answer is unique
    q_list = list(questions)
    for i in range(len(q_list)):
        for j in range(i + 1, len(q_list)):
            q1, q2 = q_list[i], q_list[j]
            ans1, ans2 = answers[q1], answers[q2]
            assert ans1 != ans2, f"Answers for '{q1}' and '{q2}' must not be identical!"


def test_db_connection_answer_content():
    """'Where is the database connection initialized?' must target connection/engine files and lines."""
    ans = run(provider.generate_response("Where is the database connection initialized?", context_chunks=ALL_TEST_CHUNKS))
    ans_lower = ans.lower()
    assert any(term in ans_lower for term in ["create_async_engine", "async_engine", "connection.py", "init_db", "async_sessionmaker"]), \
        f"Connection answer must explain engine/connection setup; got:\n{ans[:400]}"
    assert "lifespan" in ans_lower or "get_db" in ans_lower


def test_db_technology_answer_content():
    """'Which database does the project use?' must identify SQLite, aiosqlite, Postgres, ChromaDB."""
    ans = run(provider.generate_response("Which database does the project use?", context_chunks=ALL_TEST_CHUNKS))
    ans_lower = ans.lower()
    assert "sqlite" in ans_lower, "Technology answer must mention SQLite"
    assert "chroma" in ans_lower or "vector" in ans_lower, "Technology answer should mention ChromaDB / vector store"
    assert "aiosqlite" in ans_lower or "database_url" in ans_lower


def test_db_tables_answer_content():
    """'What tables exist?' must list the declared tables across models."""
    ans = run(provider.generate_response("What tables exist?", context_chunks=ALL_TEST_CHUNKS))
    ans_lower = ans.lower()
    assert "repositories" in ans_lower
    assert "repository_files" in ans_lower
    assert "conversations" in ans_lower or "messages" in ans_lower


def test_db_migrations_honest_fallback():
    """'How are database migrations handled?' must honestly report that Alembic is not used, and explain create_all."""
    ans = run(provider.generate_response("How are database migrations handled?", context_chunks=ALL_TEST_CHUNKS))
    ans_lower = ans.lower()
    assert "alembic" in ans_lower
    assert any(term in ans_lower for term in ["not employ", "no alembic", "not use", "create_all", "init_db"]), \
        f"Migration answer must honestly state migration status; got:\n{ans[:400]}"


def test_db_errors_answer_content():
    """'How are database errors handled?' must explain finally block, session.close, and rollback."""
    ans = run(provider.generate_response("How are database errors handled?", context_chunks=ALL_TEST_CHUNKS))
    ans_lower = ans.lower()
    assert any(term in ans_lower for term in ["finally", "close", "rollback", "leak", "integrityerror"]), \
        f"Error handling answer must mention resource cleanup / rollback; got:\n{ans[:400]}"


def test_db_relationships_answer_content():
    """'What relationships exist between models?' must explain foreign keys, 1:N cardinality, cascade delete."""
    ans = run(provider.generate_response("What relationships exist between models?", context_chunks=ALL_TEST_CHUNKS))
    ans_lower = ans.lower()
    assert "relationship" in ans_lower
    assert "foreignkey" in ans_lower or "foreign key" in ans_lower
    assert "cascade" in ans_lower or "delete-orphan" in ans_lower


def test_db_optimization_answer_content():
    """'How do I optimize database queries?' must explain selectinload, indexing, async."""
    ans = run(provider.generate_response("How do I optimize database queries?", context_chunks=ALL_TEST_CHUNKS))
    ans_lower = ans.lower()
    assert "selectinload" in ans_lower or "n+1" in ans_lower
    assert "index" in ans_lower or "async" in ans_lower


def test_db_troubleshooting_answer_content():
    """'Why can't I connect to the database?' must provide diagnostic checklist."""
    ans = run(provider.generate_response("Why can't I connect to the database?", context_chunks=ALL_TEST_CHUNKS))
    ans_lower = ans.lower()
    assert "database_url" in ans_lower or ".env" in ans_lower
    assert "permission" in ans_lower or "sqlite" in ans_lower or "docker" in ans_lower


# ────────────────────────── Conversation History & Follow-ups ──────────────────────────

def test_followup_question_resolves_context():
    """A follow-up question like 'Where is that configured?' resolves 'that' using conversation history."""
    history = [
        {"role": "user", "content": "Where is the database connection initialized?"},
        {"role": "assistant", "content": "The database connection is initialized in app/database/connection.py using create_async_engine(settings.DATABASE_URL)."}
    ]
    ans = run(provider.generate_response(
        "Where is that configured?",
        context_chunks=ALL_TEST_CHUNKS,
        conversation_history=history
    ))
    ans_lower = ans.lower()
    assert any(term in ans_lower for term in ["config", "database_url", "setting", "env"]), \
        f"Follow-up about connection config should reference config/settings; got:\n{ans[:400]}"


def test_unrelated_question_does_not_inherit_stale_history():
    """An unrelated topic change (e.g. asking about API endpoints after database) must NOT inherit stale answers."""
    history = [
        {"role": "user", "content": "Where is the database connection initialized?"},
        {"role": "assistant", "content": "The database connection is initialized in app/database/connection.py."}
    ]
    ans = run(provider.generate_response(
        "Which API endpoints are defined in the repository?",
        context_chunks=ALL_TEST_CHUNKS,
        conversation_history=history
    ))
    ans_lower = ans.lower()
    assert any(term in ans_lower for term in ["endpoint", "route", "get", "post", "conversations"]), \
        f"API question should answer about endpoints, not stale database connection; got:\n{ans[:400]}"


# ────────────────────────── Fine-Grained Retrieval Boosting ──────────────────────────

def test_retriever_sub_intent_boosting():
    """RepositoryRetriever boosts connection.py for connection queries and models for tables queries."""
    vs = VectorStore()
    repo_id = "test_sub_intent_repo"
    vs.index_chunks(repo_id, ALL_TEST_CHUNKS)

    retriever = RepositoryRetriever(vector_store=vs)

    # 1. Connection query should boost connection.py to top
    conn_results = retriever.retrieve_context(repo_id, "Where is the database connection initialized?", top_k=2)
    assert len(conn_results) > 0
    assert "connection" in conn_results[0]["file_path"].lower() or "connection" in conn_results[0]["content"].lower()

    # 2. Table query should boost models to top
    table_results = retriever.retrieve_context(repo_id, "What tables exist?", top_k=2)
    assert len(table_results) > 0
    assert "model" in table_results[0]["file_path"].lower() or "__tablename__" in table_results[0]["content"].lower()
