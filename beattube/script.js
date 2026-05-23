const loginBtn        = document.querySelector(".login-btn");
        const modalLogin      = document.getElementById("modalLogin");
        const modalCadastro   = document.getElementById("modalCadastro");

        // Abre modal de login
        loginBtn.addEventListener("click", () => {
            modalLogin.style.display = "flex";
        });

        // Fecha login pelo botão cancelar
        document.getElementById("fecharModalLogin").addEventListener("click", () => {
            modalLogin.style.display = "none";
        });

        // Fecha cadastro pelo botão cancelar
        document.getElementById("fecharModalCadastro").addEventListener("click", () => {
            modalCadastro.style.display = "none";
        });

        // Troca login → cadastro
        document.getElementById("irParaCadastro").addEventListener("click", (e) => {
            e.preventDefault();
            modalLogin.style.display = "none";
            modalCadastro.style.display = "flex";
        });

        // Troca cadastro → login
        document.getElementById("irParaLogin").addEventListener("click", (e) => {
            e.preventDefault();
            modalCadastro.style.display = "none";
            modalLogin.style.display = "flex";
        });

        // Fecha clicando fora
        modalLogin.addEventListener("click", (e) => {
            if (e.target === modalLogin) modalLogin.style.display = "none";
        });

        modalCadastro.addEventListener("click", (e) => {
            if (e.target === modalCadastro) modalCadastro.style.display = "none";
        });