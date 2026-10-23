const mensagem = document.getElementById("mensagem");

function mostrar(texto, erro = false) {
  mensagem.textContent = texto;
  mensagem.className = erro ? "mensagem erro" : "mensagem";
}

document.getElementById("form-login").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const form = new FormData(evento.target);
  try {
    localStorage.removeItem("token");
    const dados = await chamarApi("/auth/login", {
      metodo: "POST",
      corpo: { email: form.get("email"), senha: form.get("senha") },
    });
    salvarToken(dados.access_token);
    window.location.href = "hoje.html";
  } catch (erro) {
    mostrar(erro.message, true);
  }
});

document.getElementById("form-cadastro").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const form = new FormData(evento.target);
  try {
    await chamarApi("/auth/registrar", {
      metodo: "POST",
      corpo: {
        nome: form.get("nome"),
        email: form.get("email"),
        senha: form.get("senha"),
        cidade: form.get("cidade") || null,
      },
    });
    mostrar("Conta criada! Agora é só entrar.");
    evento.target.reset();
  } catch (erro) {
    mostrar(erro.message, true);
  }
});