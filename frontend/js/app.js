/* =========================================================
   Armário Inteligente — front-end
   Telas: Entrar, Hoje, Meu armário e Closets.
   Os dados vêm da API por chamarApi (js/api.js).
   Textos digitados entram sempre por textContent.
   ========================================================= */

/* Valores aceitos — exatamente como no contrato da API */
const TIPOS = ["Blusa", "Calça", "Casaco", "Calçado", "Acessório", "Outro"];
const ESTADOS = ["Limpa", "Suja", "Manutenção"];
const OCASIOES = ["Casual", "Trabalho", "Festa", "Esporte"];
const CLIMAS = ["Frio", "Ameno", "Quente", "Qualquer"];
const MOTIVOS = ["Venda", "Doação", "Perda", "Outro"];

const ICONE_TIPO = { "Blusa": "i-blusa", "Calça": "i-calca", "Casaco": "i-casaco", "Calçado": "i-calcado", "Acessório": "i-acessorio", "Outro": "i-outro" };

/* Cor digitada (texto livre) -> amostra visual */
const CORES = {
  branco: "#f4f2ee", branca: "#f4f2ee", preto: "#232323", preta: "#232323", cinza: "#8d8d8d",
  bege: "#d9c7a7", caramelo: "#b5803f", marrom: "#6b4630", azul: "#3d6fb6", jeans: "#4a6a8f",
  "azul-marinho": "#1f2f52", vermelho: "#b8322f", vermelha: "#b8322f", vinho: "#6d1f2c", rosa: "#e39bb0",
  verde: "#4f7d4a", amarelo: "#e2b93b", amarela: "#e2b93b", laranja: "#e07a3a", roxo: "#7a4fa0", roxa: "#7a4fa0", lilás: "#b9a2d6", creme: "#efe6cf"
};
function corHex(cor) { return CORES[(cor || "").trim().toLowerCase()] || null; }
function claridade(hex) {
  const n = parseInt(hex.slice(1), 16);
  return (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255;
}

/* =========================================================
   ESTADO DA TELA (cópia local do que veio da API)
   ========================================================= */
const estado = {
  usuario: null,
  pecas: [],       // GET /pecas (peças ativas)
  retiradas: [],   // GET /pecas/retiradas
  closets: [],     // GET /closets
  tela: "hoje",
  ocasiao: "",
  cidadeBusca: "",
  vista: "ativas",
};

/* Evita que uma resposta antiga sobrescreva uma mais nova */
let pedidoHoje = 0;
let pedidoArmario = 0;

/* =========================================================
   UTILITÁRIOS DE DOM
   ========================================================= */
function el(tag, props = {}, ...filhos) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v === undefined || v === null || v === false) continue;
    if (k === "class") n.className = v;
    else if (k === "text") n.textContent = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v === true ? "" : v);
  }
  for (const f of filhos.flat()) if (f !== null && f !== undefined && f !== false) n.append(f);
  return n;
}
function icone(id, tam = 20) {
  const ns = "http://www.w3.org/2000/svg";
  const s = document.createElementNS(ns, "svg");
  s.setAttribute("width", tam); s.setAttribute("height", tam); s.setAttribute("aria-hidden", "true");
  const u = document.createElementNS(ns, "use"); u.setAttribute("href", "#" + id); s.append(u);
  return s;
}
function amostra(cor) {
  const hex = corHex(cor);
  const s = el("span", { class: "amostra" + (hex ? "" : " desconhecida"), title: cor });
  if (hex) s.style.background = hex;
  return s;
}
function fundoPeca(cor) {
  const hex = corHex(cor);
  if (!hex) return { fundo: "var(--cartao-2)", tinta: "var(--texto-suave)" };
  return { fundo: hex, tinta: claridade(hex) > 0.6 ? "#3a3530" : "#fff" };
}
function classeEstado(e) { return { "Limpa": "limpa", "Suja": "suja", "Manutenção": "manutencao" }[e]; }
function badgeEstado(e) { return el("span", { class: "badge " + classeEstado(e) }, el("span", { class: "ponto" }), e); }
function badgeClima(c) {
  const cls = { "Frio": "frio", "Ameno": "ameno", "Quente": "quente" }[c];
  return el("span", { class: "badge " + (cls || "") }, c);
}
function toast(texto) {
  const t = el("div", { class: "toast" }, icone("i-check", 16), texto);
  document.getElementById("toasts").append(t);
  setTimeout(() => t.remove(), 2600);
}
function preencherSelect(select, valores, primeiro) {
  if (primeiro !== undefined) { select.replaceChildren(new Option(primeiro, "")); }
  else select.replaceChildren();
  for (const v of valores) select.append(new Option(v, v));
}
function dataBR(iso) { return new Date(iso).toLocaleDateString("pt-BR"); }
function estadoTela(...filhos) { return el("div", { class: "cartao estado-tela" }, ...filhos); }
function esqueletos(quantos, classe, estilo) {
  const g = el("div", { class: classe });
  for (let i = 0; i < quantos; i++) g.append(el("div", { class: "esqueleto", style: estilo }));
  return g;
}

