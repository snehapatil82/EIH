# Engineering Intelligence Hub: API Reference

Base URL: `http://localhost:8000/api/v1`

---

## 1. Repository Endpoints

### `POST /repositories`
Connects and clones a GitHub repository, extracts file hierarchy, and computes language statistics.

**Request Body:**
```json
{
  "url": "https://github.com/fastapi/fastapi",
  "branch": "master"
}
```

**Response (200 OK):**
```json
{
  "id": "e6a2bc41-d820-4354-9a84-75466487e839",
  "name": "fastapi",
  "owner": "fastapi",
  "url": "https://github.com/fastapi/fastapi",
  "default_branch": "master",
  "status": "indexed",
  "languages": { "Python": 14200, "Markdown": 3200 },
  "total_files": 128,
  "total_lines": 17400,
  "description": "GitHub repository fastapi/fastapi",
  "created_at": "2026-08-17T23:30:00Z",
  "updated_at": "2026-08-17T23:30:00Z"
}
```

### `GET /repositories`
Lists all connected repositories.

### `GET /repositories/{id}/files/tree`
Returns the recursive directory tree structure of the repository.

### `GET /repositories/{id}/file-content?path=src/auth.py`
Retrieves line-numbered contents and metadata for a specific repository file.

### `POST /repositories/{id}/index`
Triggers AST entity extraction and re-indexing into the vector database.

---

## 2. Code Intelligence Endpoints

### `GET /repositories/{id}/entities`
Returns all parsed Python AST functions, classes, methods, argument signatures, docstrings, decorators, and HTTP endpoints.

### `GET /repositories/{id}/dependencies`
Returns all manifest dependencies parsed from `requirements.txt`, `package.json`, `Cargo.toml`, or `go.mod`.

### `GET /repositories/{id}/architecture`
Generates a Mermaid architecture diagram of the repository components and module relationships.

---

## 3. Grounded AI Chat & RAG Endpoints

### `POST /repositories/{id}/ask`
Performs semantic vector search and generates a grounded explanation with explicit file and line citations.

**Request Body:**
```json
{
  "question": "How does authentication work?",
  "conversation_id": null
}
```

**Response (200 OK):**
```json
{
  "conversation_id": "93b218cd-d368-45fe-89dc-555543c7b640",
  "answer": "Authentication is implemented in `src/auth/auth_service.py` (lines 1-48)...",
  "citations": [
    {
      "file_path": "src/auth/auth_service.py",
      "start_line": 1,
      "end_line": 48,
      "snippet": "def verify_access_token(token: str)...",
      "score": 0.94
    }
  ],
  "latency_seconds": 0.42,
  "tokens_used": 184
}
```

---

## 4. Autonomous Engineering Task Endpoints

### `POST /repositories/{id}/tasks`
Launches an autonomous engineering task workflow.

**Request Body:**
```json
{
  "requirement": "Add JWT authentication and generate tests",
  "workflow_preference": "auto"
}
```

### `GET /tasks/{task_id}`
Returns current task state, complexity classification, execution steps, and logs.

### `GET /tasks/{task_id}/changes`
Returns all proposed file modifications with unified diffs.

### `GET /tasks/{task_id}/validation`
Returns automated AST syntax checks, import verification, and isolated sandbox test outputs.

### `GET /tasks/{task_id}/review`
Returns automated quality, security, and maintainability scores (0-100) with detailed comments.

---

## 5. Human-in-the-Loop Gating Endpoints

### `POST /tasks/{task_id}/approve`
Merges the staged workspace modifications safely into the target repository.

### `POST /tasks/{task_id}/reject`
Rejects proposed changes and cleans up the staging workspace.

### `POST /tasks/{task_id}/revise`
Takes developer revision notes and re-triggers the agent self-correction loop.

---

## 6. Research & Evaluation Endpoints

### `GET /research/benchmarks`
Returns comparative evaluation metrics between Single-Agent and Multi-Agent paradigms across latency, retry iterations, and quality scores.
