from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


closet_pecas = Table(
    "closet_pecas",
    Base.metadata,
    Column("closet_id", ForeignKey("closets.id", ondelete="CASCADE"), primary_key=True),
    Column("peca_id", ForeignKey("pecas.id", ondelete="CASCADE"), primary_key=True),
)


def agora_utc() -> datetime:
    return datetime.now(timezone.utc)


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String, nullable=False)
    cidade: Mapped[str | None] = mapped_column(String)
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora_utc)

    pecas: Mapped[list["Peca"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")
    closets: Mapped[list["Closet"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")


class Peca(Base):
    __tablename__ = "pecas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String, nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    cor: Mapped[str] = mapped_column(String, nullable=False)
    modelo: Mapped[str | None] = mapped_column(String)
    observacoes: Mapped[str | None] = mapped_column(String)
    estado: Mapped[str] = mapped_column(String, nullable=False, default="Limpa")
    ocasiao: Mapped[str] = mapped_column(String, nullable=False, default="Casual")
    clima_ideal: Mapped[str] = mapped_column(String, nullable=False, default="Qualquer")
    pode_chuva: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    motivo_retirada: Mapped[str | None] = mapped_column(String)
    observacao_retirada: Mapped[str | None] = mapped_column(String)
    retirada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora_utc)

    usuario: Mapped[Usuario] = relationship(back_populates="pecas")
    closets: Mapped[list["Closet"]] = relationship(
        secondary=closet_pecas, back_populates="pecas"
    )


class Closet(Base):
    __tablename__ = "closets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String, nullable=False)
    descricao: Mapped[str | None] = mapped_column(String)

    usuario: Mapped[Usuario] = relationship(back_populates="closets")
    pecas: Mapped[list[Peca]] = relationship(
        secondary=closet_pecas, back_populates="closets"
    )

    @property
    def pecas_ids(self) -> list[int]:
        return [peca.id for peca in self.pecas]