/* =========================================================
   DADOS
   ========================================================= */
async function carregarDados() {
  const respostas = await Promise.all([
    chamarApi("/pecas"),
    chamarApi("/pecas/retiradas"),
    chamarApi("/closets"),
  ]);
  estado.pecas = respostas[0];
  estado.retiradas = respostas[1];
  estado.closets = respostas[2];
}

/* =========================================================
   NAVEGAÇÃO
   ========================================================= */
async function entrar() {
  try {
    estado.usuario = await chamarApi("/auth/eu");
    await carregarDados();
  } catch (erro) {
    sair(erro.status === 401 ? "Sua sessão expirou. Entre novamente." : textoDoErro(erro));
    return;
  }
  document.getElementById("tela-entrar").hidden = true;
  document.getElementById("area-logada").hidden = false;
  atualizarMenu();
  ir("hoje");
}
function sair(msg) {
  apagarToken();
  estado.usuario = null;
  document.getElementById("area-logada").hidden = true;
  document.getElementById("tela-entrar").hidden = false;
  if (msg) msgEntrar(msg, "erro");
  else document.getElementById("msg-entrar").hidden = true;
  window.scrollTo(0, 0);
}
window.addEventListener("sessao-expirada", () => sair("Sua sessão expirou. Entre novamente."));

function ir(tela) {
  estado.tela = tela;
  for (const t of ["hoje", "armario", "closets"]) document.getElementById("tela-" + t).hidden = t !== tela;
  document.querySelectorAll(".nav-link").forEach(b => b.setAttribute("aria-current", b.dataset.ir === tela ? "page" : "false"));
  if (tela === "hoje") renderHoje();
  if (tela === "armario") renderArmario();
  if (tela === "closets") renderClosets();
  window.scrollTo(0, 0);
}
function atualizarMenu() {
  const u = estado.usuario;
  document.getElementById("btn-perfil").textContent = (u.nome || "?").trim().charAt(0).toUpperCase();
  document.getElementById("cidade-menu-texto").textContent = u.cidade || "Sem cidade";
}

/* =========================================================
   TELA HOJE — GET /looks/sugestao
   ========================================================= */
const NOMES_DAS_PARTES = { parte_de_cima: "Parte de cima", parte_de_baixo: "Parte de baixo", calcado: "Calçado", acessorio: "Acessório", casaco: "Casaco" };
const TIPO_DA_PARTE = { parte_de_cima: "Blusa", parte_de_baixo: "Calça", calcado: "Calçado", acessorio: "Acessório", casaco: "Casaco" };

function frasePraHoje(c) {
  if (c.clima === "Frio" && c.chuva) return "Dia frio e com chuva: vá de casaco e prefira peças que aguentam molhar.";
  if (c.clima === "Frio") return "Dia frio: o look inclui um casaco.";
  if (c.chuva) return "Vai chover: o look inclui um casaco e prioriza peças que podem molhar.";
  if (c.clima === "Quente") return "Dia quente: peças leves e frescas.";
  return "Temperatura agradável: dá para usar quase tudo.";
}

function renderOcasioes() {
  const area = document.getElementById("chips-ocasiao");
  area.replaceChildren();
  for (const o of ["", ...OCASIOES]) {
    area.append(el("button", { class: "chip", type: "button", "aria-pressed": String(estado.ocasiao === o),
      onclick: () => { estado.ocasiao = o; renderHoje(); } }, o || "Qualquer"));
  }
}

