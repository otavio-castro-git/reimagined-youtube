# Reimagined YouTube — BeatTube + ViewTube

Repositório: https://github.com/otavio-castro-git/reimagined-youtube

**Demos no ar:**
- ViewTube → https://view-tube.online
- BeatTube → https://beat-tube.online

Este projeto reúne **duas aplicações web independentes**, construídas em Flask, que recriam — cada uma sob um conceito diferente — a experiência de uma plataforma de streaming ao estilo YouTube:

- **ViewTube** — um clone focado em **vídeos**: canais, uploads, comentários, inscrições, playlists e histórico de visualização.
- **BeatTube** — um clone focado em **música**: artistas, álbuns, faixas, playlists, "seguir artistas" e histórico de reprodução.

As duas aplicações são projetos separados (pastas e códigos próprios), mas **compartilham o mesmo banco de dados Azure SQL**, com um schema `shared` comum (usuários, assinaturas, pagamentos) e schemas próprios `beattube` e `viewtube` para os dados específicos de cada produto. Isso significa que uma única conta de usuário pode logar nas duas plataformas.

## Visão geral da arquitetura

| | ViewTube | BeatTube |
|---|---|---|
| Domínio | Vídeos / canais | Músicas / artistas |
| Framework | Flask 3 + SQLAlchemy | Flask 3 + SQLAlchemy |
| Autenticação | Login próprio + Google OAuth | Login próprio + Google OAuth |
| Banco | Azure SQL (schema `shared` + `viewtube`) | Azure SQL (schema `shared` + `beattube`) |
| Armazenamento de mídia | Azure Blob Storage (vídeos e thumbnails) | Azure Blob Storage / uploads locais (capas) |
| Porta padrão (dev) | 5001 | 5000 |

Ambas seguem o mesmo padrão de organização interna: `app/` com `models.py`, `config.py`, `routes/` (blueprints), `templates/` (Jinja2) e `static/` (CSS/JS/imagens), inicializadas por uma factory `create_app()` em `app/__init__.py` e executadas via `run.py`.

## Banco de dados

O arquivo `full_schema_beattube_viewtube.sql` contém o **schema completo em T-SQL**, pronto para ser executado do zero em um banco Azure SQL vazio. Ele cria três schemas:

- **`shared`** — tabelas usadas pelas duas plataformas:
  - `users` (conta única, com suporte a login Google via `google_id`)
  - `user_subscriptions` e `payments` (controle de assinatura premium)
  - `user_follows_user` (relação social entre usuários)
- **`beattube`** — domínio musical:
  - `artists`, `genres`, `albums`, `songs`
  - tabelas de junção N:N: `song_artists`, `album_songs`, `song_genres`
  - `playlists` e `playlist_songs`
  - `liked_songs`, `liked_albums`, `liked_playlists`
  - `play_history`, `song_uploads`, `user_follows_artist`, `search_history`
- **`viewtube`** — domínio de vídeo:
  - `channels`, `videos`, `tags`, `video_tags`
  - `video_likes`, `comments`, `subscriptions`
  - `playlists`, `playlist_videos`
  - `watch_history`, `search_history`

Para criar o banco, basta executar o script inteiro em um banco novo (via Query Editor do portal Azure, Azure Data Studio ou `sqlcmd`).

## ViewTube — funcionalidades

- Cadastro/login (e-mail + senha, com verificação por código enviado por e-mail) e login social com Google.
- Criação e gerenciamento de **canais** (nome, descrição, imagem de perfil e banner).
- **Upload de vídeos** para Azure Blob Storage, com thumbnail, título, descrição e tags.
- Página de exibição (`watch`) com player, contagem de visualizações, curtidas e **comentários**.
- **Inscrições** em canais, com listagem de canais inscritos na sidebar.
- **Playlists** de vídeo, vídeos curtidos (`curtidos`), histórico de exibição (`historico`) e página de **tendências**.
- Busca de vídeos/canais com histórico de pesquisa salvo.
- Proteção de upload por reCAPTCHA v3 (invisível) e bloqueio de upload para contas não verificadas.

Principais blueprints (`app/routes/`): `auth`, `home`, `video`, `channel`, `upload`, `api`.

## BeatTube — funcionalidades

- Cadastro/login (e-mail + senha, com verificação por código) e login social com Google (via Flask-Dance).
- Catálogo de **artistas**, **álbuns** e **músicas**, organizados por gêneros.
- **Upload de faixas**, com capa e metadados.
- **Playlists** de música, criação e edição, com capa de playlist.
- **Seguir artistas** (`seguindo`) e ver atualizações dos artistas seguidos.
- **Histórico de reprodução** (`historico`) e página de **tendências**.
- Curtidas de músicas, álbuns e playlists.
- Proteção por reCAPTCHA v3 e envio de e-mails de verificação via SMTP (Gmail).

Principais blueprints (`app/routes/`): `auth`, `home`, `music`, `playlist`, `history`, `upload`, `seguindo`.

## Stack técnica

