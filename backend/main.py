"""FastAPI application entry point."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]


app = FastAPI(
    title="Skill Swipe API",
    description="API for the Skill Swipe service.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Check service health",
    tags=["System"],
)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