async function renderHoje() {
  const meuPedido = ++pedidoHoje;
  const hoje = new Date();
  const dataTxt = hoje.toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long" });
  document.getElementById("hoje-data").textContent = dataTxt.charAt(0).toUpperCase() + dataTxt.slice(1);
  document.getElementById("hoje-saudacao").textContent = `Oi, ${estado.usuario.nome.split(" ")[0]}! O que vestir hoje?`;
  renderOcasioes();

  const cartaoClima = document.getElementById("clima-cartao");
  const areaLook = document.getElementById("area-look");
  const listaAvisos = document.getElementById("avisos");
  const resumo = document.getElementById("look-resumo");
  cartaoClima.className = "cartao clima-cartao";
  cartaoClima.replaceChildren(
    el("div", { class: "esqueleto", style: "height:18px;width:40%" }),
    el("div", { class: "esqueleto", style: "height:64px;width:60%;margin-top:16px" }),
    el("div", { class: "esqueleto", style: "height:24px;width:80%;margin-top:16px" }));
  areaLook.replaceChildren(esqueletos(5, "look-grade", "min-height:210px;border-radius:12px"));
  listaAvisos.replaceChildren();
  resumo.textContent = "Consultando o tempo…";

  const parametros = new URLSearchParams();
  if (estado.ocasiao) parametros.set("ocasiao", estado.ocasiao);
  if (estado.cidadeBusca) parametros.set("cidade", estado.cidadeBusca);
  const cidade = estado.cidadeBusca || estado.usuario.cidade || "";

  let dados;
  try {
    dados = await chamarApi("/looks/sugestao?" + parametros);
  } catch (erro) {
    if (meuPedido !== pedidoHoje || erro.status === 401) return;
    cartaoClima.replaceChildren(); areaLook.replaceChildren(); resumo.textContent = "";
    if (erro.status === 400) {
      return erroHoje(cartaoClima, areaLook, "i-local", erro.message, "400",
        el("button", { class: "btn secundario", onclick: abrirPerfil }, "Cadastrar cidade"));
    }
    if (erro.status === 404) {
      return erroHoje(cartaoClima, areaLook, "i-local", `${erro.message}: "${cidade}"`, "404",
        el("p", { class: "suave pequeno", text: "Confira a grafia ou tente outra cidade no campo ao lado." }));
    }
    return erroHoje(cartaoClima, areaLook, "i-nuvem", erro.message, erro.status ? String(erro.status) : "sem conexão",
      el("button", { class: "btn secundario", onclick: renderHoje }, "Tentar de novo"));
  }
  if (meuPedido !== pedidoHoje) return;

  const c = dados.clima;
  cartaoClima.replaceChildren();
  cartaoClima.classList.add(c.clima.toLowerCase());
  cartaoClima.append(
    el("div", { class: "clima-cidade" }, icone("i-local", 16), c.cidade),
    el("div", { class: "clima-linha" },
      icone(c.chuva ? "i-chuva" : c.clima === "Quente" ? "i-sol" : "i-nuvem", 72),
      el("div", {},
        el("div", { class: "clima-temp", text: `${Math.round(c.temperatura)}°` }),
        el("div", { class: "suave", text: `Sensação de ${Math.round(c.sensacao)}° · ${c.descricao}` }))),
    el("div", { class: "clima-dados" },
      badgeClima(c.clima),
      c.chuva ? el("span", { class: "badge frio" }, icone("i-gota", 12), "Chuva") : null),
    el("p", { class: "clima-frase", text: frasePraHoje(c) }));
  cartaoClima.querySelectorAll(".clima-linha > svg").forEach(s => s.classList.add("clima-icone"));

  areaLook.replaceChildren();
  if (estado.pecas.length === 0) {
    resumo.textContent = "";
    areaLook.append(estadoTela(icone("i-cabide", 48),
      el("h3", { text: "Seu armário ainda está vazio" }),
      el("p", { class: "suave", text: "Cadastre algumas peças para receber sugestões de look para o tempo de hoje." }),
      el("button", { class: "btn", onclick: () => { ir("armario"); abrirModalPeca(); } }, icone("i-mais", 18), "Cadastrar primeira peça")));
    return;
  }

  const precisaCasaco = c.clima === "Frio" || c.chuva;
  const compativeis = estado.pecas.filter(p =>
    p.estado === "Limpa" &&
    (p.clima_ideal === c.clima || p.clima_ideal === "Qualquer") &&
    (!estado.ocasiao || p.ocasiao === estado.ocasiao)).length;
  resumo.textContent = `${compativeis} peça${compativeis === 1 ? "" : "s"} limpa${compativeis === 1 ? "" : "s"} combinam com o clima ${c.clima.toLowerCase()}${estado.ocasiao ? " e a ocasião " + estado.ocasiao : ""}.`;

  const grade = el("div", { class: "look-grade" });
  for (const parte of Object.keys(NOMES_DAS_PARTES)) {
    const peca = dados.look[parte];
    if (peca) {
      const cores = fundoPeca(peca.cor);
      const visual = el("div", { class: "slot-visual" }, icone(ICONE_TIPO[peca.tipo] || "i-outro", 52));
      visual.style.background = cores.fundo; visual.style.color = cores.tinta;
      if (c.chuva && peca.pode_chuva) visual.append(el("span", { class: "chuva-tag" }, icone("i-gota", 10), "chuva"));
      grade.append(el("div", { class: "slot" },
        el("span", { class: "slot-parte", text: NOMES_DAS_PARTES[parte] }),
        visual,
        el("span", { class: "slot-nome", text: peca.nome }),
        el("span", { class: "slot-meta" }, amostra(peca.cor), `${peca.cor}${peca.modelo ? " · " + peca.modelo : ""}`)));
    } else if (parte === "casaco" && !precisaCasaco) {
      grade.append(el("div", { class: "slot dispensado" },
        el("span", { class: "slot-parte", text: NOMES_DAS_PARTES[parte] }),
        el("div", { class: "slot-visual", style: "color:var(--texto-suave);opacity:.5" }, icone("i-casaco", 52)),
        el("span", { class: "slot-nome suave pequeno", text: "Não precisa hoje" })));
    } else {
      grade.append(el("div", { class: "slot vazio" },
        el("span", { class: "slot-parte", text: NOMES_DAS_PARTES[parte] }),
        el("div", { class: "slot-visual" }, icone(ICONE_TIPO[TIPO_DA_PARTE[parte]], 52)),
        el("span", { class: "slot-nome", text: "Nada disponível" })));
    }
  }
  areaLook.append(grade);

  for (const aviso of dados.avisos) {
    listaAvisos.append(el("li", {}, icone("i-alerta", 18), el("span", { text: aviso }),
      el("a", { onclick: () => { ir("armario"); abrirModalPeca(); } }, "Cadastrar peça")));
  }
}

function erroHoje(cartao, area, ic, titulo, codigo, acao) {
  cartao.append(el("div", { class: "estado-tela erro", style: "padding:16px" }, icone(ic, 48),
    el("h3", { text: titulo }), el("span", { class: "badge", text: codigo }), acao));
  area.append(estadoTela(
    el("p", { class: "suave", text: "Sem a previsão do tempo, não dá para sugerir o look de hoje." }),
    el("button", { class: "btn secundario", onclick: () => ir("armario") }, "Ver meu armário")));
}

/* =========================================================
   TELA MEU ARMÁRIO — GET /pecas, /pecas/agrupadas, /pecas/retiradas
   ========================================================= */
function parametrosDosFiltros() {
  const parametros = new URLSearchParams();
  for (const [campo, valor] of new FormData(document.getElementById("form-filtros"))) {
    if (String(valor).trim()) parametros.set(campo, String(valor).trim());
  }
  return parametros;
}

async function renderArmario() {
  const meuPedido = ++pedidoArmario;
  const ativas = estado.pecas;
  document.getElementById("cont-ativas").textContent = ativas.length;
  document.getElementById("cont-retiradas").textContent = estado.retiradas.length;
  const limpas = ativas.filter(p => p.estado === "Limpa").length;
  document.getElementById("armario-resumo").textContent =
    `${ativas.length} peças · ${limpas} limpas · ${ativas.length - limpas} sujas ou em manutenção`;

  document.querySelectorAll("[data-vista]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.vista === estado.vista)));
  document.getElementById("campo-agrupar").hidden = estado.vista !== "agrupadas";
  document.getElementById("campo-motivo").hidden = estado.vista !== "retiradas";
  document.getElementById("form-filtros").hidden = estado.vista !== "ativas";

  const area = document.getElementById("area-armario");
  area.replaceChildren(esqueletos(6, "grade", "height:260px;border-radius:12px"));

  try {
    if (estado.vista === "retiradas") {
      const motivo = document.getElementById("filtro-motivo").value;
      const lista = await chamarApi("/pecas/retiradas" + (motivo ? "?motivo=" + encodeURIComponent(motivo) : ""));
      if (meuPedido !== pedidoArmario) return;
      area.replaceChildren();
      renderRetiradas(area, lista);
      return;
    }

    if (ativas.length === 0) {
      area.replaceChildren(estadoTela(icone("i-cabide", 48),
        el("h3", { text: "Nenhuma peça por aqui ainda" }),
        el("p", { class: "suave", text: "Comece pelas peças que você mais usa: uma blusa, uma calça e um calçado já rendem um look." }),
        el("button", { class: "btn", onclick: () => abrirModalPeca() }, icone("i-mais", 18), "Cadastrar peça")));
      return;
    }

    if (estado.vista === "agrupadas") {
      const por = document.getElementById("agrupar-por").value;
      const grupos = await chamarApi("/pecas/agrupadas?por=" + por);
      if (meuPedido !== pedidoArmario) return;
      area.replaceChildren();
      for (const nome of Object.keys(grupos).sort()) {
        const pecas = grupos[nome];
        const g = el("div", { class: "grade" });
        pecas.forEach(p => g.append(cartaoPeca(p)));
        area.append(el("section", { class: "grupo" },
          el("div", { class: "grupo-titulo" }, por === "cor" ? amostra(nome) : null, el("span", { text: nome }), el("span", { class: "contador", text: pecas.length })), g));
      }
      return;
    }

    const filtradas = await chamarApi("/pecas?" + parametrosDosFiltros());
    if (meuPedido !== pedidoArmario) return;
    area.replaceChildren();
    if (filtradas.length === 0) {
      area.append(estadoTela(
        el("h3", { text: "Nenhuma peça encontrada" }),
        el("p", { class: "suave", text: "Tente remover algum filtro." }),
        el("button", { class: "btn secundario", onclick: () => { document.getElementById("form-filtros").reset(); renderArmario(); } }, "Limpar filtros")));
      return;
    }
    const g = el("div", { class: "grade" });
    filtradas.forEach(p => g.append(cartaoPeca(p)));
    area.append(g);
  } catch (erro) {
    if (meuPedido !== pedidoArmario || erro.status === 401) return;
    area.replaceChildren(estadoTela(icone("i-alerta", 48), el("h3", { text: textoDoErro(erro) })));
  }
}

function cartaoPeca(p) {
  const cores = fundoPeca(p.cor);
  const visual = el("div", { class: "peca-visual" }, icone(ICONE_TIPO[p.tipo] || "i-outro", 48), badgeEstado(p.estado));
  visual.style.background = cores.fundo; visual.style.color = cores.tinta;
  if (p.pode_chuva) visual.append(el("span", { class: "chuva-tag", title: "Pode usar na chuva" }, icone("i-gota", 10), "chuva"));

  const novoEstado = p.estado === "Limpa" ? "Suja" : "Limpa";
  return el("article", { class: "cartao-peca" },
    visual,
    el("div", { class: "peca-corpo" },
      el("span", { class: "peca-nome", text: p.nome }),
      el("span", { class: "peca-linha" }, amostra(p.cor), `${p.tipo} · ${p.cor}${p.modelo ? " · " + p.modelo : ""}`),
      el("div", { class: "peca-tags" }, el("span", { class: "badge", text: p.ocasiao }), badgeClima(p.clima_ideal)),
      p.observacoes ? el("span", { class: "peca-obs", text: `"${p.observacoes}"` }) : null),
    el("div", { class: "peca-acoes" },
      el("button", { class: "btn secundario pequeno", onclick: () => mudarEstado(p, novoEstado) },
        novoEstado === "Suja" ? "Marcar como suja" : "Marcar como limpa"),
      el("button", { class: "btn fantasma pequeno icone", title: "Editar", "aria-label": "Editar " + p.nome, onclick: () => abrirModalPeca(p) }, icone("i-lapis", 16)),
      el("button", { class: "btn perigo-contorno pequeno icone", title: "Retirar do armário", "aria-label": "Retirar " + p.nome, onclick: () => abrirRetirar(p) }, icone("i-lixo", 16))));
}

function renderRetiradas(area, lista) {
  if (!lista.length) {
    area.append(estadoTela(el("h3", { text: "Nenhuma peça retirada" }),
      el("p", { class: "suave", text: "Peças vendidas, doadas ou perdidas aparecem aqui, com o motivo." })));
    return;
  }
  const corpo = el("tbody");
  for (const p of lista) {
    corpo.append(el("tr", {},
      el("td", {}, el("span", { class: "nome-com-amostra" }, amostra(p.cor), p.nome)),
      el("td", { class: "suave", text: p.tipo }),
      el("td", {}, el("span", { class: "badge", text: p.motivo_retirada })),
      el("td", { class: "suave", text: p.observacao_retirada || "—" }),
      el("td", { class: "suave", text: dataBR(p.retirada_em) })));
  }
  area.append(el("div", { class: "cartao tabela-envolve" },
    el("table", { class: "tabela" },
      el("thead", {}, el("tr", {}, ...["Peça", "Tipo", "Motivo", "Observação", "Retirada em"].map(t => el("th", { text: t })))),
      corpo)));
}

/* PATCH /pecas/{id} — só o estado muda */
async function mudarEstado(p, novo) {
  try {
    await chamarApi(`/pecas/${p.id}`, { metodo: "PATCH", corpo: { estado: novo } });
    await carregarDados();
    toast(`${p.nome} marcada como ${novo.toLowerCase()}`);
    renderArmario();
  } catch (erro) {
    if (erro.status !== 401) toast(textoDoErro(erro));
  }
}

/* ---------- Modal peça: POST /pecas ou PUT /pecas/{id} ---------- */
let pecaEditando = null;
function abrirModalPeca(p = null) {
  pecaEditando = p;
  const form = document.getElementById("form-peca");
  form.reset();
  limparErros(form);
  document.getElementById("modal-peca-titulo").textContent = p ? "Editar peça" : "Nova peça";
  document.getElementById("btn-salvar-peca").textContent = p ? "Salvar alterações" : "Cadastrar peça";
  form.elements.estado.value = "Limpa"; form.elements.clima_ideal.value = "Qualquer";
  if (p) for (const campo of ["nome", "tipo", "cor", "modelo", "estado", "ocasiao", "clima_ideal", "observacoes"]) form.elements[campo].value = p[campo] || "";
  form.elements.pode_chuva.checked = p ? p.pode_chuva : false;
  document.getElementById("modal-peca").showModal();
}
function limparErros(form) {
  form.querySelectorAll(".com-erro").forEach(c => c.classList.remove("com-erro"));
  form.querySelectorAll(".erro-campo").forEach(e => { e.textContent = ""; });
}
/* Mostra a mensagem do erro embaixo do campo; devolve false se o campo não existe no formulário */
function marcarErro(form, nome, msg) {
  let campo = form.querySelector(`[data-nome="${nome}"]`);
  if (!campo && form.elements[nome]) campo = form.elements[nome].closest(".campo");
  if (!campo) return false;
  campo.classList.add("com-erro");
  const e = campo.querySelector(".erro-campo");
  if (e) e.textContent = msg;
  return true;
}
function mostrarErrosNoFormulario(form, erro) {
  const naoMostrados = erro.erros.filter(item => !marcarErro(form, item.campo, item.mensagem));
  if (!erro.erros.length || naoMostrados.length) toast(textoDoErro(erro));
}
document.getElementById("form-peca").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const form = ev.target;
  limparErros(form);
  const dados = Object.fromEntries(new FormData(form));
  const corpo = {
    nome: dados.nome,
    tipo: dados.tipo,
    cor: dados.cor,
    modelo: dados.modelo.trim() || null,
    observacoes: dados.observacoes.trim() || null,
    estado: dados.estado,
    ocasiao: dados.ocasiao,
    clima_ideal: dados.clima_ideal,
    pode_chuva: form.elements.pode_chuva.checked,
  };
  try {
    if (pecaEditando) await chamarApi(`/pecas/${pecaEditando.id}`, { metodo: "PUT", corpo });
    else await chamarApi("/pecas", { metodo: "POST", corpo });
    await carregarDados();
  } catch (erro) {
    if (erro.status !== 401) mostrarErrosNoFormulario(form, erro);
    return;
  }
  document.getElementById("modal-peca").close();
  toast(pecaEditando ? "Peça atualizada" : "Peça cadastrada!");
  if (estado.tela === "armario") renderArmario(); else ir("armario");
});

