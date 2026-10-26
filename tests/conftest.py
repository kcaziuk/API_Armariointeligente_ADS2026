from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app import database
from app.main import app


@pytest.fixture
def anonymous_client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-with-at-least-32-characters")
    db_engine = database.criar_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    monkeypatch.setattr(database, "engine", db_engine)
    monkeypatch.setattr(
        database,
        "SessionLocal",
        sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False),
    )
    with TestClient(app) as test_client:
        yield test_client
    db_engine.dispose()


@pytest.fixture
def client(anonymous_client) -> TestClient:
    resposta = anonymous_client.post(
        "/auth/registrar",
        json={
            "nome": "Pessoa de teste",
            "email": "teste@exemplo.com",
            "senha": "senha-segura-123",
            "cidade": "Curitiba",
        },
    )
    assert resposta.status_code == 201
    token = anonymous_client.post(
        "/auth/login",
        json={"email": "teste@exemplo.com", "senha": "senha-segura-123"},
    ).json()["access_token"]
    anonymous_client.headers["Authorization"] = f"Bearer {token}"
    return anonymous_client
