import re
from typing import Dict, Any, List
from app.agents.state import AgentState
from app.llm.provider import LLMProvider, get_llm_provider
from app.llm.mock_provider import HighFidelityMockProvider
from app.core.logging import logger

class DiagramAgent:
    def __init__(self, llm_provider: LLMProvider = None):
        self.llm = llm_provider or get_llm_provider()

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        logger.info(f"DiagramAgent: Generating diagrams for '{state.user_requirement}'")
        req = state.user_requirement.lower()
        diagrams = []

        if not isinstance(self.llm, HighFidelityMockProvider):
            try:
                system_prompt = (
                    "You are an expert Software Architecture Visualizer. Generate valid Mermaid.js diagrams "
                    "for the provided software design. Output the following diagrams:\n"
                    "1. Architecture / Component diagram (graph TD ...)\n"
                    "2. Sequence / Flow diagram (sequenceDiagram ...)\n"
                    "3. Use Case diagram (graph LR ... with actors and system boundary)\n"
                    "4. State Machine diagram (stateDiagram-v2 ...)\n"
                    "5. Data Flow Diagram (flowchart LR ... Level-1 DFD)\n"
                    "Output each diagram inside standard mermaid markdown code blocks: ```mermaid ... ```"
                )
                raw_response = await self.llm.generate_response(
                    prompt=f"Requirement: {state.user_requirement}\nDesign Doc:\n{state.design_doc or ''}",
                    system_prompt=system_prompt
                )
                blocks = re.findall(r"```(?:mermaid)?\s*\n(.*?)\n```", raw_response, re.DOTALL)
                for block in blocks:
                    cleaned = block.strip()
                    if cleaned.startswith("sequenceDiagram"):
                        diagrams.append({
                            "type": "sequence",
                            "mermaid_code": cleaned,
                            "description": f"Sequence flow for {state.user_requirement[:60]}"
                        })
                    elif cleaned.startswith("stateDiagram"):
                        diagrams.append({
                            "type": "state",
                            "mermaid_code": cleaned,
                            "description": f"State machine lifecycle for {state.user_requirement[:60]}"
                        })
                    elif "actor" in cleaned.lower() or "usecase" in cleaned.lower():
                        diagrams.append({
                            "type": "usecase",
                            "mermaid_code": cleaned,
                            "description": f"Use case diagram for {state.user_requirement[:60]}"
                        })
                    elif "data flow" in cleaned.lower() or "dfd" in cleaned.lower() or "store" in cleaned.lower():
                        diagrams.append({
                            "type": "dfd",
                            "mermaid_code": cleaned,
                            "description": f"Level-1 Data Flow Diagram for {state.user_requirement[:60]}"
                        })
                    elif cleaned.startswith("graph") or cleaned.startswith("flowchart") or cleaned.startswith("classDiagram"):
                        diagrams.append({
                            "type": "architecture",
                            "mermaid_code": cleaned,
                            "description": f"Component architecture for {state.user_requirement[:60]}"
                        })
                if diagrams:
                    logger.info(f"DiagramAgent: LLM generated {len(diagrams)} dynamic Mermaid diagrams.")
            except Exception as e:
                logger.warning(f"DiagramAgent: LLM diagram generation fallback triggered: {e}")

        # Fallback to structured templates if LLM didn't produce diagrams
        if not diagrams:
            is_user_auth = any(k in req for k in ["auth", "jwt", "login", "register", "registration", "signup", "password", "user"])
            if is_user_auth:
                # 1. Architecture Diagram
                arch_diagram = (
                    "graph TD\n"
                    '    Client["Client / Frontend Application"] --> Router["User Registration & Auth API Router"]\n'
                    '    Router --> Service["User Registration Service"]\n'
                    '    Service --> Validator["Input & Password Validator"]\n'
                    '    Service --> AuthService["Auth Service (SHA-256 Hashing & JWT)"]\n'
                    '    Service --> UserStore["User Repository / Database"]\n'
                    '    AuthService --> TokenEngine["Signed Bearer Token Engine"]'
                )
                diagrams.append({
                    "type": "architecture",
                    "mermaid_code": arch_diagram,
                    "description": "Component Architecture: Structural topology of authentication routers, services, security hashing, and database stores"
                })

                # 2. Sequence Diagram
                seq_diagram = (
                    "sequenceDiagram\n"
                    "    autonumber\n"
                    "    actor Client as User / Frontend\n"
                    "    participant Route as User API Router\n"
                    "    participant Service as UserRegistrationService\n"
                    "    participant Auth as AuthService (Hashing & JWT)\n"
                    "    participant DB as User Database\n\n"
                    "    Client->>Route: POST /api/v1/users/register (email, password, name)\n"
                    "    Route->>Service: register_user(payload)\n"
                    "    Service->>Service: validate email & password length (>= 8 chars)\n"
                    "    Service->>DB: check existing user by email\n"
                    "    DB-->>Service: no duplicate found\n"
                    "    Service->>Auth: hash_password(plain_password)\n"
                    "    Auth-->>Service: return secure SHA-256 hash\n"
                    "    Service->>DB: save user record (id, email, hash)\n"
                    "    DB-->>Service: committed\n"
                    "    Service->>Auth: create_access_token(claims)\n"
                    "    Auth-->>Service: signed JWT token\n"
                    "    Service-->>Route: UserResponse + Token\n"
                    "    Route-->>Client: 201 Created (User Data & Bearer Token)\n"
                    "    Note over Client, Route: Subsequent Login & Authentication\n"
                    "    Client->>Route: POST /api/v1/users/login (email, password)\n"
                    "    Route->>Service: login_user(payload)\n"
                    "    Service->>Auth: verify_password(raw, hash)\n"
                    "    Auth-->>Service: verification true\n"
                    "    Service-->>Client: 200 OK + JWT Access Token"
                )
                diagrams.append({
                    "type": "sequence",
                    "mermaid_code": seq_diagram,
                    "description": "Sequence Flow: Chronological message exchanges across client, registration service, password hashing, and token dispatch"
                })

                # 3. Use Case Diagram
                usecase_diagram = (
                    "graph LR\n"
                    '    subgraph AuthScope ["Authentication & Identity Boundary"]\n'
                    '        UC1["Register Account (Email & Password)"]\n'
                    '        UC2["Login & Acquire Bearer Token"]\n'
                    '        UC3["Verify Credentials & Password Hash"]\n'
                    '        UC4["Access Protected Resources"]\n'
                    '        UC5["Refresh Expired Token"]\n'
                    '    end\n'
                    '    User(["👤 End User"])\n'
                    '    Admin(["🛡️ Administrator"])\n'
                    '    User --> UC1\n'
                    '    User --> UC2\n'
                    '    User --> UC4\n'
                    '    User --> UC5\n'
                    '    Admin --> UC4\n'
                    '    UC2 -.->|"<<include>>"| UC3'
                )
                diagrams.append({
                    "type": "usecase",
                    "mermaid_code": usecase_diagram,
                    "description": "Use Case Diagram: Primary actors and functional authentication capabilities including registration, token minting, and authorization"
                })

                # 4. State Diagram
                state_diagram = (
                    "stateDiagram-v2\n"
                    "    [*] --> Unauthenticated\n"
                    "    Unauthenticated --> ValidatingCredentials : Submit Credentials\n"
                    "    ValidatingCredentials --> Authenticated : Password & Salt Verified\n"
                    "    ValidatingCredentials --> AuthFailed : Invalid Credentials\n"
                    "    AuthFailed --> Unauthenticated : Retry (< 5 attempts)\n"
                    "    AuthFailed --> AccountLocked : Max Attempts Exceeded\n"
                    "    Authenticated --> TokenRefreshed : Periodic Refresh\n"
                    "    TokenRefreshed --> Authenticated\n"
                    "    Authenticated --> LoggedOut : User Logout\n"
                    "    LoggedOut --> [*]\n"
                    "    AccountLocked --> [*]"
                )
                diagrams.append({
                    "type": "state",
                    "mermaid_code": state_diagram,
                    "description": "State Machine Diagram: State transitions from unauthenticated through validation, authenticated session, token refresh, and terminal states"
                })

                # 5. Data Flow Diagram (Level-1 DFD)
                dfd_diagram = (
                    "flowchart LR\n"
                    "    %% External Entities\n"
                    '    ClientApp["👤 Client Application / Browser"]\n'
                    "    %% Processes\n"
                    '    P1(("1.0 Ingest & Sanitize Credentials"))\n'
                    '    P2(("2.0 Verify Password & Cryptographic Hash"))\n'
                    '    P3(("3.0 Mint JWT Bearer Token"))\n'
                    "    %% Data Stores\n"
                    '    DS1[("D1: User Accounts Database")]\n'
                    '    DS2[("D2: Revoked Token Blacklist Store")]\n'
                    "    %% Data Flows\n"
                    '    ClientApp -->|"Raw Credentials Payload"| P1\n'
                    '    P1 -->|"Sanitized Input"| P2\n'
                    '    P2 <-->|"Query Salt & Hash Record"| DS1\n'
                    '    P2 -->|"Verification Succeeded"| P3\n'
                    '    P3 <-->|"Check Token Revocation"| DS2\n'
                    '    P3 -->|"Signed JWT Access Token"| ClientApp'
                )
                diagrams.append({
                    "type": "dfd",
                    "mermaid_code": dfd_diagram,
                    "description": "Level-1 Data Flow Diagram (DFD): Information pipelines showing credential sanitization, database hash verification, and token emission"
                })
            else:
                # 1. Architecture Diagram
                arch_diagram = (
                    "graph TD\n"
                    '    Client["Client Application"] --> Controller["Service Controller"]\n'
                    '    Controller --> Engine["Processing Engine"]\n'
                    '    Engine --> Validator["Input & Schema Validator"]\n'
                    '    Engine --> Storage["Persistence Layer"]'
                )
                diagrams.append({
                    "type": "architecture",
                    "mermaid_code": arch_diagram,
                    "description": "Component Architecture: Component topology and data pathways across client, controller, engine, and persistence"
                })

                # 2. Sequence Diagram
                seq_diagram = (
                    "sequenceDiagram\n"
                    "    autonumber\n"
                    "    actor Client as User / Client\n"
                    "    participant Controller as Service Controller\n"
                    "    participant Engine as Processing Engine\n"
                    "    participant Storage as Database Store\n"
                    "    Client->>Controller: Dispatch Command Payload\n"
                    "    Controller->>Engine: Execute Business Workflow\n"
                    "    Engine->>Storage: Read Domain State\n"
                    "    Storage-->>Engine: State Records\n"
                    "    Engine->>Storage: Commit State Delta\n"
                    "    Storage-->>Engine: Acknowledged\n"
                    "    Engine-->>Controller: Execution Outcome\n"
                    "    Controller-->>Client: 200 OK Response"
                )
                diagrams.append({
                    "type": "sequence",
                    "mermaid_code": seq_diagram,
                    "description": "Sequence Flow: Chronological message and execution sequence between client, controller, engine, and database"
                })

                # 3. Use Case Diagram
                usecase_diagram = (
                    "graph LR\n"
                    '    subgraph CoreCapabilities ["System Capabilities Scope"]\n'
                    '        UC1["Initiate Workflow Action"]\n'
                    '        UC2["Validate Parameters & Schema"]\n'
                    '        UC3["Execute Domain Transformation"]\n'
                    '        UC4["Query Execution Results & Metrics"]\n'
                    '    end\n'
                    '    User(["👤 Operator / User"])\n'
                    '    Admin(["🛡️ Administrator"])\n'
                    '    User --> UC1\n'
                    '    User --> UC4\n'
                    '    Admin --> UC1\n'
                    '    Admin --> UC3\n'
                    '    UC1 -.->|"<<include>>"| UC2'
                )
                diagrams.append({
                    "type": "usecase",
                    "mermaid_code": usecase_diagram,
                    "description": "Use Case Diagram: Operational actors, system boundary, and primary functional goals"
                })

                # 4. State Diagram
                state_diagram = (
                    "stateDiagram-v2\n"
                    "    [*] --> Idle\n"
                    "    Idle --> InProgress : Start Action\n"
                    "    InProgress --> Validated : Parameters Valid\n"
                    "    InProgress --> Failed : Validation Error\n"
                    "    Validated --> Completed : State Committed\n"
                    "    Validated --> Failed : Execution Fault\n"
                    "    Failed --> Idle : Reset / Retry\n"
                    "    Completed --> [*]"
                )
                diagrams.append({
                    "type": "state",
                    "mermaid_code": state_diagram,
                    "description": "State Machine Diagram: Lifecycle states tracking command dispatch, validation, execution, and termination"
                })

                # 5. Data Flow Diagram (Level-1 DFD)
                dfd_diagram = (
                    "flowchart LR\n"
                    "    %% External Entities\n"
                    '    Client["👤 User / External System"]\n'
                    "    %% Processes\n"
                    '    P1(("1.0 Command Ingestion & Validation"))\n'
                    '    P2(("2.0 Business Transformation Engine"))\n'
                    '    P3(("3.0 Outcome Formatting & Output"))\n'
                    "    %% Data Stores\n"
                    '    DS1[("D1: Operational Domain Database")]\n'
                    "    %% Data Flows\n"
                    '    Client -->|"Input Command"| P1\n'
                    '    P1 -->|"Validated Parameters"| P2\n'
                    '    P2 <-->|"Read & Update State"| DS1\n'
                    '    P2 -->|"Computation Artifacts"| P3\n'
                    '    P3 -->|"Output Result"| Client'
                )
                diagrams.append({
                    "type": "dfd",
                    "mermaid_code": dfd_diagram,
                    "description": "Level-1 Data Flow Diagram (DFD): Information movement between external client, processing pipeline stages, and domain datastore"
                })

        state.diagrams = diagrams
        return {
            "status": "success",
            "diagrams_count": len(diagrams),
            "diagrams": diagrams
        }

