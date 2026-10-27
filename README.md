# Engineering Intelligence Hub (EIH)

> **An Autonomous Agentic Software Engineering Platform for Repository Understanding, Code Generation, Testing & Documentation.**

Engineering Intelligence Hub is an AI-powered developer platform that connects to GitHub repositories, indexes codebases using AST code intelligence and vector embeddings (RAG), answers architectural and implementation questions with verified line-level citations, and autonomously executes complex software engineering requirements using collaborative multi-agent state machines with self-correction and Human-in-the-Loop gating.

---

## 🌟 Key Features

- **GitHub Repository Ingestion**: Safe cloning, recursive directory tree discovery, language breakdown, and credential/secret exclusion.
- **AST & Manifest Code Intelligence**: Deep extraction of Python AST functions, classes, decorators, signatures, docstrings, API routes, and manifest dependencies (`requirements.txt`, `package.json`, `Cargo.toml`, `go.mod`).
- **Grounded RAG with Verified Citations**: Code-aware semantic search with exact line citations (`file_path:start_line-end_line`) and interactive snippet previews.
- **12 Autonomous Specialized Agents**:
  1. *Orchestrator Agent* (Complexity routing & lifecycle)
  2. *Requirement Agent* (Task decomposition)
  3. *Repository Analysis Agent* (Tech stack discovery)
  4. *Code Understanding Agent* (Call graph tracing)
  5. *Design Agent* (Architecture & SDD)
  6. *Code Generation Agent* (Staged file modifications & diffs)
  7. *Test Generation Agent* (Automated pytest suites)
  8. *Documentation Agent* (Technical docs & README updates)
  9. *Diagram Agent* (Mermaid architecture & sequence diagrams)
  10. *Validation Agent* (AST syntax & sandbox test execution)
  11. *Review Agent* (Security audit & code quality scoring)
- **Self-Correction Loop**: Automatically captures validation/test errors and loops back to code generation up to 3 retries.
- **Human-in-the-Loop Gate**: All modifications are isolated in a staging workspace. View side-by-side/unified diffs and **Approve**, **Reject**, or **Request Revision** before any changes touch the codebase.
- **Research Benchmark Suite**: Empirical evaluation comparing Single-Agent vs Multi-Agent execution latency, pass rates, and security scores.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Mermaid.js, React Markdown, Axios |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy, Uvicorn, Python AST, GitPython |
| **Database & Vectors** | SQLite (Default, zero-setup) / PostgreSQL with pgvector, ChromaDB / Dense embeddings |
| **LLM Layer** | Abstract `LLMProvider` supporting OpenAI, Groq, Ollama, Anthropic, and High-Fidelity Local Mock |

---

## 🚀 Quickstart Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Git

### 1. Clone & Configure Environment
```bash
git clone <your-repo-url>
cd github_analyzer

# Copy environment settings
cp .env.example .env
```

### 2. Run Backend
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
python run.py
```
*The FastAPI backend will start at `http://localhost:8000` (API Docs at `http://localhost:8000/docs`).*

### 3. Run Frontend
```bash
cd ../frontend
npm install
npm run dev
```
*The React UI dashboard will start at `http://localhost:5173`.*

---

## 🐳 Docker Deployment

To launch the full system with PostgreSQL, pgvector, FastAPI, and Frontend with Docker Compose:

```bash
docker-compose up --build
```

---

## 🧪 Running Automated Tests

Run the complete backend test suite:
```bash
cd backend
.venv\Scripts\python.exe -m pytest tests -v
```

To build and verify the frontend bundle:
```bash
cd frontend
npm run build
```

---

## 📚 Documentation Index

- [Architecture Specification](docs/ARCHITECTURE.md)
- [REST API Reference](docs/API_REFERENCE.md)
- [RAG & Code Intelligence Pipeline](docs/RAG_PIPELINE.md)
- [Autonomous Agents & State Machine](docs/AGENTS.md)
- [Research Evaluation & Benchmarks](docs/RESEARCH_EVALUATION.md)
