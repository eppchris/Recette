# app/routes/event_routes.py
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from typing import Optional
from datetime import datetime

from app.models import db
from app.services.ingredient_aggregator import get_ingredient_aggregator
from app.template_config import templates

router = APIRouter()


# ============================================================================
# Routes pour la gestion des événements
# ============================================================================

@router.get("/events", response_class=HTMLResponse)
async def events_list(request: Request, lang: str = "fr"):
    """
    Affiche la liste de tous les événements
    """
    events = db.list_events()
    event_types = db.list_event_types()

    return templates.TemplateResponse(
        "events_list.html",
        {
            "request": request,
            "lang": lang,
            "events": events,
            "event_types": event_types
        }
    )


@router.get("/events/new", response_class=HTMLResponse)
async def event_new(request: Request, lang: str = "fr"):
    """
    Formulaire de création d'un nouvel événement
    """
    event_types = db.list_event_types()

    return templates.TemplateResponse(
        "event_form.html",
        {
            "request": request,
            "lang": lang,
            "event_types": event_types,
            "event": None
        }
    )


@router.post("/events/new")
async def event_create(
    request: Request,
    lang: str = Form("fr"),
    event_type_id: int = Form(...),
    name: str = Form(...),
    event_date: str = Form(...),
    location: str = Form(...),
    attendees: int = Form(...),
    notes: str = Form("")
):
    """
    Crée un nouvel événement
    """
    event_id = db.create_event(
        event_type_id=event_type_id,
        name=name,
        event_date=event_date,
        location=location,
        attendees=attendees,
        notes=notes
    )

    return RedirectResponse(
        url=f"/events/{event_id}?lang={lang}",
        status_code=303
    )


@router.get("/events/{event_id}", response_class=HTMLResponse)
async def event_detail(request: Request, event_id: int, lang: str = "fr"):
    """
    Affiche les détails d'un événement avec ses recettes
    """
    event = db.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")

    recipes = db.get_event_recipes(event_id, lang)
    all_recipes = db.list_recipes(lang)

    # Vérifier si une shopping list existe pour cet événement
    shopping_list_items = db.get_shopping_list_items(event_id)
    has_shopping_list = len(shopping_list_items) > 0

    return templates.TemplateResponse(
        "event_detail.html",
        {
            "request": request,
            "lang": lang,
            "event": event,
            "recipes": recipes,
            "all_recipes": all_recipes,
            "has_shopping_list": has_shopping_list
        }
    )


@router.get("/events/{event_id}/edit", response_class=HTMLResponse)
async def event_edit(request: Request, event_id: int, lang: str = "fr"):
    """
    Formulaire d'édition d'un événement
    """
    event = db.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")

    event_types = db.list_event_types()

    return templates.TemplateResponse(
        "event_form.html",
        {
            "request": request,
            "lang": lang,
            "event_types": event_types,
            "event": event
        }
    )


@router.post("/events/{event_id}/edit")
async def event_update(
    request: Request,
    event_id: int,
    lang: str = Form("fr"),
    event_type_id: int = Form(...),
    name: str = Form(...),
    event_date: str = Form(...),
    location: str = Form(...),
    attendees: int = Form(...),
    notes: str = Form("")
):
    """
    Met à jour un événement existant
    """
    db.update_event(
        event_id=event_id,
        event_type_id=event_type_id,
        name=name,
        event_date=event_date,
        location=location,
        attendees=attendees,
        notes=notes
    )

    return RedirectResponse(
        url=f"/events/{event_id}?lang={lang}",
        status_code=303
    )


@router.post("/events/{event_id}/delete")
async def event_delete(request: Request, event_id: int, lang: str = Form("fr")):
    """
    Supprime un événement
    """
    db.delete_event(event_id)

    return RedirectResponse(
        url=f"/events?lang={lang}",
        status_code=303
    )


# ============================================================================
# Routes pour la gestion des recettes d'un événement
# ============================================================================

