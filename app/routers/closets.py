from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import obter_sessao
from app.dependencies import usuario_atual
from app.models import Closet, Peca, Usuario
from app.routers.pecas import buscar_peca
from app.schemas import AtualizacaoCloset, ClosetResposta, DadosCloset


router = APIRouter(prefix="/closets", tags=["Closets"])


def buscar_closet(db: Session, usuario: Usuario, closet_id: int) -> Closet:
    closet = db.scalar(
        select(Closet)
        .options(selectinload(Closet.pecas))
        .where(Closet.id == closet_id, Closet.usuario_id == usuario.id)
    )
    if closet is None:
        raise HTTPException(status_code=404, detail="Closet não encontrado")
    return closet


def buscar_pecas_ativas(
    db: Session,
    usuario: Usuario,
    pecas_ids: list[int],
) -> list[Peca]:
    return [
        buscar_peca(db, usuario, peca_id, ativa=True)
        for peca_id in dict.fromkeys(pecas_ids)
    ]


@router.get("", response_model=list[ClosetResposta])
def consultar_closets(
    db: Session = Depends(obter_sessao),
    usuario: Usuario = Depends(usuario_atual),
):
    return db.scalars(
        select(Closet)
        .options(selectinload(Closet.pecas))
        .where(Closet.usuario_id == usuario.id)
        .order_by(Closet.nome)
    ).all()


@router.get("/{closet_id}", response_model=ClosetResposta)
def consultar_closet(
    closet_id: int,
    db: Session = Depends(obter_sessao),
    usuario: Usuario = Depends(usuario_atual),
):
    return buscar_closet(db, usuario, closet_id)


@router.post("", response_model=ClosetResposta, status_code=201)
def criar_closet(
    dados: DadosCloset,
    db: Session = Depends(obter_sessao),
    usuario: Usuario = Depends(usuario_atual),
):
    closet = Closet(
        nome=dados.nome,
        descricao=dados.descricao,
        usuario_id=usuario.id,
        pecas=buscar_pecas_ativas(db, usuario, dados.pecas_ids),
    )
    db.add(closet)
    db.commit()
    db.refresh(closet)
    return buscar_closet(db, usuario, closet.id)


@router.put("/{closet_id}", response_model=ClosetResposta)
def substituir_closet(
    closet_id: int,
    dados: DadosCloset,
    db: Session = Depends(obter_sessao),
    usuario: Usuario = Depends(usuario_atual),
):
    closet = buscar_closet(db, usuario, closet_id)
    closet.nome = dados.nome
    closet.descricao = dados.descricao
    closet.pecas = buscar_pecas_ativas(db, usuario, dados.pecas_ids)
    db.commit()
    return buscar_closet(db, usuario, closet.id)


@router.patch("/{closet_id}", response_model=ClosetResposta)
def atualizar_closet(
    closet_id: int,
    dados: AtualizacaoCloset,
    db: Session = Depends(obter_sessao),
    usuario: Usuario = Depends(usuario_atual),
):
    valores = dados.model_dump(exclude_unset=True)
    if not valores:
        raise HTTPException(status_code=400, detail="Informe ao menos um campo")
    if "nome" in valores and not valores["nome"]:
        raise HTTPException(status_code=400, detail="O nome não pode ficar vazio")

    closet = buscar_closet(db, usuario, closet_id)
    for campo, valor in valores.items():
        setattr(closet, campo, valor)
    db.commit()
    return buscar_closet(db, usuario, closet.id)


@router.delete("/{closet_id}", status_code=204)
def remover_closet(
    closet_id: int,
    db: Session = Depends(obter_sessao),
    usuario: Usuario = Depends(usuario_atual),
):
    closet = buscar_closet(db, usuario, closet_id)
    db.delete(closet)
    db.commit()
    return Response(status_code=204)
