from pathlib import Path

class DevConfig:
    DEBUG: bool = True
    TESTING: bool = False
    SECRET_KEY: str = "dev-secret-key-change-me"
    BASE_DIR: Path = Path(__file__).resolve().parent
    DATA_DIR: Path = BASE_DIR / "data"
    DATA_DIR.mkdir(exist_ok=True)  # s'assure que /data existe en DEV

    # Base SQLite (DEV)
    DATABASE_URL: str = f"sqlite:///{(DATA_DIR / 'recette_dev.sqlite3').as_posix()}"
    SQL_ECHO: bool = False  # Passe à True si tu veux voir les requêtes SQL dans la console
