from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import obter_sessao
from app.models import Usuario
from app.security import ler_usuario_id


autenticacao = HTTPBearer(auto_error=False)


def usuario_atual(
    credenciais: HTTPAuthorizationCredentials | None = Depends(autenticacao),
    db: Session = Depends(obter_sessao),
) -> Usuario:
    if credenciais is None:
        raise HTTPException(
            status_code=401,
            detail="Autenticação necessária",
            headers={"WWW-Authenticate": "Bearer"},
        )

    usuario_id = ler_usuario_id(credenciais.credentials)
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario
