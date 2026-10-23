const API_URL = "http://127.0.0.1:8000";

function pegarToken() {
  return localStorage.getItem("token");
}

function salvarToken(token) {
  localStorage.setItem("token", token);
}

function sair() {
  localStorage.removeItem("token");
  window.location.href = "index.html";
}

function exigirLogin() {
  if (!pegarToken()) window.location.href = "index.html";
}

async function chamarApi(caminho, opcoes = {}) {
  const cabecalhos = { "Content-Type": "application/json" };
  const token = pegarToken();
  if (token) cabecalhos["Authorization"] = "Bearer " + token;

  const resposta = await fetch(API_URL + caminho, {
    method: opcoes.metodo || "GET",
    headers: cabecalhos,
    body: opcoes.corpo ? JSON.stringify(opcoes.corpo) : undefined,
  });

  // Token vencido ou inválido: volta para a tela de login
  if (resposta.status === 401 && token) {
    sair();
    return;
  }
  if (resposta.status === 204) return null;

  const dados = await resposta.json();
  if (!resposta.ok) {
    const detalhes = dados.erros
      ? dados.erros.map((erro) => `${erro.campo}: ${erro.mensagem}`).join("; ")
      : "";
    throw new Error(detalhes ? `${dados.detail} (${detalhes})` : dados.detail);
  }
  return dados;
}