- **Backend**: Python 3 / Flask 3.0, Flask-SQLAlchemy, Flask-Login, SQLAlchemy 2.0
- **Banco de dados**: Azure SQL Server (via `pyodbc` + ODBC Driver 18)
- **Autenticação social**: Flask-Dance (Google OAuth) — usado no BeatTube
- **Armazenamento de arquivos**: Azure Blob Storage (`azure-storage-blob`)
- **Imagens**: Pillow (BeatTube, para processamento de capas)
- **E-mail**: SMTP (Gmail) para envio de códigos de verificação de cadastro
- **Anti-bot**: Google reCAPTCHA v3 (invisível)
- **Servidor WSGI (produção)**: Gunicorn
- **Frontend**: Jinja2 + CSS/JS estático (sem framework JS pesado)

## Estrutura de pastas

```
reimagined-youtube/
├── BeatTube/
│   ├── app/
│   │   ├── __init__.py        # factory create_app()
│   │   ├── config.py          # configurações e variáveis de ambiente
│   │   ├── models.py          # modelos SQLAlchemy (shared + beattube)
│   │   ├── email_utils.py     # envio de e-mails de verificação
│   │   ├── captcha_utils.py   # validação do reCAPTCHA v3
│   │   ├── routes/            # blueprints (auth, home, music, playlist, history, upload, seguindo)
│   │   ├── templates/         # páginas Jinja2
│   │   └── static/            # css, js, imagens, uploads
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
│
├── ViewTube/
│   ├── app/
│   │   ├── __init__.py        # factory create_app()
│   │   ├── config.py
│   │   ├── models.py          # modelos SQLAlchemy (shared + viewtube)
│   │   ├── email_utils.py
│   │   ├── captcha_utils.py
│   │   ├── routes/            # blueprints (auth, home, video, channel, upload, api)
│   │   ├── templates/
│   │   └── static/
│   ├── requirements.txt
│   ├── .deployment            # configuração de deploy (Azure App Service)
│   └── run.py
│
└── full_schema_beattube_viewtube.sql   # schema completo do banco (shared + beattube + viewtube)
```

## Como rodar localmente

Cada aplicação é independente e roda em sua própria porta, mas as duas apontam para o **mesmo banco Azure SQL** (schemas diferentes).

### Pré-requisitos

- Python 3.10+
- Driver ODBC 18 para SQL Server instalado (`unixodbc-dev` + driver da Microsoft)
- Uma instância Azure SQL com o schema criado a partir de `full_schema_beattube_viewtube.sql`
- (Opcional) Conta de armazenamento Azure Blob, para upload de mídia
- (Opcional) Credenciais OAuth do Google e chaves de reCAPTCHA v3

### 1. Banco de dados

Execute o script `full_schema_beattube_viewtube.sql` inteiro em um banco Azure SQL novo e vazio (Query Editor do portal Azure, Azure Data Studio ou `sqlcmd`).

### 2. ViewTube

```bash
cd ViewTube
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # preencha DB_*, AZURE_STORAGE_*, GOOGLE_*, RECAPTCHA_*, MAIL_*
python run.py          # roda em http://localhost:5001
```

### 3. BeatTube

```bash
cd BeatTube
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # preencha DB_*, GOOGLE_*, RECAPTCHA_*, MAIL_*
python run.py          # roda em http://localhost:5000
```

### Variáveis de ambiente principais

| Variável | Descrição |
|---|---|
| `SECRET_KEY` | chave secreta do Flask |
| `DB_SERVER`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_DRIVER` | conexão com o Azure SQL |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | OAuth do Google |
| `RECAPTCHA_SITE_KEY`, `RECAPTCHA_SECRET_KEY`, `RECAPTCHA_MIN_SCORE` | reCAPTCHA v3 |
| `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER` | envio de e-mail (código de verificação) |
| `AZURE_STORAGE_CONNECTION_STRING`, `AZURE_CONTAINER_VIDEOS`, `AZURE_CONTAINER_THUMBNAILS` | armazenamento de mídia (ViewTube) |
| `BASE_URL` | URL base usada nos redirects de OAuth |

> Cada projeto tem seu próprio `.env`, mas `DB_SERVER`, `DB_USER` e `DB_PASSWORD` devem apontar para o mesmo servidor/banco para que o login compartilhado funcione corretamente.

## Deploy

Os projetos foram pensados para deploy em **Azure App Service**, com o `ViewTube` incluindo um arquivo `.deployment` configurando o build automático (`SCM_DO_BUILD_DURING_DEPLOYMENT=true`). Em produção, ambas as aplicações podem ser servidas via **Gunicorn**.

## Conta única entre as plataformas

Como `shared.users` é compartilhada entre BeatTube e ViewTube, o mesmo cadastro (e-mail/senha ou login Google) funciona em ambas as aplicações — incluindo o status de assinatura premium (`shared.user_subscriptions` / `shared.payments`), que é independente do domínio (vídeo ou música) consumido.

## Participantes

Projeto desenvolvido por:

* Otavio Martins
* Rafael Leite da Silva Francisco
* Miguel Isaias Ledesma Araujo
* Murilo Santos Barbosa
* Pedro Henrique da Silva Bernardo