# app/routes/recipe_routes.py
from fastapi import APIRouter, Request, Query, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context
from pathlib import Path
import tempfile
import shutil
import os

from app.models import db
from app.services.recipe_importer import import_recipe_from_csv

router = APIRouter()

# Configuration des templates
TEMPLATES_DIR = str((Path(__file__).resolve().parents[1] / "templates"))
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Dictionnaire de traductions COMPLET
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
        "menu_recipes": "Recettes",
        "menu_events": "Événements",
        "menu_settings": "Gestion",
        "all_recipes": "Toutes les recettes",
        "import_recipe": "Importer",
        "coming_soon": "Bientôt",
        "dark_mode": "Mode nuit",
        "light_mode": "Mode jour",
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
        "menu_recipes": "レシピ",
        "menu_events": "イベント",
        "menu_settings": "設定",
        "all_recipes": "全てのレシピ",
        "import_recipe": "インポート",
        "coming_soon": "近日公開",
        "dark_mode": "ダークモード",
        "light_mode": "ライトモード",
    },
}

@pass_context
def S(ctx, key: str):
    """Fonction de traduction pour les templates"""
    lang = ctx.get("lang", "fr")
    return TRANSLATIONS.get(lang, {}).get(key, key)

templates.env.globals["S"] = S

# --------------------------------------------------------------------
# Liste des recettes
# --------------------------------------------------------------------
@router.get("/recipes", response_class=HTMLResponse)
async def recipes_list(request: Request, lang: str = Query("fr")):
    """Affiche la liste de toutes les recettes dans la langue demandée"""
    rows = db.list_recipes(lang)
    return templates.TemplateResponse(
        "recipes_list.html",
        {"request": request, "lang": lang, "rows": rows}
    )

# --------------------------------------------------------------------
# Détail d'une recette
# --------------------------------------------------------------------
@router.get("/recipe/{slug}", response_class=HTMLResponse)
async def recipe_detail(request: Request, slug: str, lang: str = Query("fr")):
    """Affiche le détail d'une recette"""
    result = db.get_recipe_by_slug(slug, lang)
    
    if not result:
        return templates.TemplateResponse(
            "not_found.html",
            {"request": request, "lang": lang, "message": f"Recette '{slug}' introuvable"},
            status_code=404,
        )
    
    rec, ings, steps = result
    
    return templates.TemplateResponse(
        "recipe_detail.html",
        {"request": request, "lang": lang, "rec": rec, "ings": ings, "steps": steps}
    )

# --------------------------------------------------------------------
# Fenêtre d'import CSV
# --------------------------------------------------------------------
@router.get("/import", response_class=HTMLResponse)
async def import_form(request: Request, lang: str = Query("fr")):
    """Affiche le formulaire d'import"""
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
    """Traite l'upload et l'import d'un fichier CSV"""
    temp_file = None
    tmp_path = None
    
    try:
        temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False)
        tmp_path = temp_file.name
        
        shutil.copyfileobj(file.file, temp_file)
        temp_file.close()
        
        import_recipe_from_csv(tmp_path)
        message = f"✅ Fichier « {file.filename} » importé avec succès."
        
    except Exception as e:
        message = f"❌ Erreur pendant l'import : {str(e)}"
        
    finally:
        if temp_file and not temp_file.closed:
            temp_file.close()
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
    
    return templates.TemplateResponse(
        "import_recipes.html",
        {"request": request, "lang": lang, "message": message}
    )