/* ---------- Modal retirar: DELETE /pecas/{id}?motivo= ---------- */
let pecaRetirando = null, motivoEscolhido = "Doação";
function renderMotivos() {
  const area = document.getElementById("chips-motivo");
  area.replaceChildren();
  for (const m of MOTIVOS) area.append(el("button", { type: "button", class: "chip", "aria-pressed": String(m === motivoEscolhido),
    onclick: () => { motivoEscolhido = m; renderMotivos(); } }, m));
  document.getElementById("campo-observacao").hidden = motivoEscolhido !== "Outro";
}
function abrirRetirar(p) {
  pecaRetirando = p; motivoEscolhido = "Doação";
  const form = document.getElementById("form-retirar");
  form.reset(); limparErros(form);
  document.getElementById("retirar-nome").textContent = p.nome;
  renderMotivos();
  document.getElementById("modal-retirar").showModal();
}
document.getElementById("form-retirar").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const form = ev.target; limparErros(form);
  const obs = form.elements.observacao.value.trim();
  if (motivoEscolhido === "Outro" && !obs) {
    const c = document.getElementById("campo-observacao"); c.classList.add("com-erro");
    c.querySelector(".erro-campo").textContent = "Conte o motivo da retirada"; return;
  }
  const parametros = new URLSearchParams({ motivo: motivoEscolhido });
  if (obs) parametros.set("observacao", obs);
  try {
    await chamarApi(`/pecas/${pecaRetirando.id}?` + parametros, { metodo: "DELETE" });
    await carregarDados();
  } catch (erro) {
    if (erro.status !== 401) toast(textoDoErro(erro));
    return;
  }
  document.getElementById("modal-retirar").close();
  toast(`${pecaRetirando.nome} retirada do armário`);
  renderArmario();
});

