import random
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import obter_sessao
from app.dependencies import usuario_atual
from app.models import Peca, Usuario
from app.schemas import ClimaResposta, LookResposta, Ocasiao
from app.services.openweather import buscar_clima


router = APIRouter(tags=["Clima e looks"])


def escolher_cidade(cidade: Optional[str], usuario: Usuario) -> str:
    cidade = (cidade or usuario.cidade or "").strip()
    if not cidade:
        raise HTTPException(status_code=400, detail="Informe a cidade ou cadastre uma no seu perfil")
    return cidade


@router.get("/clima", response_model=ClimaResposta)
def ver_clima(
    cidade: Optional[str] = None,
    usuario: Usuario = Depends(usuario_atual),
):
    return buscar_clima(escolher_cidade(cidade, usuario))


@router.get("/looks/sugestao", response_model=LookResposta)
def sugerir_look(
    ocasiao: Optional[Ocasiao] = None,
    cidade: Optional[str] = None,
    db: Session = Depends(obter_sessao),
    usuario: Usuario = Depends(usuario_atual),
):
    clima = buscar_clima(escolher_cidade(cidade, usuario))
    precisa_casaco = clima["clima"] == "Frio" or clima["chuva"]

    consulta = select(Peca).where(
        Peca.usuario_id == usuario.id,
        Peca.retirada_em.is_(None),
        Peca.estado == "Limpa",
        Peca.clima_ideal.in_([clima["clima"], "Qualquer"]),
    )
    if ocasiao:
        consulta = consulta.where(Peca.ocasiao == ocasiao.value)
    pecas = db.scalars(consulta).all()

    def escolher(tipo: str) -> Optional[Peca]:
        candidatas = [peca for peca in pecas if peca.tipo == tipo]
        if clima["chuva"]:
            candidatas = [peca for peca in candidatas if peca.pode_chuva] or candidatas
        return random.choice(candidatas) if candidatas else None

    look = {
        "parte_de_cima": escolher("Blusa"),
        "parte_de_baixo": escolher("Calça"),
        "calcado": escolher("Calçado"),
        "acessorio": escolher("Acessório"),
        "casaco": escolher("Casaco") if precisa_casaco else None,
    }

    avisos = []
    if look["parte_de_cima"] is None:
        avisos.append("Nenhuma blusa limpa para esse clima")
    if look["parte_de_baixo"] is None:
        avisos.append("Nenhuma calça limpa para esse clima")
    if look["calcado"] is None:
        avisos.append("Nenhum calçado limpo para esse clima")
    if precisa_casaco and look["casaco"] is None:
        avisos.append("Está frio ou chovendo, mas não há casaco limpo")

    return {"clima": clima, "look": look, "avisos": avisos}