@router.post("/events/{event_id}/recipes/add")
async def event_add_recipe(
    request: Request,
    event_id: int,
    lang: str = Form("fr"),
    recipe_id: int = Form(...),
    servings_multiplier: float = Form(1.0)
):
    """
    Ajoute une recette à un événement
    """
    # Vérifier si la recette n'est pas déjà dans l'événement
    existing_recipes = db.get_event_recipes(event_id, lang)
    if any(r['id'] == recipe_id for r in existing_recipes):
        # Recette déjà présente, ne pas ajouter
        # On redirige sans message pour l'instant
        return RedirectResponse(
            url=f"/events/{event_id}?lang={lang}",
            status_code=303
        )

    db.add_recipe_to_event(event_id, recipe_id, servings_multiplier)

    # Supprimer la shopping list existante car les recettes ont changé
    db.delete_all_shopping_list_items(event_id)

    return RedirectResponse(
        url=f"/events/{event_id}?lang={lang}",
        status_code=303
    )


@router.post("/events/{event_id}/recipes/add-all-by-type")
async def event_add_all_recipes_by_type(
    request: Request,
    event_id: int,
    lang: str = Form("fr")
):
    """
    Ajoute toutes les recettes du type de l'événement
    """
    # Récupérer l'événement pour connaître son type
    event = db.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")

    # Mapper le type d'événement au type de recette
    event_type_name = event['event_type_name']

    # Si le type d'événement est INVITATION, on utilise PERSO
    if event_type_name == "INVITATION":
        recipe_type = "PERSO" if lang == "fr" else "じぶん"
    else:
        # Pour PRO et MASTER, on utilise directement le nom du type
        recipe_type_map = {
            "PRO": {"fr": "PRO", "jp": "プロ"},
            "MASTER": {"fr": "MASTER", "jp": "マイスター"}
        }
        recipe_type = recipe_type_map.get(event_type_name, {}).get(lang, event_type_name)

    # Récupérer toutes les recettes de ce type
    recipes = db.list_recipes_by_type(recipe_type, lang)

    # Ajouter chaque recette à l'événement (avec multiplicateur 1.0)
    for recipe in recipes:
        # Vérifier si la recette n'est pas déjà dans l'événement
        existing_recipes = db.get_event_recipes(event_id, lang)
        if not any(r['id'] == recipe['id'] for r in existing_recipes):
            db.add_recipe_to_event(event_id, recipe['id'], 1.0)

    # Supprimer la shopping list existante car les recettes ont changé
    db.delete_all_shopping_list_items(event_id)

    return RedirectResponse(
        url=f"/events/{event_id}?lang={lang}",
        status_code=303
    )


@router.post("/events/{event_id}/recipes/{recipe_id}/remove")
async def event_remove_recipe(
    request: Request,
    event_id: int,
    recipe_id: int,
    lang: str = Form("fr")
):
    """
    Retire une recette d'un événement
    """
    db.remove_recipe_from_event(event_id, recipe_id)

    return RedirectResponse(
        url=f"/events/{event_id}?lang={lang}",
        status_code=303
    )


@router.post("/events/{event_id}/recipes/{recipe_id}/update-servings")
async def event_update_recipe_servings(
    request: Request,
    event_id: int,
    recipe_id: int,
    lang: str = Form("fr"),
    servings_multiplier: float = Form(...)
):
    """
    Met à jour le multiplicateur de portions pour une recette
    """
    db.update_event_recipe_servings(event_id, recipe_id, servings_multiplier)

    return RedirectResponse(
        url=f"/events/{event_id}?lang={lang}",
        status_code=303
    )


# ============================================================================
# Routes pour la génération de liste de courses
# ============================================================================

