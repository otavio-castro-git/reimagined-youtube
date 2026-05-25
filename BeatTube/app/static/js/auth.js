// ─── Modais ───────────────────────────────────────────────────────────────────
const modalLogin    = document.getElementById("modalLogin");
const modalCadastro = document.getElementById("modalCadastro");
const abrirLogin    = document.getElementById("abrirLogin");

if (abrirLogin) abrirLogin.addEventListener("click", () => show(modalLogin));

document.getElementById("fecharLogin")?.addEventListener("click",   () => hide(modalLogin));
document.getElementById("fecharCadastro")?.addEventListener("click",() => hide(modalCadastro));
document.getElementById("irCadastro")?.addEventListener("click", (e) => { e.preventDefault(); hide(modalLogin); show(modalCadastro); });
document.getElementById("irLogin")?.addEventListener("click", (e)    => { e.preventDefault(); hide(modalCadastro); show(modalLogin); });

// Fechar clicando fora
[modalLogin, modalCadastro].forEach(m => {
    m?.addEventListener("click", e => { if (e.target === m) hide(m); });
});

function show(el) { if (el) el.style.display = "flex"; }
function hide(el) { if (el) el.style.display = "none"; }

// ─── Login ────────────────────────────────────────────────────────────────────
document.getElementById("btnLogin")?.addEventListener("click", async () => {
    const email = document.getElementById("loginEmail").value.trim();
    const senha = document.getElementById("loginSenha").value;
    const erro  = document.getElementById("loginErro");

    const res  = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password: senha }),
    });
    const data = await res.json();

    if (data.ok) {
        window.location.href = data.redirect;
    } else {
        erro.textContent = data.msg;
    }
});

// ─── Cadastro ─────────────────────────────────────────────────────────────────
document.getElementById("btnCadastro")?.addEventListener("click", async () => {
    const email  = document.getElementById("cadEmail").value.trim();
    const senha  = document.getElementById("cadSenha").value;
    const senha2 = document.getElementById("cadSenha2").value;
    const erro   = document.getElementById("cadErro");

    const res  = await fetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password: senha, password2: senha2 }),
    });
    const data = await res.json();

    if (data.ok) {
        window.location.href = data.redirect;
    } else {
        erro.textContent = data.msg;
    }
});
