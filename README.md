# API do Armário Inteligente

API em FastAPI e SQLite para organizar peças de roupa e closets. A persistência
usa SQLAlchemy e os dados existentes em `armario.db` são associados a um usuário
provisório durante a migração, sem apagar os registros.

## Executar

Requer Python 3.12 ou superior.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure uma chave secreta com ao menos 32 caracteres no `.env` e inicie a
aplicação:

```powershell
python main.py
```

Abra http://127.0.0.1:8000 para acessar o front-end. A API e os arquivos da
interface são servidos pelo mesmo processo; não é necessário iniciar um servidor
separado para o front-end. A documentação interativa fica em
http://127.0.0.1:8000/docs.

Gere uma chave secreta com `python -c "import secrets; print(secrets.token_hex(32))"`
e substitua o valor de `SECRET_KEY` no `.env` antes de iniciar a API. O banco usa
`armario.db` na raiz do projeto; `DATABASE_URL` permite apontar para outro banco.

## Organização

```text
app/
  database.py       # engine, sessões e migração do SQLite legado
  dependencies.py   # dependência do usuário provisório desta etapa
  main.py           # inicialização da API, front-end e registro das rotas
  api.py            # compatibilidade com o comando uvicorn app.api:app
  models.py         # modelos SQLAlchemy e relacionamentos
  schemas.py        # validação dos dados de entrada e saída
  routers/
    closets.py
    pecas.py
main.py             # inicia a aplicação com python main.py
```

## Endpoints implementados

| Método | Rota | Função |
|---|---|---|
| GET | `/` | Serve a tela de login e cadastro do front-end |
| POST | `/auth/registrar` | Cria uma conta (201); senha armazenada com hash |
| POST | `/auth/login` | Valida e-mail e senha e retorna JWT |
| GET / PATCH | `/auth/eu` | Consulta ou atualiza o perfil autenticado |
| GET | `/pecas` | Lista peças ativas; aceita filtros por tipo, cor, modelo, estado, ocasião e clima ideal |
| GET | `/pecas/agrupadas?por=cor` | Agrupa peças por cor, modelo ou tipo |
| GET | `/pecas/retiradas` | Lista peças retiradas; aceita filtro por motivo |
| GET | `/pecas/{id}` | Consulta uma peça |
| POST | `/pecas` | Cadastra uma peça (201) |
| PUT | `/pecas/{id}` | Substitui os dados de uma peça ativa |
| PATCH | `/pecas/{id}` | Atualiza somente os campos enviados |
| DELETE | `/pecas/{id}?motivo=Venda` | Retira a peça sem apagar seu histórico (204) |
| GET | `/closets` e `/closets/{id}` | Lista closets ou consulta um closet |
| POST | `/closets` | Cria closet, opcionalmente com peças |
| PUT / PATCH | `/closets/{id}` | Substitui ou atualiza um closet |
| DELETE | `/closets/{id}` | Remove o closet sem remover as peças (204) |

Valores de `tipo`: `Calça`, `Blusa`, `Casaco`, `Calçado`, `Acessório` e
`Outro`. `estado`: `Limpa`, `Suja` ou `Manutenção`. `ocasiao`: `Casual`,
`Trabalho`, `Festa` ou `Esporte`. `clima_ideal`: `Frio`, `Ameno`, `Quente` ou
`Qualquer`.

Todas as rotas, exceto `/`, `/auth/registrar` e `/auth/login`, exigem
`Authorization: Bearer <token>`. Os dados de peças e closets são filtrados pelo
usuário autenticado. A primeira conta criada assume os registros legados que
foram migrados do banco antigo. As origens CORS permitidas são configuradas em
`CORS_ORIGINS`; o exemplo libera apenas os endereços locais do front-end.

O CRUD, a migração para ORM, validação HTTP, autenticação JWT, isolamento por
usuário e CORS estão implementados. A integração com clima, a sugestão de look
e as evidências e documentação finais ainda estão pendentes.

## Testes

```powershell
pytest -q
```
