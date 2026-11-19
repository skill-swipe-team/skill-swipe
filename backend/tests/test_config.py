import pytest

from backend import database


@pytest.fixture
def env_file(monkeypatch, tmp_path):
    for name in (
        "DATABASE_URL",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    ):
        monkeypatch.delenv(name, raising=False)

    path = tmp_path / ".env"
    path.write_text(
        "POSTGRES_HOST=file-host\n"
        "POSTGRES_PORT=6543\n"
        "POSTGRES_DB=test_db\n"
        "POSTGRES_USER=test_user\n"
        "POSTGRES_PASSWORD=test_password\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(database, "ENV_FILE", path)
    return path


def test_database_config_reads_env_file_with_environment_priority(
    env_file, monkeypatch
):
    expected = {
        "host": "file-host",
        "port": 6543,
        "database": "test_db",
        "user": "test_user",
        "password": "test_password",
    }
    assert database.get_database_config() == expected

    monkeypatch.setenv("POSTGRES_HOST", "process-host")
    monkeypatch.setenv("POSTGRES_PASSWORD", "process:password@/test")
    assert database.get_database_config() == expected | {
        "host": "process-host",
        "password": "process:password@/test",
    }


def test_database_url_overrides_components(env_file, monkeypatch):
    env_file.unlink()
    url = "postgresql://test_user:test_password@test-host:6543/test_db"
    monkeypatch.setenv("DATABASE_URL", url)

    assert database.get_database_config() == {"dsn": url}


def test_database_config_requires_environment_variables(env_file):
    env_file.unlink()

    with pytest.raises(RuntimeError, match="Missing database environment variables"):
        database.get_database_config()


def test_empty_password_does_not_fall_back_to_env_file(env_file, monkeypatch):
    monkeypatch.setenv("POSTGRES_PASSWORD", "")

    with pytest.raises(RuntimeError, match="POSTGRES_PASSWORD"):
        database.get_database_config()


@pytest.mark.parametrize("port", ["invalid", "0", "65536"])
def test_database_port_is_validated(env_file, monkeypatch, port):
    monkeypatch.setenv("POSTGRES_PORT", port)

    with pytest.raises(RuntimeError, match="POSTGRES_PORT must be an integer"):
        database.get_database_config()
