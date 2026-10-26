import os

import httpx2
from fastapi import HTTPException


URL_CLIMA = "https://api.openweathermap.org/data/2.5/weather"
CONDICOES_DE_CHUVA = {"Rain", "Drizzle", "Thunderstorm"}


def classificar_clima(sensacao: float) -> str:
    if sensacao < 15:
        return "Frio"
    if sensacao < 25:
        return "Ameno"
    return "Quente"


def buscar_clima(cidade: str) -> dict:
    chave = os.getenv("OPENWEATHER_API_KEY")
    if not chave or chave == "coloque-sua-chave-aqui":
        raise HTTPException(status_code=503, detail="Serviço de clima não configurado")

    try:
        resposta = httpx2.get(
            URL_CLIMA,
            params={"q": cidade, "appid": chave, "units": "metric", "lang": "pt_br"},
            timeout=10,
        )
    except httpx2.HTTPError:
        raise HTTPException(status_code=503, detail="Serviço de clima indisponível")

    if resposta.status_code == 404:
        raise HTTPException(status_code=404, detail="Cidade não encontrada")
    if resposta.status_code != 200:
        raise HTTPException(status_code=503, detail="Serviço de clima indisponível")

    dados = resposta.json()
    sensacao = dados["main"]["feels_like"]
    return {
        "cidade": dados["name"],
        "temperatura": dados["main"]["temp"],
        "sensacao": sensacao,
        "descricao": dados["weather"][0]["description"],
        "chuva": dados["weather"][0]["main"] in CONDICOES_DE_CHUVA,
        "clima": classificar_clima(sensacao),
    }
