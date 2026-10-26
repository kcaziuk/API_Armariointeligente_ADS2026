from enum import Enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TipoPeca(str, Enum):
    calca = "Calça"
    blusa = "Blusa"
    casaco = "Casaco"
    calcado = "Calçado"
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


class Ocasiao(str, Enum):
    casual = "Casual"
    trabalho = "Trabalho"
    festa = "Festa"
    esporte = "Esporte"


class ClimaIdeal(str, Enum):
    frio = "Frio"
    ameno = "Ameno"
    quente = "Quente"
    qualquer = "Qualquer"


class DadosPeca(BaseModel):
    nome: str = Field(min_length=1)
    tipo: TipoPeca
    cor: str = Field(min_length=1)
    modelo: Optional[str] = None
    observacoes: Optional[str] = None
    estado: EstadoPeca = EstadoPeca.limpa
    ocasiao: Ocasiao = Ocasiao.casual
    clima_ideal: ClimaIdeal = ClimaIdeal.qualquer
    pode_chuva: bool = False

    @field_validator("nome", mode="before")
    @classmethod
    def normalizar_nome(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return None
        return valor.strip() if isinstance(valor, str) else valor

    @field_validator("cor", "modelo", mode="before")
    @classmethod
    def normalizar_cor_modelo(cls, valor: Optional[str]) -> Optional[str]:
        return valor.strip().lower() if isinstance(valor, str) else valor


class AtualizacaoPeca(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1)
    tipo: Optional[TipoPeca] = None
    cor: Optional[str] = Field(default=None, min_length=1)
    modelo: Optional[str] = None
    observacoes: Optional[str] = None
    estado: Optional[EstadoPeca] = None
    ocasiao: Optional[Ocasiao] = None
    clima_ideal: Optional[ClimaIdeal] = None
    pode_chuva: Optional[bool] = None

    @field_validator("nome", mode="before")
    @classmethod
    def normalizar_nome(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return None
        return valor.strip() if isinstance(valor, str) else valor

    @field_validator("cor", "modelo", mode="before")
    @classmethod
    def normalizar_cor_modelo(cls, valor: Optional[str]) -> Optional[str]:
        return valor.strip().lower() if isinstance(valor, str) else valor


class PecaResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    nome: str
    tipo: str
    cor: str
    modelo: Optional[str]
    observacoes: Optional[str]
    estado: str
    ocasiao: str
    clima_ideal: str
    pode_chuva: bool
    motivo_retirada: Optional[str]
    observacao_retirada: Optional[str]
    retirada_em: Optional[datetime]
    criada_em: datetime


class DadosCloset(BaseModel):
    nome: str = Field(min_length=1)
    descricao: Optional[str] = None
    pecas_ids: list[int] = Field(default_factory=list)

    @field_validator("nome", mode="before")
    @classmethod
    def normalizar_nome(cls, valor: str) -> str:
        return valor.strip() if isinstance(valor, str) else valor


class AtualizacaoCloset(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1)
    descricao: Optional[str] = None

    @field_validator("nome", mode="before")
    @classmethod
    def normalizar_nome(cls, valor: Optional[str]) -> Optional[str]:
        return valor.strip() if isinstance(valor, str) else valor


class ClosetResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    nome: str
    descricao: Optional[str]
    pecas_ids: list[int]


class DadosUsuario(BaseModel):
    nome: str = Field(min_length=1)
    email: str = Field(
        min_length=6,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    senha: str = Field(min_length=8, max_length=128)
    cidade: Optional[str] = None

    @field_validator("nome", mode="before")
    @classmethod
    def normalizar_nome(cls, valor: str) -> str:
        return valor.strip() if isinstance(valor, str) else valor

    @field_validator("email", mode="before")
    @classmethod
    def normalizar_email(cls, valor: str) -> str:
        return valor.strip().lower() if isinstance(valor, str) else valor


class DadosLogin(BaseModel):
    email: str
    senha: str = Field(max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalizar_email(cls, valor: str) -> str:
        return valor.strip().lower() if isinstance(valor, str) else valor


class AtualizacaoUsuario(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1)
    cidade: Optional[str] = None

    @field_validator("nome", mode="before")
    @classmethod
    def normalizar_nome(cls, valor: Optional[str]) -> Optional[str]:
        return valor.strip() if isinstance(valor, str) else valor


class UsuarioResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: str
    cidade: Optional[str]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ClimaResposta(BaseModel):
    cidade: str
    temperatura: float
    sensacao: float
    descricao: str
    chuva: bool
    clima: ClimaIdeal


class LookResposta(BaseModel):
    clima: ClimaResposta
    look: dict[str, Optional[PecaResposta]]
    avisos: list[str]
