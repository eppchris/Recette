# app/routes/recipe_routes.py
from fastapi import APIRouter, Request, Query, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Optional
import tempfile
import shutil
import os

from app.models import db
from app.services.recipe_importer import import_recipe_from_csv
from app.services.translation_service import get_translation_service
from app.services.conversion_service import get_conversion_service
from app.services.web_recipe_importer import get_web_recipe_importer
from app.template_config import templates

router = APIRouter()

# --------------------------------------------------------------------
# Liste des recettes
# --------------------------------------------------------------------
@router.get("/recipes", response_class=HTMLResponse)
async def recipes_list(request: Request, lang: str = Query("fr"), creator_id: Optional[str] = Query(None)):
    """Affiche la liste de toutes les recettes dans la langue demandée"""
    # Convertir creator_id en int si ce n'est pas une chaîne vide
    user_id_filter = int(creator_id) if creator_id and creator_id.strip() else None
    rows = db.list_recipes(lang, user_id=user_id_filter)

    # Enrichir chaque recette avec ses catégories, tags et types d'événements
    for recipe in rows:
        recipe['categories'] = db.get_recipe_categories(recipe['id'])
        recipe['tags'] = db.get_recipe_tags(recipe['id'])
        recipe['event_types'] = db.get_recipe_event_types(recipe['id'])

    # Récupérer la liste des utilisateurs pour le filtre
    from app.models import list_users
    users = list_users()

    return templates.TemplateResponse(
        "recipes_list.html",
        {"request": request, "lang": lang, "rows": rows, "users": users, "creator_id": user_id_filter}
    )

