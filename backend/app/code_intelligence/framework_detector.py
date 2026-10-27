from typing import List, Dict, Any, Optional
import os
from pathlib import Path

# Mapping of package names to framework metadata
FRAMEWORK_CATALOG = {
    # Backend Frameworks
    "fastapi": {"name": "FastAPI", "category": "Backend Framework", "icon": "zap"},
    "flask": {"name": "Flask", "category": "Backend Framework", "icon": "server"},
    "django": {"name": "Django", "category": "Backend Framework", "icon": "server"},
    "express": {"name": "Express.js", "category": "Backend Framework", "icon": "server"},
    "koa": {"name": "Koa", "category": "Backend Framework", "icon": "server"},
    "nestjs": {"name": "NestJS", "category": "Backend Framework", "icon": "server"},
    "@nestjs/core": {"name": "NestJS", "category": "Backend Framework", "icon": "server"},
    "gin-gonic/gin": {"name": "Gin", "category": "Backend Framework", "icon": "server"},
    "labstack/echo": {"name": "Echo", "category": "Backend Framework", "icon": "server"},
    "gofiber/fiber": {"name": "Fiber", "category": "Backend Framework", "icon": "server"},
    "actix-web": {"name": "Actix Web", "category": "Backend Framework", "icon": "server"},
    "axum": {"name": "Axum", "category": "Backend Framework", "icon": "server"},
    "rocket": {"name": "Rocket", "category": "Backend Framework", "icon": "server"},
    "spring-boot": {"name": "Spring Boot", "category": "Backend Framework", "icon": "server"},
    "tornado": {"name": "Tornado", "category": "Backend Framework", "icon": "server"},
    "starlette": {"name": "Starlette", "category": "Backend Framework", "icon": "server"},
    "uvicorn": {"name": "Uvicorn", "category": "ASGI Server", "icon": "cpu"},
    "gunicorn": {"name": "Gunicorn", "category": "WSGI Server", "icon": "cpu"},

    # Frontend Frameworks & Libraries
    "react": {"name": "React", "category": "Frontend Framework", "icon": "layers"},
    "react-dom": {"name": "React DOM", "category": "Frontend Framework", "icon": "layers"},
    "next": {"name": "Next.js", "category": "Full-Stack Framework", "icon": "globe"},
    "vue": {"name": "Vue.js", "category": "Frontend Framework", "icon": "layers"},
    "nuxt": {"name": "Nuxt", "category": "Full-Stack Framework", "icon": "globe"},
    "@angular/core": {"name": "Angular", "category": "Frontend Framework", "icon": "layers"},
    "svelte": {"name": "Svelte", "category": "Frontend Framework", "icon": "layers"},
    "@sveltejs/kit": {"name": "SvelteKit", "category": "Full-Stack Framework", "icon": "globe"},
    "solid-js": {"name": "SolidJS", "category": "Frontend Framework", "icon": "layers"},
    "remix": {"name": "Remix", "category": "Full-Stack Framework", "icon": "globe"},
    "@remix-run/react": {"name": "Remix", "category": "Full-Stack Framework", "icon": "globe"},

    # Styling & UI Component Libraries
    "tailwindcss": {"name": "Tailwind CSS", "category": "Styling / CSS", "icon": "sparkles"},
    "@tailwindcss/vite": {"name": "Tailwind CSS", "category": "Styling / CSS", "icon": "sparkles"},
    "bootstrap": {"name": "Bootstrap", "category": "Styling / CSS", "icon": "palette"},
    "@mui/material": {"name": "Material UI", "category": "UI Component Library", "icon": "layout"},
    "antd": {"name": "Ant Design", "category": "UI Component Library", "icon": "layout"},
    "@chakra-ui/react": {"name": "Chakra UI", "category": "UI Component Library", "icon": "layout"},
    "lucide-react": {"name": "Lucide Icons", "category": "Icon Library", "icon": "sparkles"},
    "styled-components": {"name": "Styled Components", "category": "CSS-in-JS", "icon": "palette"},
    "@emotion/react": {"name": "Emotion", "category": "CSS-in-JS", "icon": "palette"},
    "sass": {"name": "Sass / SCSS", "category": "Styling / Preprocessor", "icon": "palette"},

    # Database & ORM / ODM
    "sqlalchemy": {"name": "SQLAlchemy", "category": "Database / ORM", "icon": "database"},
    "alembic": {"name": "Alembic", "category": "Database Migrations", "icon": "database"},
    "prisma": {"name": "Prisma", "category": "Database / ORM", "icon": "database"},
    "@prisma/client": {"name": "Prisma Client", "category": "Database / ORM", "icon": "database"},
    "mongoose": {"name": "Mongoose", "category": "Database / ODM (MongoDB)", "icon": "database"},
    "mongodb": {"name": "MongoDB Driver", "category": "Database Driver", "icon": "database"},
    "sequelize": {"name": "Sequelize", "category": "Database / ORM", "icon": "database"},
    "typeorm": {"name": "TypeORM", "category": "Database / ORM", "icon": "database"},
    "pg": {"name": "PostgreSQL Driver (pg)", "category": "Database Driver", "icon": "database"},
    "asyncpg": {"name": "Asyncpg", "category": "Database Driver", "icon": "database"},
    "psycopg2": {"name": "Psycopg2", "category": "Database Driver", "icon": "database"},
    "psycopg2-binary": {"name": "Psycopg2", "category": "Database Driver", "icon": "database"},
    "mysql2": {"name": "MySQL2", "category": "Database Driver", "icon": "database"},
    "redis": {"name": "Redis Client", "category": "Cache / In-Memory DB", "icon": "database"},
    "ioredis": {"name": "ioredis", "category": "Cache / In-Memory DB", "icon": "database"},
    "sqlite3": {"name": "SQLite3 Driver", "category": "Database Driver", "icon": "database"},
    "dotenv": {"name": "Dotenv", "category": "Environment Config", "icon": "shield-check"},
    "nodemon": {"name": "Nodemon", "category": "Dev Tool / Hot Reload", "icon": "zap"},

    # State Management & Data Fetching
    "redux": {"name": "Redux", "category": "State Management", "icon": "cpu"},
    "@reduxjs/toolkit": {"name": "Redux Toolkit", "category": "State Management", "icon": "cpu"},
    "zustand": {"name": "Zustand", "category": "State Management", "icon": "cpu"},
    "mobx": {"name": "MobX", "category": "State Management", "icon": "cpu"},
    "@tanstack/react-query": {"name": "TanStack Query", "category": "Data Fetching / Cache", "icon": "activity"},
    "react-query": {"name": "React Query", "category": "Data Fetching / Cache", "icon": "activity"},
    "swr": {"name": "SWR", "category": "Data Fetching", "icon": "activity"},
    "axios": {"name": "Axios", "category": "HTTP Client", "icon": "network"},
    "httpx": {"name": "HTTPX", "category": "Async HTTP Client", "icon": "network"},
    "requests": {"name": "Requests", "category": "HTTP Client", "icon": "network"},

    # Testing Frameworks
    "pytest": {"name": "Pytest", "category": "Testing Framework", "icon": "check-circle"},
    "pytest-asyncio": {"name": "Pytest AsyncIO", "category": "Testing Utility", "icon": "check-circle"},
    "jest": {"name": "Jest", "category": "Testing Framework", "icon": "check-circle"},
    "vitest": {"name": "Vitest", "category": "Testing Framework", "icon": "check-circle"},
    "mocha": {"name": "Mocha", "category": "Testing Framework", "icon": "check-circle"},
    "chai": {"name": "Chai", "category": "Testing / Assertion", "icon": "check-circle"},
    "cypress": {"name": "Cypress", "category": "E2E Testing", "icon": "check-circle"},
    "@playwright/test": {"name": "Playwright", "category": "E2E Testing", "icon": "check-circle"},
    "supertest": {"name": "Supertest", "category": "Integration Testing", "icon": "check-circle"},

    # Build Tools & Bundlers
    "vite": {"name": "Vite", "category": "Build Tool & Bundler", "icon": "zap"},
    "webpack": {"name": "Webpack", "category": "Bundler", "icon": "package"},
    "esbuild": {"name": "esbuild", "category": "Bundler", "icon": "zap"},
    "rollup": {"name": "Rollup", "category": "Bundler", "icon": "package"},
    "turbopack": {"name": "Turbopack", "category": "Bundler", "icon": "zap"},
    "babel": {"name": "Babel", "category": "Transpiler", "icon": "code"},
    "@babel/core": {"name": "Babel", "category": "Transpiler", "icon": "code"},

    # Auth & Security
    "jsonwebtoken": {"name": "JSON Web Token (JWT)", "category": "Authentication / Security", "icon": "shield-check"},
    "jose": {"name": "JOSE", "category": "Authentication / Security", "icon": "shield-check"},
    "bcrypt": {"name": "Bcrypt", "category": "Password Hashing / Security", "icon": "shield-check"},
    "bcryptjs": {"name": "Bcrypt.js", "category": "Password Hashing / Security", "icon": "shield-check"},
    "passlib": {"name": "Passlib", "category": "Password Hashing / Security", "icon": "shield-check"},
    "python-jose": {"name": "Python-JOSE", "category": "Authentication / Security", "icon": "shield-check"},
    "passport": {"name": "Passport.js", "category": "Authentication Middleware", "icon": "shield-check"},
    "next-auth": {"name": "NextAuth.js", "category": "Authentication", "icon": "shield-check"},
    "cors": {"name": "CORS Middleware", "category": "Middleware / Security", "icon": "shield-check"},

    # AI, Data & Vector Stores
    "torch": {"name": "PyTorch", "category": "AI / Machine Learning", "icon": "brain"},
    "tensorflow": {"name": "TensorFlow", "category": "AI / Machine Learning", "icon": "brain"},
    "transformers": {"name": "HuggingFace Transformers", "category": "AI / NLP", "icon": "brain"},
    "langchain": {"name": "LangChain", "category": "LLM Orchestration", "icon": "bot"},
    "openai": {"name": "OpenAI SDK", "category": "AI / LLM Provider", "icon": "bot"},
    "anthropic": {"name": "Anthropic SDK", "category": "AI / LLM Provider", "icon": "bot"},
    "chromadb": {"name": "ChromaDB", "category": "Vector Database", "icon": "database"},
    "scikit-learn": {"name": "Scikit-Learn", "category": "Machine Learning", "icon": "activity"},
    "pandas": {"name": "Pandas", "category": "Data Analysis", "icon": "bar-chart"},
    "numpy": {"name": "NumPy", "category": "Numerical Computing", "icon": "activity"},
    "pydantic": {"name": "Pydantic", "category": "Data Validation", "icon": "check-square"},
}

