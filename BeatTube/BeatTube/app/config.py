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

    # Google OAuth
    GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # Em desenvolvimento, permite OAuth sem HTTPS
    OAUTHLIB_INSECURE_TRANSPORT = os.getenv("FLASK_ENV") == "development"
