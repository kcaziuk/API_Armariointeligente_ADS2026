import pytest

from app.services import openweather


class RespostaFalsa:
    def __init__(self, status_code, dados=None):
        self.status_code = status_code
        self._dados = dados or {}

    def json(self):
        return self._dados


def clima_falso(temperatura, condicao="Clear"):
    def get_falso(url, params=None, timeout=None):
        return RespostaFalsa(200, {
            "name": params["q"],
            "main": {"temp": temperatura, "feels_like": temperatura},
            "weather": [{"main": condicao, "description": "teste"}],
        })
    return get_falso


@pytest.fixture(autouse=True)
def chave_de_teste(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "chave-de-teste")


def criar_peca(client, **campos):
    dados = {"nome": "Peça", "tipo": "Blusa", "cor": "preta", **campos}
    resposta = client.post("/pecas", json=dados)
    assert resposta.status_code == 201
    return resposta.json()


def test_classificar_clima():
    assert openweather.classificar_clima(10) == "Frio"
    assert openweather.classificar_clima(20) == "Ameno"
    assert openweather.classificar_clima(25) == "Quente"


def test_clima_usa_cidade_do_cadastro(client, monkeypatch):
    monkeypatch.setattr(openweather.httpx2, "get", clima_falso(10))
    resposta = client.get("/clima")
    assert resposta.status_code == 200
    assert resposta.json()["cidade"] == "Curitiba"
    assert resposta.json()["clima"] == "Frio"


def test_cidade_inexistente_da_404(client, monkeypatch):
    monkeypatch.setattr(openweather.httpx2, "get", lambda *args, **kwargs: RespostaFalsa(404))
    assert client.get("/clima", params={"cidade": "Xyz"}).status_code == 404


def test_servico_fora_do_ar_da_503(client, monkeypatch):
    def sem_internet(*args, **kwargs):
        raise openweather.httpx2.ConnectError("sem rede")

    monkeypatch.setattr(openweather.httpx2, "get", sem_internet)
    assert client.get("/clima").status_code == 503


def test_sem_chave_configurada_da_503(client, monkeypatch):
    monkeypatch.delenv("OPENWEATHER_API_KEY")
    assert client.get("/clima").status_code == 503


def test_clima_exige_token(anonymous_client):
    assert anonymous_client.get("/clima").status_code == 401


def test_look_no_frio_com_chuva(client, monkeypatch):
    monkeypatch.setattr(openweather.httpx2, "get", clima_falso(8, "Rain"))
    criar_peca(client, nome="Blusa de lã", clima_ideal="Frio")
    criar_peca(client, nome="Regata", clima_ideal="Quente")
    criar_peca(client, nome="Calça jeans", tipo="Calça")
    criar_peca(client, nome="Capa de chuva", tipo="Casaco", clima_ideal="Frio", pode_chuva=True)

    resposta = client.get("/looks/sugestao")
    assert resposta.status_code == 200
    look = resposta.json()["look"]
    assert look["parte_de_cima"]["nome"] == "Blusa de lã"
    assert look["parte_de_baixo"]["nome"] == "Calça jeans"
    assert look["casaco"]["nome"] == "Capa de chuva"
    assert look["calcado"] is None
    assert "Nenhum calçado limpo para esse clima" in resposta.json()["avisos"]


def test_peca_suja_nao_entra_no_look(client, monkeypatch):
    monkeypatch.setattr(openweather.httpx2, "get", clima_falso(30))
    peca = criar_peca(client, nome="Camiseta", clima_ideal="Quente")
    client.patch(f"/pecas/{peca['id']}", json={"estado": "Suja"})

    look = client.get("/looks/sugestao").json()["look"]
    assert look["parte_de_cima"] is None
