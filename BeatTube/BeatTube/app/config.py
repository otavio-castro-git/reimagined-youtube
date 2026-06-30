import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-mude-em-producao")

    # Azure SQL via pyodbc
    _server   = os.getenv("DB_SERVER", "")
    _db       = os.getenv("DB_NAME", "beattube")
    _user     = os.getenv("DB_USER", "")
    _password = os.getenv("DB_PASSWORD", "")
    _driver   = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")

    SQLALCHEMY_DATABASE_URI = (
        f"mssql+pyodbc:///?odbc_connect="
        f"Driver={{{_driver}}};"
        f"Server=tcp:{_server},1433;"
        f"Database={_db};"
        f"Uid={_user};"
        f"Pwd={_password};"
        f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Evita usar conexões "mortas" do pool (comum no Azure SQL Serverless,
    # que pausa/derruba conexões ociosas e causa o erro
    # "TCP Provider: Error code 0x68 / Connection reset by peer").
    # pool_pre_ping testa a conexão antes de cada uso e reconecta se preciso.
    # pool_recycle descarta conexões com mais de 280s (antes do Azure cortar por idle).
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    # Google OAuth
    GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # Em desenvolvimento, permite OAuth sem HTTPS
    OAUTHLIB_INSECURE_TRANSPORT = os.getenv("FLASK_ENV") == "development"

    # Google reCAPTCHA v3 (invisível)
    # Crie em https://www.google.com/recaptcha/admin
    RECAPTCHA_SITE_KEY   = os.getenv("RECAPTCHA_SITE_KEY", "")
    RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY", "")
    # Nota mínima (0.0 a 1.0) para considerar a ação "humana". 0.5 é o recomendado pelo Google.
    RECAPTCHA_MIN_SCORE  = float(os.getenv("RECAPTCHA_MIN_SCORE", "0.5"))

    # Email (Gmail SMTP) — usado para enviar o código de verificação no cadastro
    MAIL_SERVER   = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT     = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS  = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    # Use uma "senha de app" do Gmail (não a senha normal da conta).
    # Gere em: https://myaccount.google.com/apppasswords
    MAIL_PASSWORD     = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", os.getenv("MAIL_USERNAME", ""))