# --------------------------------------------------------------------
# Détail d'une recette
# --------------------------------------------------------------------
@router.get("/recipe/{slug}", response_class=HTMLResponse)
async def recipe_detail(request: Request, slug: str, lang: str = Query("fr"), event_id: Optional[int] = Query(None), from_event: Optional[int] = Query(None)):
    """Affiche le détail d'une recette"""
    # Priorité à from_event si fourni, sinon event_id (pour compatibilité)
    event_context = from_event or event_id

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

    # Vérifier si une traduction existe dans la langue actuelle
    has_translation = db.check_translation_exists(recipe_id, lang) if recipe_id else False

    # Récupérer la liste des utilisateurs pour le sélecteur
    all_users = db.list_users()

    return templates.TemplateResponse(
        "recipe_detail.html",
        {
            "request": request,
            "lang": lang,
            "slug": slug,
            "rec": rec,
            "ings": ings,
            "steps": steps_with_ids,  # Utiliser steps_with_ids au lieu de steps
            "has_translation": has_translation,
            "event_id": event_context,
            "all_users": all_users
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

        # Message de succès
        if lang == "fr":
            message = f"✅ {file.filename} importé avec succès"
        else:
            message = f"✅ {file.filename} のインポートに成功しました"

    except Exception as e:
        # Message d'erreur
        if lang == "fr":
            message = f"❌ Erreur lors de l'import : {str(e)}"
        else:
            message = f"❌ インポートエラー: {str(e)}"

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

    # Si la traduction existe déjà, la supprimer pour permettre la retraduction
    if db.check_translation_exists(recipe_id, target_lang):
        db.delete_recipe_language(recipe_id, target_lang)

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
            {'name': ing['name'], 'unit': ing['unit'], 'notes': ing.get('notes', '')}
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

        # Traduire le type de recette
        recipe_type_map = {
            "fr": {
                "PRO": "PRO",
                "MASTER": "MASTER",
                "PERSO": "PERSO",
                "プロ": "PRO",
                "マイスター": "MASTER",
                "じぶん": "PERSO"
            },
            "jp": {
                "PRO": "プロ",
                "MASTER": "マイスター",
                "PERSO": "じぶん",
                "プロ": "プロ",
                "マイスター": "マイスター",
                "じぶん": "じぶん"
            }
        }

        translated_type = recipe_type_map.get(target_lang, {}).get(recipe['type'], recipe['type'])

        # Insérer la traduction de la recette
        db.insert_recipe_translation(
            recipe_id,
            target_lang,
            translated_title,
            translated_type
        )

        # Insérer les traductions des ingrédients
        for i, ing in enumerate(ingredients):
            db.insert_ingredient_translation(
                ing['id'],
                target_lang,
                translated_ingredients[i]['name'],
                translated_ingredients[i]['unit'],
                translated_ingredients[i].get('notes', '')
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

        # Utiliser une seule transaction pour toutes les mises à jour
        db.update_recipe_complete(recipe_id, lang, data)

        return JSONResponse({
            "success": True,
            "message": "Recette mise à jour avec succès",
            "updated_ingredients": len(data.get('ingredients', [])),
            "updated_steps": len(data.get('steps', []))
        })

    except Exception as e:
        print(f"Erreur lors de la mise à jour de la recette: {e}")
        return JSONResponse(
            {"success": False, "message": f"Erreur: {str(e)}"},
            status_code=500
        )


# --------------------------------------------------------------------
# API de suppression de recette
# --------------------------------------------------------------------
@router.delete("/api/recipe/{slug}")
async def delete_recipe(slug: str, lang: str = Query(...)):
    """Supprime une recette et toutes ses données associées

    Args:
        slug: Slug de la recette à supprimer
        lang: Langue (utilisée pour les messages de retour)

    Returns:
        JSON avec le statut de la suppression
    """
    try:
        # Tenter de supprimer la recette
        success = db.delete_recipe(slug)

        if success:
            return JSONResponse({
                "success": True,
                "message": "Recette supprimée avec succès" if lang == 'fr' else "レシピが削除されました"
            })
        else:
            return JSONResponse(
                {
                    "success": False,
                    "message": f"Recette '{slug}' introuvable" if lang == 'fr' else f"レシピ '{slug}' が見つかりません"
                },
                status_code=404
            )

    except Exception as e:
        print(f"Erreur lors de la suppression de la recette: {e}")
        return JSONResponse(
            {
                "success": False,
                "message": f"Erreur: {str(e)}"
            },
            status_code=500
        )


# --------------------------------------------------------------------
# API de gestion des images
# --------------------------------------------------------------------
@router.post("/api/recipe/{slug}/image")
async def upload_recipe_image(slug: str, file: UploadFile = File(...)):
    """
    Upload une image pour une recette

    Args:
        slug: Slug de la recette
        file: Fichier image uploadé

    Returns:
        JSON avec les URLs de l'image et du thumbnail
    """
    from app.services.image_service import save_recipe_image, delete_recipe_image

    # Vérifier que la recette existe
    recipe_id = db.get_recipe_id_by_slug(slug)
    if not recipe_id:
        return JSONResponse(
            {"success": False, "message": f"Recette '{slug}' introuvable"},
            status_code=404
        )

    try:
        # Lire le fichier uploadé
        file_data = await file.read()

        # Récupérer les anciennes URLs pour les supprimer
        old_image_url, old_thumbnail_url = db.get_recipe_image_urls(recipe_id)

        # Sauvegarder la nouvelle image
        image_url, thumbnail_url = save_recipe_image(file_data, file.filename)

        # Mettre à jour la base de données
        db.update_recipe_image(recipe_id, image_url, thumbnail_url)

        # Supprimer les anciennes images si elles existaient
        if old_image_url:
            delete_recipe_image(old_image_url, old_thumbnail_url)

        return JSONResponse({
            "success": True,
            "image_url": image_url,
            "thumbnail_url": thumbnail_url,
            "message": "Image uploadée avec succès"
        })

    except ValueError as e:
        return JSONResponse(
            {"success": False, "message": str(e)},
            status_code=400
        )
    except Exception as e:
        return JSONResponse(
            {"success": False, "message": f"Erreur lors de l'upload: {str(e)}"},
            status_code=500
        )


@router.delete("/api/recipe/{slug}/image")
async def delete_recipe_image_endpoint(slug: str):
    """
    Supprime l'image d'une recette

    Args:
        slug: Slug de la recette

    Returns:
        JSON avec le statut de la suppression
    """
    from app.services.image_service import delete_recipe_image

    # Vérifier que la recette existe
    recipe_id = db.get_recipe_id_by_slug(slug)
    if not recipe_id:
        return JSONResponse(
            {"success": False, "message": f"Recette '{slug}' introuvable"},
            status_code=404
        )

    try:
        # Récupérer les URLs actuelles
        image_url, thumbnail_url = db.get_recipe_image_urls(recipe_id)

        if not image_url:
            return JSONResponse(
                {"success": False, "message": "Aucune image à supprimer"},
                status_code=404
            )

        # Supprimer les fichiers
        delete_recipe_image(image_url, thumbnail_url)

        # Mettre à jour la base de données (NULL)
        db.update_recipe_image(recipe_id, None, None)

        return JSONResponse({
            "success": True,
            "message": "Image supprimée avec succès"
        })

    except Exception as e:
        return JSONResponse(
            {"success": False, "message": f"Erreur lors de la suppression: {str(e)}"},
            status_code=500
        )


# --------------------------------------------------------------------
# API de conversion de recettes
# --------------------------------------------------------------------
@router.post("/api/recipe/{slug}/convert")
async def convert_recipe_servings(slug: str, request: Request, lang: str = Query(...)):
    """
    Convertit une recette pour un nombre de personnes différent

    Args:
        slug: Slug de la recette
        lang: Langue de la recette
        request: Body JSON avec target_servings

    Returns:
        JSON avec les ingrédients convertis
    """
    service = get_conversion_service()

    if not service:
        return JSONResponse(
            {"success": False, "message": "Service de conversion non disponible"},
            status_code=503
        )

    # Vérifier que la recette existe
    recipe_id = db.get_recipe_id_by_slug(slug)
    if not recipe_id:
        return JSONResponse(
            {"success": False, "message": f"Recette '{slug}' introuvable"},
            status_code=404
        )

    try:
        data = await request.json()
        target_servings = data.get('target_servings')

        if not target_servings or target_servings <= 0:
            return JSONResponse(
                {"success": False, "message": "Nombre de personnes invalide"},
                status_code=400
            )

        # Récupérer la recette
        recipe, ingredients, steps = db.get_recipe_by_slug(slug, lang)

        if not recipe:
            return JSONResponse(
                {"success": False, "message": "Recette introuvable"},
                status_code=404
            )

        original_servings = recipe.get('servings', 1)

        # Convertir les ingrédients
        converted_ingredients = service.convert_recipe_servings(
            ingredients,
            original_servings,
            target_servings,
            lang
        )

        return JSONResponse({
            "success": True,
            "original_servings": original_servings,
            "target_servings": target_servings,
            "ingredients": converted_ingredients,
            "message": f"Recette convertie pour {target_servings} personne(s)" if lang == 'fr' else f"{target_servings}人分に変換されました"
        })

    except Exception as e:
        print(f"Erreur lors de la conversion: {e}")
        return JSONResponse(
            {"success": False, "message": f"Erreur: {str(e)}"},
            status_code=500
        )


# --------------------------------------------------------------------
# Coût de la recette
# --------------------------------------------------------------------
@router.get("/recipe/{slug}/cost", response_class=HTMLResponse)
async def recipe_cost(request: Request, slug: str, lang: str = Query("fr"), servings: Optional[int] = Query(None)):
    """Affiche le coût détaillé d'une recette"""
    # Calculer le coût de la recette
    cost_data = db.calculate_recipe_cost(slug, lang, servings)

    if not cost_data:
        return templates.TemplateResponse(
            "not_found.html",
            {"request": request, "lang": lang, "message": f"Recette '{slug}' introuvable"},
            status_code=404,
        )

    return templates.TemplateResponse(
        "recipe_cost.html",
        {
            "request": request,
            "lang": lang,
            "slug": slug,
            "recipe": cost_data['recipe'],
            "servings": cost_data['servings'],
            "original_servings": cost_data['original_servings'],
            "ingredients": cost_data['ingredients'],
            "total_planned": cost_data['total_planned'],
            "currency": cost_data['currency']
        }
    )


# ============================================================================
# API - CATÉGORIES ET TAGS
# ============================================================================

@router.get("/api/categories")
async def api_get_categories():
    """Récupère toutes les catégories disponibles"""
    return db.get_all_categories()


@router.get("/api/tags")
async def api_get_tags():
    """Récupère tous les tags disponibles"""
    return db.get_all_tags()


@router.get("/api/recipes/{recipe_id}/categories")
async def api_get_recipe_categories(recipe_id: int):
    """Récupère les catégories d'une recette spécifique"""
    return db.get_recipe_categories(recipe_id)


@router.get("/api/recipes/{recipe_id}/tags")
async def api_get_recipe_tags(recipe_id: int):
    """Récupère les tags d'une recette spécifique"""
    return db.get_recipe_tags(recipe_id)


@router.post("/api/recipes/{recipe_id}/categories")
async def api_set_recipe_categories(recipe_id: int, request: Request):
    """Définit les catégories d'une recette"""
    data = await request.json()
    category_ids = data.get('category_ids', [])
    db.set_recipe_categories(recipe_id, category_ids)
    return {"status": "ok", "message": "Categories updated"}


@router.post("/api/recipes/{recipe_id}/tags")
async def api_set_recipe_tags(recipe_id: int, request: Request):
    """Définit les tags d'une recette"""
    data = await request.json()
    tag_ids = data.get('tag_ids', [])
    db.set_recipe_tags(recipe_id, tag_ids)
    return {"status": "ok", "message": "Tags updated"}


@router.get("/api/recipes/{recipe_id}/event-types")
async def api_get_recipe_event_types(recipe_id: int):
    """Récupère les types d'événements d'une recette spécifique"""
    return db.get_recipe_event_types(recipe_id)


@router.post("/api/recipes/{recipe_id}/event-types")
async def api_set_recipe_event_types(recipe_id: int, request: Request):
    """Définit les types d'événements d'une recette"""
    data = await request.json()
    event_type_ids = data.get('event_type_ids', [])
    db.set_recipe_event_types(recipe_id, event_type_ids)
    return {"status": "ok", "message": "Event types updated"}


@router.post("/api/categories")
async def api_create_category(request: Request):
    """Crée une nouvelle catégorie"""
    data = await request.json()
    category_id = db.create_category(
        name_fr=data.get('name_fr'),
        name_jp=data.get('name_jp'),
        description_fr=data.get('description_fr'),
        description_jp=data.get('description_jp')
    )
    return {"status": "ok", "category_id": category_id}


@router.put("/api/categories/{category_id}")
async def api_update_category(category_id: int, request: Request):
    """Modifie une catégorie existante"""
    try:
        data = await request.json()
        success = db.update_category(
            category_id=category_id,
            name_fr=data.get('name_fr'),
            name_jp=data.get('name_jp'),
            description_fr=data.get('description_fr'),
            description_jp=data.get('description_jp')
        )
        if success:
            return {"status": "ok", "message": "Category updated"}
        else:
            return JSONResponse(
                {"status": "error", "message": "Category not found"},
                status_code=400
            )
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )


@router.delete("/api/categories/{category_id}")
async def api_delete_category(category_id: int):
    """Supprime une catégorie (seulement si non utilisée)"""
    try:
        db.delete_category(category_id)
        return {"status": "ok", "message": "Category deleted"}
    except ValueError as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=400
        )


@router.post("/api/tags")
async def api_create_tag(request: Request):
    """Crée un nouveau tag personnalisé"""
    data = await request.json()
    tag_id = db.create_tag(
        name_fr=data.get('name_fr'),
        name_jp=data.get('name_jp'),
        description_fr=data.get('description_fr'),
        description_jp=data.get('description_jp'),
        color=data.get('color', '#3B82F6')
    )
    return {"status": "ok", "tag_id": tag_id}


@router.put("/api/tags/{tag_id}")
async def api_update_tag(tag_id: int, request: Request):
    """Modifie un tag existant (seulement si non-système)"""
    try:
        data = await request.json()
        success = db.update_tag(
            tag_id=tag_id,
            name_fr=data.get('name_fr'),
            name_jp=data.get('name_jp'),
            description_fr=data.get('description_fr'),
            description_jp=data.get('description_jp'),
            color=data.get('color')
        )
        if success:
            return {"status": "ok", "message": "Tag updated"}
        else:
            return JSONResponse(
                {"status": "error", "message": "Cannot update system tag or tag not found"},
                status_code=400
            )
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )


@router.delete("/api/tags/{tag_id}")
async def api_delete_tag(tag_id: int):
    """Supprime un tag (seulement si non-système)"""
    try:
        db.delete_tag(tag_id)
        return {"status": "ok", "message": "Tag deleted"}
    except ValueError as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=400
        )


# ============================================================================
# API - TYPES D'ÉVÉNEMENTS
# ============================================================================

@router.get("/api/event-types")
async def api_get_event_types():
    """Récupère tous les types d'événements disponibles"""
    return db.get_all_event_types()


@router.post("/api/event-types")
async def api_create_event_type(request: Request):
    """Crée un nouveau type d'événement"""
    data = await request.json()
    event_type_id = db.create_event_type(
        name_fr=data.get('name_fr'),
        name_jp=data.get('name_jp'),
        description_fr=data.get('description_fr'),
        description_jp=data.get('description_jp')
    )
    return {"status": "ok", "event_type_id": event_type_id}


@router.put("/api/event-types/{event_type_id}")
async def api_update_event_type(event_type_id: int, request: Request):
    """Modifie un type d'événement existant"""
    try:
        data = await request.json()
        success = db.update_event_type(
            event_type_id=event_type_id,
            name_fr=data.get('name_fr'),
            name_jp=data.get('name_jp'),
            description_fr=data.get('description_fr'),
            description_jp=data.get('description_jp')
        )
        if success:
            return {"status": "ok", "message": "Event type updated"}
        else:
            return JSONResponse(
                {"status": "error", "message": "Event type not found"},
                status_code=400
            )
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )


@router.delete("/api/event-types/{event_type_id}")
async def api_delete_event_type(event_type_id: int):
    """Supprime un type d'événement (seulement si non utilisé)"""
    try:
        db.delete_event_type(event_type_id)
        return {"status": "ok", "message": "Event type deleted"}
    except ValueError as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=400
        )


@router.get("/admin/tags", response_class=HTMLResponse)
async def tags_admin_page(request: Request, lang: str = Query("fr")):
    """Page d'administration des tags et catégories"""
    return templates.TemplateResponse(
        "tags_admin.html",
        {"request": request, "lang": lang}
    )


@router.get("/api/recipes/search")
async def api_search_recipes(
    search: str = Query(None),
    categories: str = Query(None),  # IDs séparés par virgules
    tags: str = Query(None),         # IDs séparés par virgules
    lang: str = Query("fr")
):
    """
    Recherche avancée de recettes avec filtres multiples

    Paramètres:
    - search: texte à rechercher dans titre/ingrédients
    - categories: IDs de catégories séparés par virgules (ex: "1,2,3")
    - tags: IDs de tags séparés par virgules (ex: "5,9")
    - lang: langue (fr/jp)
    """
    category_ids = [int(x) for x in categories.split(',')] if categories else None
    tag_ids = [int(x) for x in tags.split(',')] if tags else None

    results = db.search_recipes_by_filters(
        search_text=search,
        category_ids=category_ids,
        tag_ids=tag_ids,
        lang=lang
    )

    # Enrichir avec les catégories et tags de chaque recette
    for recipe in results:
        recipe['categories'] = db.get_recipe_categories(recipe['id'])
        recipe['tags'] = db.get_recipe_tags(recipe['id'])

    return results


