import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.rag.vector_store import VectorStore
from app.core.config import settings
from app.core.logging import logger
from app.repository.file_scanner import FileScanner
from app.rag.chunker import CodeAwareChunker


class RepositoryRetriever:
    def __init__(self, vector_store: Optional[VectorStore] = None):
        self.vector_store = vector_store or VectorStore()
        self.file_scanner = FileScanner()
        self.chunker = CodeAwareChunker()

    def _ensure_indexed(self, repository_id: str):
        """If repository chunks are not present in vector store, scans and indexes from disk."""
        repo_dir = Path(settings.CLONED_REPOS_DIR) / repository_id
        if not repo_dir.exists() or not repo_dir.is_dir():
            # Check if there's any directory matching repository_id in cloned_repos
            subdirs = list(Path(settings.CLONED_REPOS_DIR).glob(f"*{repository_id}*"))
            if subdirs and subdirs[0].is_dir():
                repo_dir = subdirs[0]
            else:
                return

        try:
            files_data, _, _, _ = self.file_scanner.scan_repository(repo_dir)
            all_chunks = []
            for f in files_data:
                content = f.get("content")
                if not content:
                    continue
                file_path = f["path"]
                lang = f.get("language")
                file_chunks = self.chunker.chunk_file(file_path, content, language=lang)
                all_chunks.extend(file_chunks)

            if all_chunks:
                self.vector_store.index_chunks(repository_id, all_chunks)
                logger.info(f"Dynamically indexed {len(all_chunks)} chunks for {repository_id}")
        except Exception as e:
            logger.warning(f"Dynamic re-indexing failed for {repository_id}: {e}")

    def _extract_query_symbols(self, query: str) -> List[str]:
        """Extract likely code symbol names from the query (CamelCase, snake_case, filenames)."""
        symbols = []
        # CamelCase identifiers
        symbols += re.findall(r'\b[A-Z][a-zA-Z0-9]+\b', query)
        # snake_case identifiers (more than one segment)
        symbols += re.findall(r'\b[a-z]+(?:_[a-z]+)+\b', query)
        # quoted identifiers
        symbols += re.findall(r'[`\'"]([a-zA-Z0-9_./-]+)[`\'"]', query)
        # file name references like "auth.py" or "auth_service"
        symbols += re.findall(r'\b([a-zA-Z0-9_]+\.py\b)', query)
        symbols += re.findall(r'\b([a-zA-Z0-9_]+\.ts\b)', query)
        return list(dict.fromkeys(s.lower() for s in symbols if len(s) > 2))

    def _contextualize_query(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Expands follow-up queries using conversation history to resolve pronouns like
        'that', 'it', 'this' or implicit context.
        """
        if not conversation_history:
            return query

        ql = query.lower().strip()
        followup_signals = [
            "that", "it", "this", "those", "these", "its", "there",
            "where is that", "where is it", "show me that", "how does it",
            "what about", "can you show", "which one", "why is that",
        ]
        is_followup = (
            any(sig in ql for sig in followup_signals)
            or (len(ql.split()) <= 4 and not any(k in ql for k in ["what", "how", "where", "why", "list"]))
        )

        if not is_followup:
            return query

        # Extract context terms from previous messages (most recent user or assistant turns)
        context_terms = []
        for msg in reversed(conversation_history):
            content = msg.get("content", "")
            if not content:
                continue
            # Look for mentioned entities, symbols, or key topics
            entities = re.findall(r'[`\'"]([a-zA-Z0-9_./-]+)[`\'"]', content)
            if entities:
                context_terms.extend(entities[:3])
            # Look for domain keywords in past messages
            for domain_kw in [
                "database connection", "database", "authentication", "jwt",
                "repository", "model", "api endpoint", "schema", "test",
                "sqlite", "postgres", "migration", "error handling"
            ]:
                if domain_kw in content.lower() and domain_kw not in ql:
                    context_terms.append(domain_kw)
                    break
            if context_terms:
                break

        if context_terms:
            expanded = f"{query} {' '.join(dict.fromkeys(context_terms))}"
            logger.info(f"Contextualized follow-up query: '{query}' -> '{expanded}'")
            return expanded

        return query

    def retrieve_context(
        self,
        repository_id: str,
        query: str,
        top_k: int = 5,
        target_file_filter: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves relevant source code and documentation chunks.
        Performs multi-signal boosting: fine-grained intent match, symbol match,
        file match, content keyword density, and follow-up contextualization.
        """
        search_query = self._contextualize_query(query, conversation_history)
        results = self.vector_store.query(repository_id, search_query, top_k=top_k * 3)

        # If vector store was empty (e.g. server restart with in-memory store), re-index from disk and retry
        if not results:
            self._ensure_indexed(repository_id)
            results = self.vector_store.query(repository_id, search_query, top_k=top_k * 3)

        # If still empty, scan top files directly from disk to provide context
        if not results:
            repo_dir = Path(settings.CLONED_REPOS_DIR) / repository_id
            if repo_dir.exists():
                files_data, _, _, _ = self.file_scanner.scan_repository(repo_dir)
                for f in files_data[:top_k]:
                    content = f.get("content", "")
                    if content:
                        lines = content.splitlines()
                        results.append({
                            "content": "\n".join(lines[:60]),
                            "file_path": f["path"],
                            "start_line": 1,
                            "end_line": min(len(lines), 60),
                            "entity_name": f["filename"],
                            "entity_type": "file",
                            "language": f.get("language"),
                            "score": 0.85
                        })

        if target_file_filter:
            results = [r for r in results if target_file_filter.lower() in r["file_path"].lower()]

        # ── Fine-grained Multi-signal boosting ────────────────────────────────
        query_lower = search_query.lower()
        orig_query_lower = query.lower()
        query_words = [w for w in query_lower.split() if len(w) > 2]
        query_symbols = self._extract_query_symbols(search_query)

        # Detect specific sub-intent indicators
        is_connection = any(w in query_lower for w in ["connection", "connect", "initialize", "init_db", "engine", "sessionmaker", "session", "lifespan", "startup"])
        is_technology = any(w in query_lower for w in ["which database", "what database", "dbms", "database use", "sqlite", "postgres", "dialect", "postgresql"])
        is_tables = any(w in query_lower for w in ["table", "tables", "what models", "list models", "entities", "schema structure"])
        is_relationships = any(w in query_lower for w in ["relationship", "relationships", "foreign key", "foreignkey", "cardinality", "association", "back_populates"])
        is_migrations = any(w in query_lower for w in ["migration", "migrations", "alembic", "schema migration", "revision"])
        is_db_errors = any(w in query_lower for w in ["error", "exception", "rollback", "integrityerror", "database error", "failure", "crash"])
        is_db_optimization = any(w in query_lower for w in ["optimize", "optimization", "index", "indexes", "slow query", "performance", "n+1", "eager"])
        is_db_troubleshoot = any(w in query_lower for w in ["can't connect", "cannot connect", "connection error", "connection refused", "troubleshoot"])

        for item in results:
            boost = 0.0
            file_name = (item.get("file_path") or "").lower()
            entity_name = (item.get("entity_name") or "").lower()
            content_lower = (item.get("content") or "").lower()

            # 1. Exact symbol / entity name match in query
            if entity_name and entity_name in query_lower:
                boost += 0.35
            elif any(sym in entity_name for sym in query_symbols if sym):
                boost += 0.25

            # 2. Symbol names found in file path
            if any(sym in file_name for sym in query_symbols if sym):
                boost += 0.20

            # 3. File name matches query words (strong signal)
            fname_stem = file_name.rsplit("/", 1)[-1].replace("_", " ").replace(".", " ")
            if any(w in fname_stem for w in query_words if len(w) > 3):
                boost += 0.20

            # 4. Content keyword density — more query words in content = more relevant
            keyword_hits = sum(1 for w in query_words if w in content_lower)
            if keyword_hits > 0:
                boost += min(0.20, keyword_hits * 0.04)

            # 5. Workflow / entrypoint files for flow/run/start questions
            if any(w in query_lower for w in ["workflow", "flow", "run", "entry", "start", "main", "pipeline"]):
                if any(k in file_name for k in ["main", "app", "index", "server", "router", "pipeline", "workflow", "orchestrat"]):
                    boost += 0.30

            # 6. README / docs boost for general/overview questions
            if any(w in query_lower for w in ["how", "what", "architecture", "overview", "explain", "describe"]):
                if "readme" in file_name or "doc" in file_name:
                    boost += 0.15

            # 7. Auth files for auth questions
            if any(w in query_lower for w in ["auth", "jwt", "login", "token", "password", "security"]):
                if any(k in file_name for k in ["auth", "jwt", "token", "user", "session", "security", "guard"]):
                    boost += 0.30

            # 8. Test files for test questions
            if any(w in query_lower for w in ["test", "spec", "pytest", "coverage"]):
                if "test" in file_name:
                    boost += 0.30

            # 9. Granular Database Sub-Intent Boosts (Replaces blunt keyword rule)
            if is_connection:
                if any(k in file_name for k in ["connection", "database/connection", "engine", "session", "config", "main"]):
                    boost += 0.35
                if any(k in content_lower for k in ["create_async_engine", "create_engine", "async_sessionmaker", "init_db", "get_db", "lifespan"]):
                    boost += 0.30

            if is_technology:
                if any(k in file_name for k in ["config", "settings", "docker-compose", "database", ".env"]):
                    boost += 0.35
                if any(k in content_lower for k in ["database_url", "aiosqlite", "sqlite", "postgres", "chroma"]):
                    boost += 0.25

            if is_tables:
                if any(k in file_name for k in ["models", "model", "schema"]):
                    boost += 0.35
                if "__tablename__" in content_lower or "base" in content_lower:
                    boost += 0.25

            if is_relationships:
                if "models" in file_name or "model" in file_name:
                    boost += 0.25
                if "relationship(" in content_lower or "foreignkey(" in content_lower:
                    boost += 0.40

            if is_migrations:
                if any(k in file_name for k in ["migration", "alembic", "versions", "connection"]):
                    boost += 0.35
                if any(k in content_lower for k in ["create_all", "alembic", "init_db"]):
                    boost += 0.25

            if is_db_errors:
                if any(k in content_lower for k in ["try:", "except", "rollback", "session.close", "httpexception"]):
                    boost += 0.35

            if is_db_optimization:
                if any(k in content_lower for k in ["index=true", "unique=true", "selectinload", "joinedload", "asyncsessionlocal"]):
                    boost += 0.35

            if is_db_troubleshoot:
                if any(k in file_name for k in ["config", "connection", "docker-compose", "settings"]):
                    boost += 0.35

            # General DB boost only when no specific sub-intent was detected but model/db is mentioned
            if not (is_connection or is_technology or is_tables or is_relationships or is_migrations or is_db_errors or is_db_optimization or is_db_troubleshoot):
                if any(w in query_lower for w in ["database", "db", "model", "orm"]):
                    if any(k in file_name for k in ["model", "schema", "db", "database"]):
                        boost += 0.20

            # 10. API files for API questions
            if any(w in query_lower for w in ["api", "endpoint", "route", "rest", "http", "url"]):
                if any(k in file_name for k in ["api", "route", "controller", "handler", "endpoint"]):
                    boost += 0.30

            item["score"] = min(1.0, item["score"] + boost)

        # Sort by updated boosted score
        results.sort(key=lambda x: x["score"], reverse=True)

        # Deduplicate overlapping chunks by (file_path, start_line)
        seen_keys = set()
        deduped = []
        for r in results:
            key = (r.get("file_path"), r.get("start_line"))
            if key not in seen_keys:
                seen_keys.add(key)
                deduped.append(r)

        return deduped[:top_k]
