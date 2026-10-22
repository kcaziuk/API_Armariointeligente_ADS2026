# Armário Inteligente API

API em FastAPI + SQLite para gerenciar peças de roupa e closets. Compatível com Python 3.6+.

O código foi mantido em uma estrutura pequena: `app/main.py` inicia o serviço,
`app/api.py` reúne os endpoints e `app/models.py` e `app/schemas.py` definem
os dados da aplicação. Os nomes das classes Python estão em português; os
nomes dos campos enviados e recebidos pela API permanecem iguais.

## Executar

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Documentação interativa: http://127.0.0.1:8000/docs

O arquivo `.env` já vem configurado. Em produção, gere outra chave:
`python -c "import secrets;print(secrets.token_hex(32))"`

## Onde os dados ficam

```
data/
  app.db                 # cadastro de usuários
  users/
    1/closet.db          # peças e closets do usuário 1
    2/closet.db          # peças e closets do usuário 2
```

## Endpoints

Todos, exceto `/auth/register`, `/auth/login` e `/`, exigem `Authorization: Bearer <token>`.

| Método | Rota | Função |
|---|---|---|
| POST | /auth/register | Cadastra usuário (cria a pasta dele) |
| POST | /auth/login | Retorna o token (campo `username` = e-mail) |
| GET | /auth/me | Dados do usuário logado |
| POST | /garments | Adiciona peça |
| GET | /garments | Consulta com filtros: `type`, `color`, `model`, `status`, `q`, `include_removed`, `skip`, `limit` |
| GET | /garments/grouped?by=color\|model\|type | Separa as peças por cor, modelo ou tipo |
| GET | /garments/{id} | Detalhe da peça |
| PUT | /garments/{id} | Substitui todos os dados |
| PATCH | /garments/{id} | Altera só os campos enviados |
| PATCH | /garments/{id}/status | `limpa`, `suja` ou `manutencao` (+ `notes`) |
| DELETE | /garments/{id}?reason=venda\|doacao\|perda\|outro&notes= | Retira a peça (mantém histórico; `notes` obrigatório se `outro`) |
| GET | /garments/removed?reason= | Histórico de retiradas |
| POST | /garments/{id}/restore | Desfaz a retirada |
| POST | /closets | Cria closet (com `garment_ids` opcional) |
| GET | /closets, /closets/{id} | Lista / detalha |
| PUT / PATCH | /closets/{id} | Substitui / altera |
| DELETE | /closets/{id} | Apaga o closet (as peças ficam) |
| POST / DELETE | /closets/{id}/garments/{garment_id} | Adiciona / remove peça do closet |

Tipos de peça: `calca`, `blusa`, `acessorio`, `outro`. Cores e modelos são normalizados para minúsculas.

## Testes

```bash
pytest -q
```