# File signatures that indicate specific frameworks
FILE_SIGNATURES = [
    {"pattern": "manage.py", "name": "Django", "category": "Backend Framework", "icon": "server"},
    {"pattern": "vite.config.ts", "name": "Vite", "category": "Build Tool & Bundler", "icon": "zap"},
    {"pattern": "vite.config.js", "name": "Vite", "category": "Build Tool & Bundler", "icon": "zap"},
    {"pattern": "tailwind.config.js", "name": "Tailwind CSS", "category": "Styling / CSS", "icon": "sparkles"},
    {"pattern": "tailwind.config.ts", "name": "Tailwind CSS", "category": "Styling / CSS", "icon": "sparkles"},
    {"pattern": "next.config.js", "name": "Next.js", "category": "Full-Stack Framework", "icon": "globe"},
    {"pattern": "next.config.mjs", "name": "Next.js", "category": "Full-Stack Framework", "icon": "globe"},
    {"pattern": "next.config.ts", "name": "Next.js", "category": "Full-Stack Framework", "icon": "globe"},
    {"pattern": "Dockerfile", "name": "Docker", "category": "Containerization / DevOps", "icon": "container"},
    {"pattern": "docker-compose.yml", "name": "Docker Compose", "category": "Containerization / DevOps", "icon": "container"},
    {"pattern": "docker-compose.yaml", "name": "Docker Compose", "category": "Containerization / DevOps", "icon": "container"},
    {"pattern": "tsconfig.json", "name": "TypeScript", "category": "Language / Compiler", "icon": "code"},
    {"pattern": "pom.xml", "name": "Maven / Java", "category": "Build Tool / JVM", "icon": "package"},
    {"pattern": "build.gradle", "name": "Gradle / Java", "category": "Build Tool / JVM", "icon": "package"},
    {"pattern": "requirements.txt", "name": "Python Pip", "category": "Package Manager / Python", "icon": "package"},
    {"pattern": "package.json", "name": "Node.js / NPM", "category": "Runtime & Package Manager", "icon": "cpu"},
]

