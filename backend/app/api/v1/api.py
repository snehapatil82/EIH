from fastapi import APIRouter
from app.api.v1.repositories import router as repositories_router
from app.api.v1.intelligence import router as intelligence_router
from app.api.v1.chat import router as chat_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.changes import router as changes_router
from app.api.v1.research import router as research_router
from app.api.v1.documentation import router as documentation_router
from app.api.v1.terminal import router as terminal_router
from app.api.v1.github_publish import router as github_publish_router

api_router = APIRouter()

api_router.include_router(repositories_router)
api_router.include_router(intelligence_router)
api_router.include_router(chat_router)
api_router.include_router(tasks_router)
api_router.include_router(changes_router)
api_router.include_router(research_router)
api_router.include_router(documentation_router)
api_router.include_router(terminal_router)
api_router.include_router(github_publish_router)

