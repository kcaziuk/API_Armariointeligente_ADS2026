from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import obter_sessao
from app.dependencies import usuario_atual
from app.models import Usuario
from app.schemas import (
    AtualizacaoUsuario,
    DadosLogin,
    DadosUsuario,
    Token,
    UsuarioResposta,
)
from app.security import criar_token, gerar_hash_senha, verificar_senha


router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/registrar", response_model=UsuarioResposta, status_code=201)
def registrar(dados: DadosUsuario, db: Session = Depends(obter_sessao)):
    usuario = db.scalar(select(Usuario).where(Usuario.email == dados.email))
    if usuario is not None:
        raise HTTPException(status_code=409, detail="Já existe uma conta com este e-mail")

    senha_hash = gerar_hash_senha(dados.senha)
    usuario_legado = db.get(Usuario, 1)
    if usuario_legado is not None and usuario_legado.email == "legado@armario.local":
        usuario_legado.nome = dados.nome
        usuario_legado.email = dados.email
        usuario_legado.senha_hash = senha_hash
        usuario_legado.cidade = dados.cidade
        usuario = usuario_legado
    else:
        usuario = Usuario(
            nome=dados.nome,
            email=dados.email,
            senha_hash=senha_hash,
            cidade=dados.cidade,
        )
        db.add(usuario)

    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/login", response_model=Token)
def login(dados: DadosLogin, db: Session = Depends(obter_sessao)):
    usuario = db.scalar(select(Usuario).where(Usuario.email == dados.email))
    if usuario is None or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=401,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=criar_token(usuario.id))


@router.get("/eu", response_model=UsuarioResposta)
def ver_meus_dados(usuario: Usuario = Depends(usuario_atual)):
    return usuario


@router.patch("/eu", response_model=UsuarioResposta)
def atualizar_meus_dados(
    dados: AtualizacaoUsuario,
    db: Session = Depends(obter_sessao),
    usuario: Usuario = Depends(usuario_atual),
):
    valores = dados.model_dump(exclude_unset=True)
    if not valores:
        raise HTTPException(status_code=400, detail="Informe ao menos um campo")
    if "nome" in valores and not valores["nome"]:
        raise HTTPException(status_code=400, detail="O nome não pode ficar vazio")

    for campo, valor in valores.items():
        setattr(usuario, campo, valor)
    db.commit()
    db.refresh(usuario)
    return usuario