/* =========================================================
   TELA CLOSETS — GET/POST/PUT/DELETE /closets
   ========================================================= */
function renderClosets() {
  const area = document.getElementById("area-closets");
  area.replaceChildren();
  if (!estado.closets.length) {
    area.append(estadoTela(icone("i-cabide", 48),
      el("h3", { text: "Você ainda não tem closets" }),
      el("p", { class: "suave", text: "Monte coleções para viagens, trabalho ou estações do ano." }),
      el("button", { class: "btn", onclick: () => abrirModalCloset() }, icone("i-mais", 18), "Criar closet")));
    return;
  }
  const grade = el("div", { class: "grade-closets" });
  for (const c of estado.closets) {
    const pecas = c.pecas_ids.map(id => estado.pecas.find(p => p.id === id)).filter(Boolean);
    const mosaico = el("div", { class: "closet-mosaico" });
    for (let i = 0; i < 5; i++) {
      const p = pecas[i];
      const quad = el("div", {});
      if (p) {
        const cores = fundoPeca(p.cor);
        quad.style.background = cores.fundo; quad.style.color = cores.tinta;
        quad.append(icone(ICONE_TIPO[p.tipo] || "i-outro", 22)); quad.title = p.nome;
      } else {
        quad.style.border = "1.5px dashed var(--borda)";
      }
      mosaico.append(quad);
    }
    grade.append(el("article", { class: "cartao cartao-closet" },
      mosaico,
      el("div", {}, el("h3", { text: c.nome }), c.descricao ? el("p", { class: "suave pequeno", style: "margin-top:4px", text: c.descricao }) : null),
      el("div", { class: "closet-pecas" },
        pecas.length ? pecas.map(p => el("span", {}, amostra(p.cor), p.nome)) : el("span", { class: "suave", text: "Nenhuma peça" })),
      el("div", { class: "closet-rodape" },
        el("span", { class: "suave pequeno", style: "margin-right:auto;align-self:center", text: `${pecas.length} peça${pecas.length === 1 ? "" : "s"}` }),
        el("button", { class: "btn fantasma pequeno", onclick: () => abrirModalCloset(c) }, icone("i-lapis", 16), "Editar"),
        el("button", { class: "btn perigo-contorno pequeno", onclick: () => apagarCloset(c) }, icone("i-lixo", 16), "Apagar"))));
  }
  area.append(grade);
}