@router.get("/api/recipes/search-by-ingredients")
async def api_search_recipes_by_ingredients(
    ingredients: str = Query(..., description="Ingrédients séparés par des virgules"),
    lang: str = Query("fr")
):
    """
    Recherche des recettes contenant tous les ingrédients spécifiés

    Paramètres:
    - ingredients: Liste d'ingrédients séparés par virgules (ex: "tomate,basilic,mozzarella")
    - lang: langue (fr/jp)

    Retourne: Liste de recettes contenant TOUS les ingrédients
    """
    # Séparer les ingrédients et nettoyer les espaces
    ingredient_list = [ing.strip() for ing in ingredients.split(',') if ing.strip()]

    if not ingredient_list:
        return []

    results = db.search_recipes_by_ingredients(ingredient_list, lang)

    # Enrichir avec les catégories, tags et event types
    for recipe in results:
        recipe['categories'] = db.get_recipe_categories(recipe['id'])
        recipe['tags'] = db.get_recipe_tags(recipe['id'])
        recipe['event_types'] = db.get_recipe_event_types(recipe['id'])
        # Ajouter le nom du créateur si disponible
        recipe['creator_name'] = None

    return results

# ============================================================================
# Import de recettes depuis PDF
# ============================================================================

@router.get("/import-pdf", response_class=HTMLResponse)
async def import_pdf_form(request: Request, lang: str = Query("fr")):
    """Affiche le formulaire d'import PDF"""
    return templates.TemplateResponse(
        "import_pdf.html",
        {"request": request, "lang": lang}
    )


