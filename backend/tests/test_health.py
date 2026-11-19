from unittest.mock import MagicMock, Mock

import asyncpg
from fastapi.testclient import TestClient

from backend import database
from backend.main import app


def test_health(monkeypatch):
    pool = MagicMock(spec=asyncpg.Pool)
    pool.__aenter__.return_value = pool
    pool.__aexit__.return_value = False
    pool.fetchval.return_value = 1
    monkeypatch.setattr(database, "get_database_config", dict)
    monkeypatch.setattr(database.asyncpg, "create_pool", Mock(return_value=pool))

    with TestClient(app) as client:
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        pool.fetchval.assert_awaited_once_with("SELECT 1")

    pool.__aexit__.assert_awaited_once()
