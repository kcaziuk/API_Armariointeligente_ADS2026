def test_crud_pecas_e_closets(client):
    resposta = client.post(
        "/pecas",
        json={
            "nome": "  Blusa de lã ",
            "tipo": "Blusa",
            "cor": " AZUL ",
            "modelo": " Tricô ",
            "ocasiao": "Trabalho",
            "clima_ideal": "Frio",
            "pode_chuva": True,
        },
    )
    assert resposta.status_code == 201
    peca = resposta.json()
    assert peca["nome"] == "Blusa de lã"
    assert peca["cor"] == "azul"
    assert peca["modelo"] == "tricô"
    peca_id = peca["id"]

    assert client.get("/pecas?cor=AZUL").json()[0]["id"] == peca_id
    assert client.get("/pecas/agrupadas?por=cor").json()["azul"][0]["id"] == peca_id

    resposta = client.post(
        "/closets",
        json={"nome": "Inverno", "pecas_ids": [peca_id, peca_id]},
    )
    assert resposta.status_code == 201
    closet = resposta.json()
    assert closet["pecas_ids"] == [peca_id]
    closet_id = closet["id"]

    resposta = client.patch(f"/pecas/{peca_id}", json={"estado": "Suja"})
    assert resposta.status_code == 200
    assert resposta.json()["estado"] == "Suja"

    resposta = client.delete(f"/pecas/{peca_id}?motivo=Doação")
    assert resposta.status_code == 204
    assert resposta.content == b""
    assert client.get("/pecas").json() == []
    assert client.get("/pecas/retiradas").json()[0]["id"] == peca_id
    assert client.get(f"/closets/{closet_id}").json()["pecas_ids"] == []


def test_validacao_e_recursos_inexistentes(client):
    resposta = client.post("/pecas", json={"nome": "", "tipo": "Camiseta", "cor": ""})
    assert resposta.status_code == 400
    assert resposta.json()["detail"] == "Dados inválidos"
    assert resposta.json()["erros"]

    assert client.get("/pecas/999").status_code == 404
    assert client.delete("/closets/999").status_code == 404
    assert client.patch("/closets/1", json={"nome": None}).status_code == 400


def test_closet_delete_responde_sem_conteudo(client):
    closet = client.post("/closets", json={"nome": "Trabalho"}).json()
    resposta = client.delete(f"/closets/{closet['id']}")
    assert resposta.status_code == 204
    assert resposta.content == b""


def test_rotas_protegidas_exigem_token(anonymous_client):
    resposta = anonymous_client.get("/pecas")
    assert resposta.status_code == 401
    assert resposta.headers["www-authenticate"] == "Bearer"


def test_frontend_served_from_root_and_assets(anonymous_client):
    pagina = anonymous_client.get("/")
    assert pagina.status_code == 200
    assert "text/html" in pagina.headers["content-type"]
    assert 'id="form-login"' in pagina.text

    script = anonymous_client.get("/js/api.js")
    assert script.status_code == 200
    assert "javascript" in script.headers["content-type"]
