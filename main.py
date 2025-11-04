# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context
from pathlib import Path

app = FastAPI(title="Recette FR/JA")

# (garde ton mount static existant)
app.mount("/static", StaticFiles(directory="static"), name="static")

# chemin des templates (ajuste si besoin)
TEMPLATES_DIR = str((Path(__file__).resolve().parent / "app" / "templates"))
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# --- >>> AJOUT pour la traduction S() <<< ---
@pass_context
def S(ctx, key: str):
    lang = ctx.get("lang", "fr")  # récupère la variable `lang` passée au template
    texts = {
        "fr": {
            "recipes": "Recettes",
            "import": "Importer",
            "back": "Retour",
        },
        "ja": {
            "recipes": "レシピ一覧",
            "import": "インポート",
            "back": "戻る",
        },
    }
    return texts.get(lang, {}).get(key, key)

templates.env.globals["S"] = S
# --- <<< FIN AJOUT ---

# importe et monte tes routes après la création de `templates`
from app.routes.recipe_routes import router as recipe_router
app.include_router(recipe_router)

# (garde ton endpoint "/" qui redirige vers /recipes?lang=fr)