@router.get("/events/{event_id}/shopping-list", response_class=HTMLResponse)
async def event_shopping_list(request: Request, event_id: int, lang: str = "fr", regenerate: bool = False):
    """
    Affiche la liste de courses pour un événement
    Si la liste n'existe pas ou si regenerate=True, elle est générée depuis les recettes
    IMPORTANT: Régénère automatiquement si la langue change
    """
    event = db.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")

    # Récupérer les recettes pour affichage dans la langue demandée
    recipes_data = db.get_event_recipes_with_ingredients(event_id, lang)

    # Vérifier si une liste existe déjà
    saved_items = db.get_shopping_list_items(event_id)

    # Détecter si on doit régénérer (pas de liste OU changement de langue)
    needs_regeneration = not saved_items or regenerate

    # Vérifier si la langue a changé en comparant les noms de recettes
    if saved_items and not regenerate and recipes_data:
        # Si le premier ingrédient a des source_recipes, vérifier la langue
        for item in saved_items:
            if item.get('source_recipes'):
                stored_recipe_names = {s['recipe_name'] for s in item['source_recipes']}
                current_recipe_names = {r['recipe_name'] for r in recipes_data}
                # Si aucun nom ne correspond, c'est que la langue a changé
                if not stored_recipe_names & current_recipe_names:
                    needs_regeneration = True
                break

    # Si pas de liste ou régénération nécessaire, créer une nouvelle liste
    if needs_regeneration:
        # Agréger les ingrédients depuis les recettes
        aggregator = get_ingredient_aggregator()
        aggregated_ingredients = aggregator.aggregate_ingredients(recipes_data, lang)

        # Sauvegarder dans la base de données
        db.save_shopping_list_items(event_id, aggregated_ingredients)

        # Recharger les items sauvegardés
        saved_items = db.get_shopping_list_items(event_id)

    return templates.TemplateResponse(
        "shopping_list.html",
        {
            "request": request,
            "lang": lang,
            "event": event,
            "ingredients": saved_items,
            "recipes": recipes_data
        }
    )


# ============================================================================
# Routes API JSON pour les types d'événements
# ============================================================================

@router.get("/api/event-types")
async def api_list_event_types():
    """
    API: Liste tous les types d'événements
    """
    return JSONResponse(content=db.list_event_types())


@router.post("/api/event-types")
async def api_create_event_type(name: str = Form(...)):
    """
    API: Crée un nouveau type d'événement
    """
    event_type_id = db.create_event_type(name)
    return JSONResponse(content={"id": event_type_id, "name": name})


@router.delete("/api/event-types/{event_type_id}")
async def api_delete_event_type(event_type_id: int):
    """
    API: Supprime un type d'événement
    """
    success = db.delete_event_type(event_type_id)
    if success:
        return JSONResponse(content={"success": True})
    else:
        raise HTTPException(status_code=400, detail="Type d'événement utilisé ou erreur")


# ============================================================================
# Routes API pour la liste de courses
# ============================================================================

@router.post("/api/shopping-list/items/{item_id}/update")
async def api_update_shopping_list_item(
    item_id: int,
    purchase_quantity: Optional[float] = Form(None),
    purchase_unit: Optional[str] = Form(None),
    is_checked: Optional[bool] = Form(None),
    notes: Optional[str] = Form(None)
):
    """
    API: Met à jour un item de liste de courses
    """
    success = db.update_shopping_list_item(
        item_id=item_id,
        purchase_quantity=purchase_quantity,
        purchase_unit=purchase_unit,
        is_checked=is_checked,
        notes=notes
    )

    if success:
        return JSONResponse(content={"success": True})
    else:
        raise HTTPException(status_code=400, detail="Erreur lors de la mise à jour")


@router.post("/events/{event_id}/shopping-list/regenerate")
async def event_regenerate_shopping_list(request: Request, event_id: int, lang: str = Form("fr")):
    """
    Régénère la liste de courses depuis les recettes
    """
    event = db.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")

    # Régénérer la liste
    db.regenerate_shopping_list(event_id, lang)

    return RedirectResponse(
        url=f"/events/{event_id}/shopping-list?lang={lang}",
        status_code=303
    )
