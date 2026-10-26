# Armário Inteligente — API "O que vestir hoje?"

API REST para organizar o guarda-roupa e sugerir o look do dia com base no clima. A pessoa cadastra suas peças (tipo, cor, ocasião, clima ideal), marca o que está sujo ou precisando de conserto (botão solto, zíper quebrado), organiza closets e, todos os dias, a API consulta a previsão do tempo da cidade dela no OpenWeatherMap e monta um look só com peças limpas e adequadas à temperatura e à chuva.

Trabalho da disciplina **Arquitetura e Desenvolvimento de APIs** (Uninter, 2026).

## Funcionalidades

- Cadastro e login com senha protegida por hash e token JWT.
- CRUD de peças: cadastrar, listar com filtros, consultar, substituir (PUT), alterar parcialmente (PATCH) e retirar (DELETE) com motivo.
- Agrupamento de peças por cor, modelo ou tipo.
- Retirada lógica: a peça sai do armário, mas fica no histórico com motivo (venda, doação, perda ou outro).
- Closets: coleções de peças (ex.: "Viagem", "Trabalho de inverno").
- Clima atual da cidade do usuário (OpenWeatherMap).
- Sugestão de look por clima, chuva e ocasião.
- Cada usuário só acessa os próprios dados.

## Tecnologias

| Tecnologia | Uso |
| --- | --- |
| Python 3.13 | Linguagem |
| FastAPI | Framework da API e documentação Swagger automática |
| Uvicorn | Servidor que executa a API |
| SQLite | Banco de dados (arquivo único) |
| SQLAlchemy 2 | ORM: mapeia as classes Python para as tabelas |
| Pydantic 2 | Validação dos dados de entrada e saída |
| PyJWT | Geração e validação dos tokens JWT |
| python-dotenv | Leitura das configurações do arquivo `.env` |
| httpx2 | Chamadas HTTP ao OpenWeatherMap e cliente dos testes |
| pytest | Testes automatizados |
| OpenWeatherMap | API externa de clima (plano gratuito) |

## Pré-requisitos

