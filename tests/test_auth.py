def test_cadastro_login_e_duplicidade(anonymous_client):
    dados = {
        "nome": "  Kely ",
        "email": " KELY@EXEMPLO.COM ",
        "senha": "senha-segura-123",
        "cidade": "Curitiba",
    }

    resposta = anonymous_client.post("/auth/registrar", json=dados)
    assert resposta.status_code == 201
    assert resposta.json()["nome"] == "Kely"
    assert resposta.json()["email"] == "kely@exemplo.com"
    assert "senha_hash" not in resposta.json()

    assert anonymous_client.post("/auth/registrar", json=dados).status_code == 409
    assert anonymous_client.post(
        "/auth/login",
        json={"email": "kely@exemplo.com", "senha": "senha-errada-123"},
    ).status_code == 401

    login = anonymous_client.post(
        "/auth/login",
        json={"email": "kely@exemplo.com", "senha": "senha-segura-123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    perfil = anonymous_client.get(
        "/auth/eu",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert perfil.status_code == 200
    assert perfil.json()["cidade"] == "Curitiba"


def test_pecas_isoladas_por_usuario(anonymous_client):
    primeiro = {
        "nome": "Pessoa um",
        "email": "um@exemplo.com",
        "senha": "senha-segura-123",
    }
    assert anonymous_client.post("/auth/registrar", json=primeiro).status_code == 201
    token_um = anonymous_client.post(
        "/auth/login",
        json={"email": primeiro["email"], "senha": primeiro["senha"]},
    ).json()["access_token"]

    peca = anonymous_client.post(
        "/pecas",
        headers={"Authorization": f"Bearer {token_um}"},
        json={"nome": "Blusa", "tipo": "Blusa", "cor": "azul"},
    )
    assert peca.status_code == 201

    segundo = {
        "nome": "Pessoa dois",
        "email": "dois@exemplo.com",
        "senha": "senha-segura-456",
    }
    assert anonymous_client.post("/auth/registrar", json=segundo).status_code == 201
    token_dois = anonymous_client.post(
        "/auth/login",
        json={"email": segundo["email"], "senha": segundo["senha"]},
    ).json()["access_token"]

    resposta = anonymous_client.get(
        "/pecas",
        headers={"Authorization": f"Bearer {token_dois}"},
    )
    assert resposta.status_code == 200
    assert resposta.json() == []

    resposta = anonymous_client.get(
        "/pecas",
        headers={"Authorization": f"Bearer {token_um}"},
    )
    assert [item["id"] for item in resposta.json()] == [peca.json()["id"]]


def test_cors_restringe_origens(anonymous_client):
    resposta = anonymous_client.options(
        "/pecas",
        headers={
            "Origin": "http://127.0.0.1:5500",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert resposta.status_code == 200
    assert resposta.headers["access-control-allow-origin"] == "http://127.0.0.1:5500"

    resposta = anonymous_client.options(
        "/pecas",
        headers={
            "Origin": "http://site-externo.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in resposta.headers