let closetEditando = null;
function atualizarContagemCloset() {
  const n = document.querySelectorAll("#closet-pecas input:checked").length;
  document.getElementById("closet-contagem").textContent = n ? `${n} selecionada${n === 1 ? "" : "s"}` : "Nenhuma selecionada";
}
function abrirModalCloset(c = null) {
  closetEditando = c;
  const form = document.getElementById("form-closet");
  form.reset(); limparErros(form);
  document.getElementById("modal-closet-titulo").textContent = c ? "Editar closet" : "Novo closet";
  document.getElementById("btn-salvar-closet").textContent = c ? "Salvar alterações" : "Criar closet";
  if (c) { form.elements.nome.value = c.nome; form.elements.descricao.value = c.descricao || ""; }
  const area = document.getElementById("closet-pecas");
  area.replaceChildren();
  if (!estado.pecas.length) area.append(el("p", { class: "suave pequeno", text: "Cadastre peças no armário para adicioná-las aqui." }));
  for (const p of estado.pecas) {
    const caixa = el("input", { type: "checkbox", name: "pecas_ids", value: p.id, onchange: atualizarContagemCloset });
    if (c && c.pecas_ids.includes(p.id)) caixa.checked = true;
    area.append(el("label", {}, caixa, amostra(p.cor), el("span", { text: p.nome })));
  }
  atualizarContagemCloset();
  document.getElementById("modal-closet").showModal();
}
document.getElementById("form-closet").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const form = ev.target; limparErros(form);
  const corpo = {
    nome: form.elements.nome.value.trim(),
    descricao: form.elements.descricao.value.trim() || null,
    pecas_ids: new FormData(form).getAll("pecas_ids").map(Number),
  };
  if (!corpo.nome) { marcarErro(form, "nome", "Dê um nome ao closet"); return; }
  try {
    if (closetEditando) await chamarApi(`/closets/${closetEditando.id}`, { metodo: "PUT", corpo });
    else await chamarApi("/closets", { metodo: "POST", corpo });
    await carregarDados();
  } catch (erro) {
    if (erro.status !== 401) mostrarErrosNoFormulario(form, erro);
    return;
  }
  document.getElementById("modal-closet").close();
  toast(closetEditando ? "Closet atualizado" : "Closet criado!");
  renderClosets();
});

function apagarCloset(c) {
  const modal = document.getElementById("modal-confirmar");
  document.getElementById("confirmar-titulo").textContent = `Apagar "${c.nome}"?`;
  document.getElementById("confirmar-texto").textContent = "O closet será apagado, mas as peças continuam no seu armário.";
  modal.returnValue = "";
  modal.showModal();
  modal.addEventListener("close", async function aoFechar() {
    modal.removeEventListener("close", aoFechar);
    if (modal.returnValue !== "sim") return;
    try {
      await chamarApi(`/closets/${c.id}`, { metodo: "DELETE" });
      await carregarDados();
    } catch (erro) {
      if (erro.status !== 401) toast(textoDoErro(erro));
      return;
    }
    toast("Closet apagado");
    renderClosets();
  });
}

/* =========================================================
   PERFIL — GET / PATCH /auth/eu
   ========================================================= */
function abrirPerfil() {
  const form = document.getElementById("form-perfil");
  form.elements.nome.value = estado.usuario.nome;
  form.elements.email.value = estado.usuario.email;
  form.elements.cidade.value = estado.usuario.cidade || "";
  document.getElementById("modal-perfil").showModal();
}
document.getElementById("form-perfil").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const f = ev.target;
  const corpo = { cidade: f.elements.cidade.value.trim() || null };
  const nome = f.elements.nome.value.trim();
  if (nome) corpo.nome = nome;
  try {
    estado.usuario = await chamarApi("/auth/eu", { metodo: "PATCH", corpo });
  } catch (erro) {
    if (erro.status !== 401) toast(textoDoErro(erro));
    return;
  }
  estado.cidadeBusca = "";
  document.getElementById("hoje-cidade").value = "";
  document.getElementById("modal-perfil").close();
  atualizarMenu(); toast("Perfil atualizado");
  if (estado.tela === "hoje") renderHoje();
});

/* =========================================================
   TELA ENTRAR — POST /auth/login e /auth/registrar
   ========================================================= */
