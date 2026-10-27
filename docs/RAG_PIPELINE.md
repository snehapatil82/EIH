# Engineering Intelligence Hub: RAG & Knowledge Pipeline

## 1. Codebase Ingestion Architecture

```
GitHub Repository
   ↓
Clone & Clean Sandbox (GitService)
   ↓
File Discovery & Ignore Filtering (.git, node_modules, .venv, binaries excluded)
   ↓
Language Detection (Python, TypeScript, Go, Rust, Java, Dockerfile, etc.)
   ↓
AST Code Parsing (Python AST / Generic Symbol & Manifest Parser)
   ↓
Code-Aware Chunking (Preserves Class/Function Boundaries & Exact Line Ranges)
   ↓
Embedding Generation (Deterministic Local Dense / SentenceTransformers / OpenAI)
   ↓
Vector Store Indexing (ChromaDB / In-Memory Fallback)
   ↓
Hybrid Semantic Retrieval (Cosine Similarity + Symbol & Keyword Boosting)
   ↓
Grounded LLM Generation + Strict Citation Linking (`file:start_line-end_line`)
```

---

## 2. Code-Aware Chunking Strategy

Traditional text chunkers split by character count or whitespace, often bisecting function signatures or control loops.

The `CodeAwareChunker`:
1. **Entity-Aware Boundaries**: Identifies AST class and function ranges (`start_line` to `end_line`) and treats whole semantic units as individual chunks.
2. **Line-Number Preservation**: Explicitly tags each chunk with `start_line` and `end_line`.
3. **Sliding Overlap**: For large modules, applies an overlapping sliding window ensuring no cross-function references are lost.

---

## 3. Verifiable Citation System

To prevent hallucination, every answer generated in AI Chat mode includes source citations in the standard format:
- `file_path`: Relative path inside the repository.
- `start_line`: Exact starting line number.
- `end_line`: Exact ending line number.
- `snippet`: Extracted source code preview.

The frontend renders interactive citations that allow developers to inspect the exact lines of code cited by the AI model.
