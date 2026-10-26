import base64
import binascii
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException


ALGORITHM = "HS256"
ITERATIONS = 310_000
TOKEN_MINUTES = 60


def obter_chave_secreta() -> str:
    chave = os.getenv("SECRET_KEY")
    if not chave or len(chave) < 32 or chave.startswith("SUBSTITUA-"):
        raise RuntimeError("Configure SECRET_KEY com ao menos 32 caracteres")
    return chave


def gerar_hash_senha(senha: str) -> str:
    sal = secrets.token_bytes(16)
    derivada = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), sal, ITERATIONS)
    sal_codificado = base64.urlsafe_b64encode(sal).decode("ascii")
    hash_codificado = base64.urlsafe_b64encode(derivada).decode("ascii")
    return f"pbkdf2_sha256${sal_codificado}${hash_codificado}"


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        algoritmo, sal_codificado, hash_codificado = senha_hash.split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        sal = base64.urlsafe_b64decode(sal_codificado.encode("ascii"))
        esperado = base64.urlsafe_b64decode(hash_codificado.encode("ascii"))
    except (ValueError, TypeError, binascii.Error):
        return False

    calculado = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), sal, ITERATIONS)
    return hmac.compare_digest(calculado, esperado)


def criar_token(usuario_id: int) -> str:
    agora = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(usuario_id),
            "iat": agora,
            "exp": agora + timedelta(minutes=TOKEN_MINUTES),
        },
        obter_chave_secreta(),
        algorithm=ALGORITHM,
    )


def ler_usuario_id(token: str) -> int:
    try:
        dados = jwt.decode(token, obter_chave_secreta(), algorithms=[ALGORITHM])
        return int(dados["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