document.querySelectorAll("[data-aba]").forEach(aba => aba.addEventListener("click", () => {
  document.querySelectorAll("[data-aba]").forEach(a => a.setAttribute("aria-selected", String(a === aba)));
  document.getElementById("form-login").hidden = aba.dataset.aba !== "login";
  document.getElementById("form-cadastro").hidden = aba.dataset.aba !== "cadastro";
  document.getElementById("msg-entrar").hidden = true;
}));
function msgEntrar(texto, tipo) {
  const m = document.getElementById("msg-entrar");
  m.textContent = texto; m.className = "mensagem " + tipo; m.hidden = false;
}
document.getElementById("form-login").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const f = new FormData(ev.target);
  if (!f.get("email") || !f.get("senha")) return msgEntrar("Informe e-mail e senha", "erro");
  apagarToken();
  try {
    const resposta = await chamarApi("/auth/login", { metodo: "POST", corpo: { email: f.get("email"), senha: f.get("senha") } });
    salvarToken(resposta.access_token);
  } catch (erro) {
    return msgEntrar(textoDoErro(erro), "erro");
  }
  ev.target.reset();
  entrar();
});
document.getElementById("form-cadastro").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const f = new FormData(ev.target);
  if (!f.get("nome") || !f.get("email")) return msgEntrar("Preencha nome e e-mail", "erro");
  if ((f.get("senha") || "").length < 8) return msgEntrar("A senha precisa ter pelo menos 8 caracteres", "erro");
  try {
    await chamarApi("/auth/registrar", { metodo: "POST", corpo: {
      nome: f.get("nome"), email: f.get("email"), senha: f.get("senha"), cidade: f.get("cidade") || null,
    } });
  } catch (erro) {
    return msgEntrar(textoDoErro(erro), "erro");
  }
  const email = f.get("email");
  ev.target.reset();
  document.querySelector('[data-aba="login"]').click();
  document.getElementById("form-login").elements.email.value = email;
  msgEntrar("Conta criada! Agora é só entrar.", "ok");
});

/* =========================================================
   LIGAÇÕES GERAIS
   ========================================================= */
document.querySelectorAll("[data-ir]").forEach(b => b.addEventListener("click", (ev) => { ev.preventDefault(); ir(b.dataset.ir); }));
document.getElementById("btn-sair").addEventListener("click", () => sair());
document.getElementById("btn-perfil").addEventListener("click", abrirPerfil);
document.getElementById("btn-cidade-menu").addEventListener("click", abrirPerfil);
document.getElementById("btn-sugerir").addEventListener("click", renderHoje);
document.getElementById("btn-buscar-cidade").addEventListener("click", () => {
  estado.cidadeBusca = document.getElementById("hoje-cidade").value.trim(); renderHoje();
});
document.getElementById("hoje-cidade").addEventListener("keydown", (ev) => {
  if (ev.key === "Enter") { estado.cidadeBusca = ev.target.value.trim(); renderHoje(); }
});
document.getElementById("btn-nova-peca").addEventListener("click", () => abrirModalPeca());
document.getElementById("btn-novo-closet").addEventListener("click", () => abrirModalCloset());
document.querySelectorAll("[data-vista]").forEach(b => b.addEventListener("click", () => { estado.vista = b.dataset.vista; renderArmario(); }));
document.getElementById("agrupar-por").addEventListener("change", renderArmario);
document.getElementById("filtro-motivo").addEventListener("change", renderArmario);

const formFiltros = document.getElementById("form-filtros");
let esperaFiltro = null;
formFiltros.addEventListener("input", () => {
  // Espera a pessoa parar de digitar antes de chamar a API
  clearTimeout(esperaFiltro);
  esperaFiltro = setTimeout(renderArmario, 350);
});
formFiltros.addEventListener("reset", () => setTimeout(renderArmario));
formFiltros.addEventListener("submit", ev => ev.preventDefault());
document.querySelectorAll("[data-fechar]").forEach(b => b.addEventListener("click", () => b.closest("dialog").close()));

// Preenche os selects a partir dos valores aceitos
const fp = document.getElementById("form-peca").elements;
preencherSelect(fp.tipo, TIPOS); preencherSelect(fp.estado, ESTADOS);
preencherSelect(fp.ocasiao, OCASIOES); preencherSelect(fp.clima_ideal, CLIMAS);
const ff = formFiltros.elements;
preencherSelect(ff.tipo, TIPOS, "Todos"); preencherSelect(ff.estado, ESTADOS, "Todos");
preencherSelect(ff.ocasiao, OCASIOES, "Todas"); preencherSelect(ff.clima_ideal, CLIMAS, "Todos");
const dl = document.getElementById("lista-cores");
for (const c of ["branco", "preto", "cinza", "bege", "caramelo", "marrom", "azul", "jeans", "vermelho", "vinho", "rosa", "verde", "amarelo", "laranja", "roxo"]) dl.append(new Option(c));

// Já tem token guardado? Entra direto; senão, mostra a tela de login
if (pegarToken()) entrar();
