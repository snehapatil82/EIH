import pytest
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore
from app.rag.retriever import RepositoryRetriever
from app.rag.citation_builder import CitationBuilder

def test_embedding_service_deterministic_local():
    service = EmbeddingService()
    vec = service.generate_local_embedding("def authenticate_user(token): return True")
    assert len(vec) == 384
    assert isinstance(vec[0], float)

def test_vector_store_and_retrieval():
    vs = VectorStore()
    repo_id = "test_repo_123"
    
    sample_chunks = [
        {
            "file_path": "src/auth/jwt.py",
            "start_line": 1,
            "end_line": 25,
            "content": "def create_jwt_token(user_id): return 'token_abc'",
            "entity_name": "create_jwt_token",
            "entity_type": "function",
            "language": "Python"
        },
        {
            "file_path": "src/database/connection.py",
            "start_line": 1,
            "end_line": 30,
            "content": "def get_db_connection(): return engine.connect()",
            "entity_name": "get_db_connection",
            "entity_type": "function",
            "language": "Python"
        }
    ]

    indexed_count = vs.index_chunks(repo_id, sample_chunks)
    assert indexed_count == 2

    retriever = RepositoryRetriever(vector_store=vs)
    results = retriever.retrieve_context(repo_id, "How to create JWT token?", top_k=2)
    assert len(results) > 0
    assert "jwt" in results[0]["file_path"].lower()

    citations = CitationBuilder.build_citations(results)
    assert len(citations) > 0
    assert citations[0]["file_path"] == "src/auth/jwt.py"
    assert citations[0]["start_line"] == 1
    assert citations[0]["end_line"] == 25
