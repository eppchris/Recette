# config.py
"""Configuration unifiée pour tous les environnements"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()


class Config:
    """Configuration unifiée - valeurs chargées depuis variables d'environnement"""

    # Environnement
    ENV = os.getenv("ENV", "dev")  # dev ou prod
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

    # Chemins
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / "data"
    DATA_DIR.mkdir(exist_ok=True)

    # Base de données (nom unifié)
    DB_PATH = str(DATA_DIR / "recette.sqlite3")
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    SQL_ECHO = False

    # Serveur
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "8000"))
    WORKERS = int(os.getenv("WORKERS", "1"))

    # Sécurité
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    REQUIRE_PASSWORD = os.getenv("REQUIRE_PASSWORD", "False").lower() == "true"
    SHARED_PASSWORD = os.getenv("SHARED_PASSWORD", "")

    # API externe
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

    # Logs
    LOG_LEVEL = os.getenv("LOG_LEVEL", "info" if ENV == "prod" else "debug")
    LOG_PATH = os.getenv("LOG_PATH", str(BASE_DIR / "logs" / "recette.log"))


# Créer les répertoires nécessaires
os.makedirs(os.path.dirname(Config.LOG_PATH), exist_ok=True)
os.makedirs(Config.DATA_DIR, exist_ok=True)
