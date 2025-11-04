# main.py
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context
from pathlib import Path

app = FastAPI(title="Recette FR/JP")

# Montage des fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuration des templates
TEMPLATES_DIR = str((Path(__file__).resolve().parent / "app" / "templates"))
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Dictionnaire de traductions complet
TRANSLATIONS = {
    "fr": {
        "recipes": "Recettes",
        "all": "Toutes les recettes",
        "import": "Importer",
        "back": "Retour",
        "type": "Type",
        "servings": "Convives",
        "tags": "Tags",
        "ingredients": "Ingrédients",
        "steps": "Étapes",
        "source": "Source",
        "lang_fr": "Français",
        "lang_jp": "日本語",
    },
    "jp": {
        "recipes": "レシピ一覧",
        "all": "全てのレシピ",
        "import": "インポート",
        "back": "戻る",
        "type": "タイプ",
        "servings": "人数",
        "tags": "タグ",
        "ingredients": "材料",
        "steps": "手順",
        "source": "ソース",
        "lang_fr": "Français",
        "lang_jp": "日本語",
    },
}

@pass_context
def S(ctx, key: str):
    """Fonction de traduction pour les templates"""
    lang = ctx.get("lang", "fr")
    return TRANSLATIONS.get(lang, {}).get(key, key)

templates.env.globals["S"] = S

# Import et montage des routes
from app.routes.recipe_routes import router as recipe_router
app.include_router(recipe_router)

# Page d'accueil : redirection vers la liste des recettes
@app.get("/")
async def root():
    return RedirectResponse(url="/recipes?lang=fr")