# app/routes/recipe_routes.py
from fastapi import APIRouter, Request, Query, UploadFile, File
from fastapi.responses import HTMLResponse
import tempfile, shutil, os
from pathlib import Path
from fastapi.templating import Jinja2Templates

from app.models import db  # doit exposer list_recipes(lang) et get_recipe_by_slug(slug, lang)
from app.services.recipe_importer import import_recipe_from_csv

router = APIRouter()

# chemin absolu vers app/templates
TEMPLATES_DIR = str((Path(__file__).resolve().parents[1] / "templates"))
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# --- ajouter S() dans CETTE instance de Jinja ---
from jinja2 import pass_context

@pass_context
def S(ctx, key: str):
    lang = ctx.get("lang", "fr")
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
# --- fin ajout ---

# --------------------------------------------------------------------
# Liste des recettes (bascule FR/JA via ?lang=fr|ja)
# --------------------------------------------------------------------
@router.get("/recipes", response_class=HTMLResponse)
async def recipes(request: Request, lang: str = Query("fr")):
    rows = db.list_recipes(lang)  # renvoie les lignes pour la langue demandée
    return templates.TemplateResponse(
        "recipes_list.html",
        {"request": request, "lang": lang, "rows": rows}
    )

# --------------------------------------------------------------------
# Détail d'une recette par slug/uid
# URL: /recipe/{slug}?lang=fr
# --------------------------------------------------------------------
@router.get("/recipe/{slug}", response_class=HTMLResponse)
async def recipe_detail(request: Request, slug: str, lang: str = Query("fr")):
    rec = db.get_recipe_by_slug(slug, lang)  # doit renvoyer titre, ingrédients et étapes localisés
    if not rec:
        return templates.TemplateResponse(
            "not_found.html",  # mets un template simple "introuvable", ou remplace par recipes_list
            {"request": request, "lang": lang, "slug": slug},
            status_code=404,
        )
    return templates.TemplateResponse(
        "recipe_detail.html",
        {"request": request, "lang": lang, "recipe": rec}
    )

# --------------------------------------------------------------------
# Fenêtre d'import CSV
# --------------------------------------------------------------------
@router.get("/import", response_class=HTMLResponse)
async def import_form(request: Request, lang: str = Query("fr")):
    # Réutilise ton template existant import_recipes.html
    return templates.TemplateResponse(
        "import_recipes.html",
        {"request": request, "lang": lang, "message": None}
    )

@router.post("/import", response_class=HTMLResponse)
async def import_post(
    request: Request,
    file: UploadFile = File(...),
    lang: str = Query("fr")
):
    # Enregistre temporairement le CSV uploadé
    tmp_path = tempfile.mktemp(suffix=".csv")
    with open(tmp_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    # Lance l'import
    try:
        import_recipe_from_csv(tmp_path)
        message = f"✅ Fichier « {file.filename} » importé avec succès."
    except Exception as e:
        message = f"❌ Erreur pendant l'import : {e}"
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

    # Réaffiche la fenêtre d'import avec le message
    return templates.TemplateResponse(
        "import_recipes.html",
        {"request": request, "lang": lang, "message": message}
    )
