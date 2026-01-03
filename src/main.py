"""Main application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import connectors, workflows, executions, transformations
from src.core.config import settings

app = FastAPI(
    title="API Integration Framework",
    description="Multi-connector integration hub with workflows and transformations",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(connectors.router, prefix="/api/connectors", tags=["connectors"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
app.include_router(executions.router, prefix="/api/executions", tags=["executions"])
app.include_router(transformations.router, prefix="/api/transformations", tags=["transformations"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
