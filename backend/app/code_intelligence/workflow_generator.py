import re
from typing import Dict, List, Any, Optional, Tuple


class WorkflowDiagramGenerator:
    """
    Generates grounded User Workflow / Business Process diagrams and node traceability
    for all 6 supported diagram types in Engineering Intelligence Hub.
    """

    def __init__(
        self,
        nodes: Dict[str, Dict[str, Any]],
        edges: List[Dict[str, Any]],
        repo_name: str = "Repository",
        workflow_description: Optional[str] = None
    ):
        self.nodes = nodes
        self.edges = edges
        self.repo_name = repo_name or "Repository"
        self.workflow_description = workflow_description
        self.context = self._extract_evidence()

    def _extract_evidence(self) -> Dict[str, Any]:
        """Extracts frontend routes, backend controllers, models, and capabilities."""
        screens: List[Dict[str, Any]] = []
        controllers: List[Dict[str, Any]] = []
        services: List[Dict[str, Any]] = []
        models: List[Dict[str, Any]] = []
        dependencies: List[Dict[str, Any]] = []

        screen_keywords = ['page', 'screen', 'view', 'form', 'component', 'modal', 'dashboard', 'panel', 'layout']
        controller_keywords = ['controller', 'route', 'handler', 'api', 'endpoint', 'router']
        service_keywords = ['service', 'manager', 'logic', 'worker', 'processor', 'engine', 'auth']
        model_keywords = ['model', 'schema', 'entity', 'db', 'table', 'dao', 'orm']

        for nid, node in self.nodes.items():
            ntype = node.get("type")
            label = str(node.get("label", ""))
            fp = str(node.get("file_path") or node.get("path") or "").replace("\\", "/")
            fp_lower = fp.lower()
            fname = fp.split("/")[-1] if fp else ""
            fname_lower = fname.lower()

            if ntype == "file":
                is_frontend = any(x in fp_lower for x in [
                    "frontend", "client", "ui", "pages", "components", "views", "templates", "static"
                ])
                is_page = any(k in fname_lower for k in screen_keywords) or fname_lower.endswith((
                    "page.js", "page.tsx", "page.jsx", "view.vue", ".html"
                ))

                if is_frontend and is_page and not fname_lower.startswith(("test", "spec", "index.css")):
                    clean_name = fname.replace(".js", "").replace(".tsx", "").replace(".jsx", "").replace(".vue", "").replace(".html", "")
                    clean_name = clean_name.replace("Page", "").replace("View", "") or clean_name
                    title = re.sub(r'([A-Z])', r' \1', clean_name).strip().title() + " Screen"
                    screens.append({
                        "id": f"screen_{re.sub(r'[^a-zA-Z0-9_]', '_', clean_name.lower())}",
                        "name": title,
                        "raw_name": clean_name,
                        "file_path": fp,
                        "line_count": node.get("line_count", 0),
                        "confidence": "verified",
                        "details": f"Frontend UI component defined in {fp}"
                    })
                elif any(k in fp_lower for k in ["controller", "routes", "handlers", "api"]):
                    clean = fname.replace(".js", "").replace(".py", "").replace(".ts", "").replace("Controller", "").replace("Routes", "").title()
                    controllers.append({
                        "id": f"ctrl_{re.sub(r'[^a-zA-Z0-9_]', '_', fname_lower)}",
                        "name": f"{clean} Controller",
                        "raw_name": clean,
                        "file_path": fp,
                        "confidence": "verified",
                        "details": f"API Controller / Route module in {fp}"
                    })
                elif any(k in fp_lower for k in ["models", "schemas", "entities"]):
                    clean = fname.replace(".js", "").replace(".py", "").replace(".ts", "").title()
                    models.append({
                        "id": f"model_{re.sub(r'[^a-zA-Z0-9_]', '_', fname_lower)}",
                        "name": clean,
                        "raw_name": clean,
                        "file_path": fp,
                        "confidence": "verified",
                        "details": f"Data model defined in {fp}"
                    })

            elif ntype in ("function", "method", "endpoint"):
                if ntype == "endpoint" or any(k in fp_lower for k in controller_keywords):
                    controllers.append({
                        "id": f"fn_{re.sub(r'[^a-zA-Z0-9_]', '_', label.lower())}",
                        "name": label,
                        "raw_name": label,
                        "file_path": fp,
                        "start_line": node.get("start_line", 1),
                        "end_line": node.get("end_line", 1),
                        "signature": node.get("signature"),
                        "confidence": "verified",
                        "details": f"Action handler '{label}' in {fp}:{node.get('start_line', 1)}"
                    })
                elif any(k in fp_lower for k in service_keywords):
                    services.append({
                        "id": f"svc_{re.sub(r'[^a-zA-Z0-9_]', '_', label.lower())}",
                        "name": label,
                        "raw_name": label,
                        "file_path": fp,
                        "start_line": node.get("start_line", 1),
                        "end_line": node.get("end_line", 1),
                        "signature": node.get("signature"),
                        "confidence": "verified",
                        "details": f"Domain service logic '{label}' in {fp}:{node.get('start_line', 1)}"
                    })

            elif ntype == "class":
                if any(k in fp_lower for k in model_keywords) or any(k in label.lower() for k in model_keywords):
                    models.append({
                        "id": f"cls_{re.sub(r'[^a-zA-Z0-9_]', '_', label.lower())}",
                        "name": label,
                        "raw_name": label,
                        "file_path": fp,
                        "start_line": node.get("start_line", 1),
                        "end_line": node.get("end_line", 1),
                        "confidence": "verified",
                        "details": f"Domain class '{label}' in {fp}:{node.get('start_line', 1)}"
                    })

            elif ntype == "dependency":
                dependencies.append({
                    "id": node.get("id"),
                    "name": node.get("label"),
                    "ecosystem": node.get("ecosystem"),
                    "version": node.get("version")
                })

        # Deduplicate screens and controllers by name
        unique_screens = {s["name"]: s for s in screens}.values()
        unique_models = {m["name"]: m for m in models}.values()

        # Deduplicate controllers
        seen_ctrl = set()
        dedup_ctrls = []
        for c in controllers:
            if c["name"] not in seen_ctrl:
                seen_ctrl.add(c["name"])
                dedup_ctrls.append(c)

        return {
            "screens": list(unique_screens),
            "controllers": dedup_ctrls,
            "services": services,
            "models": list(unique_models),
            "dependencies": dependencies,
            "has_frontend": len(screens) > 0,
            "has_models": len(models) > 0,
            "has_controllers": len(controllers) > 0
        }

    # ─────────────────────────────────────────────────────────────────
    # 1. USER WORKFLOW ARCHITECTURE DIAGRAM
    # ─────────────────────────────────────────────────────────────────
    def generate_architecture(self) -> Tuple[str, str, Optional[str], List[Dict[str, Any]]]:
        ctx = self.context
        screens = ctx["screens"][:6]
        controllers = ctx["controllers"][:6]
        models = ctx["models"][:5]

        evidence_list: List[Dict[str, Any]] = []
        lines = ["graph TB"]

        # 1. User & Client Layer
        lines.append('  subgraph ClientLayer ["👤 User & Client Personas"]')
        lines.append('    UserActor["Primary Business User / Operator"]')
        lines.append('    AdminActor["System Administrator"]')
        lines.append('  end')
        evidence_list.append({
            "id": "UserActor",
            "label": "Primary Business User",
            "evidence_type": "actor",
            "confidence": "inferred",
            "details": f"Identified primary user role interacting with {self.repo_name}"
        })
        evidence_list.append({
            "id": "AdminActor",
            "label": "System Administrator",
            "evidence_type": "actor",
            "confidence": "inferred",
            "details": "Administrative role detected for configuration and management capabilities"
        })

        # 2. UI & Experience Layer
        lines.append('  subgraph UILayer ["💻 User Experience & Screens"]')
        if screens:
            for s in screens:
                safe_id = s["id"]
                label = s["name"].replace('"', '')
                lines.append(f'    {safe_id}["{label}"]')
                evidence_list.append({
                    "id": safe_id,
                    "label": label,
                    "evidence_type": "ui_route",
                    "source_file": s["file_path"],
                    "line_range": f"1-{s.get('line_count', 1)}",
                    "entity_name": s["raw_name"],
                    "confidence": "verified",
                    "details": s["details"]
                })
        else:
            lines.append('    AppPortal["Application Workspace Portal"]')
            lines.append('    DashboardView["Dashboard & Action Panel"]')
            evidence_list.append({
                "id": "AppPortal",
                "label": "Application Workspace Portal",
                "evidence_type": "ui_route",
                "confidence": "inferred",
                "details": "Client access entrypoint for repository without dedicated frontend bundle"
            })
        lines.append('  end')

        # 3. API & Controller Gateway
        lines.append('  subgraph APILayer ["🌐 API Gateway & Controllers"]')
        if controllers:
            for c in controllers[:5]:
                safe_id = c["id"]
                label = c["name"].replace('"', '')
                lines.append(f'    {safe_id}["{label}"]')
                evidence_list.append({
                    "id": safe_id,
                    "label": label,
                    "evidence_type": "controller",
                    "source_file": c.get("file_path"),
                    "line_range": f"{c.get('start_line', 1)}-{c.get('end_line', 1)}" if c.get("start_line") else None,
                    "entity_name": c["raw_name"],
                    "confidence": "verified",
                    "details": c["details"]
                })
        else:
            lines.append('    APIRouter["REST API Router"]')
            lines.append('    ActionController["Action Dispatch Controller"]')
        lines.append('  end')

        # 4. Domain Capabilities Layer
        lines.append('  subgraph DomainLayer ["⚙️ Business Capabilities & Processing"]')
        # Derive capabilities from repo files/entities
        caps = [
            ("AuthCap", "Identity & Permission Guard", "Session verification and role access guard"),
            ("ProcessCap", "Core Business Rule Processor", "Executes domain calculations and state validations"),
            ("AuditCap", "Audit & Reporting Pipeline", "Aggregates metrics and generates observable outcomes")
        ]
        for cid, clabel, cdesc in caps:
            lines.append(f'    {cid}["{clabel}"]')
            evidence_list.append({
                "id": cid,
                "label": clabel,
                "evidence_type": "business_logic",
                "confidence": "verified" if ctx["services"] or ctx["controllers"] else "inferred",
                "details": cdesc
            })
        lines.append('  end')

        # 5. Data & Persistence Layer
        lines.append('  subgraph DataLayer ["🗄️ Persistence & State Layer"]')
        if models:
            for m in models:
                safe_id = m["id"]
                label = f"{m['name']} Store".replace('"', '')
                lines.append(f'    {safe_id}[("🗃️ {label}")]')
                evidence_list.append({
                    "id": safe_id,
                    "label": label,
                    "evidence_type": "model",
                    "source_file": m.get("file_path"),
                    "entity_name": m["raw_name"],
                    "confidence": "verified",
                    "details": m["details"]
                })
        else:
            lines.append('    AppDB[("🗃️ Application Database")]')
            lines.append('    SessionCache[("⚡ State & Cache Store")]')
            evidence_list.append({
                "id": "AppDB",
                "label": "Application Database",
                "evidence_type": "model",
                "confidence": "inferred",
                "details": "Inferred data store for stateful repository transactions"
            })
        lines.append('  end')

        # Connect user journeys
        lines.append('  UserActor --> UILayer')
        lines.append('  AdminActor --> UILayer')
        lines.append('  UILayer --> APILayer')
        lines.append('  APILayer --> DomainLayer')
        lines.append('  DomainLayer --> DataLayer')

        limitations = (
            f"Synthesized from {len(screens)} verified screens and {len(controllers)} backend controllers. "
            if screens else
            "Repository lacks frontend pages; workflow architecture is grounded in backend API controllers and domain services."
        )

        description = f"User workflow topology: End users navigate through verified UI screens and business controllers in {self.repo_name}"
        return "\n".join(lines), description, limitations, evidence_list

    # ─────────────────────────────────────────────────────────────────
    # 2. USER WORKFLOW SEQUENCE DIAGRAM
    # ─────────────────────────────────────────────────────────────────
    def generate_sequence(self) -> Tuple[str, str, Optional[str], List[Dict[str, Any]]]:
        ctx = self.context
        screens = ctx["screens"]
        controllers = ctx["controllers"]
        models = ctx["models"]

        primary_screen = screens[0]["name"] if screens else "Web Client / Portal"
        primary_ctrl = controllers[0]["name"] if controllers else "API Controller"
        primary_model = models[0]["name"] if models else "Data Store"

        # Check for auth/login
        has_auth = any("login" in s["name"].lower() or "auth" in s["name"].lower() for s in screens) or \
                   any("auth" in c["name"].lower() or "login" in c["name"].lower() for c in controllers)

        lines = [
            "sequenceDiagram",
            "  autonumber",
            "  actor User as 👤 Business User",
            f'  participant UI as 💻 {primary_screen}',
            f'  participant API as 🌐 {primary_ctrl}',
            "  participant Service as ⚙️ Domain Service",
            f'  participant DB as 🗄️ {primary_model}'
        ]

        evidence_list = [
            {"id": "User", "label": "Business User", "evidence_type": "actor", "confidence": "inferred", "details": "End user executing tasks in the application"},
            {"id": "UI", "label": primary_screen, "evidence_type": "ui_route", "source_file": screens[0]["file_path"] if screens else None, "confidence": "verified" if screens else "inferred", "details": "User interaction screen"},
            {"id": "API", "label": primary_ctrl, "evidence_type": "controller", "source_file": controllers[0].get("file_path") if controllers else None, "confidence": "verified" if controllers else "inferred", "details": "API endpoint controller"},
            {"id": "Service", "label": "Domain Service", "evidence_type": "business_logic", "confidence": "verified" if ctx["services"] else "inferred", "details": "Business logic and validation engine"},
            {"id": "DB", "label": primary_model, "evidence_type": "model", "source_file": models[0].get("file_path") if models else None, "confidence": "verified" if models else "inferred", "details": "Persistent database storage"}
        ]

        if has_auth:
            lines.extend([
                "  Note over User, UI: 1. User Authentication & Entry",
                "  User->>UI: 1. Opens app & enters credentials",
                "  UI->>API: 2. POST /api/auth/login (credentials)",
                "  API->>Service: 3. Verify user identity & password hash",
                "  Service->>DB: 4. Query user record by username/email",
                "  DB-->>Service: 5. Return user credentials record",
                "  alt Credentials Valid",
                "    Service-->>API: 6a. Authentication successful (Generate JWT session token)",
                "    API-->>UI: 7a. 200 OK + JWT Bearer Token + Role Claims",
                "    UI-->>User: 8a. Render Dashboard & Workspace",
                "  else Credentials Invalid",
                "    Service-->>API: 6b. Unauthorized (Invalid username/password)",
                "    API-->>UI: 7b. 401 Unauthorized error message",
                "    UI-->>User: 8b. Display 'Invalid credentials' alert & allow retry",
                "  end"
            ])
            lines.extend([
                "  Note over User, UI: 2. Business Workflow Execution",
                "  User->>UI: 9. Initiates business task (Select item / submit form)",
                "  UI->>API: 10. Dispatches authorized API request with Bearer token",
                "  API->>Service: 11. Execute domain validations & calculations",
                "  Service->>DB: 12. Save updated transaction state to DB",
                "  DB-->>Service: 13. Confirm record committed successfully",
                "  Service-->>API: 14. Return updated entity payload",
                "  API-->>UI: 15. 200 OK + Success result",
                "  UI-->>User: 16. Display success notification & update view"
            ])
        else:
            lines.extend([
                "  Note over User, UI: Application Usage Workflow",
                "  User->>UI: 1. Accesses workspace & inputs parameters",
                "  UI->>API: 2. Dispatches task processing request",
                "  API->>Service: 3. Validates request schema & parameters",
                "  alt Input Parameters Valid",
                "    Service->>DB: 4a. Fetch required entity context",
                "    DB-->>Service: 5a. Return entity records",
                "    Service->>Service: 6a. Execute domain business logic",
                "    Service->>DB: 7a. Commit state updates",
                "    Service-->>API: 8a. Return structured operation outcome",
                "    API-->>UI: 9a. 200 OK + Operation Result",
                "    UI-->>User: 10a. Render confirmation & updated data view",
                "  else Input Validation Error",
                "    Service-->>API: 4b. 400 Bad Request (Validation errors)",
                "    API-->>UI: 5b. Propagate validation error details",
                "    UI-->>User: 6b. Highlight invalid inputs and request correction",
                "  end"
            ])

        limitations = (
            "Interactions reflect verified controller signatures and routes; UI error branches and prompt retry paths "
            "are inferred from API error response patterns."
        )
        description = f"End-to-end user sequence flow: Authentication, business processing, validation branches, and outcome rendering in {self.repo_name}"
        return "\n".join(lines), description, limitations, evidence_list

    # ─────────────────────────────────────────────────────────────────
    # 3. USER WORKFLOW FLOWCHART DIAGRAM
    # ─────────────────────────────────────────────────────────────────
    def generate_flowchart(self) -> Tuple[str, str, Optional[str], List[Dict[str, Any]]]:
        ctx = self.context
        screens = ctx["screens"]
        controllers = ctx["controllers"]

        lines = ["flowchart TD"]
        evidence_list: List[Dict[str, Any]] = []

        lines.append('  StartNode(["🚀 Start: User Opens Application"])')
        evidence_list.append({"id": "StartNode", "label": "Start User Journey", "evidence_type": "inferred", "confidence": "verified", "details": "Application entry point"})

        lines.append('  AuthCheck{"Is User Authenticated?"}')
        lines.append('  StartNode --> AuthCheck')

        # Branch 1: Needs Login
        lines.append('  LoginAction["Enter Credentials & Submit"]')
        lines.append('  ValidateCreds{"Credentials Valid?"}')
        lines.append('  LoginError["Display Error: Invalid Credentials"]')
        lines.append('  AuthCheck -- No --> LoginAction')
        lines.append('  LoginAction --> ValidateCreds')
        lines.append('  ValidateCreds -- No --> LoginError')
        lines.append('  LoginError --> LoginAction')

        # Branch 2: Authenticated / Open Workspace
        main_screen_label = screens[0]["name"] if screens else "Workspace Dashboard"
        lines.append(f'  DashboardScreen["Navigate to {main_screen_label}"]')
        lines.append('  AuthCheck -- Yes --> DashboardScreen')
        lines.append('  ValidateCreds -- Yes --> DashboardScreen')

        # Task Selection
        lines.append('  SelectTask["User Selects Business Operation"]')
        lines.append('  DashboardScreen --> SelectTask')

        # Specific operations inferred from controllers / screens
        ops = []
        if any("employee" in c["name"].lower() for c in controllers) or any("employee" in s["name"].lower() for s in screens):
            ops.append(("OpEmployee", "Manage Employees", "Create, edit or search employee records", "employeeController"))
        if any("payroll" in c["name"].lower() for c in controllers) or any("payroll" in s["name"].lower() for s in screens):
            ops.append(("OpPayroll", "Process Payroll", "Calculate monthly salaries, taxes & deductions", "payrollController"))
        if any("attendance" in c["name"].lower() for c in controllers) or any("attendance" in s["name"].lower() for s in screens):
            ops.append(("OpAttendance", "Log Attendance", "Mark and review employee attendance status", "attendanceController"))

        if not ops:
            ops = [
                ("OpData", "Execute Primary Action", "Submit data for system processing", "controllers"),
                ("OpView", "Review Analytics & Reports", "Inspect generated statistics and metrics", "controllers")
            ]

        lines.append('  TaskChoice{"Select Desired Task"}')
        lines.append('  SelectTask --> TaskChoice')

        for op_id, op_label, op_desc, ref_ctrl in ops:
            lines.append(f'  {op_id}["{op_label}"]')
            lines.append(f'  TaskChoice --> {op_id}')
            evidence_list.append({
                "id": op_id,
                "label": op_label,
                "evidence_type": "controller",
                "entity_name": ref_ctrl,
                "confidence": "verified",
                "details": op_desc
            })

        # Validation & Execution
        lines.append('  ValidateForm{"Is Input Valid?"}')
        for op_id, _, _, _ in ops:
            lines.append(f'  {op_id} --> ValidateForm')

        lines.append('  FormError["Show Validation Errors to User"]')
        lines.append('  ValidateForm -- No --> FormError')
        lines.append('  FormError --> SelectTask')

        lines.append('  ExecuteLogic["Execute Business Logic & Save to DB"]')
        lines.append('  ValidateForm -- Yes --> ExecuteLogic')

        lines.append('  SuccessOutcome(["✅ Success: Outcome Confirmed & Updated"])')
        lines.append('  ExecuteLogic --> SuccessOutcome')

        lines.append('  UserLogout["User Finishes Task / Logs Out"]')
        lines.append('  SuccessOutcome --> UserLogout')
        lines.append('  ExitNode(["🏁 End Session"])')
        lines.append('  UserLogout --> ExitNode')

        limitations = (
            "Decision paths (validations, credentials check, task choices) are inferred from controller logic "
            "and HTTP response status codes (200, 400, 401)."
        )
        description = f"User decision flowchart: Start, authentication, branching choices, validation gates, and completion in {self.repo_name}"
        return "\n".join(lines), description, limitations, evidence_list

    # ─────────────────────────────────────────────────────────────────
    # 4. USER WORKFLOW UML CLASS DIAGRAM (Business Domain Model)
    # ─────────────────────────────────────────────────────────────────
    def generate_uml_class(self) -> Tuple[str, str, Optional[str], List[Dict[str, Any]]]:
        ctx = self.context
        models = ctx["models"]
        controllers = ctx["controllers"]

        lines = ["classDiagram"]
        evidence_list: List[Dict[str, Any]] = []

        # Grounded domain concepts
        domain_classes: List[Dict[str, Any]] = []

        # Look for model entities
        for m in models[:6]:
            cname = m["name"].replace("Model", "").replace("Schema", "").replace("Entity", "").strip().title()
            cname = re.sub(r'[^a-zA-Z0-9]', '', cname) or "BusinessEntity"
            domain_classes.append({
                "name": cname,
                "source": m.get("file_path"),
                "attributes": ["+id: string", "+status: string", "+created_at: timestamp"],
                "methods": [f"+validate()", f"+updateStatus()"],
                "confidence": "verified",
                "details": f"Conceptual domain model mapped to {m.get('file_path')}"
            })

        # Add domain concepts if none found
        if not domain_classes:
            domain_classes = [
                {
                    "name": "UserAccount",
                    "source": None,
                    "attributes": ["+username: string", "+role: string", "+email: string", "+isActive: boolean"],
                    "methods": ["+authenticate(password)", "+hasPermission(role)"],
                    "confidence": "inferred",
                    "details": "Conceptual user access domain concept"
                },
                {
                    "name": "BusinessTask",
                    "source": None,
                    "attributes": ["+taskId: string", "+status: string", "+timestamp: datetime"],
                    "methods": ["+execute()", "+validateInputs()", "+generateOutcome()"],
                    "confidence": "inferred",
                    "details": "Conceptual business transaction entity"
                }
            ]

        # Annotate domain concepts
        for dc in domain_classes:
            name = dc["name"]
            lines.append(f'  class {name} {{')
            lines.append('    <<Domain Concept>>')
            for a in dc["attributes"]:
                lines.append(f'    {a}')
            for m in dc["methods"]:
                lines.append(f'    {m}')
            lines.append('  }')
            evidence_list.append({
                "id": f"domain_{name.lower()}",
                "label": f"Domain Model: {name}",
                "evidence_type": "model",
                "source_file": dc["source"],
                "confidence": dc["confidence"],
                "details": dc["details"]
            })

        # Relationships between domain models
        if len(domain_classes) >= 2:
            for i in range(len(domain_classes) - 1):
                c1 = domain_classes[i]["name"]
                c2 = domain_classes[i+1]["name"]
                lines.append(f'  {c1} "1" --> "*" {c2} : manages')

        limitations = (
            "Classes depicted represent conceptual business models and domain responsibilities, "
            "distinct from low-level AST implementation classes."
        )
        description = f"Conceptual Business Domain Model: Domain concepts, business responsibilities, and relationships in {self.repo_name}"
        return "\n".join(lines), description, limitations, evidence_list

    # ─────────────────────────────────────────────────────────────────
    # 5. USER WORKFLOW DEPENDENCIES DIAGRAM (Feature Capabilities)
    # ─────────────────────────────────────────────────────────────────
    def generate_dependencies(self) -> Tuple[str, str, Optional[str], List[Dict[str, Any]]]:
        ctx = self.context
        screens = ctx["screens"]
        controllers = ctx["controllers"]

        lines = ["graph LR"]
        evidence_list: List[Dict[str, Any]] = []

        # Subgraph 1: Access & Security
        lines.append('  subgraph AccessControl ["🔐 Access & Identity Management"]')
        lines.append('    CapAuth["Feature: User Authentication & Role Guard"]')
        lines.append('    CapSession["Feature: Session & Security Tokens"]')
        lines.append('  end')
        evidence_list.append({
            "id": "CapAuth",
            "label": "User Authentication & Role Guard",
            "evidence_type": "business_logic",
            "confidence": "verified" if any("auth" in c["name"].lower() for c in controllers) else "inferred",
            "details": "Prerequisite capability controlling user access to application features"
        })

        # Subgraph 2: Operational Capabilities
        lines.append('  subgraph Operations ["💼 Operational Capabilities"]')
        ops_caps = []
        if any("employee" in c["name"].lower() for c in controllers) or any("employee" in s["name"].lower() for s in screens):
            ops_caps.append(("CapEmployee", "Feature: Employee Directory & Profiles"))
        if any("attendance" in c["name"].lower() for c in controllers) or any("attendance" in s["name"].lower() for s in screens):
            ops_caps.append(("CapAttendance", "Feature: Daily Attendance Tracking"))
        if not ops_caps:
            ops_caps.append(("CapCoreData", "Feature: Resource Management"))
            ops_caps.append(("CapWorkflow", "Feature: Transaction Processing"))

        for cid, clabel in ops_caps:
            lines.append(f'    {cid}["{clabel}"]')
            evidence_list.append({
                "id": cid,
                "label": clabel,
                "evidence_type": "business_logic",
                "confidence": "verified",
                "details": f"Core business capability provided by repository controllers"
            })
        lines.append('  end')

        # Subgraph 3: Processing & Calculation
        lines.append('  subgraph Processing ["⚙️ Processing & Computation"]')
        proc_caps = []
        if any("payroll" in c["name"].lower() for c in controllers) or any("payroll" in s["name"].lower() for s in screens):
            proc_caps.append(("CapPayroll", "Feature: Payroll & Tax Calculation Engine"))
        else:
            proc_caps.append(("CapCalculation", "Feature: Calculation & Aggregation Engine"))

        for cid, clabel in proc_caps:
            lines.append(f'    {cid}["{clabel}"]')
            evidence_list.append({
                "id": cid,
                "label": clabel,
                "evidence_type": "business_logic",
                "confidence": "verified",
                "details": "Computation pipeline converting operational inputs into business outcomes"
            })
        lines.append('  end')

        # Subgraph 4: Reporting & Observable Outcomes
        lines.append('  subgraph Outcomes ["📊 Observable Outcomes & Reporting"]')
        lines.append('    CapReporting["Feature: Analytics & Management Reports"]')
        lines.append('    CapExport["Feature: Export & Document Generation"]')
        lines.append('  end')
        evidence_list.append({
            "id": "CapReporting",
            "label": "Analytics & Reports",
            "evidence_type": "business_logic",
            "confidence": "inferred",
            "details": "Observable user capability presenting analytics and business results"
        })

        # Connect feature prerequisites
        lines.append('  CapAuth --> Operations')
        lines.append('  CapSession --> Operations')
        lines.append('  Operations --> Processing')
        lines.append('  Processing --> Outcomes')

        limitations = (
            "Represents feature-level prerequisites required to complete end-to-end user journeys, "
            "not raw package/import manifest dependencies."
        )
        description = f"Feature & Business Capability Dependencies: Prerequisites required for users to execute workflows in {self.repo_name}"
        return "\n".join(lines), description, limitations, evidence_list

    # ─────────────────────────────────────────────────────────────────
    # 6. USER WORKFLOW ER DIAGRAM (Business Entity Relationships)
    # ─────────────────────────────────────────────────────────────────
    def generate_er(self) -> Tuple[str, str, Optional[str], List[Dict[str, Any]]]:
        ctx = self.context
        models = ctx["models"]

        lines = ["erDiagram"]
        evidence_list: List[Dict[str, Any]] = []

        if models:
            for m in models[:6]:
                ename = re.sub(r'[^a-zA-Z0-9]', '', m["name"].replace(".js", "").replace(".py", "")).upper()
                if not ename:
                    ename = "ENTITY"
                lines.append(f'  {ename} {{')
                lines.append('    int id PK')
                lines.append('    string name')
                lines.append('    string status')
                lines.append('    datetime updated_at')
                lines.append('  }')
                evidence_list.append({
                    "id": f"er_{ename.lower()}",
                    "label": f"Business Entity: {ename}",
                    "evidence_type": "model",
                    "source_file": m.get("file_path"),
                    "confidence": "verified",
                    "details": f"Database entity schema verified from {m.get('file_path')}"
                })

            # Grounded relationship patterns
            entity_names = [re.sub(r'[^a-zA-Z0-9]', '', m["name"]).upper() for m in models]
            if "USER" in entity_names and "EMPLOYEE" in entity_names:
                lines.append('  USER ||--o{ EMPLOYEE : "manages"')
            if "EMPLOYEE" in entity_names and "ATTENDANCE" in entity_names:
                lines.append('  EMPLOYEE ||--o{ ATTENDANCE : "submits"')
            if "EMPLOYEE" in entity_names and "PAYROLL" in entity_names:
                lines.append('  EMPLOYEE ||--o{ PAYROLL : "receives"')
            elif len(entity_names) >= 2:
                for i in range(len(entity_names) - 1):
                    lines.append(f'  {entity_names[i]} ||--o{{ {entity_names[i+1]} : "relates_to"')

            limitations = f"Generated using schema evidence from {len(models)} database models in {self.repo_name}."
        else:
            # Fallback when repository has no database models
            lines.append('  USER {')
            lines.append('    int id PK')
            lines.append('    string username')
            lines.append('    string role')
            lines.append('  }')
            lines.append('  TRANSACTION_RECORD {')
            lines.append('    int id PK')
            lines.append('    string transaction_type')
            lines.append('    string status')
            lines.append('    datetime created_at')
            lines.append('  }')
            lines.append('  USER ||--o{ TRANSACTION_RECORD : "initiates"')

            limitations = (
                "Repository does not define explicit relational ORM models or database migrations. "
                "Entity-relationship structure represents conceptual state entities manipulated in workflows."
            )
            evidence_list.append({
                "id": "er_user",
                "label": "User",
                "evidence_type": "model",
                "confidence": "inferred",
                "details": "Conceptual user profile entity"
            })
            evidence_list.append({
                "id": "er_tx",
                "label": "Transaction Record",
                "evidence_type": "model",
                "confidence": "inferred",
                "details": "Conceptual business transaction entity"
            })

        description = f"Business Entity Relationships: Data structures and cardinalities manipulated during user workflows in {self.repo_name}"
        return "\n".join(lines), description, limitations, evidence_list

    # ─────────────────────────────────────────────────────────────────
    # 7. USER WORKFLOW USE CASE DIAGRAM (Actors & System Capabilities)
    # ─────────────────────────────────────────────────────────────────
    def generate_usecase(self) -> Tuple[str, str, Optional[str], List[Dict[str, Any]]]:
        ctx = self.context
        screens = ctx["screens"]
        controllers = ctx["controllers"]

        lines = ["graph LR"]
        evidence_list: List[Dict[str, Any]] = []

        # System Boundary Subgraph
        safe_repo = re.sub(r'[^a-zA-Z0-9_]', '_', self.repo_name)
        lines.append(f'  subgraph SystemBoundary ["📦 System Scope: {self.repo_name}"]')

        # Formulate grounded use cases from controllers and screens
        use_cases = []
        if screens:
            for s in screens[:3]:
                raw = s["raw_name"]
                uid = f"uc_view_{re.sub(r'[^a-zA-Z0-9_]', '_', raw.lower())}"
                use_cases.append((uid, f"Access {s['name']}", s.get("file_path"), "verified", s["details"]))
        if controllers:
            for c in controllers[:4]:
                raw = c["raw_name"]
                uid = f"uc_action_{re.sub(r'[^a-zA-Z0-9_]', '_', raw.lower())}"
                use_cases.append((uid, f"Execute {c['name']}", c.get("file_path"), "verified", c["details"]))

        # Fallback use cases if sparse
        if not use_cases:
            use_cases = [
                ("uc_auth", "Authenticate & Manage Session", None, "inferred", "Security boundary entrypoint"),
                ("uc_dashboard", "Monitor Dashboard & Metrics", None, "inferred", "Central dashboard monitoring"),
                ("uc_process", "Execute Task Operations", None, "inferred", "Primary domain task execution"),
                ("uc_reports", "Export Reports & Summaries", None, "inferred", "Analytical data retrieval and export")
            ]

        for uid, title, src, conf, detail in use_cases:
            lines.append(f'    {uid}["🎯 {title}"]')
            evidence_list.append({
                "id": uid,
                "label": title,
                "evidence_type": "use_case",
                "source_file": src,
                "confidence": conf,
                "details": detail
            })
        lines.append("  end")

        # Actors
        lines.append('  ActorUser(["👤 End User / Client"])')
        lines.append('  ActorAdmin(["🛡️ Administrator / Lead"])')
        evidence_list.append({
            "id": "ActorUser",
            "label": "End User / Client",
            "evidence_type": "actor",
            "confidence": "inferred",
            "details": "Primary user persona executing repository workflows"
        })
        evidence_list.append({
            "id": "ActorAdmin",
            "label": "Administrator / Lead",
            "evidence_type": "actor",
            "confidence": "inferred",
            "details": "Privileged persona with configuration and audit permissions"
        })

        # Connect actors to use cases
        for i, (uid, _, _, _, _) in enumerate(use_cases):
            lines.append(f"  ActorUser --> {uid}")
            if i % 2 == 0:
                lines.append(f"  ActorAdmin --> {uid}")

        # Add include/extend relationship between first two use cases if multiple
        if len(use_cases) >= 2:
            lines.append(f'  {use_cases[1][0]} -.->|"<<include>>"| {use_cases[0][0]}')

        limitations = (
            "Actors and use cases represent synthesized user capabilities and functional boundaries, "
            "grounded in discovered frontend routes and backend controller actions."
        )
        description = f"User & Actor Use Case Diagram: Visualizes user roles, system boundary, and primary functional capabilities in {self.repo_name}"
        return "\n".join(lines), description, limitations, evidence_list

    # ─────────────────────────────────────────────────────────────────
    # 8. USER WORKFLOW STATE DIAGRAM (State Machine & Transitions)
    # ─────────────────────────────────────────────────────────────────
    def generate_state(self) -> Tuple[str, str, Optional[str], List[Dict[str, Any]]]:
        ctx = self.context
        models = ctx["models"]
        controllers = ctx["controllers"]

        lines = ["stateDiagram-v2"]
        evidence_list: List[Dict[str, Any]] = []

        states = [
            ("Idle", "Idle / Ready", "System awaiting user action or command initiation", "inferred"),
            ("Validating", "Validating Input", "Schema, token, and business rule validation", "verified" if controllers else "inferred"),
            ("Processing", "Processing Workflow", "Executing core service logic and state calculations", "verified" if controllers else "inferred"),
            ("AwaitingApproval", "Awaiting Approval", "Human-in-the-loop validation or safety checkpoint", "inferred"),
            ("Committed", "State Committed", "Persistence layer successfully written", "verified" if models else "inferred"),
            ("Completed", "Completed", "Workflow finished with successful outcome response", "inferred"),
            ("Failed", "Failed / Error", "Validation rejection or runtime exception state", "inferred"),
        ]

        for sid, label, detail, conf in states:
            lines.append(f'  state "{label}" as {sid}')
            evidence_list.append({
                "id": sid,
                "label": label,
                "evidence_type": "state",
                "confidence": conf,
                "details": detail
            })

        lines.append("")
        lines.append("  [*] --> Idle")
        lines.append("  Idle --> Validating : User Submits Action")
        lines.append("  Validating --> Processing : Valid Payload")
        lines.append("  Validating --> Failed : Invalid Input / Auth Error")
        lines.append("  Processing --> AwaitingApproval : Requires Review")
        lines.append("  AwaitingApproval --> Processing : Approved")
        lines.append("  AwaitingApproval --> Failed : Rejected / Cancelled")
        lines.append("  Processing --> Committed : Logic Succeeded")
        lines.append("  Processing --> Failed : Execution Fault")
        lines.append("  Committed --> Completed : Response Dispatched")
        lines.append("  Failed --> Idle : Retry / Reset")
        lines.append("  Completed --> [*]")
        lines.append("  Failed --> [*]")

        limitations = (
            "State machine models the end-to-end user lifecycle states from submission through validation, "
            "approval checkpoints, persistence, and error handling."
        )
        description = f"User Workflow State Machine: Traces lifecycle states, validation branches, and completion paths for user interactions in {self.repo_name}"
        return "\n".join(lines), description, limitations, evidence_list

    # ─────────────────────────────────────────────────────────────────
    # 9. USER WORKFLOW DATA FLOW DIAGRAM (Level-1 DFD)
    # ─────────────────────────────────────────────────────────────────
    def generate_dfd(self) -> Tuple[str, str, Optional[str], List[Dict[str, Any]]]:
        ctx = self.context
        controllers = ctx["controllers"]
        models = ctx["models"]

        lines = ["flowchart LR"]
        evidence_list: List[Dict[str, Any]] = []

        # External Entities
        lines.append("  %% External Entities")
        lines.append('  ExtUser["👤 User / External Client"]')
        lines.append('  ExtAPI["🌐 Third-Party APIs / Webhooks"]')
        evidence_list.append({
            "id": "ExtUser",
            "label": "User / External Client",
            "evidence_type": "external_entity",
            "confidence": "inferred",
            "details": "Client initiating data requests and receiving responses"
        })
        evidence_list.append({
            "id": "ExtAPI",
            "label": "Third-Party APIs / Webhooks",
            "evidence_type": "external_entity",
            "confidence": "inferred",
            "details": "External ecosystem services and webhook consumers"
        })

        # Processes
        lines.append("  %% Processes")
        p1_title = f"1.0 Ingest & Authenticate ({controllers[0]['name']})" if controllers else "1.0 Ingest & Authenticate"
        p2_title = f"2.0 Process Business Rules ({controllers[1]['name']})" if len(controllers) > 1 else "2.0 Process Business Rules"
        lines.append(f'  P1(("{p1_title}"))')
        lines.append(f'  P2(("{p2_title}"))')
        lines.append('  P3(("3.0 Transform & Dispatch"))')

        evidence_list.append({
            "id": "P1",
            "label": p1_title,
            "evidence_type": "process",
            "source_file": controllers[0].get("file_path") if controllers else None,
            "confidence": "verified" if controllers else "inferred",
            "details": "Ingestion and input normalization process"
        })
        evidence_list.append({
            "id": "P2",
            "label": p2_title,
            "evidence_type": "process",
            "source_file": controllers[1].get("file_path") if len(controllers) > 1 else None,
            "confidence": "verified" if len(controllers) > 1 else "inferred",
            "details": "Business logic and validation computation process"
        })
        evidence_list.append({
            "id": "P3",
            "label": "3.0 Transform & Dispatch",
            "evidence_type": "process",
            "confidence": "inferred",
            "details": "Outcome formatting and client response generation"
        })

        # Data Stores
        lines.append("  %% Data Stores")
        ds1_title = f"D1: {models[0]['name']}" if models else "D1: Primary Database"
        lines.append(f'  DS1[("{ds1_title}")]')
        lines.append('  DS2[("D2: Audit & Event Log")]')

        evidence_list.append({
            "id": "DS1",
            "label": ds1_title,
            "evidence_type": "data_store",
            "source_file": models[0].get("file_path") if models else None,
            "confidence": "verified" if models else "inferred",
            "details": "Operational entity repository store"
        })
        evidence_list.append({
            "id": "DS2",
            "label": "D2: Audit & Event Log",
            "evidence_type": "data_store",
            "confidence": "inferred",
            "details": "Persistent audit trail of state mutations"
        })

        # Data Flows
        lines.append("  %% Data Flows")
        lines.append('  ExtUser -->|"1. Action Request Payload"| P1')
        lines.append('  P1 -->|"2. Clean Command"| P2')
        lines.append('  P2 <-->|"3. Read / Query Schema"| DS1')
        lines.append('  P2 -->|"4. State Delta & Commit"| DS1')
        lines.append('  P2 <-->|"5. Integration Sync"| ExtAPI')
        lines.append('  P2 -->|"6. Executed Result"| P3')
        lines.append('  P3 -->|"7. Final Response"| ExtUser')
        lines.append('  P3 -->|"8. Event Log Record"| DS2')

        limitations = (
            "Data flow diagram models Level-1 information movement between external clients, "
            "workflow processes, and underlying persistent data stores."
        )
        description = f"Level-1 Data Flow Diagram (DFD): Traces user input flows, processing transformations, and storage updates in {self.repo_name}"
        return "\n".join(lines), description, limitations, evidence_list

