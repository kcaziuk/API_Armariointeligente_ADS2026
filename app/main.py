from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import iniciar_banco
from app.routers import auth, closets, pecas
from app.security import obter_chave_secreta


@asynccontextmanager
async def lifespan(_: FastAPI):
    obter_chave_secreta()
    iniciar_banco()
    yield


app = FastAPI(title="API do Armário Inteligente", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origem.strip()
        for origem in os.getenv(
            "CORS_ORIGINS",
            "http://127.0.0.1:5500,http://localhost:5500",
        ).split(",")
        if origem.strip()
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(RequestValidationError)
async def erro_de_validacao(_: Request, exc: RequestValidationError) -> JSONResponse:
    erros = [
        {
            "campo": ".".join(str(parte) for parte in erro["loc"] if parte not in ("body", "query", "path")),
            "mensagem": erro["msg"],
        }
        for erro in exc.errors()
    ]
    return JSONResponse(
        status_code=400,
        content={"detail": "Dados inválidos", "erros": erros},
    )


@app.get("/", tags=["Início"])
def inicio(request: Request):
    return {
        "mensagem": "API do Armário Inteligente",
        "documentacao": str(request.base_url) + "docs",
    }


app.include_router(pecas.router)
app.include_router(closets.router)
app.include_router(auth.router)
