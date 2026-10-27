import os
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from app.core.config import settings
from app.core.logging import logger
from app.rag.embeddings import EmbeddingService

class VectorStore:
    """
    Unified Vector Store interface for repository code chunks.
    Uses ChromaDB with an in-memory vector fallback if ChromaDB is unavailable.
    """
    _shared_memory_store: Dict[str, List[Dict[str, Any]]] = {}

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self._chroma_client = None
        self._memory_store = VectorStore._shared_memory_store

        self._init_chroma()

    def _init_chroma(self):
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            self._chroma_client = chromadb.PersistentClient(
                path=str(settings.CHROMA_PERSIST_DIR)
            )
            logger.info("ChromaDB persistent client initialized successfully.")
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed: {e}. Using in-memory fallback.")
            self._chroma_client = None

    def _get_collection_name(self, repository_id: str) -> str:
        # Chroma collection names must be 3-63 chars alphanumeric
        clean_id = repository_id.replace("-", "_")
        return f"repo_{clean_id}"[:63]

    def index_chunks(self, repository_id: str, chunks: List[Dict[str, Any]]) -> int:
        if not chunks:
            return 0

        texts = [c["content"] for c in chunks]
        embeddings = self.embedding_service.embed_documents(texts)
        ids = [str(uuid.uuid4()) for _ in chunks]

        # Try ChromaDB first
        if self._chroma_client:
            try:
                coll_name = self._get_collection_name(repository_id)
                # Delete existing collection if re-indexing
                try:
                    self._chroma_client.delete_collection(name=coll_name)
                except Exception:
                    pass

                collection = self._chroma_client.create_collection(
                    name=coll_name,
                    metadata={"hnsw:space": "cosine"}
                )

                metadatas = []
                for c in chunks:
                    metadatas.append({
                        "file_path": c["file_path"],
                        "start_line": int(c.get("start_line", 1)),
                        "end_line": int(c.get("end_line", 1)),
                        "entity_name": str(c.get("entity_name") or ""),
                        "entity_type": str(c.get("entity_type") or ""),
                        "language": str(c.get("language") or "")
                    })

                # Batch add in chunks of 200
                batch_size = 200
                for i in range(0, len(chunks), batch_size):
                    end_idx = min(len(chunks), i + batch_size)
                    collection.add(
                        ids=ids[i:end_idx],
                        embeddings=embeddings[i:end_idx],
                        documents=texts[i:end_idx],
                        metadatas=metadatas[i:end_idx]
                    )
                logger.info(f"Indexed {len(chunks)} chunks into ChromaDB collection {coll_name}")
                return len(chunks)
            except Exception as e:
                logger.error(f"Failed indexing in ChromaDB: {e}. Falling back to memory store.")

        # In-Memory fallback store
        items = []
        for i, c in enumerate(chunks):
            items.append({
                "id": ids[i],
                "content": c["content"],
                "file_path": c["file_path"],
                "start_line": c.get("start_line", 1),
                "end_line": c.get("end_line", 1),
                "entity_name": c.get("entity_name"),
                "entity_type": c.get("entity_type"),
                "language": c.get("language"),
                "vector": np.array(embeddings[i], dtype=np.float32)
            })
        self._memory_store[repository_id] = items
        logger.info(f"Indexed {len(chunks)} chunks into in-memory store for repository {repository_id}")
        return len(chunks)

    def query(self, repository_id: str, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_vec = self.embedding_service.embed_query(query_text)

        # Query ChromaDB if available
        if self._chroma_client:
            try:
                coll_name = self._get_collection_name(repository_id)
                collection = self._chroma_client.get_collection(name=coll_name)
                results = collection.query(
                    query_embeddings=[query_vec],
                    n_results=top_k,
                    include=["documents", "metadatas", "distances"]
                )

                formatted = []
                if results and "documents" in results and results["documents"]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0]
                    distances = results.get("distances", [[0]*len(docs)])[0]

                    for doc, meta, dist in zip(docs, metas, distances):
                        # Convert distance to similarity score
                        score = max(0.0, 1.0 - float(dist)) if dist is not None else 0.8
                        formatted.append({
                            "content": doc,
                            "file_path": meta.get("file_path"),
                            "start_line": meta.get("start_line"),
                            "end_line": meta.get("end_line"),
                            "entity_name": meta.get("entity_name"),
                            "entity_type": meta.get("entity_type"),
                            "language": meta.get("language"),
                            "score": round(score, 4)
                        })
                return formatted
            except Exception as e:
                logger.warning(f"Chroma query failed: {e}. Falling back to memory store.")

        # In-Memory Cosine Similarity query
        items = self._memory_store.get(repository_id, [])
        if not items:
            return []

        q_arr = np.array(query_vec, dtype=np.float32)
        q_norm = np.linalg.norm(q_arr)
        if q_norm < 1e-6:
            q_norm = 1.0

        scored = []
        for item in items:
            v = item["vector"]
            v_norm = np.linalg.norm(v)
            if v_norm < 1e-6:
                v_norm = 1.0
            cos_sim = float(np.dot(q_arr, v) / (q_norm * v_norm))
            scored.append((cos_sim, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_items = scored[:top_k]

        return [{
            "content": item["content"],
            "file_path": item["file_path"],
            "start_line": item["start_line"],
            "end_line": item["end_line"],
            "entity_name": item["entity_name"],
            "entity_type": item["entity_type"],
            "language": item["language"],
            "score": round(score, 4)
        } for score, item in top_items]
