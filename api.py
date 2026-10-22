import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field


BANCO = os.path.join(os.path.dirname(__file__), "armario.db")
app = FastAPI(title="API do Armário Inteligente")


class TipoPeca(str, Enum):
    calca = "Calça"
    blusa = "Blusa"
    acessorio = "Acessório"
    outro = "Outro"


class EstadoPeca(str, Enum):
    limpa = "Limpa"
    suja = "Suja"
    manutencao = "Manutenção"


class MotivoRetirada(str, Enum):
    venda = "Venda"
    doacao = "Doação"
    perda = "Perda"
    outro = "Outro"


class DadosPeca(BaseModel):
    nome: str = Field(..., min_length=1)
    tipo: TipoPeca
    cor: str = Field(..., min_length=1)
    modelo: Optional[str] = None
    observacoes: Optional[str] = None
    estado: EstadoPeca = EstadoPeca.limpa


class AtualizacaoPeca(BaseModel):
    nome: Optional[str] = None
    tipo: Optional[TipoPeca] = None
    cor: Optional[str] = None
    modelo: Optional[str] = None
    observacoes: Optional[str] = None
    estado: Optional[EstadoPeca] = None


class DadosCloset(BaseModel):
    nome: str = Field(..., min_length=1)
    descricao: Optional[str] = None
    pecas_ids: list = Field(default_factory=list)