- Python 3.12 ou superior (desenvolvido com 3.13)
- Git
- Uma chave gratuita do [OpenWeatherMap](https://openweathermap.org/) (em **My API keys**; uma chave nova pode levar até 2 horas para ativar)

## Instalação

```powershell
git clone https://github.com/kcaziuk/API_Armariointeligente_ADS2026.git
cd API_Armariointeligente_ADS2026
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

No Linux ou macOS, ative o ambiente com `source .venv/bin/activate`.

Se o PowerShell recusar a ativação, rode uma vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## Configuração (.env)

Copie o arquivo de exemplo e preencha os valores reais. O `.env` não vai para o repositório.

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```

| Variável | O que é | Exemplo |
| --- | --- | --- |
| `DATABASE_URL` | Endereço do banco | `sqlite:///./armario.db` |
| `SECRET_KEY` | Chave que assina os tokens JWT. Obrigatória, com 32 caracteres ou mais (use o valor gerado pelo comando acima) | `a3f9…` |
| `CORS_ORIGINS` | Origens que o navegador pode usar para chamar a API, separadas por vírgula | `http://127.0.0.1:5500,http://localhost:5500` |
| `OPENWEATHER_API_KEY` | Sua chave do OpenWeatherMap | `1a2b3c…` |

A API se recusa a iniciar se a `SECRET_KEY` estiver vazia, curta ou com o texto de exemplo.

## Banco de dados

Não é preciso criar o banco manualmente. Na primeira execução, a API cria o arquivo `armario.db` e as tabelas `usuarios`, `pecas`, `closets` e `closet_pecas` a partir dos modelos do SQLAlchemy (`app/models.py`). Para recomeçar do zero, apague o `armario.db`.

Se existir um `armario.db` da versão antiga do projeto (sem usuários), as colunas novas são adicionadas automaticamente e os registros antigos passam para a primeira conta criada.

## Como executar

```powershell
python -m uvicorn app.main:app --reload
```

| Endereço | O que abre |
| --- | --- |
| http://127.0.0.1:8000/ | Mensagem de boas-vindas |
| http://127.0.0.1:8000/docs | Documentação interativa (Swagger) |
| http://127.0.0.1:8000/redoc | Documentação alternativa (ReDoc) |

## Como testar a autenticação

1. Abra o Swagger em `/docs`.
2. Em `POST /auth/registrar`, crie uma conta de teste (senha com 8 caracteres ou mais):
   ```json
   {"nome": "Teste", "email": "teste@exemplo.com", "senha": "senha12345", "cidade": "Recife"}
   ```
3. Em `POST /auth/login`, entre com o mesmo e-mail e senha e copie o `access_token`.
4. Clique em **Authorize**, cole o token e confirme. O token vale 60 minutos.
5. As rotas de peças, closets, clima e looks passam a funcionar. Sem o token, elas respondem **401**.

## Endpoints

Todas as rotas, exceto `/`, `/auth/registrar` e `/auth/login`, exigem o cabeçalho `Authorization: Bearer <token>`.

| Método | Rota | Finalidade | Entrada principal | Respostas |
| --- | --- | --- | --- | --- |
| GET | `/` | Boas-vindas e link do Swagger | — | 200 |
| POST | `/auth/registrar` | Criar conta | JSON: nome, email, senha, cidade | 201 / 400 / 409 |
| POST | `/auth/login` | Entrar e receber o token | JSON: email, senha | 200 / 400 / 401 |
| GET | `/auth/eu` | Dados de quem está logado | Token | 200 / 401 |
| PATCH | `/auth/eu` | Alterar nome ou cidade | JSON parcial | 200 / 400 / 401 |
| GET | `/pecas` | Listar peças ativas | Filtros: tipo, cor, modelo, estado, ocasiao, clima_ideal | 200 / 400 / 401 |
| GET | `/pecas/agrupadas` | Separar peças por cor, modelo ou tipo | `?por=cor` | 200 / 400 / 401 |
| GET | `/pecas/retiradas` | Histórico de peças retiradas | `?motivo=` opcional | 200 / 400 / 401 |
| GET | `/pecas/{id}` | Consultar uma peça | id | 200 / 401 / 404 |
| POST | `/pecas` | Cadastrar peça | JSON da peça | 201 / 400 / 401 |
| PUT | `/pecas/{id}` | Substituir todos os dados da peça | id + JSON completo | 200 / 400 / 401 / 404 |
| PATCH | `/pecas/{id}` | Alterar só alguns campos (ex.: marcar como suja) | id + JSON parcial | 200 / 400 / 401 / 404 |
| DELETE | `/pecas/{id}` | Retirar a peça com motivo | id + `?motivo=Doação&observacao=` | 204 / 400 / 401 / 404 |
| GET | `/closets` | Listar closets | Token | 200 / 401 |
| GET | `/closets/{id}` | Consultar um closet | id | 200 / 401 / 404 |
| POST | `/closets` | Criar closet | JSON: nome, descricao, pecas_ids | 201 / 400 / 401 / 404 |
| PUT | `/closets/{id}` | Substituir closet e suas peças | id + JSON completo | 200 / 400 / 401 / 404 |
| PATCH | `/closets/{id}` | Alterar nome ou descrição | id + JSON parcial | 200 / 400 / 401 / 404 |
| DELETE | `/closets/{id}` | Apagar o closet (as peças continuam) | id | 204 / 401 / 404 |
| GET | `/clima` | Clima atual da cidade do usuário | `?cidade=` opcional | 200 / 400 / 401 / 404 / 503 |
| GET | `/looks/sugestao` | Sugerir o look do dia | `?ocasiao=` e `?cidade=` opcionais | 200 / 400 / 401 / 404 / 503 |

**Valores aceitos (exatamente como escritos):**

| Campo | Valores |
| --- | --- |
| `tipo` | Calça, Blusa, Casaco, Calçado, Acessório, Outro |
| `estado` | Limpa, Suja, Manutenção (peça precisando de conserto) |
| `ocasiao` | Casual, Trabalho, Festa, Esporte |
| `clima_ideal` | Frio, Ameno, Quente, Qualquer |
| `motivo` (retirada) | Venda, Doação, Perda, Outro (Outro exige `observacao`) |

**Erros:** sempre no formato `{"detail": "mensagem"}`. Dados inválidos respondem **400** com a lista `erros`, em português:

```json
{
  "detail": "Dados inválidos",
  "erros": [
    {"campo": "nome", "mensagem": "Texto muito curto"},
    {"campo": "cor", "mensagem": "Campo obrigatório"}
  ]
}
```

## Exemplo de requisição

Cadastrar uma peça (troque `SEU_TOKEN` pelo `access_token` do login):

```bash
curl -X POST http://127.0.0.1:8000/pecas \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nome": "Moletom cinza", "tipo": "Casaco", "cor": "cinza", "ocasiao": "Casual", "clima_ideal": "Frio", "pode_chuva": true}'
```

Resposta **201**: a peça criada, com `id`, `estado` "Limpa" e a cor normalizada em minúsculas.

Sugestão de look:

```bash
curl "http://127.0.0.1:8000/looks/sugestao?ocasiao=Casual" -H "Authorization: Bearer SEU_TOKEN"
```

## Regra da sugestão de look

| Situação | O que a API faz |
| --- | --- |
| Sensação térmica abaixo de 15 °C | Clima **Frio** |
| De 15 °C a 24,9 °C | Clima **Ameno** |
| 25 °C ou mais | Clima **Quente** |
| Peças consideradas | Só as do usuário, não retiradas, com estado Limpa e `clima_ideal` igual ao do dia ou Qualquer |
| Ocasião informada | Filtra também pela ocasião |
| Chuva | Dá preferência às peças com `pode_chuva` |
| Montagem | 1 blusa, 1 calça, 1 calçado, 1 acessório e, se estiver frio ou chovendo, 1 casaco |
| Faltou alguma parte | A parte vem `null` e o motivo aparece em `avisos` |

## Segurança e CORS

- Senhas guardadas com hash PBKDF2-SHA256 e sal aleatório; a API nunca devolve senha nem hash.
- Login devolve um token JWT (HS256) válido por 60 minutos.
- CORS libera apenas as origens de `CORS_ORIGINS` (por padrão, o front-end local na porta 5500), os métodos GET, POST, PUT, PATCH e DELETE e os cabeçalhos `Authorization` e `Content-Type`. Não usamos `*` para que outros sites abertos no navegador não consigam chamar a API.

## Estrutura do projeto

```text
app/
  main.py              inicia a API, CORS, tratamento de erros e rotas
  database.py          conexão com o SQLite, sessões e criação das tabelas
  models.py            modelos do ORM: Usuario, Peca, Closet
  schemas.py           validação de entrada e saída (Pydantic)
  security.py          hash de senha e tokens JWT
  dependencies.py      dependência do usuário autenticado
  routers/
    auth.py            cadastro, login e perfil
    pecas.py           CRUD de peças
    closets.py         CRUD de closets
    clima.py           clima e sugestão de look
  services/
    openweather.py     integração com o OpenWeatherMap
tests/                 testes automatizados (pytest)
.env.example           modelo das variáveis de ambiente
requirements.txt       dependências
```

## Testes automatizados

```powershell
python -m pytest -q
```

São 16 testes: cadastro e login, duplicidade de e-mail, isolamento entre usuários, CRUD de peças e closets, validação, CORS, migração do banco antigo, clima e sugestão de look. Os testes de clima usam respostas simuladas do OpenWeatherMap, então não precisam de internet nem de chave real.

## Autoras

- Kely Caziuk
- Mariana Soares
