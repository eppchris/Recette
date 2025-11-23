# init_db.py
from app import create_app
from app.models.db import BaseModel, get_engine

# Import des modèles pour qu'ils soient connus de SQLAlchemy avant create_all
from app.models import recipe  # noqa: F401

def main() -> None:
    app = create_app()
    engine = get_engine()
    assert engine is not None, "Engine non configuré"
    with app.app_context():
        BaseModel.metadata.create_all(bind=engine)
        print("✅ Tables créées dans SQLite (data/recette_dev.sqlite3)")

if __name__ == "__main__":
    main()
