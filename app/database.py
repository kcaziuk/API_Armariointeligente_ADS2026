import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from dotenv import load_dotenv

from app.models import Base


load_dotenv()
DATABASE_FILE = Path(__file__).resolve().parents[1] / "armario.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_FILE.as_posix()}")


def criar_engine(url: str) -> Engine:
    opcoes = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {}
    engine = create_engine(url, **opcoes)

    if url.startswith("sqlite"):
        from sqlalchemy import event

        @event.listens_for(engine, "connect")
        def habilitar_chaves_estrangeiras(conexao, _):
            cursor = conexao.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = criar_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def migrar_schema_legado(db_engine: Engine) -> None:
    tabelas = set(inspect(db_engine).get_table_names())
    if not {"pecas", "closets"}.issubset(tabelas):
        return

    with db_engine.begin() as conexao:
        conexao.execute(
            text(
                """
                INSERT OR IGNORE INTO usuarios
                    (id, nome, email, senha_hash, cidade, criada_em)
                VALUES (1, 'Dados migrados', 'legado@armario.local',
                        'autenticacao-ainda-nao-configurada', NULL, CURRENT_TIMESTAMP)
                """
            )
        )

        migracoes = {
            "pecas": {
                "usuario_id": "INTEGER REFERENCES usuarios(id) ON DELETE CASCADE",
                "ocasiao": "VARCHAR NOT NULL DEFAULT 'Casual'",
                "clima_ideal": "VARCHAR NOT NULL DEFAULT 'Qualquer'",
                "pode_chuva": "BOOLEAN NOT NULL DEFAULT 0",
            },
            "closets": {
                "usuario_id": "INTEGER REFERENCES usuarios(id) ON DELETE CASCADE",
            },
        }

        for tabela, colunas in migracoes.items():
            existentes = {
                coluna["name"] for coluna in inspect(db_engine).get_columns(tabela)
            }
            for coluna, definicao in colunas.items():
                if coluna not in existentes:
                    conexao.execute(
                        text(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")
                    )

            if "usuario_id" in colunas:
                conexao.execute(
                    text(f"UPDATE {tabela} SET usuario_id = 1 WHERE usuario_id IS NULL")
                )


def iniciar_banco(db_engine: Engine | None = None) -> None:
    db_engine = db_engine or engine
    Base.metadata.create_all(bind=db_engine)
    migrar_schema_legado(db_engine)


def obter_sessao() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
