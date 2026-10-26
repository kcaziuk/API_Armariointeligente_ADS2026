/* =========================================================
   Conversa com a API. Todas as telas usam chamarApi:
   ela coloca o token, envia o corpo em JSON e transforma
   as respostas de erro em mensagens.
   ========================================================= */
const API_URL = "http://127.0.0.1:8000";

function pegarToken() {
  return localStorage.getItem("token");
}

function salvarToken(token) {
  localStorage.setItem("token", token);
}

function apagarToken() {
  localStorage.removeItem("token");
}

class ErroApi extends Error {
  constructor(status, mensagem, erros) {
    super(mensagem);
    this.status = status;
    this.erros = erros || [];
  }
}

async function chamarApi(caminho, opcoes = {}) {
  const cabecalhos = {};
  if (opcoes.corpo !== undefined) cabecalhos["Content-Type"] = "application/json";
  const token = pegarToken();
  if (token) cabecalhos["Authorization"] = "Bearer " + token;

  let resposta;
  try {
    resposta = await fetch(API_URL + caminho, {
      method: opcoes.metodo || "GET",
      headers: cabecalhos,
      body: opcoes.corpo !== undefined ? JSON.stringify(opcoes.corpo) : undefined,
    });
  } catch (erro) {
    // A API está desligada ou o CORS bloqueou a chamada
    throw new ErroApi(0, "Não foi possível conectar à API. Confira se ela está ligada em " + API_URL + ".");
  }

  // Token vencido ou inválido: avisa a tela para voltar ao login
  if (resposta.status === 401 && token) {
    apagarToken();
    window.dispatchEvent(new Event("sessao-expirada"));
  }
  if (resposta.status === 204) return null;

  let dados = null;
  try {
    dados = await resposta.json();
  } catch (erro) {
    dados = null;
  }

  if (!resposta.ok) {
    const detalhe = dados && typeof dados.detail === "string" ? dados.detail : "Erro " + resposta.status;
    throw new ErroApi(resposta.status, detalhe, dados && dados.erros);
  }
  return dados;
}

function textoDoErro(erro) {
  if (erro.erros && erro.erros.length) {
    return erro.erros.map((item) => (item.campo ? item.campo + ": " : "") + item.mensagem).join("; ");
  }
  return erro.message;
}