class AtualizacaoCloset(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None


@contextmanager
def conectar():
    banco = sqlite3.connect(BANCO)
    banco.row_factory = sqlite3.Row
    banco.execute("PRAGMA foreign_keys = ON")
    try:
        yield banco
        banco.commit()
    except Exception:
        banco.rollback()
        raise
    finally:
        banco.close()

def criar_tabelas():
    with conectar() as banco:
        banco.executescript(
            """
            CREATE TABLE IF NOT EXISTS pecas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                tipo TEXT NOT NULL,
                cor TEXT NOT NULL,
                modelo TEXT,
                observacoes TEXT,
                estado TEXT NOT NULL,
                motivo_retirada TEXT,
                observacao_retirada TEXT,
                retirada_em TEXT,
                criada_em TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS closets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                descricao TEXT
            );

            CREATE TABLE IF NOT EXISTS closet_pecas (
                closet_id INTEGER NOT NULL,
                peca_id INTEGER NOT NULL,
                PRIMARY KEY (closet_id, peca_id),
                FOREIGN KEY (closet_id) REFERENCES closets(id) ON DELETE CASCADE,
                FOREIGN KEY (peca_id) REFERENCES pecas(id) ON DELETE CASCADE
            );
            """
        )

def buscar_peca(banco, peca_id, ativa=False):
    consulta = "SELECT * FROM pecas WHERE id = ?"
    if ativa:
        consulta += " AND retirada_em IS NULL"

    peca = banco.execute(consulta, (peca_id,)).fetchone()
    if peca is None:
        raise HTTPException(status_code=404, detail="Peça não encontrada")
    return dict(peca)

def buscar_closet(banco, closet_id):
    closet = banco.execute(
        "SELECT * FROM closets WHERE id = ?", (closet_id,)
    ).fetchone()
    if closet is None:
        raise HTTPException(status_code=404, detail="Closet não encontrado")

    resultado = dict(closet)
    pecas = banco.execute(
        "SELECT peca_id FROM closet_pecas WHERE closet_id = ?",
        (closet_id,),
    ).fetchall()
    resultado["pecas_ids"] = [peca["peca_id"] for peca in pecas]
    return resultado

def preparar_dados_peca(dados):
    dados = dict(dados)
    for campo in ("tipo", "estado"):
        if isinstance(dados.get(campo), Enum):
            dados[campo] = dados[campo].value

    for campo in ("nome", "cor", "modelo"):
        if isinstance(dados.get(campo), str):
            dados[campo] = dados[campo].strip()

    if dados.get("cor"):
        dados["cor"] = dados["cor"].lower()
    if dados.get("modelo"):
        dados["modelo"] = dados["modelo"].lower()

    return dados

@app.on_event("startup")
def iniciar_api():
    criar_tabelas()

@app.get("/")
def inicio(request: Request):
    return {
        "mensagem": "API do Armário Inteligente",
        "documentacao": str(request.base_url) + "docs"
    }

@app.get("/pecas")
def consultar_pecas(
    tipo: Optional[TipoPeca] = None,
    cor: Optional[str] = None,
    modelo: Optional[str] = None,
    estado: Optional[EstadoPeca] = None,
):
    filtros = ["retirada_em IS NULL"]
    valores = []

    if tipo:
        filtros.append("tipo = ?")
        valores.append(tipo.value)
    if cor:
        filtros.append("cor = ?")
        valores.append(cor.strip().lower())
    if modelo:
        filtros.append("modelo = ?")
        valores.append(modelo.strip().lower())
    if estado:
        filtros.append("estado = ?")
        valores.append(estado.value)

    consulta = "SELECT * FROM pecas WHERE " + " AND ".join(filtros)
    consulta += " ORDER BY nome"

    with conectar() as banco:
        pecas = banco.execute(consulta, valores).fetchall()
        return [dict(peca) for peca in pecas]

@app.get("/pecas/agrupadas")
def agrupar_pecas(
    por: str = Query("cor", regex="^(cor|modelo|tipo)$")
):
    with conectar() as banco:
        pecas = banco.execute(
            "SELECT * FROM pecas WHERE retirada_em IS NULL ORDER BY nome"
        ).fetchall()

    grupos = {}
    for peca in pecas:
        peca = dict(peca)
        chave = peca[por] or "Não informado"
        grupos.setdefault(chave, []).append(peca)

    return grupos

@app.get("/pecas/retiradas")
def consultar_pecas_retiradas(
    motivo: Optional[MotivoRetirada] = None,
):
    consulta = "SELECT * FROM pecas WHERE retirada_em IS NOT NULL"
    valores = []

    if motivo:
        consulta += " AND motivo_retirada = ?"
        valores.append(motivo.value)

    consulta += " ORDER BY retirada_em DESC"

    with conectar() as banco:
        pecas = banco.execute(consulta, valores).fetchall()
        return [dict(peca) for peca in pecas]

@app.get("/pecas/{peca_id}")
def consultar_peca(peca_id: int):
    with conectar() as banco:
        return buscar_peca(banco, peca_id)
    
@app.post("/pecas", status_code=201)
def adicionar_peca(dados: DadosPeca):
    valores = preparar_dados_peca(dados.dict())

    with conectar() as banco:
        cursor = banco.execute(
            """
            INSERT INTO pecas
                (nome, tipo, cor, modelo, observacoes, estado, criada_em)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                valores["nome"],
                valores["tipo"],
                valores["cor"],
                valores["modelo"],
                valores["observacoes"],
                valores["estado"],
                datetime.utcnow().isoformat(),
            ),
        )
        return buscar_peca(banco, cursor.lastrowid)

@app.put("/pecas/{peca_id}")
def substituir_peca(peca_id: int, dados: DadosPeca):
    valores = preparar_dados_peca(dados.dict())

    with conectar() as banco:
        buscar_peca(banco, peca_id, ativa=True)
        banco.execute(
            """
            UPDATE pecas
            SET nome = ?, tipo = ?, cor = ?, modelo = ?,
                observacoes = ?, estado = ?
            WHERE id = ?
            """,
            (
                valores["nome"],
                valores["tipo"],
                valores["cor"],
                valores["modelo"],
                valores["observacoes"],
                valores["estado"],
                peca_id,
            ),
        )
        return buscar_peca(banco, peca_id)

@app.patch("/pecas/{peca_id}")
def atualizar_peca(peca_id: int, dados: AtualizacaoPeca):
    valores = preparar_dados_peca(dados.dict(exclude_unset=True))
    if not valores:
        raise HTTPException(status_code=400, detail="Informe ao menos um campo")

    campos = ", ".join("{} = ?".format(campo) for campo in valores)

    with conectar() as banco:
        buscar_peca(banco, peca_id, ativa=True)
        banco.execute(
            "UPDATE pecas SET {} WHERE id = ?".format(campos),
            list(valores.values()) + [peca_id],
        )
        return buscar_peca(banco, peca_id)

@app.delete("/pecas/{peca_id}")
def retirar_peca(
    peca_id: int,
    motivo: MotivoRetirada,
    observacao: Optional[str] = None,
):
    if motivo == MotivoRetirada.outro and not (observacao and observacao.strip()):
        raise HTTPException(
            status_code=400,
            detail="Informe uma observação para o motivo 'outro'",
        )

    with conectar() as banco:
        buscar_peca(banco, peca_id, ativa=True)
        banco.execute(
            """
            UPDATE pecas
            SET motivo_retirada = ?, observacao_retirada = ?, retirada_em = ?
            WHERE id = ?
            """,
            (motivo.value, observacao, datetime.utcnow().isoformat(), peca_id),
        )
        return buscar_peca(banco, peca_id)

@app.get("/closets")
def consultar_closets():
    with conectar() as banco:
        closets = banco.execute("SELECT id FROM closets ORDER BY nome").fetchall()
        return [buscar_closet(banco, closet["id"]) for closet in closets]

@app.get("/closets/{closet_id}")
def consultar_closet(closet_id: int):
    with conectar() as banco:
        return buscar_closet(banco, closet_id)

@app.post("/closets", status_code=201)
def criar_closet(dados: DadosCloset):
    with conectar() as banco:
        cursor = banco.execute(
            "INSERT INTO closets (nome, descricao) VALUES (?, ?)",
            (dados.nome.strip(), dados.descricao),
        )
        closet_id = cursor.lastrowid

        for peca_id in dados.pecas_ids:
            buscar_peca(banco, peca_id, ativa=True)
            banco.execute(
                "INSERT INTO closet_pecas (closet_id, peca_id) VALUES (?, ?)",
                (closet_id, peca_id),
            )

        return buscar_closet(banco, closet_id)

@app.put("/closets/{closet_id}")
def substituir_closet(closet_id: int, dados: DadosCloset):
    with conectar() as banco:
        buscar_closet(banco, closet_id)
        banco.execute(
            "UPDATE closets SET nome = ?, descricao = ? WHERE id = ?",
            (dados.nome.strip(), dados.descricao, closet_id),
        )
        banco.execute(
            "DELETE FROM closet_pecas WHERE closet_id = ?", (closet_id,)
        )

        for peca_id in dados.pecas_ids:
            buscar_peca(banco, peca_id, ativa=True)
            banco.execute(
                "INSERT INTO closet_pecas (closet_id, peca_id) VALUES (?, ?)",
                (closet_id, peca_id),
            )

        return buscar_closet(banco, closet_id)

@app.patch("/closets/{closet_id}")
def atualizar_closet(closet_id: int, dados: AtualizacaoCloset):
    valores = dados.dict(exclude_unset=True)
    if not valores:
        raise HTTPException(status_code=400, detail="Informe ao menos um campo")

    campos = ", ".join("{} = ?".format(campo) for campo in valores)

    with conectar() as banco:
        buscar_closet(banco, closet_id)
        banco.execute(
            "UPDATE closets SET {} WHERE id = ?".format(campos),
            list(valores.values()) + [closet_id],
        )
        return buscar_closet(banco, closet_id)

@app.delete("/closets/{closet_id}")
def remover_closet(closet_id: int):
    with conectar() as banco:
        buscar_closet(banco, closet_id)
        banco.execute("DELETE FROM closets WHERE id = ?", (closet_id,))
        return {"mensagem": "Closet removido"}