# reimagined-youtube

Projeto desenvolvido por:

- Otavio Martins
- Rafael Leite da Silva Francisco
- Miguel Isaias Ledesma Araujo
- Murilo Santos Barbosa
- Pedro Henrique da Silva Bernardo

---

## Sobre o projeto

Este repositório contém dois projetos web desenvolvidos em Flask:

**ViewTube** — plataforma de vídeos com upload, canais, playlists, histórico, curtidas e sistema de inscrições. Banco de dados: Azure SQL Server.

**BeatTube** — plataforma voltada a música, com funcionalidades similares ao ViewTube. Banco de dados: Azure SQL Server. Armazenamento de arquivos: Azure Blob Storage.

---

## Estrutura de pastas

```
viewtube/
├── app/
│   ├── routes/       # Rotas da aplicação (blueprints)
│   ├── static/       # CSS, JS e imagens
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   ├── templates/    # HTMLs (Jinja2)
│   ├── __init__.py
│   └── models.py
├── .env.example
├── requirements.txt
└── run.py

beattube/
├── app/
│   ├── routes/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   ├── templates/
│   ├── __init__.py
│   └── models.py
├── .env.example
├── requirements.txt
└── run.py
```

---

## Requisitos

Antes de começar, instale:

- **Python 3.12** — https://www.python.org/downloads/
  Na instalação, marque **"Add Python to PATH"** antes de clicar em Install.

- **Driver ODBC para Azure SQL** — https://aka.ms/downloadmsodbcsql
  Baixe o arquivo **x64** e instale normalmente (next → next → finish).

---

## Como rodar (ViewTube e BeatTube seguem o mesmo processo)

### 1. Extrair o ZIP

Extraia em algum lugar fácil, como `C:\ViewTube` ou `C:\BeatTube`.

### 2. Abrir o terminal na pasta do projeto

Abra a pasta `viewtube` (ou `beattube`) no Explorer, clique na barra de endereço, digite `cmd` e pressione Enter.

Ou no VS Code, abra a pasta e use o terminal integrado com `Ctrl + '`.

### 3. Criar o ambiente virtual

```
python -m venv venv
```

### 4. Ativar o ambiente virtual

```
venv\Scripts\activate
```

O terminal vai mostrar `(venv)` no início quando ativado corretamente.

### 5. Instalar as dependências

```
python -m pip install -r requirements.txt
```

Instale também os pacotes adicionais:

```
pip install pillow
pip install azure-storage-blob
```

### 6. Configurar o .env

Dentro da pasta do projeto tem um arquivo `.env.example`. Copie ele e renomeie a cópia para `.env` (sem o `.example`):

```
copy .env.example .env
```

Abra o `.env` com o Bloco de Notas e preencha com as credenciais do Azure SQL, Azure Blob Storage e Google OAuth que serão fornecidas separadamente.

O arquivo tem este formato:

```
SECRET_KEY=
FLASK_ENV=development
FLASK_DEBUG=1

DB_SERVER=seu-servidor.database.windows.net
DB_NAME=nome-do-banco
DB_USER=seu-usuario
DB_PASSWORD=sua-senha
DB_DRIVER=ODBC Driver 18 for SQL Server

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

BASE_URL=http://localhost:5000

# Apenas BeatTube:
AZURE_STORAGE_CONNECTION_STRING=
AZURE_CONTAINER_VIDEOS=videos
AZURE_CONTAINER_THUMBNAILS=thumbnails
```

**Nunca suba o `.env` para o repositório.**

### 7. Rodar

```
python run.py
```

Acesse no navegador: **http://localhost:5000** (ViewTube roda na porta 5001 se ambos estiverem ativos ao mesmo tempo)

---

## Problemas comuns

| Problema | Solução |
|---|---|
| `python` não reconhecido | Reinstale o Python marcando "Add to PATH" |
| `pip` não reconhecido | Rode `python -m pip` no lugar de `pip` |
| Erro de conexão com o banco | Confirme que o `.env` está preenchido corretamente e que o servidor Azure está acessível |
| Erro no driver ODBC | Verifique se instalou o driver x64 corretamente |
| Porta já em uso | Mude a porta no `run.py` ou encerre o processo que está usando |

---

## Observações

O banco de dados fica em um servidor remoto no Azure, então todos que rodarem o projeto com as mesmas credenciais acessam os mesmos dados. Cada pessoa configura o `.env` localmente com as credenciais fornecidas — sem isso o projeto não conecta.