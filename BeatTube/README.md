# BeatTube — Setup Completo

## Estrutura do Projeto

```
beattube/
├── app/
│   ├── __init__.py          # Factory Flask
│   ├── config.py            # Configurações
│   ├── models.py            # SQLAlchemy (espelha o .sql)
│   ├── routes/
│   │   ├── auth.py          # Login, Cadastro, Google OAuth
│   │   ├── home.py          # Página principal
│   │   ├── music.py         # Músicas, álbuns, artistas, tendências
│   │   ├── playlist.py      # Playlists
│   │   └── history.py       # Histórico
│   ├── static/
│   │   ├── css/             # Copie seus arquivos style.css, style2.css etc.
│   │   ├── js/              # auth.js (gerado) + seus scripts
│   │   └── img/             # Copie banner.jpg, capa.jpeg, beattube_logo.png, bruno.jpeg
│   └── templates/           # HTMLs Jinja2
│       ├── base.html        # Layout base (header + sidebar + modais)
│       ├── index.html
│       ├── historico.html
│       └── ... (criar os demais)
├── .env.example             # Modelo de configuração
├── requirements.txt
└── run.py                   # Iniciar o servidor
```

---

## 1. Pré-requisitos

### Python e dependências
```bash
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### Driver ODBC para Azure SQL
**Ubuntu/Debian:**
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt update
sudo ACCEPT_EULA=Y apt install -y msodbcsql18 unixodbc-dev
```

**Windows:** baixe em https://aka.ms/downloadmsodbcsql

---

## 2. Configurar o banco Azure SQL

### No portal Azure:
1. Acesse **Azure SQL Database** → seu banco → **Connection strings**
2. Copie os dados: servidor, banco, usuário, senha
3. Em **Networking**: ative "Allow Azure services" e adicione seu IP

### Arquivo .env (copie de .env.example):
```env
SECRET_KEY=coloque-algo-aleatorio-aqui
DB_SERVER=seu-servidor.database.windows.net
DB_NAME=beattube
DB_USER=seu-usuario
DB_PASSWORD=sua-senha
DB_DRIVER=ODBC Driver 18 for SQL Server
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
BASE_URL=http://localhost:5000
```

### Criar as tabelas (rodar o SQL já existente):
Use o Azure Data Studio, DBeaver, ou o portal Azure Query Editor:
```sql
-- Cole o conteúdo de beattube_final.sql e execute
```

**Nota:** o `google_id` precisa ser adicionado manualmente à tabela `shared.users`:
```sql
ALTER TABLE shared.users ADD google_id NVARCHAR(255) NULL UNIQUE;
```

---

## 3. Configurar Google OAuth

1. Acesse https://console.cloud.google.com
2. Crie um projeto → **APIs & Services** → **Credentials**
3. Crie **OAuth 2.0 Client ID** (tipo: Web application)
4. Em **Authorized redirect URIs**, adicione:
   - `http://localhost:5000/auth/google/callback` (desenvolvimento)
   - `https://seu-dominio.com/auth/google/callback` (produção)
5. Copie Client ID e Client Secret para o `.env`

---

## 4. Copiar arquivos estáticos

```bash
# Imagens
cp banner.jpg  app/static/img/
cp capa.jpeg   app/static/img/
cp bruno.jpeg  app/static/img/
cp beattube_logo.png app/static/img/
cp playlist1.jpg app/static/img/
cp playlist2.jpg app/static/img/

# CSS
cp style.css           app/static/css/
cp style2.css          app/static/css/
cp style3.css          app/static/css/
cp historico_style.css app/static/css/
```

---

## 5. Rodar o servidor

```bash
python run.py
```

Acesse: http://localhost:5000

---

## 6. Templates ainda a criar

Baseie-se em `base.html` e use `{% extends "base.html" %}`:

| Arquivo             | Rota                      |
|---------------------|---------------------------|
| `music.html`        | `/musica/<id>`            |
| `tendencias.html`   | `/tendencias`             |
| `playlist.html`     | `/playlists`              |
| `artist.html`       | `/artista/<id>`           |

---

## 7. Deploy no Azure App Service (opcional)

```bash
# Instale Azure CLI
az login
az webapp up --name beattube-app --resource-group meu-rg --runtime "PYTHON:3.11"

# Configure as variáveis de ambiente no App Service → Configuration
```
