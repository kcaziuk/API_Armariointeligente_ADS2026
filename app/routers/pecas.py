from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import obter_sessao
from app.dependencies import usuario_atual
from app.models import Peca, Usuario
from app.schemas import (
    AtualizacaoPeca,
    ClimaIdeal,
    DadosPeca,
    EstadoPeca,
    MotivoRetirada,
    Ocasiao,
    PecaResposta,
    TipoPeca,
)


router = APIRouter(prefix="/pecas", tags=["Peças"])


def buscar_peca(db: Session, usuario: Usuario, peca_id: int, ativa: bool = False) -> Peca:
    consulta = select(Peca).where(
        Peca.id == peca_id,
        Peca.usuario_id == usuario.id,
    )
    if ativa:
        consulta = consulta.where(Peca.retirada_em.is_(None))

    peca = db.scalar(consulta)
    if peca is None:
        raise HTTPException(status_code=404, detail="Peça não encontrada")
    return peca


@router.get("", response_model=list[PecaResposta])
def consultar_pecas(
    tipo: Optional[TipoPeca] = None,
    cor: Optional[str] = None,
    modelo: Optional[str] = None,
    estado: Optional[EstadoPeca] = None,
    ocasiao: Optional[Ocasiao] = None,
    clima_ideal: Optional[ClimaIdeal] = None,
    db: Session = Depends(obter_sessao),
    usuario: Usuario = Depends(usuario_atual),
):
    consulta = select(Peca).where(
        Peca.usuario_id == usuario.id,
        Peca.retirada_em.is_(None),
    )
    if tipo:
        consulta = consulta.where(Peca.tipo == tipo.value)
    if cor:
        consulta = consulta.where(Peca.cor == cor.strip().lower())
    if modelo:
        consulta = consulta.where(Peca.modelo == modelo.strip().lower())
    if estado:
        consulta = consulta.where(Peca.estado == estado.value)
    if ocasiao:
        consulta = consulta.where(Peca.ocasiao == ocasiao.value)
    if clima_ideal:
        consulta = consulta.where(Peca.clima_ideal == clima_ideal.value)

    return db.scalars(consulta.order_by(Peca.nome)).all()


@router.get("/agrupadas", response_model=dict[str, list[PecaResposta]])
def agrupar_pecas(
    por: str = Query(default="cor", pattern="^(cor|modelo|tipo)$"),
    db: Session = Depends(obter_sessao),
    usuario: Usuario = Depends(usuario_atual),
):
    pecas = db.scalars(
        select(Peca)
        .where(Peca.usuario_id == usuario.id, Peca.retirada_em.is_(None))
        .order_by(Peca.nome)
    ).all()

    grupos: dict[str, list[Peca]] = {}
    for peca in pecas:
        chave = getattr(peca, por) or "Não informado"
        grupos.setdefault(chave, []).append(peca)
    return grupos


@router.get("/retiradas", response_model=list[PecaResposta])
def consultar_pecas_retiradas(
    motivo: Optional[MotivoRetirada] = None,
    db: Session = Depends(obter_sessao),
    usuario: Usuario = Depends(usuario_atual),
):
    consulta = select(Peca).where(
        Peca.usuario_id == usuario.id,
        Peca.retirada_em.is_not(None),
    )
    if motivo:
        consulta = consulta.where(Peca.motivo_retirada == motivo.value)
    return db.scalars(consulta.order_by(Peca.retirada_em.desc())).all()


@router.get("/{peca_id}", response_model=PecaResposta)
def consultar_peca(
    peca_id: int,
    db: Session = Depends(obter_sessao),
    usuario: Usuario = Depends(usuario_atual),
):
    return buscar_peca(db, usuario, peca_id)


@router.post("", response_model=PecaResposta, status_code=201)
def adicionar_peca(
    dados: DadosPeca,
    db: Session = Depends(obter_sessao),
    usuario: Usuario = Depends(usuario_atual),
):
    peca = Peca(**dados.model_dump(mode="json"), usuario_id=usuario.id)
    db.add(peca)
    db.commit()
    db.refresh(peca)
    return peca


@router.put("/{peca_id}", response_model=PecaResposta)
def substituir_peca(
    peca_id: int,
    dados: DadosPeca,
    db: Session = Depends(obter_sessao),
    usuario: Usuario = Depends(usuario_atual),
):
    peca = buscar_peca(db, usuario, peca_id, ativa=True)
    for campo, valor in dados.model_dump(mode="json").items():
        setattr(peca, campo, valor)
    db.commit()
    db.refresh(peca)
    return peca


@router.patch("/{peca_id}", response_model=PecaResposta)
def atualizar_peca(
    peca_id: int,
    dados: AtualizacaoPeca,
    db: Session = Depends(obter_sessao),
    usuario: Usuario = Depends(usuario_atual),
):
    valores = dados.model_dump(mode="json", exclude_unset=True)
    if not valores:
        raise HTTPException(status_code=400, detail="Informe ao menos um campo")

    campos_obrigatorios = {"nome", "tipo", "cor", "estado", "ocasiao", "clima_ideal", "pode_chuva"}
    nulos = sorted(campo for campo in campos_obrigatorios if campo in valores and valores[campo] is None)
    if nulos:
        raise HTTPException(
            status_code=400,
            detail="Estes campos não podem ficar vazios: " + ", ".join(nulos),
        )

    peca = buscar_peca(db, usuario, peca_id, ativa=True)
    for campo, valor in valores.items():
        setattr(peca, campo, valor)
    db.commit()
    db.refresh(peca)
    return peca


@router.delete("/{peca_id}", status_code=204)
def retirar_peca(
    peca_id: int,
    motivo: MotivoRetirada,
    observacao: Optional[str] = None,
    db: Session = Depends(obter_sessao),
    usuario: Usuario = Depends(usuario_atual),
):
    if motivo == MotivoRetirada.outro and not (observacao and observacao.strip()):
        raise HTTPException(
            status_code=400,
            detail="Informe uma observação para o motivo 'Outro'",
        )

    peca = buscar_peca(db, usuario, peca_id, ativa=True)
    peca.motivo_retirada = motivo.value
    peca.observacao_retirada = observacao
    peca.retirada_em = datetime.now(timezone.utc)
    peca.closets.clear()
    db.commit()
    return Response(status_code=204)
