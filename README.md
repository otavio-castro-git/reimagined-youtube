# reimagined-youtube

Otavio Martins,
Rafael Leite da Silva Francisco, 
Miguel Isaias Ledesma Araujo, 
Murilo Santos Barbosa,
Pedro henrique da Silva Bernado.

Professora, boa noite, tudo bem? então, abrir o projeto na sua maquina talvez nn seja tão facil, então deixei aqui um mini tutorial que eu acho necessario,

# ViewTube — Como Rodar o Projeto

## Requisitos

Instale os programas abaixo antes de começar:

- **Python 3.12** — https://www.python.org/downloads/
  - Durante a instalação, marque "Add Python to PATH"
- **MySQL 8.0** — https://dev.mysql.com/downloads/installer/
  - Escolha "Server Only" ou "Developer Default"
  - Anote a senha do root que você definir

---

## Passo a Passo

### 1. Abrir o terminal na pasta do projeto

No VS Code, abra a pasta do projeto e o terminal integrado (Ctrl + ').

Entre na pasta correta:

    cd viewtube

### 2. Criar o banco de dados

Conecte ao MySQL:

    mysql -u root -p

Digite sua senha quando pedido. Depois:

    CREATE DATABASE viewtube;
    EXIT;

### 3. Importar o banco de dados

    cmd /c "mysql -u root -p viewtube < viewtube.sql"

### 4. Criar o usuário padrão no banco

    mysql -u root -pSUA_SENHA viewtube -e "INSERT INTO users (id, username, email, password_hash) VALUES (1, 'admin', 'admin@viewtube.com', 'admin');"

Substitua SUA_SENHA pela sua senha do MySQL.

### 5. Configurar o arquivo .env

Copie o arquivo de exemplo:

    copy .env.example .env

Abra o .env e preencha com seus dados:

    DB_HOST=localhost
    DB_PORT=3306
    DB_USER=root
    DB_PASSWORD=sua_senha_aqui
    DB_NAME=viewtube

### 6. Instalar as dependências

    pip install -r requirements.txt

### 7. Rodar o projeto

    python app.py

Acesse no navegador: http://127.0.0.1:5000

---

## Problemas Comuns

| Problema | Solução |
|---|---|
| mysql nao reconhecido | Adicione ao PATH: C:\Program Files\MySQL\MySQL Server 8.0\bin |
| python nao reconhecido | Reinstale o Python marcando "Add to PATH" |
| Erro de conexao com banco | Verifique se o MySQL esta rodando: net start mysql80 (como administrador) |
| Erro 500 ao publicar | Verifique se o passo 4 foi executado |

---

## Observacoes

O banco de dados roda localmente em cada maquina. Cada pessoa que rodar o projeto
tera sua propria instancia do banco, sem compartilhamento de dados entre maquinas.

Na proxima versao do projeto, o banco de dados sera migrado para um servidor remoto,
permitindo que todos os usuarios acessem os mesmos dados independente da maquina.