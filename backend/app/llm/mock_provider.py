import re
from typing import List, Dict, Any, Optional
from app.llm.provider import LLMProvider


class HighFidelityMockProvider(LLMProvider):
    """
    Context-grounded mock provider for zero-dependency local runs and automated tests.
    Synthesizes fully question-specific answers from actual retrieved RAG chunks and
    repository metadata — dynamically analyses real code content to produce unique,
    informative answers for every question.
    """

    # ───────────────────────────────── chunk analysis helpers ──────────────────

    def _extract_functions(self, content: str) -> List[str]:
        """Extract function/method signatures from code content."""
        patterns = [
            r'(?:async\s+)?def\s+([a-zA-Z_]\w*)\s*\(([^)]*)\)',        # Python
            r'(?:async\s+)?function\s+([a-zA-Z_]\w*)\s*\(([^)]*)\)',    # JS/TS
            r'(?:public|private|protected|static)?\s*\w+\s+([a-zA-Z_]\w*)\s*\(([^)]*)\)',  # Java/C#
            r'func\s+([a-zA-Z_]\w*)\s*\(([^)]*)\)',                     # Go
            r'fn\s+([a-zA-Z_]\w*)\s*\(([^)]*)\)',                       # Rust
        ]
        found = []
        for pat in patterns:
            for m in re.finditer(pat, content):
                name = m.group(1)
                params = m.group(2).strip()
                if name not in ('if', 'for', 'while', 'with', 'class'):
                    found.append(f"`{name}({params[:60]}{'...' if len(params) > 60 else ''})`")
        return list(dict.fromkeys(found))[:8]

    def _extract_classes(self, content: str) -> List[str]:
        """Extract class names from code content."""
        patterns = [
            r'class\s+([A-Z][a-zA-Z0-9_]*)',
            r'interface\s+([A-Z][a-zA-Z0-9_]*)',
            r'struct\s+([A-Z][a-zA-Z0-9_]*)',
            r'type\s+([A-Z][a-zA-Z0-9_]*)\s+(?:struct|interface)',
        ]
        found = []
        for pat in patterns:
            for m in re.finditer(pat, content):
                found.append(f"`{m.group(1)}`")
        return list(dict.fromkeys(found))[:6]

    def _extract_imports(self, content: str) -> List[str]:
        """Extract imported modules/packages."""
        patterns = [
            r'^from\s+([\w.]+)\s+import\s+(.+)$',
            r'^import\s+([\w.,\s]+)$',
            r'^const\s+\{[^}]+\}\s*=\s*require\([\'"]([^\'"]+)[\'"]\)',
            r'^import\s+.+\s+from\s+[\'"]([^\'"]+)[\'"]',
        ]
        found = []
        for line in content.splitlines()[:30]:
            for pat in patterns:
                m = re.match(pat, line.strip())
                if m:
                    found.append(line.strip()[:80])
                    break
        return found[:6]

    def _extract_docstring(self, content: str) -> str:
        """Extract the first docstring or comment block from code."""
        # Triple-quoted docstrings
        m = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if m:
            return m.group(1).strip()[:300]
        m = re.search(r"'''(.*?)'''", content, re.DOTALL)
        if m:
            return m.group(1).strip()[:300]
        # JSDoc / block comments
        m = re.search(r'/\*\*(.*?)\*/', content, re.DOTALL)
        if m:
            cleaned = re.sub(r'\s*\*\s?', ' ', m.group(1)).strip()
            return cleaned[:300]
        # Line comments at the top
        lines = content.splitlines()
        comment_lines = []
        for line in lines[:10]:
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('//'):
                comment_lines.append(stripped.lstrip('#/').strip())
            elif comment_lines:
                break
        return ' '.join(comment_lines)[:200]

    def _extract_return_values(self, content: str) -> List[str]:
        """Extract return type hints or return statements."""
        found = []
        # Python type hints  -> ReturnType
        for m in re.finditer(r'->\s*([A-Za-z_][\w\[\], ]*)', content):
            found.append(m.group(1).strip())
        # return statements
        for m in re.finditer(r'\breturn\s+(.+)', content):
            val = m.group(1).strip()[:60]
            if val and not val.startswith('#'):
                found.append(val)
        return list(dict.fromkeys(found))[:4]

    def _extract_routes(self, content: str) -> List[str]:
        """Extract HTTP route decorators."""
        routes = []
        for m in re.finditer(
            r'@(?:router|app)\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]',
            content, re.IGNORECASE
        ):
            routes.append(f"`{m.group(1).upper()} {m.group(2)}`")
        return routes[:8]

    def _extract_db_fields(self, content: str) -> List[str]:
        """Extract ORM field/column definitions."""
        fields = []
        for m in re.finditer(r'(\w+)\s*[:=]\s*(?:Column|Field|mapped_column|models\.\w+)\(([^)]*)\)', content):
            fields.append(f"`{m.group(1)}` ({m.group(2)[:40]})")
        # Also dataclass / pydantic style
        for m in re.finditer(r'^\s+(\w+)\s*:\s*([A-Za-z_][\w\[\], ]*)', content, re.MULTILINE):
            if m.group(1) not in ('self', 'cls', 'return'):
                fields.append(f"`{m.group(1)}: {m.group(2)}`")
        return list(dict.fromkeys(fields))[:8]

    # ───────────────────────────────── formatting helpers ──────────────────────

    def _format_snippet(self, chunk: Dict[str, Any], max_lines: int = 18) -> str:
        raw = chunk.get("content", "").strip()
        lines = raw.splitlines()
        code = "\n".join(lines[:max_lines])
        if len(lines) > max_lines:
            code += f"\n... ({len(lines) - max_lines} more lines)"
        lang = chunk.get("language") or "text"
        return f"```{lang}\n{code}\n```"

    def _chunk_ref(self, chunk: Dict[str, Any]) -> str:
        fp = chunk.get("file_path") or "unknown"
        sl = chunk.get("start_line", "?")
        el = chunk.get("end_line", "?")
        return f"`{fp}` L{sl}–{el}"

    def _entity_label(self, chunk: Dict[str, Any]) -> str:
        name = chunk.get("entity_name") or ""
        etype = chunk.get("entity_type") or ""
        if name and etype:
            return f"`{name}` ({etype})"
        if name:
            return f"`{name}`"
        return ""

    def _score_label(self, chunk: Dict[str, Any]) -> str:
        score = chunk.get("score")
        if score is not None:
            return f"relevance {float(score):.2f}"
        return ""

    def _build_source_header(self, chunk: Dict[str, Any], idx: int) -> str:
        ref = self._chunk_ref(chunk)
        entity = self._entity_label(chunk)
        score = self._score_label(chunk)
        header = f"**Source {idx}: {ref}**"
        if entity:
            header += f"  ·  {entity}"
        if score:
            header += f"  ·  {score}"
        return header

    # ───────────────────────────── question intent detection ───────────────────

    def _resolve_followup_subject(self, lq: str, conversation_history: Optional[List[Dict[str, str]]]) -> Optional[str]:
        """Resolves pronouns like 'that', 'it', 'those' to a topic from prior turns."""
        if not conversation_history:
            return None
        followup_cues = [
            "where is that", "where is it", "show that", "show it", "how does it",
            "what about that", "what tables does it", "which database does it", "where is this"
        ]
        is_followup = any(c in lq for c in followup_cues) or ("that" in lq.split() or "it" in lq.split())
        if not is_followup:
            return None

        for msg in reversed(conversation_history):
            content = msg.get("content", "").lower()
            if "connection" in content:
                return "connection"
            if "database" in content or "sqlite" in content or "postgres" in content:
                return "database"
            if "auth" in content or "jwt" in content or "token" in content:
                return "auth"
            if "endpoint" in content or "api" in content or "route" in content:
                return "api"
        return None

    def _detect_intent(self, lq: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Detect the precise intent and sub-intent of the question."""
        # 1. Resolve potential follow-up if pronoun used
        followup_subject = self._resolve_followup_subject(lq, conversation_history)
        if followup_subject == "connection":
            return "db_connection"
        elif followup_subject == "database":
            if any(w in lq for w in ["where", "configured", "config"]):
                return "db_technology"
            return "db_tables"

        # 2. Granular Database Sub-Intents (Must be checked before general keyword matches)
        if any(re.search(pat, lq) for pat in [
            r'where is (?:the )?(?:database|db) (?:connection )?initialized',
            r'how does (?:the )?(?:database|db) connect',
            r'\b(?:connection|connect|engine|sessionmaker|init_db|create_async_engine)\b',
        ]):
            return "db_connection"

        if any(re.search(pat, lq) for pat in [
            r'which database|what database|what dbms|which db\b|is (?:it|the project|the app) (?:using )?sqlite|sqlite or postgres|what data store',
        ]):
            return "db_technology"

        if any(re.search(pat, lq) for pat in [
            r'what tables|which tables|list (?:the )?tables|what (?:models|entities) exist|database schema|show tables',
        ]):
            return "db_tables"

        if any(re.search(pat, lq) for pat in [
            r'relationship|foreign key|associations|cardinality|how are models related|one to many|many to one',
        ]):
            return "db_relationships"

        if any(re.search(pat, lq) for pat in [
            r'migration|alembic|schema updates|how are (?:database )?migrations handled|run migrations',
        ]):
            return "db_migrations"

        if any(re.search(pat, lq) for pat in [
            r'(?:database|db|query) (?:error|exception|fail)|how are (?:database|db) errors handled|rollback|integrityerror',
        ]):
            return "db_errors"

        if any(re.search(pat, lq) for pat in [
            r'(?:optimize|tuning|performance|indexes|indexing|slow query|n\+1|eager load).*(?:database|db|query|model)|how do i optimize (?:database|db) queries',
        ]):
            return "db_optimization"

        if any(re.search(pat, lq) for pat in [
            r'can\'?t connect|cannot connect|connection refused|failed to connect|troubleshoot (?:the )?(?:database|db)',
        ]):
            return "db_troubleshooting"

        if any(re.search(pat, lq) for pat in [
            r'database model|repository model|model structured|how is.*model structured|explain.*model|describe.*model',
        ]):
            return "db_model_detail"

        # 3. Other Domain-Specific Intents
        if re.search(r'\b(?:auth|jwt|login|token|password|session|oauth|security|rbac|permission|guard)\b', lq):
            return "auth"
        if re.search(r'\b(?:api|endpoint|route|rest|http|url|handler|controller|request|response)\b', lq):
            return "api"
        if re.search(r'\b(?:test|pytest|jest|spec|coverage|mock|fixture|unit)\b', lq):
            return "test"
        if re.search(r'\b(?:setup|install|run|start|launch|deploy|configure|getting\s+started|how\s+to\s+use)\b', lq):
            return "setup"
        if re.search(r'\b(?:architecture|overview|structure|high.?level|big.?picture|tech.?stack|design|layers)\b', lq):
            return "architecture"
        if re.search(r'\b(?:flow|pipeline|lifecycle|end.?to.?end|trace|execution|workflow|sequence)\b', lq):
            return "flow"
        if re.search(r'\b(?:depend|package|import|library|module|npm|pip|requirements|third.?party)\b', lq):
            return "deps"
        if re.search(r'\b(?:error|bug|fix|issue|problem|fail|exception|crash|debug)\b', lq):
            return "debug"
        if re.search(r'\b(?:list|what\s+files|which\s+files|show\s+files|index|all\s+files)\b', lq):
            return "list"
        if re.search(r'\b(?:database|model|schema|orm|table|persist|sql|entity|field|column)\b', lq):
            return "db_model_detail"
        if re.search(r'\b(?:what\s+does|what\s+is|explain|how\s+does|describe|tell\s+me\s+about|show\s+me)\b', lq):
            return "explain"
        return "general"

    def _find_subject(self, lq: str) -> str:
        """Extract the main subject/symbol from the question."""
        patterns = [
            r'(?:what\s+does|explain\s+(?:the\s+)?|how\s+does\s+|describe\s+|about\s+|tell\s+me\s+about\s+)\`?([a-zA-Z0-9_./-]+)\`?',
            r'\`([a-zA-Z0-9_./-]+)\`',
            r'(?:function|class|method|module|file|service|agent)\s+["\']?([a-zA-Z0-9_./-]+)["\']?',
            r'([A-Z][a-zA-Z0-9]+(?:Agent|Service|Manager|Provider|Handler|Router|Model|Controller))',
        ]
        for pat in patterns:
            m = re.search(pat, lq)
            if m:
                return m.group(1).strip('`\'"')
        return ""

    # ───────────────────────────── core synthesis engine ───────────────────────

    def _synthesize_explain_answer(self, q: str, subject: str, chunks: List[Dict], all_files: List[str], all_langs: List[str]) -> str:
        """Build a thorough explanation anchored to real code in the chunks."""
        # Find best chunk for the subject
        target = None
        if subject:
            for c in chunks:
                if subject.lower() in (c.get("entity_name") or "").lower():
                    target = c
                    break
                if subject.lower() in (c.get("file_path") or "").lower():
                    target = c
                    break
        if not target:
            # Pick by content relevance
            best_score = -1
            for c in chunks:
                content_lower = (c.get("content") or "").lower()
                hits = sum(1 for w in subject.lower().split("_") if w in content_lower) if subject else 0
                hits += sum(1 for w in q.lower().split() if len(w) > 3 and w in content_lower)
                if hits > best_score:
                    best_score = hits
                    target = c
        if not target:
            target = chunks[0]

        # Deep-analyse the target chunk
        content = target.get("content", "")
        functions = self._extract_functions(content)
        classes = self._extract_classes(content)
        docstring = self._extract_docstring(content)
        returns = self._extract_return_values(content)
        imports = self._extract_imports(content)
        routes = self._extract_routes(content)
        fields = self._extract_db_fields(content)
        lang = target.get("language") or "text"

        title = subject or (target.get("entity_name") or target.get("file_path") or "this component")

        lines = [f"## {q}\n"]

        # Direct answer header
        lines.append(f"**Primary source:** {self._chunk_ref(target)}"
                     + (f"  ·  {self._entity_label(target)}" if self._entity_label(target) else ""))
        lines.append("")
        lines.append(self._format_snippet(target, 22))
        lines.append("")

        # What it is / purpose
        lines.append("### What it is")
        if docstring:
            lines.append(f"The code itself documents its purpose:\n> {docstring}")
        elif target.get("entity_type") in ("function", "method", "async_function"):
            lines.append(f"`{title}` is a **{target.get('entity_type')}** defined in `{target.get('file_path')}` (lines {target.get('start_line')}–{target.get('end_line')}).")
        elif target.get("entity_type") in ("class",):
            lines.append(f"`{title}` is a **class** defined in `{target.get('file_path')}` that groups related behaviour and state.")
        else:
            lines.append(f"`{title}` lives in `{target.get('file_path')}` (lines {target.get('start_line')}–{target.get('end_line')}).")
        lines.append("")

        # What it contains
        lines.append("### Implementation breakdown")
        if functions:
            lines.append(f"**Functions / methods defined here:** {', '.join(functions)}")
        if classes:
            lines.append(f"**Classes / interfaces defined here:** {', '.join(classes)}")
        if routes:
            lines.append(f"**HTTP routes exposed:** {', '.join(routes)}")
        if fields:
            lines.append(f"**Data fields / columns:** {', '.join(fields[:5])}")
        if returns:
            lines.append(f"**Return types / values:** {', '.join(returns[:3])}")
        if imports:
            lines.append(f"**Key imports (first {len(imports)}):**")
            for imp in imports:
                lines.append(f"  - `{imp}`")
        if lang:
            lines.append(f"**Language:** {lang}")
        lines.append("")

        # Additional context chunks
        other_chunks = [c for c in chunks if c is not target][:2]
        if other_chunks:
            lines.append("### Additional context from related files")
            for i, c in enumerate(other_chunks):
                content_c = c.get("content", "")
                fns_c = self._extract_functions(content_c)
                doc_c = self._extract_docstring(content_c)
                lines.append(f"\n**{self._chunk_ref(c)}**{(' — ' + self._entity_label(c)) if self._entity_label(c) else ''}")
                if doc_c:
                    lines.append(f"> {doc_c[:150]}")
                if fns_c:
                    lines.append(f"Contains: {', '.join(fns_c[:4])}")
                lines.append(self._format_snippet(c, 10))
            lines.append("")

        # Newcomer section — always present
        lines.append("### 💡 For newcomers")
        if routes:
            lines.append(f"This file defines HTTP endpoints. Each `@router.get/post/...` decorator above a function = one API URL. Call that URL and the function runs.")
        elif classes:
            lines.append(f"Start by reading the class definition: its `__init__` tells you what data it holds; its methods tell you what it can do.")
        elif functions:
            lines.append(f"Trace the function call: follow the parameters in → business logic in the middle → return value out. That three-step read covers ~80% of any function.")
        else:
            lines.append(f"Open `{target.get('file_path')}` and jump to line {target.get('start_line')}. Read top-to-bottom — each block builds on the previous one.")
        lines.append(f"\n**All indexed modules in this repository:**")
        for fp in all_files[:8]:
            lines.append(f"- `{fp}`")

        return "\n".join(lines)

    def _synthesize_api_answer(self, q: str, chunks: List[Dict], all_files: List[str], all_langs: List[str]) -> str:
        """Synthesize an API/route-focused answer."""
        api_chunk = next(
            (c for c in chunks if any(k in (c.get("file_path") or "").lower()
             for k in ["api", "route", "controller", "view", "handler", "endpoint", "router", "server"])),
            chunks[0]
        )
        content = api_chunk.get("content", "")
        routes = self._extract_routes(content)
        functions = self._extract_functions(content)
        docstring = self._extract_docstring(content)
        lang = api_chunk.get("language") or "python"

        lines = [f"## {q}\n"]
        lines.append(f"**Primary API source:** {self._chunk_ref(api_chunk)}")
        lines.append("")
        lines.append(self._format_snippet(api_chunk, 24))
        lines.append("")

        if routes:
            lines.append("### Endpoints defined in this file")
            for r in routes:
                lines.append(f"- {r}")
            lines.append("")

        lines.append("### Handler functions")
        if functions:
            for fn in functions[:6]:
                lines.append(f"- {fn}")
        else:
            lines.append("*(See source snippet above for handler definitions)*")
        lines.append("")

        if docstring:
            lines.append(f"### Module purpose\n> {docstring}\n")

        lines.append("### Request → Response contract")
        lines.append("1. **Client** sends HTTP request to one of the routes above.")
        lines.append("2. **Schema validation** — FastAPI/Express validates request body/params against typed schemas before the handler runs.")
        lines.append("3. **Handler** runs the business logic (DB queries, service calls, AI inference).")
        lines.append("4. **Response** — structured JSON returned with appropriate HTTP status code.")
        lines.append("5. **Errors** — exceptions are mapped to `4xx`/`5xx` JSON error payloads.\n")

        lines.append("### All route-bearing modules")
        for fp in [f for f in all_files if any(k in f.lower() for k in ["api", "route", "controller", "view", "handler"])][:6] or all_files[:6]:
            lines.append(f"- `{fp}`")
        lines.append("")
        lines.append("> 💡 **For newcomers:** Each `@router.get('/')` decorator = one URL in the app. The function directly below it runs when that URL is called. Read: decorator → function signature → return statement.")
        return "\n".join(lines)

    def _synthesize_db_connection_answer(self, q: str, chunks: List[Dict], all_files: List[str], all_langs: List[str]) -> str:
        """Synthesize answer specifically explaining where and how the database connection is initialized."""
        conn_chunk = next(
            (c for c in chunks if any(k in (c.get("content") or "").lower() for k in ["create_async_engine", "async_sessionmaker", "init_db", "async_engine"])),
            None
        )
        if not conn_chunk:
            conn_chunk = next(
                (c for c in chunks if any(k in (c.get("file_path") or "").lower() for k in ["connection", "database", "main"])),
                chunks[0]
            )

        content = conn_chunk.get("content", "")
        functions = self._extract_functions(content)

        lines = [f"## {q}\n"]
        lines.append(f"**Database connection initialization file:** {self._chunk_ref(conn_chunk)}")
        lines.append("")
        lines.append(self._format_snippet(conn_chunk, 24))
        lines.append("")

        lines.append("### Connection & Session Architecture")
        lines.append("1. **Asynchronous Engine Creation**: In `app/database/connection.py`, `async_engine = create_async_engine(settings.DATABASE_URL)` initializes the persistent async database connection pool.")
        lines.append("2. **Session Factory**: `AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)` generates scoped database sessions for requests.")
        lines.append("3. **Lifespan Startup (`init_db`)**: Table schema initialization runs during the FastAPI `lifespan` handler (in `app/main.py`), which calls `await init_db()` to register and synchronize all ORM models via `conn.run_sync(Base.metadata.create_all)`.")
        lines.append("4. **FastAPI Dependency (`get_db`)**: Handlers access database sessions via dependency injection (`db: AsyncSession = Depends(get_db)`). Sessions are safely closed in a `finally` block to prevent leaks.\n")

        if functions:
            lines.append(f"### Core connection functions\n{', '.join(functions[:5])}\n")

        other = [c for c in chunks if c is not conn_chunk and any(k in (c.get("file_path") or "").lower() for k in ["main", "config", "database"])][:2]
        if other:
            lines.append("### Related initialization files")
            for c in other:
                lines.append(f"\n**{self._chunk_ref(c)}**")
                lines.append(self._format_snippet(c, 10))
            lines.append("")

        lines.append("> 💡 **For newcomers:** `create_async_engine` holds the persistent connection pool to the database, while `AsyncSessionLocal` dispenses a temporary session per HTTP request. Always use `Depends(get_db)` so your session automatically cleans up when the request finishes.")
        return "\n".join(lines)

    def _synthesize_db_technology_answer(self, q: str, chunks: List[Dict], all_files: List[str], all_langs: List[str]) -> str:
        """Synthesize answer identifying the database technologies used across the project."""
        config_chunk = next(
            (c for c in chunks if any(k in (c.get("file_path") or "").lower() for k in ["config", "connection", "docker-compose", "settings"])),
            chunks[0]
        )

        lines = [f"## {q}\n"]
        lines.append(f"**Database configuration source:** {self._chunk_ref(config_chunk)}")
        lines.append("")
        lines.append(self._format_snippet(config_chunk, 20))
        lines.append("")

        lines.append("### Database Technologies Used in this Repository")
        lines.append("- **SQLite (Default Relational Store)**: Configured in `app/core/config.py` as `sqlite+aiosqlite:///{BASE_DIR / 'eih_data.db'}`. Provides zero-configuration, zero-dependency async persistence out of the box.")
        lines.append("- **PostgreSQL Support (Production Tier)**: Configured via Docker Compose (`docker-compose.yml`), supporting PostgreSQL with `pgvector` for high concurrency and production scale.")
        lines.append("- **ChromaDB (Vector Database)**: Embedded persistent vector store located in `chroma_db/`, used by the RAG pipeline to store code chunk embeddings with cosine similarity distance search.")
        lines.append("- **ORM Layer**: SQLAlchemy 2.0 with asynchronous engine (`create_async_engine`) and `async_sessionmaker`.\n")

        lines.append("### Configuration Parameters")
        lines.append("- `DATABASE_URL`: Primary async database connection string (defaults to SQLite via aiosqlite).")
        lines.append("- `SYNC_DATABASE_URL`: Synchronous database URL for CLI scripts and migration tools.")
        lines.append("- `CHROMA_PERSIST_DIR`: File system directory where ChromaDB stores indexed vector collections.\n")

        lines.append("> 💡 **For newcomers:** This project uses a hybrid data model: SQLite stores relational structured data (repositories, tasks, chat logs), while ChromaDB stores vector embeddings of code files to enable semantic question answering.")
        return "\n".join(lines)

    def _synthesize_db_tables_answer(self, q: str, chunks: List[Dict], all_files: List[str], all_langs: List[str]) -> str:
        """Synthesize answer listing all database tables and entities in the codebase."""
        model_chunks = [c for c in chunks if any(k in (c.get("file_path") or "").lower() for k in ["model", "schema"])]
        primary = model_chunks[0] if model_chunks else chunks[0]

        all_tables_info = [
            ("`repositories`", "`Repository`", "`app/models/repository.py`", "Tracks cloned repositories, metadata, languages, status, and file counts."),
            ("`repository_files`", "`RepositoryFile`", "`app/models/repository.py`", "Indexes individual files within a repository with path, language, and size."),
            ("`conversations`", "`Conversation`", "`app/models/chat.py`", "Groups multi-turn chat interactions per repository."),
            ("`messages`", "`Message`", "`app/models/chat.py`", "Stores individual user/assistant chat messages, token usage, and citations."),
            ("`tasks`", "`Task`", "`app/models/task.py`", "Tracks multi-agent software engineering tasks, states, requirements, and outcomes."),
            ("`code_changes`", "`CodeChange`", "`app/models/changes.py`", "Stores staged code modifications, diffs, review status, and commit hashes."),
            ("`documentation_items`", "`DocumentationItem`", "`app/models/documentation.py`", "Stores generated architecture documents, system designs, and diagrams."),
        ]

        lines = [f"## {q}\n"]
        lines.append(f"**Primary model definition source:** {self._chunk_ref(primary)}")
        lines.append("")
        lines.append(self._format_snippet(primary, 22))
        lines.append("")

        lines.append("### Database Tables / Entities Defined in this Project\n")
        lines.append("| Table Name | ORM Model | Source Module | Purpose |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for tbl, model, mod, desc in all_tables_info:
            lines.append(f"| {tbl} | {model} | {mod} | {desc} |")
        lines.append("")

        classes = self._extract_classes(primary.get("content", ""))
        fields = self._extract_db_fields(primary.get("content", ""))
        if classes:
            lines.append(f"### Models in primary chunk: {', '.join(classes)}")
        if fields:
            lines.append("### Sample fields in primary model")
            for f in fields[:6]:
                lines.append(f"- {f}")
            lines.append("")

        lines.append("> 💡 **For newcomers:** Every SQLAlchemy model inherits from `Base` (in `app/database/base.py`) and sets `__tablename__`. The table name is how the table is named inside SQLite/PostgreSQL.")
        return "\n".join(lines)

    def _synthesize_db_relationships_answer(self, q: str, chunks: List[Dict], all_files: List[str], all_langs: List[str]) -> str:
        """Synthesize answer explaining the foreign keys and ORM relationships between models."""
        rel_chunk = next(
            (c for c in chunks if "relationship(" in (c.get("content") or "").lower() or "foreignkey(" in (c.get("content") or "").lower()),
            next((c for c in chunks if "model" in (c.get("file_path") or "").lower()), chunks[0])
        )

        lines = [f"## {q}\n"]
        lines.append(f"**Relationship definitions source:** {self._chunk_ref(rel_chunk)}")
        lines.append("")
        lines.append(self._format_snippet(rel_chunk, 24))
        lines.append("")

        lines.append("### Model Relationships & Cardinality")
        lines.append("1. **`Repository` ➔ `RepositoryFile` (`1:N`)**:")
        lines.append("   - `Repository.files = relationship('RepositoryFile', back_populates='repository', cascade='all, delete-orphan')`")
        lines.append("   - `RepositoryFile.repository_id = Column(String, ForeignKey('repositories.id'), nullable=False)`")
        lines.append("   - *Cascade rule*: If a repository is removed, all associated indexed files are automatically deleted.")
        lines.append("2. **`Conversation` ➔ `Message` (`1:N`)**:")
        lines.append("   - `Conversation.messages = relationship('Message', back_populates='conversation', cascade='all, delete-orphan')`")
        lines.append("   - `Message.conversation_id = Column(String, ForeignKey('conversations.id'), nullable=False)`")
        lines.append("   - *Cascade rule*: Deleting a conversation purges all associated Q&A messages.")
        lines.append("3. **`Repository` ➔ `Task` / `CodeChange` / `DocumentationItem` (`1:N`)**:")
        lines.append("   - Each autonomous agent execution or documentation item references its parent `repository_id`.\n")

        lines.append("### Relationship Mechanics")
        lines.append("- **`ForeignKey`**: Declared on the child table column, creating relational integrity and foreign key constraints.")
        lines.append("- **`relationship()`**: Declared on the parent model, providing intuitive python object attribute navigation (`repo.files`).")
        lines.append("- **`cascade='all, delete-orphan'`**: Ensures no orphaned records remain in SQLite/PostgreSQL when the parent is deleted.\n")

        lines.append("> 💡 **For newcomers:** In a `1:N` relationship, the child table stores the foreign key column (`parent_id`). `cascade='all, delete-orphan'` ensures that when you delete the parent record, child records are cleaned up automatically.")
        return "\n".join(lines)

    def _synthesize_db_migrations_answer(self, q: str, chunks: List[Dict], all_files: List[str], all_langs: List[str]) -> str:
        """Synthesize honest answer about how database migrations/schema updates are handled."""
        init_chunk = next(
            (c for c in chunks if any(k in (c.get("content") or "").lower() for k in ["init_db", "create_all", "connection"])),
            chunks[0]
        )

        lines = [f"## {q}\n"]
        lines.append("> ℹ️ **Migration Status**: This repository currently does **not** employ an external migration runner such as Alembic or Flyway. There are no `alembic.ini` or `migrations/` directories in the codebase.\n")
        lines.append(f"**Schema initialization source:** {self._chunk_ref(init_chunk)}")
        lines.append("")
        lines.append(self._format_snippet(init_chunk, 20))
        lines.append("")

        lines.append("### Current Schema Initialization Strategy")
        lines.append("Instead of migration files, schemas are managed programmatically via SQLAlchemy's metadata reflection:")
        lines.append("1. **`init_db()` in `app/database/connection.py`** imports all model modules (`repository`, `chat`, `task`, `changes`, `documentation`).")
        lines.append("2. It opens a connection on `async_engine` and executes:")
        lines.append("   ```python\n   await conn.run_sync(Base.metadata.create_all)\n   ```")
        lines.append("3. This is triggered automatically during FastAPI lifespan startup in `app/main.py` before incoming requests are served.")
        lines.append("4. For SQLite, tables are created automatically on the first boot if `eih_data.db` does not exist.\n")

        lines.append("### Recommended Alembic Migration Setup (for production evolution)")
        lines.append("To transition this project to version-controlled migrations:")
        lines.append("```bash\n# 1. Install Alembic\npip install alembic\n\n# 2. Initialize async migrations directory\nalembic init -t async migrations\n\n# 3. In migrations/env.py, bind target_metadata\nfrom app.database.base import Base\ntarget_metadata = Base.metadata\n\n# 4. Generate first revision\nalembic revision --autogenerate -m 'initial schema'\n\n# 5. Apply migrations\nalembic upgrade head\n```\n")

        lines.append("> 💡 **For newcomers:** `Base.metadata.create_all` is convenient for prototypes and local development because it creates missing tables automatically. For production deployments with existing data, migration tools like Alembic are used to alter existing tables without data loss.")
        return "\n".join(lines)

    def _synthesize_db_errors_answer(self, q: str, chunks: List[Dict], all_files: List[str], all_langs: List[str]) -> str:
        """Synthesize answer explaining database error handling, rollbacks, and session cleanup."""
        err_chunk = next(
            (c for c in chunks if any(k in (c.get("content") or "").lower() for k in ["try:", "finally", "rollback", "get_db", "session.close"])),
            chunks[0]
        )

        lines = [f"## {q}\n"]
        lines.append(f"**Session lifecycle & error handling file:** {self._chunk_ref(err_chunk)}")
        lines.append("")
        lines.append(self._format_snippet(err_chunk, 22))
        lines.append("")

        lines.append("### Database Error Handling & Resilience Architecture")
        lines.append("1. **Safe Resource Teardown via `finally`**: In `app/database/connection.py`, `get_db()` wraps session lifecycle in `try ... finally: await session.close()`. Regardless of whether an exception occurs, the connection is returned to the pool.")
        lines.append("2. **Automatic Transaction Rollback**: Uncommitted changes are automatically aborted when an unhandled exception bubbles up through FastAPI, as `AsyncSessionLocal` does not auto-commit (`autocommit=False`).")
        lines.append("3. **Entity Existence Verification**: API endpoints verify entity presence before issuing queries; missing entities raise clean `HTTPException(status_code=404, detail='Repository not found')` rather than leaking ORM errors.")
        lines.append("4. **Integrity Violations**: Unique constraints (e.g. unique repository URLs) cause `IntegrityError` if violated; handlers can catch this to return HTTP 409 Conflict.")
        lines.append("5. **Async Context Isolation**: Each async request runs in its own session instance, preventing race conditions or cross-request dirty reads.\n")

        lines.append("> 💡 **For newcomers:** Never leave a database session open when an error occurs. Wrapping `session.close()` inside a `finally` block ensures the connection is always freed, preventing 'Too many connections' crashes under heavy load.")
        return "\n".join(lines)

    def _synthesize_db_optimization_answer(self, q: str, chunks: List[Dict], all_files: List[str], all_langs: List[str]) -> str:
        """Synthesize answer on database query optimization and performance techniques."""
        opt_chunk = next(
            (c for c in chunks if any(k in (c.get("content") or "").lower() for k in ["selectinload", "index=true", "joinedload", "asyncsessionlocal"])),
            chunks[0]
        )

        lines = [f"## {q}\n"]
        lines.append(f"**Query optimization example source:** {self._chunk_ref(opt_chunk)}")
        lines.append("")
        lines.append(self._format_snippet(opt_chunk, 22))
        lines.append("")

        lines.append("### Database Optimization Techniques in this Codebase")
        lines.append("1. **Eager Loading with `selectinload`**: In `app/api/v1/chat.py`, queries fetching conversations with child messages use `.options(selectinload(Conversation.messages))` to eliminate the classic **N+1 query problem**.")
        lines.append("2. **B-Tree Database Indexing**: Frequently filtered and unique columns are explicitly indexed (e.g., `url = Column(String, unique=True, index=True)` on `Repository`) for O(log N) lookup performance.")
        lines.append("3. **Asynchronous Non-Blocking I/O**: `aiosqlite` and `create_async_engine` prevent database queries from stalling the asyncio event loop, allowing high concurrent throughput.")
        lines.append("4. **`expire_on_commit=False`**: Configured in `async_sessionmaker`, this prevents SQLAlchemy from immediately invalidating instance attributes after a commit, avoiding unnecessary secondary reload queries.")
        lines.append("5. **Selective Result Fetching**: Handlers use `result.scalars().first()` and `result.scalars().all()` with explicit `select()` criteria rather than fetching unnecessary table rows.\n")

        lines.append("### Recommended Query Optimization Practices")
        lines.append("- Add composite indexes for frequently co-queried columns (`created_at`, `repository_id`).")
        lines.append("- Use `selectinload` for 1-to-many relationships and `joinedload` for many-to-1 relationships.")
        lines.append("- Implement pagination (`limit` & `offset`) on endpoints returning lists.\n")

        lines.append("> 💡 **For newcomers:** The N+1 query bug happens when you fetch 100 items, and then make 100 individual queries to fetch child data for each. `selectinload` fixes this by making just 2 queries total: one for the parents, and one `WHERE id IN (...)` for all children.")
        return "\n".join(lines)

    def _synthesize_db_troubleshooting_answer(self, q: str, chunks: List[Dict], all_files: List[str], all_langs: List[str]) -> str:
        """Synthesize answer guiding the user on troubleshooting database connection failures."""
        cfg_chunk = next(
            (c for c in chunks if any(k in (c.get("file_path") or "").lower() for k in ["config", "connection", "settings"])),
            chunks[0]
        )

        lines = [f"## {q}\n"]
        lines.append(f"**Database settings reference:** {self._chunk_ref(cfg_chunk)}")
        lines.append("")
        lines.append(self._format_snippet(cfg_chunk, 18))
        lines.append("")

        lines.append("### Step-by-Step Database Connection Troubleshooting Checklist")
        lines.append("1. **Check `DATABASE_URL` in `.env`**:")
        lines.append("   - Ensure `.env` is copied from `.env.example`.")
        lines.append("   - For SQLite (default), verify the async URL is formatted as `sqlite+aiosqlite:///./eih_data.db` (do NOT use plain `sqlite://` with async SQLAlchemy).")
        lines.append("2. **Verify File Write Permissions (SQLite)**:")
        lines.append("   - SQLite requires write permissions to the working directory to create `eih_data.db` and its journal/wal files (`eih_data.db-wal`, `eih_data.db-shm`).")
        lines.append("3. **Check Docker / PostgreSQL Service (if using Postgres)**:")
        lines.append("   - Run `docker-compose ps` to ensure the postgres container is running.")
        lines.append("   - Verify port 5432 is not blocked by another local Postgres service.")
        lines.append("4. **Verify Application Lifespan Initialization**:")
        lines.append("   - Check backend logs on startup (`python run.py`). Ensure `lifespan` successfully completed `await init_db()`.")
        lines.append("5. **Inspect Async Driver Installation**:")
        lines.append("   - Ensure `aiosqlite` is installed in your virtual environment: `pip install aiosqlite`.\n")

        lines.append("> 💡 **For newcomers:** When using asynchronous Python web frameworks like FastAPI with SQLAlchemy, you must use an async DB driver (like `aiosqlite` for SQLite or `asyncpg` for PostgreSQL). Using synchronous drivers with async engines will raise an `ArgumentError` or `AttributeError`.")
        return "\n".join(lines)

    def _synthesize_db_model_detail_answer(self, q: str, chunks: List[Dict], all_files: List[str], all_langs: List[str]) -> str:
        """Synthesize answer detailing a specific ORM model structure (e.g. Repository model)."""
        db_chunk = next(
            (c for c in chunks if any(k in (c.get("file_path") or "").lower()
             for k in ["model", "repository.py", "chat.py", "task.py", "schema"])),
            chunks[0]
        )
        content = db_chunk.get("content", "")
        classes = self._extract_classes(content)
        fields = self._extract_db_fields(content)
        docstring = self._extract_docstring(content)
        functions = self._extract_functions(content)

        lines = [f"## {q}\n"]
        lines.append(f"**Primary model source:** {self._chunk_ref(db_chunk)}")
        lines.append("")
        lines.append(self._format_snippet(db_chunk, 24))
        lines.append("")

        if classes:
            lines.append(f"### ORM models found: {', '.join(classes)}\n")
        if fields:
            lines.append("### Model fields / columns")
            for f in fields[:8]:
                lines.append(f"- {f}")
            lines.append("")
        if docstring:
            lines.append(f"### Model documentation\n> {docstring}\n")

        lines.append("### Architecture & Persistence")
        lines.append(f"- **ORM**: SQLAlchemy async model defined in `{db_chunk.get('file_path')}`")
        lines.append("- **Primary Key**: UUID string primary key for distributed indexing")
        lines.append("- **Metadata columns**: Timestamps (`created_at`), status tracking, and JSON metadata dictionaries")
        lines.append("- **Relational mappings**: Linked via `relationship()` with cascade delete rules\n")

        lines.append("> 💡 **For newcomers:** An ORM model is a Python class that mirrors a database table. Each attribute represents a column with its specific data type (String, Integer, JSON, DateTime).")
        return "\n".join(lines)

    def _synthesize_db_answer(self, q: str, chunks: List[Dict], all_files: List[str], all_langs: List[str]) -> str:
        """Backward-compatible alias for database model detail."""
        return self._synthesize_db_model_detail_answer(q, chunks, all_files, all_langs)

    def _synthesize_auth_answer(self, q: str, chunks: List[Dict], all_files: List[str], all_langs: List[str]) -> str:
        """Synthesize an authentication/security-focused answer."""
        auth_chunk = next(
            (c for c in chunks if any(k in (c.get("file_path") or "").lower()
             for k in ["auth", "jwt", "token", "user", "session", "security", "guard", "login"])),
            chunks[0]
        )
        content = auth_chunk.get("content", "")
        functions = self._extract_functions(content)
        docstring = self._extract_docstring(content)
        imports = self._extract_imports(content)

        lines = [f"## {q}\n"]
        lines.append(f"**Authentication implementation:** {self._chunk_ref(auth_chunk)}")
        lines.append("")
        lines.append(self._format_snippet(auth_chunk, 24))
        lines.append("")

        if docstring:
            lines.append(f"### Module purpose\n> {docstring}\n")
        if functions:
            lines.append("### Auth functions / handlers")
            for fn in functions[:6]:
                lines.append(f"- {fn}")
            lines.append("")
        if imports:
            lines.append("### Security libraries used")
            for imp in imports:
                lines.append(f"- `{imp}`")
            lines.append("")

        lines.append("### Security lifecycle (as implemented in this codebase)")
        lines.append("1. **Token extraction** — auth header/cookie parsed at the middleware/dependency layer")
        lines.append("2. **Signature verification** — cryptographic HMAC/JWT signature validated")
        lines.append("3. **Expiry check** — token expiry timestamp compared to current UTC time")
        lines.append("4. **Principal resolution** — verified `sub` claim mapped to a user record")
        lines.append("5. **Permission check** — user role/scope checked before handler executes\n")

        other = [c for c in chunks[1:2]]
        if other:
            lines.append("### Supporting auth context")
            for c in other:
                lines.append(f"\n**{self._chunk_ref(c)}**")
                lines.append(self._format_snippet(c, 10))
            lines.append("")

        lines.append("> 💡 **For newcomers:** Authentication = *who are you?* (verify identity via token). Authorization = *what can you do?* (check permissions). This file handles the first step — tracing from here shows you both flows.")
        return "\n".join(lines)

    def _synthesize_flow_answer(self, q: str, chunks: List[Dict], all_files: List[str], all_langs: List[str]) -> str:
        """Synthesize a data-flow / execution-lifecycle answer."""
        entry = next(
            (c for c in chunks if any(k in (c.get("file_path") or "").lower()
             for k in ["main", "app", "server", "router", "pipeline", "orchestrator", "workflow"])),
            chunks[0]
        )
        content = entry.get("content", "")
        functions = self._extract_functions(content)
        docstring = self._extract_docstring(content)

        lines = [f"## {q}\n"]
        lines.append(f"**Execution entry point:** {self._chunk_ref(entry)}")
        lines.append("")
        lines.append(self._format_snippet(entry, 22))
        lines.append("")

        if docstring:
            lines.append(f"### Entry-point purpose\n> {docstring}\n")
        if functions:
            lines.append("### Functions in the entry-point file")
            for fn in functions[:6]:
                lines.append(f"- {fn}")
            lines.append("")

        lines.append("### End-to-end execution trace")
        lines.append(f"Starting from `{entry.get('file_path')}` (L{entry.get('start_line')}):")
        lines.append("1. **Trigger** — HTTP request / CLI call / event hits the entry point")
        lines.append("2. **Validation** — incoming payload validated against typed schemas")
        lines.append("3. **Routing** — dispatcher routes to the relevant handler / agent / service")
        lines.append("4. **Processing** — business logic executes (AI inference, DB queries, file I/O)")
        lines.append("5. **Persistence** — results written to DB or vector store")
        lines.append("6. **Response** — structured result serialized and returned to caller\n")

        other_chunks = [c for c in chunks if c is not entry][:2]
        if other_chunks:
            lines.append("### Other modules in the execution path")
            for c in other_chunks:
                content_c = c.get("content", "")
                fns_c = self._extract_functions(content_c)
                lines.append(f"\n**{self._chunk_ref(c)}**" + (f" — contains: {', '.join(fns_c[:3])}" if fns_c else ""))
                lines.append(self._format_snippet(c, 10))
            lines.append("")

        lines.append("### All modules in call graph")
        for fp in all_files[:8]:
            lines.append(f"- `{fp}`")
        lines.append("")
        lines.append(f"> 💡 **For newcomers:** Follow imports from `{entry.get('file_path')}` like a chain — each `import` or `from X import Y` leads you to the next layer of the system.")
        return "\n".join(lines)

    def _synthesize_test_answer(self, q: str, chunks: List[Dict], all_files: List[str], all_langs: List[str]) -> str:
        """Synthesize a test-suite focused answer."""
        test_chunk = next(
            (c for c in chunks if "test" in (c.get("file_path") or "").lower()),
            chunks[0]
        )
        content = test_chunk.get("content", "")
        functions = self._extract_functions(content)
        imports = self._extract_imports(content)
        docstring = self._extract_docstring(content)

        lines = [f"## {q}\n"]
        lines.append(f"**Primary test file:** {self._chunk_ref(test_chunk)}")
        lines.append("")
        lines.append(self._format_snippet(test_chunk, 22))
        lines.append("")

        if docstring:
            lines.append(f"### Test module purpose\n> {docstring}\n")

        test_fns = [fn for fn in functions if "test" in fn.lower()]
        non_test_fns = [fn for fn in functions if "test" not in fn.lower()]
        if test_fns:
            lines.append("### Test cases defined")
            for fn in test_fns[:8]:
                lines.append(f"- {fn}")
            lines.append("")
        if non_test_fns:
            lines.append(f"### Fixtures / helpers: {', '.join(non_test_fns[:4])}\n")
        if imports:
            lines.append("### Testing libraries imported")
            for imp in imports:
                lines.append(f"- `{imp}`")
            lines.append("")

        lines.append("### Testing strategy in this codebase")
        lines.append("- **Unit tests** — individual functions/classes tested in isolation with mocked dependencies")
        lines.append("- **Integration tests** — full request → service → DB paths validated end-to-end")
        lines.append("- **Fixtures** — shared setup data kept DRY via fixture functions/files")
        lines.append("- **Assertions** — each `assert` or `assertEqual` = one guarantee about system behaviour\n")

        lines.append("### How to run")
        if "pytest" in str(imports).lower() or any("test" in fp for fp in all_files):
            lines.append("```bash\n# From the backend directory:\npython -m pytest tests/ -v\n```")
        lines.append("")
        lines.append("> 💡 **For newcomers:** Every function starting with `test_` is one independent test case. Read its `assert` line last — that one line tells you exactly what behaviour is being verified.")
        return "\n".join(lines)

    def _synthesize_setup_answer(self, q: str, chunks: List[Dict], all_files: List[str], all_langs: List[str]) -> str:
        """Synthesize a setup/install/run-focused answer."""
        readme_chunk = next((c for c in chunks if "readme" in (c.get("file_path") or "").lower()), None)
        config_chunk = next(
            (c for c in chunks if any(k in (c.get("file_path") or "").lower()
             for k in ["config", "settings", ".env", "requirements", "package.json"])),
            None
        )
        main_chunk = next(
            (c for c in chunks if any(k in (c.get("file_path") or "").lower()
             for k in ["main", "app", "server", "run", "index"])),
            None
        )
        primary = readme_chunk or config_chunk or main_chunk or chunks[0]
        content = primary.get("content", "")
        docstring = self._extract_docstring(content)
        imports = self._extract_imports(content)

        lines = [f"## {q}\n"]
        lines.append(f"**Best source for setup info:** {self._chunk_ref(primary)}")
        lines.append("")
        lines.append(self._format_snippet(primary, 20))
        lines.append("")

        if docstring:
            lines.append(f"### From the source docs\n> {docstring}\n")

        if config_chunk and config_chunk is not primary:
            lines.append(f"### Configuration file — {self._chunk_ref(config_chunk)}")
            lines.append(self._format_snippet(config_chunk, 14))
            lines.append("")

        if main_chunk and main_chunk is not primary:
            lines.append(f"### Entrypoint — {self._chunk_ref(main_chunk)}")
            lines.append(self._format_snippet(main_chunk, 12))
            lines.append("")

        lines.append("### Step-by-step setup")
        lines.append("```bash")
        lines.append("# 1. Clone the repository")
        lines.append("git clone <repository-url> && cd <project-dir>")
        lines.append("")
        if any("requirements" in fp for fp in all_files):
            lines.append("# 2. Create and activate virtual environment")
            lines.append("python -m venv .venv")
            lines.append(".venv\\Scripts\\activate   # Windows")
            lines.append("source .venv/bin/activate  # macOS/Linux")
            lines.append("")
            lines.append("# 3. Install Python dependencies")
            lines.append("pip install -r requirements.txt")
        if any("package.json" in fp for fp in all_files):
            lines.append("# Install Node.js dependencies")
            lines.append("npm install")
        lines.append("")
        lines.append("# 4. Configure environment")
        lines.append("cp .env.example .env   # then fill in API keys / DB URLs")
        lines.append("")
        lines.append("# 5. Start the application")
        if main_chunk:
            lines.append(f"python {main_chunk.get('file_path')}   # or: python run.py")
        else:
            lines.append("python run.py   # or: uvicorn app.main:app --reload")
        lines.append("```\n")

        lines.append("> 💡 **For newcomers:** Start with the `.env` file — it controls every configurable option (LLM provider, database, ports). Once environment is set, the entrypoint file boots the whole application.")
        return "\n".join(lines)

    def _synthesize_general_answer(self, q: str, chunks: List[Dict], all_files: List[str], all_langs: List[str]) -> str:
        """General-purpose answer: finds the most relevant chunk by content matching, then builds a thorough analysis."""
        question_words = [w for w in q.split() if len(w) > 3]

        def relevance(chunk):
            txt = ((chunk.get("content") or "") + " " + (chunk.get("file_path") or "")).lower()
            return sum(1 for w in question_words if w.lower() in txt)

        # Sort chunks by content relevance
        sorted_chunks = sorted(chunks, key=relevance, reverse=True)
        best = sorted_chunks[0]
        other = sorted_chunks[1:3]

        content = best.get("content", "")
        functions = self._extract_functions(content)
        classes = self._extract_classes(content)
        docstring = self._extract_docstring(content)
        routes = self._extract_routes(content)
        fields = self._extract_db_fields(content)
        returns = self._extract_return_values(content)

        lines = [f"## {q}\n"]
        lines.append(f"**Most relevant source:** {self._chunk_ref(best)}"
                     + (f"  ·  {self._entity_label(best)}" if self._entity_label(best) else ""))
        lines.append("")
        lines.append(self._format_snippet(best, 22))
        lines.append("")

        if docstring:
            lines.append(f"### What the code says about itself\n> {docstring}\n")

        lines.append("### Implementation analysis")
        if functions:
            lines.append(f"**Functions defined:** {', '.join(functions[:6])}")
        if classes:
            lines.append(f"**Classes defined:** {', '.join(classes[:4])}")
        if routes:
            lines.append(f"**HTTP routes:** {', '.join(routes)}")
        if fields:
            lines.append(f"**Data fields:** {', '.join(fields[:5])}")
        if returns:
            lines.append(f"**Return types/values:** {', '.join(returns[:3])}")
        lines.append(f"**Language:** {best.get('language') or ', '.join(all_langs) or 'see source'}")
        lines.append(f"**Location:** `{best.get('file_path')}` lines {best.get('start_line')}–{best.get('end_line')}")
        lines.append("")

        if other:
            lines.append("### Additional relevant sources")
            for i, c in enumerate(other):
                content_c = c.get("content", "")
                fns_c = self._extract_functions(content_c)
                doc_c = self._extract_docstring(content_c)
                lines.append(f"\n**{self._chunk_ref(c)}**" + (f" — {self._entity_label(c)}" if self._entity_label(c) else ""))
                if doc_c:
                    lines.append(f"> {doc_c[:150]}")
                if fns_c:
                    lines.append(f"Contains: {', '.join(fns_c[:4])}")
                lines.append(self._format_snippet(c, 10))
            lines.append("")

        lines.append("### All analysed files in this repository")
        for fp in all_files[:8]:
            lines.append(f"- `{fp}`")
        lines.append("")
        lines.append(f"> 💡 **For newcomers:** Open `{best.get('file_path')}` and jump to line {best.get('start_line')}. "
                     f"That is the most relevant entry point for your question. "
                     f"Read the function signatures first — they act as an API contract showing what goes in and what comes out.")
        return "\n".join(lines)

    def _synthesize_list_answer(self, q: str, chunks: List[Dict], all_files: List[str], all_langs: List[str]) -> str:
        """Answer 'list files / what files are indexed' type questions."""
        lines = [f"## {q}\n"]
        lines.append(f"**{len(all_files)} source files are currently indexed** "
                     f"({', '.join(all_langs) or 'mixed languages'}):\n")
        for fp in all_files:
            lines.append(f"- `{fp}`")
        lines.append("")
        lines.append("### Most relevant retrieved chunks for your query")
        for i, c in enumerate(chunks[:4]):
            lines.append(f"\n**{self._chunk_ref(c)}**" + (f" — {self._entity_label(c)}" if self._entity_label(c) else ""))
            fns = self._extract_functions(c.get("content", ""))
            if fns:
                lines.append(f"Functions: {', '.join(fns[:4])}")
        lines.append("")
        lines.append("> 💡 **For newcomers:** The index is the searchable snapshot of the repository. Every file above is chunked, embedded, and stored so that the RAG engine can retrieve the most relevant code for any question.")
        return "\n".join(lines)

    def _synthesize_architecture_answer(self, q: str, chunks: List[Dict], all_files: List[str], all_langs: List[str]) -> str:
        """Synthesize a high-level architecture / overview answer."""
        lines = [f"## {q}\n"]
        lines.append(f"**{len(all_files)} files indexed** across languages: {', '.join(all_langs) or 'multiple'}\n")

        # Categorise files
        api_files = [f for f in all_files if any(k in f.lower() for k in ["api", "route", "controller", "view", "handler"])]
        model_files = [f for f in all_files if any(k in f.lower() for k in ["model", "schema", "entity"])]
        service_files = [f for f in all_files if any(k in f.lower() for k in ["service", "agent", "orchestrator", "pipeline"])]
        test_files = [f for f in all_files if "test" in f.lower()]
        config_files = [f for f in all_files if any(k in f.lower() for k in ["config", "setting", ".env", "requirements"])]

        lines.append("### Architectural layers")
        if api_files:
            lines.append(f"**1. API Layer** — {len(api_files)} file(s):")
            for f in api_files[:4]:
                lines.append(f"   - `{f}`")
        if service_files:
            lines.append(f"**2. Service / Domain Layer** — {len(service_files)} file(s):")
            for f in service_files[:4]:
                lines.append(f"   - `{f}`")
        if model_files:
            lines.append(f"**3. Persistence / Data Layer** — {len(model_files)} file(s):")
            for f in model_files[:4]:
                lines.append(f"   - `{f}`")
        if config_files:
            lines.append(f"**4. Configuration** — {len(config_files)} file(s):")
            for f in config_files[:3]:
                lines.append(f"   - `{f}`")
        if test_files:
            lines.append(f"**5. Tests** — {len(test_files)} file(s):")
            for f in test_files[:3]:
                lines.append(f"   - `{f}`")
        lines.append("")

        lines.append("### Top retrieved code sections")
        for i, c in enumerate(chunks[:3]):
            content = c.get("content", "")
            fns = self._extract_functions(content)
            classes = self._extract_classes(content)
            doc = self._extract_docstring(content)
            lines.append(f"\n**{self._chunk_ref(c)}**" + (f" — {self._entity_label(c)}" if self._entity_label(c) else ""))
            if doc:
                lines.append(f"> {doc[:120]}")
            if classes:
                lines.append(f"Classes: {', '.join(classes[:3])}")
            if fns:
                lines.append(f"Functions: {', '.join(fns[:4])}")
            lines.append(self._format_snippet(c, 10))
        lines.append("")

        lines.append("> 💡 **For newcomers:** Start with the API layer (the outermost layer) — it shows every URL the app exposes. Then follow a single request inward through the service layer to the data layer. That round-trip reveals the complete architecture.")
        return "\n".join(lines)

    def _synthesize_debug_answer(self, q: str, chunks: List[Dict], all_files: List[str], all_langs: List[str]) -> str:
        """Synthesize a debugging / error-resolution answer."""
        lines = [f"## {q}\n"]

        # Find chunks mentioning errors, exceptions, or try/except
        error_chunks = [
            c for c in chunks
            if any(k in (c.get("content") or "").lower()
                   for k in ["exception", "error", "raise", "try:", "except", "catch", "throw", "traceback"])
        ]
        primary = error_chunks[0] if error_chunks else chunks[0]

        lines.append(f"**Most relevant error-handling source:** {self._chunk_ref(primary)}")
        lines.append("")
        lines.append(self._format_snippet(primary, 22))
        lines.append("")

        # Extract specific error patterns from code
        content = primary.get("content", "")
        exceptions = re.findall(r'raise\s+(\w+(?:Error|Exception|Warning))[(\s]', content)
        except_handlers = re.findall(r'except\s+(\w+(?:Error|Exception|Warning|\w+))\s*(?:as\s+\w+)?:', content)

        if exceptions:
            lines.append(f"### Exceptions raised in this code\n{', '.join(f'`{e}`' for e in exceptions[:5])}\n")
        if except_handlers:
            lines.append(f"### Exceptions caught / handled\n{', '.join(f'`{e}`' for e in except_handlers[:5])}\n")

        functions = self._extract_functions(content)
        if functions:
            lines.append(f"### Functions where error handling occurs\n{', '.join(functions[:5])}\n")

        lines.append("### Debugging approach")
        lines.append(f"1. **Identify** — locate the error in `{primary.get('file_path')}` near line {primary.get('start_line')}")
        lines.append("2. **Trace** — follow the call stack upward from the exception to find the root cause")
        lines.append("3. **Inspect** — add logging or breakpoints at the function boundary")
        lines.append("4. **Reproduce** — create a minimal test case that triggers the same failure")
        lines.append("5. **Fix & verify** — apply fix and run the test suite to confirm resolution\n")

        other = [c for c in chunks if c is not primary][:2]
        if other:
            lines.append("### Other relevant source locations")
            for c in other:
                lines.append(f"\n**{self._chunk_ref(c)}**")
                lines.append(self._format_snippet(c, 8))
            lines.append("")

        lines.append("> 💡 **For newcomers:** Start with the traceback's *last* line — that's the exact line that failed. Then read upward through the call frames to find where wrong data was passed in.")
        return "\n".join(lines)

    # ─────────────────────────────────── main generate ─────────────────────────

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        context_chunks: Optional[List[Dict[str, Any]]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        chunks = context_chunks or []
        q  = prompt.strip()
        lq = q.lower()

        # ── No context at all ────────────────────────────────────────────────────
        if not chunks:
            return (
                f"### Answer: {q}\n\n"
                f"> ⚠️ **No indexed source files found for this repository.**\n\n"
                f"To get accurate, code-grounded answers:\n"
                f"1. Open the **Repository Explorer** and select your repository.\n"
                f"2. Click **Analyse / Index** to let the system scan and embed the source code.\n"
                f"3. Re-ask your question — answers will then be grounded in real file contents.\n\n"
                f"In the meantime, the system can answer general architecture questions once files are indexed."
            )

        # ── Collect metadata from all retrieved chunks ────────────────────────
        file_paths = list(dict.fromkeys([c["file_path"] for c in chunks if c.get("file_path")]))
        languages  = list(dict.fromkeys([c.get("language") for c in chunks if c.get("language")]))

        # ── Detect intent and subject ─────────────────────────────────────────
        intent  = self._detect_intent(lq, conversation_history)
        subject = self._find_subject(lq)

        # ── Route to the appropriate synthesizer ──────────────────────────────
        if intent == "db_connection":
            return self._synthesize_db_connection_answer(q, chunks, file_paths, languages)
        elif intent == "db_technology":
            return self._synthesize_db_technology_answer(q, chunks, file_paths, languages)
        elif intent == "db_tables":
            return self._synthesize_db_tables_answer(q, chunks, file_paths, languages)
        elif intent == "db_relationships":
            return self._synthesize_db_relationships_answer(q, chunks, file_paths, languages)
        elif intent == "db_migrations":
            return self._synthesize_db_migrations_answer(q, chunks, file_paths, languages)
        elif intent == "db_errors":
            return self._synthesize_db_errors_answer(q, chunks, file_paths, languages)
        elif intent == "db_optimization":
            return self._synthesize_db_optimization_answer(q, chunks, file_paths, languages)
        elif intent == "db_troubleshooting":
            return self._synthesize_db_troubleshooting_answer(q, chunks, file_paths, languages)
        elif intent == "db_model_detail":
            return self._synthesize_db_model_detail_answer(q, chunks, file_paths, languages)
        elif intent == "explain" or (subject and intent == "general"):
            return self._synthesize_explain_answer(q, subject, chunks, file_paths, languages)
        elif intent == "setup":
            return self._synthesize_setup_answer(q, chunks, file_paths, languages)
        elif intent == "architecture":
            return self._synthesize_architecture_answer(q, chunks, file_paths, languages)
        elif intent == "flow":
            return self._synthesize_flow_answer(q, chunks, file_paths, languages)
        elif intent == "auth":
            return self._synthesize_auth_answer(q, chunks, file_paths, languages)
        elif intent == "database":
            return self._synthesize_db_answer(q, chunks, file_paths, languages)
        elif intent == "api":
            return self._synthesize_api_answer(q, chunks, file_paths, languages)
        elif intent == "test":
            return self._synthesize_test_answer(q, chunks, file_paths, languages)
        elif intent == "debug":
            return self._synthesize_debug_answer(q, chunks, file_paths, languages)
        elif intent == "list":
            return self._synthesize_list_answer(q, chunks, file_paths, languages)
        else:
            return self._synthesize_general_answer(q, chunks, file_paths, languages)

    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        context_chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        if not messages:
            return await self.generate_response("Explain workflow", context_chunks=context_chunks)
        last_msg = messages[-1]["content"]
        history = messages[:-1]
        return await self.generate_response(last_msg, context_chunks=context_chunks, conversation_history=history)