def detect_frameworks(
    dependencies: List[Dict[str, Any]],
    file_paths: List[str],
    languages: Optional[Dict[str, int]] = None
) -> List[Dict[str, Any]]:
    """
    Detects frameworks, libraries, and tools from dependencies, file markers, and code structure.
    """
    detected: Dict[str, Dict[str, Any]] = {}

    # 1. Detect from dependencies
    for dep in dependencies:
        dep_name = dep.get("name", "").strip().lower()
        version = dep.get("version")
        source = dep.get("source_file", "manifest")

        matched_key = None
        if dep_name in FRAMEWORK_CATALOG:
            matched_key = dep_name
        else:
            # Check prefix / normalized name
            clean_name = dep_name.split("/")[-1]
            if clean_name in FRAMEWORK_CATALOG:
                matched_key = clean_name

        if matched_key:
            info = FRAMEWORK_CATALOG[matched_key]
            name = info["name"]
            if name not in detected:
                detected[name] = {
                    "name": name,
                    "category": info["category"],
                    "version": version,
                    "source": f"Dependency in {source}",
                    "icon": info["icon"],
                    "confidence": "high",
                }

    # 2. Detect from file markers
    for p in file_paths:
        p_name = Path(p).name
        for sig in FILE_SIGNATURES:
            if p_name.lower() == sig["pattern"].lower():
                name = sig["name"]
                if name not in detected:
                    detected[name] = {
                        "name": name,
                        "category": sig["category"],
                        "version": None,
                        "source": f"Configuration file {p_name}",
                        "icon": sig["icon"],
                        "confidence": "high",
                    }

    # 3. Detect Node.js / Express or Python backend pattern from directory structure if not caught yet
    file_paths_lower = [f.lower() for f in file_paths]
    if not any("Express" in k for k in detected):
        has_routes = any("routes" in p for p in file_paths_lower)
        has_controllers = any("controllers" in p for p in file_paths_lower)
        has_server_js = any(p.endswith("server.js") or p.endswith("app.js") for p in file_paths_lower)
        if (has_routes and has_controllers) or (has_server_js and (has_routes or has_controllers)):
            detected["Express.js"] = {
                "name": "Express.js",
                "category": "Backend Framework (MVC Architecture)",
                "version": None,
                "source": "Detected Controller & Route Structure",
                "icon": "server",
                "confidence": "high",
            }

    # 4. Detect React / Node if JSX/TSX exists
    if not any("React" in k for k in detected):
        has_react_files = any(p.endswith(".jsx") or p.endswith(".tsx") for p in file_paths_lower)
        if has_react_files:
            detected["React"] = {
                "name": "React",
                "category": "Frontend Framework",
                "version": None,
                "source": "Detected JSX/TSX Components",
                "icon": "layers",
                "confidence": "high",
            }

    return list(detected.values())