@router.post("/api/import-pdf/analyze")
async def analyze_pdf_recipe(
    request: Request,
    file: UploadFile = File(...),
    lang: str = Query("fr")
):
    """
    Analyse un PDF et extrait les informations de la recette avec l'IA
    """
    from app.services.pdf_recipe_extractor import get_pdf_extractor

    # Vérifier que c'est un PDF
    if not file.filename.lower().endswith('.pdf'):
        return JSONResponse(
            {"success": False, "error": "Le fichier doit être un PDF"},
            status_code=400
        )

    # Sauvegarder temporairement le fichier
    temp_path = None
    try:
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            temp_path = tmp.name
            # Copier le contenu uploadé
            shutil.copyfileobj(file.file, tmp)

        # Extraire et analyser la recette
        extractor = get_pdf_extractor()
        recipe_data = extractor.extract_recipe_from_pdf(temp_path, lang)

        if not recipe_data:
            return JSONResponse(
                {"success": False, "error": "Impossible d'extraire la recette du PDF"},
                status_code=500
            )

        return JSONResponse({
            "success": True,
            "recipe": recipe_data
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )
    finally:
        # Nettoyer le fichier temporaire
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


@router.post("/api/import-pdf/save")
async def save_pdf_recipe(request: Request, lang: str = Query("fr")):
    """
    Sauvegarde la recette extraite du PDF après validation par l'utilisateur
    """
    import sqlite3
    from app.models.db_core import DB_PATH

    data = await request.json()

    try:
        # Créer le slug depuis le nom
        import re
        import unicodedata

        def create_slug(text: str) -> str:
            # Normaliser et convertir en ASCII
            text = unicodedata.normalize('NFKD', text)
            text = text.encode('ascii', 'ignore').decode('ascii')
            # Convertir en minuscules et remplacer espaces par tirets
            text = text.lower()
            text = re.sub(r'[^a-z0-9]+', '-', text)
            text = text.strip('-')
            return text[:50]  # Limiter à 50 caractères

        # Déterminer la langue de la recette
        recipe_lang = data.get('detected_language', lang)

        # Créer le slug
        recipe_name = data.get('name', 'recette-importee')
        slug = create_slug(recipe_name)

        # Si le slug est vide, trop court, ou composé uniquement de chiffres, utiliser un slug par défaut
        if not slug or len(slug) < 2 or slug.isdigit():
            slug = 'recipe-import'

        # Connexion à la base
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()

        try:
            # Vérifier que le slug n'existe pas déjà
            cur.execute("SELECT id FROM recipe WHERE slug = ?", (slug,))
            if cur.fetchone():
                # Ajouter un suffixe numérique
                counter = 1
                while True:
                    test_slug = f"{slug}-{counter}"
                    cur.execute("SELECT id FROM recipe WHERE slug = ?", (test_slug,))
                    if not cur.fetchone():
                        slug = test_slug
                        break
                    counter += 1

            # Créer la recette
            servings = data.get('servings', 4)
            country = data.get('country', '')
            recipe_type = data.get('recipe_type', 'PERSO')
            user_id = request.session.get('user_id')  # Récupérer l'utilisateur connecté

            cur.execute(
                "INSERT INTO recipe (slug, country, servings_default, user_id) VALUES (?, ?, ?, ?)",
                (slug, country, servings, user_id)
            )
            recipe_id = cur.lastrowid

            # Ajouter la traduction de la recette dans la langue détectée UNIQUEMENT
            # L'autre langue restera vide, permettant d'utiliser la traduction automatique
            cur.execute(
                "INSERT INTO recipe_translation (recipe_id, lang, name, recipe_type) VALUES (?, ?, ?, ?)",
                (recipe_id, recipe_lang, recipe_name, recipe_type)
            )

            # Ajouter les ingrédients
            for position, ing in enumerate(data.get('ingredients', []), 1):
                quantity_float = ing.get('quantity')
                if quantity_float is not None:
                    try:
                        quantity_float = float(quantity_float)
                    except (ValueError, TypeError):
                        quantity_float = None

                # Insérer recipe_ingredient
                cur.execute(
                    "INSERT INTO recipe_ingredient (recipe_id, position, quantity) VALUES (?, ?, ?)",
                    (recipe_id, position, quantity_float)
                )
                recipe_ingredient_id = cur.lastrowid

                # Insérer la traduction de l'ingrédient
                cur.execute(
                    "INSERT INTO recipe_ingredient_translation (recipe_ingredient_id, lang, name, unit, notes) VALUES (?, ?, ?, ?, ?)",
                    (recipe_ingredient_id, recipe_lang, ing.get('name', ''),
                     ing.get('unit') or None, ing.get('notes') or None)
                )

            # Ajouter les étapes
            for position, step_text in enumerate(data.get('steps', []), 1):
                # Insérer step
                cur.execute(
                    "INSERT INTO step (recipe_id, position) VALUES (?, ?)",
                    (recipe_id, position)
                )
                step_id = cur.lastrowid

                # Insérer la traduction de l'étape
                cur.execute(
                    "INSERT INTO step_translation (step_id, lang, text) VALUES (?, ?, ?)",
                    (step_id, recipe_lang, step_text)
                )

            con.commit()

            return JSONResponse({
                "success": True,
                "recipe_id": recipe_id,
                "slug": slug
            })

        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

# ============================================================================
# Import de recettes depuis URL web
# ============================================================================

@router.get("/import-url", response_class=HTMLResponse)
async def import_url_form(request: Request, lang: str = Query("fr")):
    """Affiche le formulaire d'import depuis URL"""
    return templates.TemplateResponse(
        "import_url.html",
        {"request": request, "lang": lang}
    )


@router.post("/api/import-url/analyze")
async def analyze_url_recipe(
    request: Request,
    url: str = Form(...),
    target_lang: str = Form("fr")
):
    """
    Analyse une URL et extrait les informations de la recette avec l'IA
    """
    try:
        # Récupérer l'importateur web
        importer = get_web_recipe_importer()

        # Importer la recette
        recipe_data = importer.import_recipe(url, target_lang)

        return JSONResponse({
            "success": True,
            "recipe": recipe_data
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


@router.post("/api/import-url/save")
async def save_url_recipe(request: Request, lang: str = Query("fr")):
    """
    Sauvegarde la recette extraite de l'URL après validation par l'utilisateur
    """
    import sqlite3
    from app.models.db_core import DB_PATH

    data = await request.json()

    try:
        # Créer le slug depuis le nom
        import re
        import unicodedata

        def create_slug(text: str) -> str:
            # Normaliser et convertir en ASCII
            text = unicodedata.normalize('NFKD', text)
            text = text.encode('ascii', 'ignore').decode('ascii')
            # Convertir en minuscules et remplacer espaces par tirets
            text = text.lower()
            text = re.sub(r'[^a-z0-9]+', '-', text)
            text = text.strip('-')
            return text[:50]  # Limiter à 50 caractères

        # Créer le slug
        recipe_name = data.get('name', 'recette-importee')
        slug = create_slug(recipe_name)

        # Si le slug est vide, trop court, ou composé uniquement de chiffres, utiliser un slug par défaut
        if not slug or len(slug) < 2 or slug.isdigit():
            slug = 'recipe-import'

        # Connexion à la base
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()

        try:
            # Vérifier que le slug n'existe pas déjà
            cur.execute("SELECT id FROM recipe WHERE slug = ?", (slug,))
            if cur.fetchone():
                # Ajouter un suffixe numérique
                counter = 1
                while True:
                    test_slug = f"{slug}-{counter}"
                    cur.execute("SELECT id FROM recipe WHERE slug = ?", (test_slug,))
                    if not cur.fetchone():
                        slug = test_slug
                        break
                    counter += 1

            # Récupérer la langue cible depuis les données
            target_lang = data.get('target_lang', lang)

            # Créer la recette
            servings = data.get('servings', 4)
            country = data.get('country', '')
            user_id = request.session.get('user_id')  # Récupérer l'utilisateur connecté

            # Mapper recipe_type depuis le format texte vers le format DB
            recipe_type_text = data.get('recipe_type', 'autre')
            recipe_type_map = {
                'apéritif': 'PERSO',
                'entrée': 'PERSO',
                'plat': 'PERSO',
                'dessert': 'PERSO',
                'autre': 'PERSO'
            }
            recipe_type = recipe_type_map.get(recipe_type_text.lower(), 'PERSO')

            cur.execute(
                """INSERT INTO recipe
                   (slug, country, servings_default, user_id)
                   VALUES (?, ?, ?, ?)""",
                (slug, country, servings, user_id)
            )
            recipe_id = cur.lastrowid

            # Ajouter la traduction de la recette dans la langue cible
            description = data.get('description', '')
            cur.execute(
                """INSERT INTO recipe_translation
                   (recipe_id, lang, name, recipe_type, description)
                   VALUES (?, ?, ?, ?, ?)""",
                (recipe_id, target_lang, recipe_name, recipe_type, description)
            )

            # Ajouter les ingrédients
            for position, ing in enumerate(data.get('ingredients', []), 1):
                quantity_float = ing.get('quantity')
                if quantity_float is not None:
                    try:
                        quantity_float = float(quantity_float)
                    except (ValueError, TypeError):
                        quantity_float = None

                # Insérer recipe_ingredient
                cur.execute(
                    "INSERT INTO recipe_ingredient (recipe_id, position, quantity) VALUES (?, ?, ?)",
                    (recipe_id, position, quantity_float)
                )
                recipe_ingredient_id = cur.lastrowid

                # Insérer la traduction de l'ingrédient
                cur.execute(
                    """INSERT INTO recipe_ingredient_translation
                       (recipe_ingredient_id, lang, name, unit, notes)
                       VALUES (?, ?, ?, ?, ?)""",
                    (recipe_ingredient_id, target_lang, ing.get('name', ''),
                     ing.get('unit') or None, ing.get('notes') or None)
                )

            # Ajouter les étapes
            for position, step_text in enumerate(data.get('steps', []), 1):
                # Insérer step
                cur.execute(
                    "INSERT INTO step (recipe_id, position) VALUES (?, ?)",
                    (recipe_id, position)
                )
                step_id = cur.lastrowid

                # Insérer la traduction de l'étape
                cur.execute(
                    "INSERT INTO step_translation (step_id, lang, text) VALUES (?, ?, ?)",
                    (step_id, target_lang, step_text)
                )

            con.commit()

            return JSONResponse({
                "success": True,
                "recipe_id": recipe_id,
                "slug": slug
            })

        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )
