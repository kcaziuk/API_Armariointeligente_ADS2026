from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.database import iniciar_banco
from app.routers import auth, closets, pecas
from app.security import obter_chave_secreta


FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")


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


@app.get("/")
def inicio() -> FileResponse:
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


app.include_router(pecas.router)
app.include_router(closets.router)
app.include_router(auth.router)
app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend")
