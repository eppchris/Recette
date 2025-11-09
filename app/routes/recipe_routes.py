# app/routes/recipe_routes.py
from fastapi import APIRouter, Request, Query, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context
from pathlib import Path
import tempfile
import shutil
import os

from app.models import db
from app.services.recipe_importer import import_recipe_from_csv
from app.services.translation_service import get_translation_service

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

    # Récupérer les steps avec leurs IDs pour l'édition
    recipe_id = db.get_recipe_id_by_slug(slug)
    steps_with_ids = db.get_recipe_steps_with_ids(recipe_id, lang) if recipe_id else []

    return templates.TemplateResponse(
        "recipe_detail.html",
        {
            "request": request,
            "lang": lang,
            "rec": rec,
            "ings": ings,
            "steps": steps_with_ids  # Utiliser steps_with_ids au lieu de steps
        }
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

# --------------------------------------------------------------------
# API de traduction
# --------------------------------------------------------------------
@router.get("/api/translation/status")
async def translation_api_status():
    """Vérifie le statut de l'API de traduction Groq"""
    service = get_translation_service()

    if not service:
        return JSONResponse({"status": "unavailable", "message": "Service non initialisé"})

    is_operational = service.check_api_status()

    return JSONResponse({
        "status": "operational" if is_operational else "error",
        "message": "API Groq opérationnelle" if is_operational else "API Groq non disponible"
    })


@router.post("/api/translate/{slug}")
async def translate_recipe(slug: str, target_lang: str = Query(...)):
    """Traduit une recette vers une langue cible

    Args:
        slug: Slug de la recette à traduire
        target_lang: Langue cible (fr ou jp)

    Returns:
        JSON avec le statut de la traduction
    """
    service = get_translation_service()

    if not service:
        return JSONResponse(
            {"success": False, "message": "Service de traduction non disponible"},
            status_code=503
        )

    # Vérifier que la recette existe
    recipe_id = db.get_recipe_id_by_slug(slug)
    if not recipe_id:
        return JSONResponse(
            {"success": False, "message": f"Recette '{slug}' introuvable"},
            status_code=404
        )

    # Vérifier si la traduction existe déjà
    if db.check_translation_exists(recipe_id, target_lang):
        return JSONResponse(
            {"success": False, "message": f"La traduction existe déjà en {target_lang}"},
            status_code=400
        )

    # Déterminer la langue source
    source_lang = db.get_source_language(recipe_id)
    if not source_lang:
        return JSONResponse(
            {"success": False, "message": "Aucune langue source trouvée pour cette recette"},
            status_code=400
        )

    # Récupérer la recette dans la langue source
    recipe, ingredients, steps = db.get_recipe_by_slug(slug, source_lang)

    # Récupérer les étapes avec leurs IDs
    steps_with_ids = db.get_recipe_steps_with_ids(recipe_id, source_lang)

    try:
        # Traduire le titre
        translated_title = service.translate_recipe_title(
            recipe['name'],
            source_lang,
            target_lang
        )

        if not translated_title:
            return JSONResponse(
                {"success": False, "message": "Erreur lors de la traduction du titre"},
                status_code=500
            )

        # Préparer les ingrédients pour la traduction
        ingredients_to_translate = [
            {'name': ing['name'], 'unit': ing['unit']}
            for ing in ingredients
        ]

        # Traduire les ingrédients
        translated_ingredients = service.translate_ingredients(
            ingredients_to_translate,
            source_lang,
            target_lang
        )

        if translated_ingredients is None:
            return JSONResponse(
                {"success": False, "message": "Erreur lors de la traduction des ingrédients"},
                status_code=500
            )

        # Préparer les étapes pour la traduction
        steps_to_translate = [step['text'] for step in steps_with_ids]

        # Traduire les étapes
        translated_steps = service.translate_steps(
            steps_to_translate,
            source_lang,
            target_lang
        )

        if translated_steps is None:
            return JSONResponse(
                {"success": False, "message": "Erreur lors de la traduction des étapes"},
                status_code=500
            )

        # Insérer la traduction de la recette
        db.insert_recipe_translation(
            recipe_id,
            target_lang,
            translated_title,
            recipe['type']  # Copie du type
        )

        # Insérer les traductions des ingrédients
        for i, ing in enumerate(ingredients):
            db.insert_ingredient_translation(
                ing['id'],
                target_lang,
                translated_ingredients[i]['name'],
                translated_ingredients[i]['unit']
            )

        # Insérer les traductions des étapes
        for i, step in enumerate(steps_with_ids):
            db.insert_step_translation(
                step['id'],
                target_lang,
                translated_steps[i]
            )

        return JSONResponse({
            "success": True,
            "message": f"Recette traduite avec succès en {target_lang}",
            "translated_title": translated_title,
            "translated_ingredients_count": len(translated_ingredients),
            "translated_steps_count": len(translated_steps)
        })

    except Exception as e:
        print(f"Erreur lors de la traduction: {e}")
        return JSONResponse(
            {"success": False, "message": f"Erreur: {str(e)}"},
            status_code=500
        )

# --------------------------------------------------------------------
# API de modification de recette
# --------------------------------------------------------------------
@router.put("/api/recipe/{slug}")
async def update_recipe(slug: str, request: Request, lang: str = Query(...)):
    """Met à jour les données d'une recette

    Args:
        slug: Slug de la recette à modifier
        lang: Langue des modifications
        request: Données JSON contenant ingredients et steps

    Returns:
        JSON avec le statut de la mise à jour
    """
    # Vérifier que la recette existe
    recipe_id = db.get_recipe_id_by_slug(slug)
    if not recipe_id:
        return JSONResponse(
            {"success": False, "message": f"Recette '{slug}' introuvable"},
            status_code=404
        )

    try:
        data = await request.json()
        ingredients = data.get('ingredients', [])
        steps = data.get('steps', [])

        # Mettre à jour les ingrédients
        for ing in ingredients:
            # Mettre à jour la quantité (indépendante de la langue)
            if 'quantity' in ing:
                db.update_ingredient_quantity(ing['id'], ing['quantity'])

            # Mettre à jour la traduction (nom, unité, notes)
            if 'name' in ing or 'unit' in ing:
                db.update_ingredient_translation(
                    ing['id'],
                    lang,
                    ing.get('name', ''),
                    ing.get('unit', ''),
                    ing.get('notes', '')
                )

        # Mettre à jour les étapes
        for step in steps:
            if 'text' in step:
                db.update_step_translation(
                    step['id'],
                    lang,
                    step['text']
                )

        return JSONResponse({
            "success": True,
            "message": "Recette mise à jour avec succès",
            "updated_ingredients": len(ingredients),
            "updated_steps": len(steps)
        })

    except Exception as e:
        print(f"Erreur lors de la mise à jour de la recette: {e}")
        return JSONResponse(
            {"success": False, "message": f"Erreur: {str(e)}"},
            status_code=500
        )