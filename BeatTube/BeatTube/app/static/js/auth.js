// ─── Modais ───────────────────────────────────────────────────────────────────
const modalLogin               = document.getElementById("modalLogin");
const modalCadastro            = document.getElementById("modalCadastro");
const modalVerificarEmail      = document.getElementById("modalVerificarEmail");
const modalTermosUso           = document.getElementById("modalTermosUso");
const modalPoliticaPrivacidade = document.getElementById("modalPoliticaPrivacidade");
const abrirLogin               = document.getElementById("abrirLogin");

if (abrirLogin) abrirLogin.addEventListener("click", () => show(modalLogin));

document.getElementById("fecharLogin")?.addEventListener("click",   () => hide(modalLogin));
document.getElementById("fecharCadastro")?.addEventListener("click",() => hide(modalCadastro));
document.getElementById("fecharVerificarEmail")?.addEventListener("click", () => hide(modalVerificarEmail));
document.getElementById("irCadastro")?.addEventListener("click", (e) => { e.preventDefault(); hide(modalLogin); show(modalCadastro); });
document.getElementById("irLogin")?.addEventListener("click", (e)    => { e.preventDefault(); hide(modalCadastro); show(modalLogin); });

// Abrir/fechar os modais de Termos de Uso e Política de Privacidade
// (ficam "por cima" do modal de cadastro, que continua aberto por baixo)
document.getElementById("abrirTermosUso")?.addEventListener("click", (e) => {
    e.preventDefault();
    show(modalTermosUso);
});
document.getElementById("abrirPoliticaPrivacidade")?.addEventListener("click", (e) => {
    e.preventDefault();
    show(modalPoliticaPrivacidade);
});
document.getElementById("fecharTermosUso")?.addEventListener("click", () => hide(modalTermosUso));
document.getElementById("fecharPoliticaPrivacidade")?.addEventListener("click", () => hide(modalPoliticaPrivacidade));

// Fechar clicando fora
[modalLogin, modalCadastro, modalVerificarEmail, modalTermosUso, modalPoliticaPrivacidade].forEach(m => {
    m?.addEventListener("click", e => { if (e.target === m) hide(m); });
});

function show(el) { if (el) el.style.display = "flex"; }
function hide(el) { if (el) el.style.display = "none"; }

// ─── Captcha (Google reCAPTCHA v3) ─────────────────────────────────────────────
// Gera um token novo a cada ação (login/register), como recomendado pelo Google,
// já que cada token só vale para uma submissão.
async function getCaptchaToken(acao) {
    if (!window.RECAPTCHA_SITE_KEY || !window.grecaptcha) {
        // Captcha não configurado no .env — segue sem token (o back-end também
        // libera nesse caso, mas avisa no log do servidor).
        return "";
    }
    return new Promise((resolve) => {
        grecaptcha.ready(() => {
            grecaptcha.execute(window.RECAPTCHA_SITE_KEY, { action: acao })
                .then(resolve)
                .catch(() => resolve(""));
        });
    });
}

// ─── Login ────────────────────────────────────────────────────────────────────
document.getElementById("btnLogin")?.addEventListener("click", async () => {
    const email = document.getElementById("loginEmail").value.trim();
    const senha = document.getElementById("loginSenha").value;
    const erro  = document.getElementById("loginErro");
    erro.textContent = "";

    const captcha_token = await getCaptchaToken("login");

    const res  = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password: senha, captcha_token }),
    });
    const data = await res.json();

    if (data.ok) {
        window.location.href = data.redirect;
    } else {
        erro.textContent = data.msg;
    }
});

// ─── Cadastro — Passo 1: enviar dados e receber código por email ──────────────
let emailCadastroPendente = "";

document.getElementById("btnCadastro")?.addEventListener("click", async () => {
    const email  = document.getElementById("cadEmail").value.trim();
    const senha  = document.getElementById("cadSenha").value;
    const senha2 = document.getElementById("cadSenha2").value;
    const aceitouTermos = document.getElementById("cadAceiteTermos").checked;
    const erro   = document.getElementById("cadErro");
    erro.textContent = "";

    if (!aceitouTermos) {
        erro.textContent = "Você precisa aceitar os Termos de Uso e a Política de Privacidade para se cadastrar.";
        return;
    }

    const captcha_token = await getCaptchaToken("register");

    const res  = await fetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password: senha, password2: senha2, captcha_token, aceitou_termos: aceitouTermos }),
    });
    const data = await res.json();

    if (data.ok) {
        emailCadastroPendente = data.email;
        document.getElementById("verificarEmailTexto").textContent = data.email;
        document.getElementById("verificarErro").textContent = "";
        document.getElementById("codigoVerificacao").value = "";
        hide(modalCadastro);
        show(modalVerificarEmail);
    } else {
        erro.textContent = data.msg;
    }
});

// ─── Cadastro — Passo 2: confirmar código recebido por email ──────────────────
document.getElementById("btnConfirmarCodigo")?.addEventListener("click", async () => {
    const codigo = document.getElementById("codigoVerificacao").value.trim();
    const erro   = document.getElementById("verificarErro");
    erro.textContent = "";

    if (!codigo) {
        erro.textContent = "Digite o código recebido por email.";
        return;
    }

    const res  = await fetch("/auth/register/confirmar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: emailCadastroPendente, codigo }),
    });
    const data = await res.json();

    if (data.ok) {
        window.location.href = data.redirect;
    } else {
        erro.textContent = data.msg;
    }
});

// ─── Cadastro — reenviar código ────────────────────────────────────────────────
document.getElementById("btnReenviarCodigo")?.addEventListener("click", async () => {
    const erro = document.getElementById("verificarErro");
    erro.textContent = "";

    const res  = await fetch("/auth/register/reenviar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: emailCadastroPendente }),
    });
    const data = await res.json();

    if (data.ok) {
        erro.style.color = "#4caf50";
        erro.textContent = "Código reenviado!";
    } else {
        erro.style.color = "";
        erro.textContent = data.msg;
    }
});

// ─── Sidebar mobile (hamburger) ─────────────────────────────────────────────────
const sidebarEl      = document.querySelector(".sidebar");
const hamburgerBtn   = document.getElementById("hamburgerBtn");
const sidebarOverlay = document.getElementById("sidebarOverlay");

function fecharSidebarMobile() {
    sidebarEl?.classList.remove("mobile-open");
    sidebarOverlay?.classList.remove("visible");
}

hamburgerBtn?.addEventListener("click", () => {
    sidebarEl?.classList.toggle("mobile-open");
    sidebarOverlay?.classList.toggle("visible");
});

sidebarOverlay?.addEventListener("click", fecharSidebarMobile);

// fecha o menu automaticamente se a tela for redimensionada para desktop
window.addEventListener("resize", () => {
    if (window.innerWidth > 768) fecharSidebarMobile();
});
