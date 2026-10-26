import sqlite3

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import criar_engine, iniciar_banco
from app.models import Closet, Peca, Usuario


def test_migra_schema_legado_sem_perder_registros(tmp_path):
    caminho = tmp_path / "legado.db"
    conexao = sqlite3.connect(caminho)
    conexao.executescript(
        """
        CREATE TABLE pecas (
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
        CREATE TABLE closets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT
        );
        CREATE TABLE closet_pecas (
            closet_id INTEGER NOT NULL,
            peca_id INTEGER NOT NULL,
            PRIMARY KEY (closet_id, peca_id),
            FOREIGN KEY (closet_id) REFERENCES closets(id) ON DELETE CASCADE,
            FOREIGN KEY (peca_id) REFERENCES pecas(id) ON DELETE CASCADE
        );
        INSERT INTO pecas (id, nome, tipo, cor, estado, criada_em)
        VALUES (7, 'Casaco', 'Blusa', 'cinza', 'Limpa', '2026-01-01T12:00:00');
        INSERT INTO closets (id, nome, descricao) VALUES (3, 'Inverno', NULL);
        INSERT INTO closet_pecas (closet_id, peca_id) VALUES (3, 7);
        """
    )
    conexao.commit()
    conexao.close()

    db_engine = criar_engine(f"sqlite:///{caminho.as_posix()}")
    iniciar_banco(db_engine)
    with Session(db_engine) as db:
        usuario = db.get(Usuario, 1)
        peca = db.scalar(select(Peca).where(Peca.id == 7))
        closet = db.scalar(
            select(Closet).options(selectinload(Closet.pecas)).where(Closet.id == 3)
        )
        assert usuario is not None
        assert peca is not None
        assert peca.usuario_id == usuario.id
        assert peca.ocasiao == "Casual"
        assert peca.clima_ideal == "Qualquer"
        assert peca.pode_chuva is False
        assert closet is not None
        assert closet.usuario_id == usuario.id
        assert closet.pecas_ids == [7]
    db_engine.dispose()
