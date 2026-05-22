# ViewTube — Flask + MySQL

Plataforma de vídeos conectada ao banco de dados MySQL.

## Estrutura do Projeto

```
viewtube/
├── app.py                  # Backend Flask (rotas, queries MySQL)
├── requirements.txt        # Dependências Python
├── .env.example            # Exemplo de variáveis de ambiente
├── templates/
│   └── index.html          # HTML principal (Jinja2)
└── static/
    ├── css/
    │   └── style.css       # Todos os estilos
    └── js/
        └── main.js         # Toda a lógica frontend
```

## Como rodar

### 1. Configurar o banco de dados

Importe o schema no MySQL:
```bash
mysql -u root -p < viewtube.sql
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Edite .env com suas credenciais MySQL
```

### 3. Instalar dependências Python

```bash
pip install -r requirements.txt
```

### 4. Rodar o servidor

```bash
python app.py
```

Acesse: **http://localhost:5000**

---

## API Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/videos` | Lista vídeos (filtro por `?tag=`) |
| GET | `/api/videos/trending` | Top 8 em alta |
| GET | `/api/videos/search?q=` | Busca por título/canal |
| POST | `/api/videos/<id>/like` | Curtir/descurtir |
| POST | `/api/videos/<id>/watch` | Registrar visualização |
| POST | `/api/videos/upload` | Enviar novo vídeo |
| GET | `/api/channels` | Lista canais |
| GET | `/api/channels/<id>/videos` | Vídeos de um canal |
| POST | `/api/channels/<id>/subscribe` | Inscrever/desinscrever |
| GET | `/api/playlists` | Playlists do usuário |
| POST | `/api/playlists` | Criar playlist |
| GET | `/api/history` | Histórico de assistidos |
| GET | `/api/liked` | Vídeos curtidos |
| GET | `/api/tags` | Tags disponíveis |
| GET | `/api/db/tables` | Tabelas do banco |
| POST | `/api/db/query` | Executar SELECT (explorer) |
| GET | `/api/db/schema/<table>` | Schema de uma tabela |
| GET | `/api/stats` | Estatísticas gerais |

> O explorer de banco de dados aceita apenas SELECT, SHOW e DESCRIBE por segurança.
