# Engineering Intelligence Hub: Multi-Agent Architecture

## 1. Autonomous Agent Specialization

The platform orchestrates 12 specialized autonomous agents:

| Agent Name | Primary Responsibility | Input Context | Output Artifact |
| :--- | :--- | :--- | :--- |
| **Orchestrator Agent** | Task complexity routing, agent coordination, and self-correction control | User requirement & State | Executed workflow & Final status |
| **Requirement Agent** | Decomposes raw natural language into structured, ordered engineering tasks | User requirement string | Structured `TaskPlan` |
| **Repository Agent** | Discovers tech stack, frameworks, configurations, and entry points | Cloned repository path | File list & language statistics |
| **Code Understanding Agent** | Analyzes symbol relationships, call hierarchy, and execution paths | Workspace source files | AST entities & API endpoints |
| **Design Agent** | Generates software architecture, component models, and API interfaces | Requirement & Repo context | Software Design Document (SDD) |
| **Code Generation Agent** | Synthesizes new source code and modifies existing files with unified diffs | Staging workspace | Proposed code modifications |
| **Test Generation Agent** | Synthesizes automated pytest test suites covering edge cases | Proposed code & workspace | `tests/test_*.py` |
| **Documentation Agent** | Updates technical README, API specifications, and usage examples | Code changes & SDD | Markdown documentation |
| **Diagram Agent** | Generates valid Mermaid sequence, flowchart, and component diagrams | System flow & Architecture | Mermaid diagram code |
| **Validation Agent** | Validates AST syntax, checks imports, and executes tests in a safe sandbox | Staging workspace files | Validation report |
| **Review Agent** | Performs automated security audit and evaluates code quality/maintainability | Proposed changes & tests | Quality/Security scores (0-100) |

---

## 2. Self-Correction Loop

When code generation produces a syntax error or a test fails in the sandbox:
1. `ValidationAgent` captures the exact error trace and assigns `status="failed"`.
2. `OrchestratorAgent` registers the diagnostic error into `state.validation_results["error_summary"]`.
3. `CodeGenerationAgent` re-executes with the explicit error context and resolves the syntax or test assertion flaw.
4. The loop repeats until validation passes or `MAX_AGENT_RETRIES=3` is reached.
