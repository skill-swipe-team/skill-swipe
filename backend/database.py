"""PostgreSQL connection pool and request dependency."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import asyncpg
from dotenv import dotenv_values
from fastapi import FastAPI, Request

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def get_database_config() -> dict[str, str | int]:
    values = {**dotenv_values(ENV_FILE), **os.environ}
    if database_url := values.get("DATABASE_URL"):
        return {"dsn": database_url}

    required = (
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    )
    missing = [name for name in required if not values.get(name)]
    if missing:
        raise RuntimeError(
            f"Missing database environment variables: {', '.join(missing)}. "
            "Create .env from .env.example or set the variables in the environment."
        )

    try:
        port = int(str(values["POSTGRES_PORT"]))
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        raise RuntimeError(
            "POSTGRES_PORT must be an integer between 1 and 65535."
        ) from None

    return {
        "host": str(values["POSTGRES_HOST"]),
        "port": port,
        "database": str(values["POSTGRES_DB"]),
        "user": str(values["POSTGRES_USER"]),
        "password": str(values["POSTGRES_PASSWORD"]),
    }


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with asyncpg.create_pool(
        **get_database_config(),
        min_size=1,
        max_size=10,
        timeout=5,
        command_timeout=5,
        server_settings={"search_path": "skillswipe"},
    ) as pool:
        await pool.fetchval("SELECT 1")
        app.state.db_pool = pool
        try:
            yield
        finally:
            del app.state.db_pool


async def get_connection(request: Request) -> AsyncIterator[asyncpg.Connection]:
    async with request.app.state.db_pool.acquire(timeout=5) as connection:
        yield connection
