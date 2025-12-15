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
    Affiche la liste des événements
    - L'utilisateur 'admin' voit tous les événements
    - Les autres utilisateurs voient uniquement leurs événements
    """
    user_id = request.session.get('user_id')
    username = request.session.get('username')

    # Si l'utilisateur est 'admin', afficher tous les événements, sinon filtrer par user_id
    if username == 'admin':
        events = db.list_events()
    else:
        events = db.list_events(user_id=user_id)

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
    date_debut: str = Form(...),
    date_fin: str = Form(...),
    nombre_jours: int = Form(1),
    location: str = Form(...),
    attendees: int = Form(...),
    notes: str = Form("")
):
    """
    Crée un nouvel événement avec gestion multi-jours
    """
    user_id = request.session.get('user_id')

    # Créer l'événement
    event_id = db.create_event(
        event_type_id=event_type_id,
        name=name,
        event_date=event_date,
        location=location,
        attendees=attendees,
        notes=notes,
        user_id=user_id,
        date_debut=date_debut,
        date_fin=date_fin,
        nombre_jours=nombre_jours
    )

    # Récupérer et sauvegarder les dates sélectionnées
    form_data = await request.form()
    dates = []
    i = 0
    while f"event_dates[{i}][date]" in form_data:
        dates.append({
            'date': form_data[f"event_dates[{i}][date]"],
            'is_selected': form_data[f"event_dates[{i}][selected]"] == "1"
        })
        i += 1

    if dates:
        db.save_event_dates(event_id, dates)

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

    # Récupérer les participants et groupes (avec gestion d'erreur si tables non migrées)
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    is_admin = (username == 'admin')

    try:
        event_participants = db.get_event_participants(event_id)
        all_participants = db.list_participants(user_id=user_id, is_admin=is_admin)
        all_groups = db.list_groups(user_id=user_id, is_admin=is_admin)
    except Exception:
        # Tables participants pas encore migrées
        event_participants = []
        all_participants = []
        all_groups = []

    return templates.TemplateResponse(
        "event_detail.html",
        {
            "request": request,
            "lang": lang,
            "event": event,
            "recipes": recipes,
            "all_recipes": all_recipes,
            "has_shopping_list": has_shopping_list,
            "event_participants": event_participants,
            "all_participants": all_participants,
            "all_groups": all_groups
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

    # Récupérer les dates de l'événement
    event_dates = db.get_event_dates(event_id)

    return templates.TemplateResponse(
        "event_form.html",
        {
            "request": request,
            "lang": lang,
            "event_types": event_types,
            "event": event,
            "event_dates": event_dates
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
    date_debut: str = Form(...),
    date_fin: str = Form(...),
    nombre_jours: int = Form(1),
    location: str = Form(...),
    attendees: int = Form(...),
    notes: str = Form("")
):
    """
    Met à jour un événement existant avec gestion multi-jours
    Si le nombre de participants change et qu'une liste de courses existe,
    la liste est automatiquement régénérée pour refléter le nouveau nombre.
    """
    # Récupérer l'ancien événement pour comparer le nombre de participants
    old_event = db.get_event_by_id(event_id)
    old_attendees = old_event['attendees'] if old_event else None

    # Mettre à jour l'événement
    db.update_event(
        event_id=event_id,
        event_type_id=event_type_id,
        name=name,
        event_date=event_date,
        location=location,
        attendees=attendees,
        notes=notes,
        date_debut=date_debut,
        date_fin=date_fin,
        nombre_jours=nombre_jours
    )

    # Récupérer et sauvegarder les dates sélectionnées
    form_data = await request.form()
    dates = []
    i = 0
    while f"event_dates[{i}][date]" in form_data:
        dates.append({
            'date': form_data[f"event_dates[{i}][date]"],
            'is_selected': form_data[f"event_dates[{i}][selected]"] == "1"
        })
        i += 1

    if dates:
        db.save_event_dates(event_id, dates)

    # Si le nombre de participants a changé, ajuster les multiplicateurs de portions
    # et régénérer la liste de courses si elle existe
    if old_attendees is not None and old_attendees != attendees and old_attendees > 0:
        # Calculer le ratio de changement du nombre de participants
        ratio = attendees / old_attendees

        # Mettre à jour tous les servings_multiplier des recettes de l'événement
        db.update_event_recipes_multipliers(event_id, ratio)

        # Si une liste de courses existe, la régénérer avec les nouvelles quantités
        shopping_list_items = db.get_shopping_list_items(event_id)

        if len(shopping_list_items) > 0:
            # Récupérer les recettes de l'événement avec les ingrédients (avec les nouveaux multiplicateurs)
            recipes_data = db.get_event_recipes_with_ingredients(event_id, lang)

            if recipes_data:
                # Régénérer la liste de courses avec les nouvelles quantités
                from app.services.ingredient_aggregator import get_ingredient_aggregator
                aggregator = get_ingredient_aggregator()
                aggregated_ingredients = aggregator.aggregate_ingredients(recipes_data, lang)
                db.save_shopping_list_items(event_id, aggregated_ingredients)

    return RedirectResponse(
        url=f"/events/{event_id}?lang={lang}",
        status_code=303
    )


@router.get("/events/{event_id}/copy", response_class=HTMLResponse)
async def event_copy_form(request: Request, event_id: int, lang: str = "fr"):
    """
    Formulaire de copie d'un événement
    Pré-remplit tous les champs avec les données de l'événement source
    """
    # Récupérer l'événement source
    source_event = db.get_event_by_id(event_id)
    if not source_event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")

    # Récupérer la liste des types d'événements
    event_types = db.list_event_types()

    # Récupérer les recettes de l'événement source
    source_recipes = db.get_event_recipes(event_id, lang)

    return templates.TemplateResponse(
        "event_copy_form.html",
        {
            "request": request,
            "lang": lang,
            "source_event": source_event,
            "event_types": event_types,
            "source_recipes": source_recipes
        }
    )


@router.post("/events/copy")
async def event_copy_create(
    request: Request,
    lang: str = Form("fr"),
    source_event_id: int = Form(...),
    event_type_id: int = Form(...),
    name: str = Form(...),
    date_debut: str = Form(...),
    date_fin: str = Form(...),
    location: str = Form(""),
    attendees: int = Form(...),
    notes: str = Form("")
):
    """
    Crée une copie d'un événement existant avec de nouvelles valeurs
    """
    user_id = request.session.get('user_id')

    # Créer la copie de l'événement
    new_event_id = db.copy_event(
        event_id=source_event_id,
        new_name=name,
        new_event_type_id=event_type_id,
        new_date_debut=date_debut,
        new_date_fin=date_fin,
        new_location=location if location else None,
        new_attendees=attendees if attendees else None,
        new_notes=notes if notes else None,
        user_id=user_id
    )

    # Rediriger vers la page de détail du nouvel événement
    return RedirectResponse(
        url=f"/events/{new_event_id}?lang={lang}",
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

    # Récupérer toutes les recettes liées à ce type d'événement via many-to-many
    event_type_id = event['event_type_id']
    recipes = db.list_recipes_by_event_types([event_type_id], lang)

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

    # Supprimer la shopping list existante car les recettes ont changé
    db.delete_all_shopping_list_items(event_id)

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

    # Supprimer la shopping list existante car les quantités ont changé
    db.delete_all_shopping_list_items(event_id)

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


# ============================================================================
# Routes API pour la gestion du budget
# ============================================================================

@router.get("/events/{event_id}/budget")
async def event_budget_view(request: Request, event_id: int, lang: str = "fr"):
    """
    Affiche la page de gestion du budget pour un événement
    """
    event = db.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")

    # Récupérer les catégories de dépenses
    categories = db.list_expense_categories(lang)

    # Récupérer les dépenses existantes
    expenses = db.get_event_expenses(event_id, lang)

    # Récupérer le résumé budgétaire
    budget_summary = db.get_event_budget_summary(event_id)

    # Récupérer la liste de courses
    shopping_list = db.get_shopping_list_items(event_id)

    # Si la liste est vide, essayer de la générer depuis les recettes de l'événement
    if not shopping_list:
        recipes_data = db.get_event_recipes_with_ingredients(event_id, lang)
        if recipes_data:
            from app.services.ingredient_aggregator import get_ingredient_aggregator
            aggregator = get_ingredient_aggregator()
            aggregated_ingredients = aggregator.aggregate_ingredients(recipes_data, lang)
            db.save_shopping_list_items(event_id, aggregated_ingredients)
            shopping_list = db.get_shopping_list_items(event_id)
    # Vérifier si la liste doit être régénérée pour la bonne langue
    elif shopping_list:
        # Vérifier si la liste contient des caractères japonais
        first_item_name = shopping_list[0]['ingredient_name'] if shopping_list else ''
        has_japanese = any(ord(char) > 0x3000 for char in first_item_name)
        needs_regen = (lang == 'fr' and has_japanese) or (lang == 'jp' and not has_japanese)

        if needs_regen:
            # Régénérer la liste dans la bonne langue
            recipes_data = db.get_event_recipes_with_ingredients(event_id, lang)
            if recipes_data:
                from app.services.ingredient_aggregator import get_ingredient_aggregator
                aggregator = get_ingredient_aggregator()
                aggregated_ingredients = aggregator.aggregate_ingredients(recipes_data, lang)
                db.save_shopping_list_items(event_id, aggregated_ingredients)
                shopping_list = db.get_shopping_list_items(event_id)

    # Enrichir chaque ingrédient avec son prix calculé pour la quantité demandée
    # Utiliser la langue de l'interface pour déterminer la devise à afficher
    currency = 'EUR' if lang == 'fr' else 'JPY'
    for item in shopping_list:
        # Calculer le prix réel pour la quantité demandée (needed_quantity)
        quantity = item.get('needed_quantity') or item.get('total_quantity', 0)
        unit = item.get('needed_unit') or item.get('unit', '')

        if quantity > 0 and unit:
            price_result = db.calculate_ingredient_price(
                item['ingredient_name'],
                quantity,
                unit,
                currency
            )
            if price_result:
                item['total_price'] = price_result['total_price']
                item['unit_price'] = price_result['unit_price']
                item['catalog_unit'] = price_result['catalog_unit']
                item['catalog_qty'] = price_result['catalog_qty']
                item['catalog_price'] = price_result['catalog_price']
            else:
                item['catalog_price'] = None
                item['total_price'] = None
        else:
            item['catalog_price'] = None

    return templates.TemplateResponse(
        "event_budget.html",
        {
            "request": request,
            "lang": lang,
            "event": event,
            "categories": categories,
            "expenses": expenses,
            "budget_summary": budget_summary,
            "shopping_list": shopping_list,
            "currency": currency
        }
    )


@router.post("/events/{event_id}/budget/planned")
async def event_update_budget_planned(
    request: Request,
    event_id: int,
    lang: str = Form("fr"),
    budget_planned: float = Form(...)
):
    """
    Met à jour le budget prévisionnel d'un événement
    """
    # Récupérer l'événement pour vérifier la devise
    event = db.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")

    # Si la devise n'est pas définie, la définir en fonction de la langue actuelle
    if not event.get('currency') or event.get('currency') is None:
        currency = 'EUR' if lang == 'fr' else 'JPY'
        db.update_event_currency(event_id, currency)

    success = db.update_event_budget_planned(event_id, budget_planned)

    if success:
        return RedirectResponse(
            url=f"/events/{event_id}/budget?lang={lang}",
            status_code=303
        )
    else:
        raise HTTPException(status_code=400, detail="Erreur lors de la mise à jour")


@router.post("/events/{event_id}/expenses/add")
async def event_add_expense(
    request: Request,
    event_id: int,
    lang: str = Form("fr"),
    category_id: int = Form(...),
    description: str = Form(...),
    planned_amount: float = Form(...),
    actual_amount: Optional[str] = Form(None),
    is_paid: Optional[str] = Form(None),
    paid_date: Optional[str] = Form(None),
    notes: Optional[str] = Form("")
):
    """
    Ajoute une dépense à un événement
    """
    # Récupérer l'événement pour vérifier la devise
    event = db.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")

    # Si la devise n'est pas définie, la définir en fonction de la langue actuelle
    if not event.get('currency') or event.get('currency') is None:
        currency = 'EUR' if lang == 'fr' else 'JPY'
        db.update_event_currency(event_id, currency)

    # Convertir actual_amount en float (gérer chaîne vide)
    actual_amount_float = None
    if actual_amount and actual_amount.strip():
        try:
            actual_amount_float = float(actual_amount)
        except ValueError:
            actual_amount_float = None

    # Convertir is_paid en booléen (checkbox non cochée = None, cochée = "1")
    is_paid_bool = is_paid == "1" if is_paid else False

    # Convertir paid_date (gérer chaîne vide)
    paid_date_str = paid_date if paid_date and paid_date.strip() else None

    expense_id = db.create_event_expense(
        event_id=event_id,
        category_id=category_id,
        description=description,
        planned_amount=planned_amount,
        actual_amount=actual_amount_float,
        is_paid=is_paid_bool,
        paid_date=paid_date_str,
        notes=notes
    )

    if expense_id:
        return RedirectResponse(
            url=f"/events/{event_id}/budget?lang={lang}",
            status_code=303
        )
    else:
        raise HTTPException(status_code=400, detail="Erreur lors de la création")


@router.post("/events/{event_id}/expenses/ingredients/add")
async def event_add_ingredients_expense(
    request: Request,
    event_id: int,
    lang: str = Form("fr"),
    description: str = Form(...)
):
    """
    Crée une dépense basée sur la liste de courses avec les prix des ingrédients
    """
    # Récupérer l'événement
    event = db.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")

    # Récupérer tous les paramètres du formulaire
    form_data = await request.form()

    # Récupérer la liste de courses
    shopping_list = db.get_shopping_list_items(event_id)

    # Calculer le total et préparer les données des ingrédients
    ingredients_data = []
    total_planned = 0.0

    for item in shopping_list:
        price_key = f"ingredient_{item['id']}_price"
        unit_price_str = form_data.get(price_key)

        if unit_price_str:
            try:
                unit_price = float(unit_price_str)
                # Utiliser needed_quantity ou purchase_quantity
                quantity = float(item.get('needed_quantity') or item.get('purchase_quantity') or 0)
                if quantity == 0:
                    continue  # Ignorer si pas de quantité

                item_total = unit_price * quantity
                total_planned += item_total

                # Utiliser needed_unit ou purchase_unit
                unit = item.get('needed_unit') or item.get('purchase_unit') or ''

                ingredients_data.append({
                    'shopping_list_item_id': item['id'],
                    'ingredient_name': item['ingredient_name'],
                    'quantity': quantity,
                    'unit': unit,
                    'planned_unit_price': unit_price,
                    'actual_unit_price': None
                })
            except (ValueError, TypeError):
                pass  # Ignorer les prix invalides

    # Créer la dépense avec catégorie None (ou créer une catégorie spéciale)
    # Pour l'instant, on utilise la première catégorie disponible
    categories = db.list_expense_categories(lang)
    category_id = categories[0]['id'] if categories else 1

    expense_id = db.create_event_expense(
        event_id=event_id,
        category_id=category_id,
        description=description,
        planned_amount=total_planned,
        actual_amount=None,
        is_paid=False,
        paid_date=None,
        notes="Dépense générée depuis la liste de courses"
    )

    if expense_id and ingredients_data:
        # Sauvegarder le détail des ingrédients
        db.save_expense_ingredient_details(expense_id, ingredients_data)

    return RedirectResponse(
        url=f"/events/{event_id}/budget?lang={lang}",
        status_code=303
    )


@router.post("/events/{event_id}/budget/ingredients/save")
async def save_ingredient_budget(
    request: Request,
    event_id: int,
    lang: str = Form("fr")
):
    """
    Sauvegarde les prix prévus des ingrédients et le montant total réel
    """
    # Récupérer l'événement
    event = db.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")

    # Récupérer tous les paramètres du formulaire
    form_data = await request.form()

    # Récupérer la liste de courses
    shopping_list = db.get_shopping_list_items(event_id)

    # Sauvegarder les prix unitaires prévus et montants dépensés pour chaque ingrédient
    for item in shopping_list:
        planned_price_key = f"ingredient_{item['id']}_price"
        actual_total_key = f"ingredient_{item['id']}_actual"

        planned_price_str = form_data.get(planned_price_key)
        actual_total_str = form_data.get(actual_total_key)

        planned_price = None
        actual_total = None

        if planned_price_str:
            try:
                planned_price = float(planned_price_str)
            except (ValueError, TypeError):
                pass

        if actual_total_str:
            try:
                actual_total = float(actual_total_str)
            except (ValueError, TypeError):
                pass

        # Mettre à jour les prix prévus et montants dépensés
        if planned_price is not None or actual_total is not None:
            db.update_shopping_list_item_prices(item['id'], planned_price, actual_total)

    # Sauvegarder le montant total réel des ingrédients au niveau de l'événement
    ingredients_actual_total_str = form_data.get('ingredients_actual_total')
    if ingredients_actual_total_str:
        try:
            ingredients_actual_total = float(ingredients_actual_total_str)
            db.update_event_ingredients_actual_total(event_id, ingredients_actual_total)
        except (ValueError, TypeError):
            pass

    return RedirectResponse(
        url=f"/events/{event_id}/budget?lang={lang}",
        status_code=303
    )


@router.post("/events/{event_id}/budget/ingredients/sync-catalog")
async def sync_ingredient_prices_from_catalog(
    event_id: int,
    lang: str = Form("fr")
):
    """
    Synchronise les prix des ingrédients du budget avec les prix actuels du catalogue
    """
    # Récupérer l'événement
    event = db.get_event_by_id(event_id)
    if not event:
        return JSONResponse(
            content={"success": False, "error": "Événement non trouvé"},
            status_code=404
        )

    # Récupérer la liste de courses
    shopping_list = db.get_shopping_list_items(event_id)

    # Déterminer la devise selon la langue
    currency = 'EUR' if lang == 'fr' else 'JPY'

    updated_count = 0
    updated_items = []

    # Pour chaque ingrédient, récupérer le prix actuel du catalogue
    for item in shopping_list:
        ingredient_name = item['ingredient_name']
        quantity = item.get('needed_quantity') or item.get('purchase_quantity') or 0
        unit = item.get('needed_unit') or item.get('purchase_unit', '')

        # Sauter si pas de quantité
        if not quantity:
            continue

        # Calculer le prix depuis le catalogue
        price_result = db.calculate_ingredient_price(
            ingredient_name,
            quantity,
            unit,
            currency
        )

        if price_result and price_result.get('unit_price') is not None:
            unit_price = price_result['unit_price']

            # Mettre à jour le prix prévu avec le prix du catalogue
            db.update_shopping_list_item_prices(item['id'], unit_price, None)

            updated_count += 1
            updated_items.append({
                'id': item['id'],
                'name': ingredient_name,
                'unit_price': unit_price,
                'total_price': price_result.get('total_price', 0)
            })

    return JSONResponse(content={
        "success": True,
        "updated_count": updated_count,
        "items": updated_items,
        "message": f"{updated_count} prix mis à jour depuis le catalogue" if lang == 'fr'
                   else f"{updated_count}個の価格がカタログから更新されました"
    })


@router.post("/events/{event_id}/expenses/{expense_id}/update")
async def event_update_expense(
    request: Request,
    event_id: int,
    expense_id: int,
    lang: str = Form("fr"),
    category_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    planned_amount: Optional[str] = Form(None),
    actual_amount: Optional[str] = Form(None),
    is_paid: Optional[str] = Form(None),
    paid_date: Optional[str] = Form(None),
    notes: Optional[str] = Form(None)
):
    """
    Met à jour une dépense
    """
    # Convertir planned_amount en float si fourni
    planned_amount_float = None
    if planned_amount and planned_amount.strip():
        try:
            planned_amount_float = float(planned_amount)
        except ValueError:
            planned_amount_float = None

    # Convertir actual_amount en float si fourni
    actual_amount_float = None
    if actual_amount and actual_amount.strip():
        try:
            actual_amount_float = float(actual_amount)
        except ValueError:
            actual_amount_float = None

    # Convertir is_paid en booléen si fourni
    is_paid_bool = None
    if is_paid is not None:
        is_paid_bool = is_paid == "1"

    # Convertir paid_date (gérer chaîne vide)
    paid_date_str = None
    if paid_date and paid_date.strip():
        paid_date_str = paid_date

    success = db.update_event_expense(
        expense_id=expense_id,
        category_id=category_id,
        description=description,
        planned_amount=planned_amount_float,
        actual_amount=actual_amount_float,
        is_paid=is_paid_bool,
        paid_date=paid_date_str,
        notes=notes
    )

    if success:
        return RedirectResponse(
            url=f"/events/{event_id}/budget?lang={lang}",
            status_code=303
        )
    else:
        raise HTTPException(status_code=400, detail="Erreur lors de la mise à jour")


@router.post("/events/{event_id}/expenses/{expense_id}/delete")
async def event_delete_expense(
    request: Request,
    event_id: int,
    expense_id: int,
    lang: str = Form("fr")
):
    """
    Supprime une dépense
    """
    success = db.delete_event_expense(expense_id)

    if success:
        return RedirectResponse(
            url=f"/events/{event_id}/budget?lang={lang}",
            status_code=303
        )
    else:
        raise HTTPException(status_code=400, detail="Erreur lors de la suppression")


@router.get("/api/ingredient-price-suggestion")
async def api_get_ingredient_price_suggestion(
    ingredient_name: str,
    unit: str
):
    """
    API: Récupère les suggestions de prix pour un ingrédient
    """
    suggestions = db.get_ingredient_price_suggestions(ingredient_name, unit)
    return JSONResponse(content=suggestions)


@router.post("/api/shopping-list/items/{item_id}/update-prices")
async def api_update_shopping_list_item_prices(
    item_id: int,
    planned_unit_price: Optional[str] = Form(None),
    actual_unit_price: Optional[str] = Form(None),
    is_purchased: Optional[str] = Form(None)
):
    """
    API: Met à jour les prix d'un item de liste de courses
    """
    # Convertir planned_unit_price en float si fourni
    planned_price_float = None
    if planned_unit_price and planned_unit_price.strip():
        try:
            planned_price_float = float(planned_unit_price)
        except ValueError:
            planned_price_float = None

    # Convertir actual_unit_price en float si fourni
    actual_price_float = None
    if actual_unit_price and actual_unit_price.strip():
        try:
            actual_price_float = float(actual_unit_price)
        except ValueError:
            actual_price_float = None

    # Convertir is_purchased en booléen si fourni
    is_purchased_bool = None
    if is_purchased is not None:
        is_purchased_bool = is_purchased == "1"

    success = db.update_shopping_list_item(
        item_id=item_id,
        planned_unit_price=planned_price_float,
        actual_unit_price=actual_price_float,
        is_purchased=is_purchased_bool
    )

    if success:
        return JSONResponse(content={"success": True})
    else:
        raise HTTPException(status_code=400, detail="Erreur lors de la mise à jour")


@router.get("/api/ingredient-catalog-info")
async def api_get_ingredient_catalog_info(
    ingredient_name: str,
    lang: str = "fr"
):
    """
    API: Récupère les informations du catalogue pour un ingrédient
    Cherche par nom (français ou japonais selon la langue)
    """
    with db.get_db() as conn:
        cursor = conn.cursor()

        # Chercher l'ingrédient dans le catalogue (insensible à la casse)
        cursor.execute("""
            SELECT
                id,
                ingredient_name_fr,
                ingredient_name_jp,
                unit_fr,
                unit_jp,
                price_eur,
                price_jpy,
                qty,
                updated_at
            FROM ingredient_price_catalog
            WHERE LOWER(ingredient_name_fr) = LOWER(?) OR LOWER(ingredient_name_jp) = LOWER(?)
            LIMIT 1
        """, (ingredient_name, ingredient_name))

        result = cursor.fetchone()

        if result:
            return JSONResponse(content=dict(result))
        else:
            # Pas trouvé dans le catalogue, retourner un objet vide avec le nom
            return JSONResponse(content={
                "id": None,
                "ingredient_name_fr": ingredient_name if lang == "fr" else "",
                "ingredient_name_jp": ingredient_name if lang == "jp" else "",
                "unit_fr": "",
                "unit_jp": "",
                "price_eur": None,
                "price_jpy": None,
                "qty": 1.0,
                "updated_at": None
            })


@router.post("/api/ingredient-catalog-update")
async def api_update_ingredient_catalog(
    ingredient_id: Optional[int] = Form(None),
    ingredient_name_fr: str = Form(...),
    ingredient_name_jp: str = Form(""),
    unit_fr: str = Form("g"),
    unit_jp: str = Form("g"),
    price_eur: Optional[float] = Form(None),
    price_jpy: Optional[float] = Form(None),
    qty: float = Form(1.0)
):
    """
    API: Met à jour ou crée une entrée dans le catalogue de prix
    """
    with db.get_db() as conn:
        cursor = conn.cursor()

        if ingredient_id:
            # Mise à jour d'un ingrédient existant
            cursor.execute("""
                UPDATE ingredient_price_catalog
                SET ingredient_name_fr = ?,
                    ingredient_name_jp = ?,
                    unit_fr = ?,
                    unit_jp = ?,
                    price_eur = ?,
                    price_jpy = ?,
                    qty = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (ingredient_name_fr, ingredient_name_jp, unit_fr, unit_jp,
                  price_eur, price_jpy, qty, ingredient_id))

            return JSONResponse(content={"success": True, "id": ingredient_id})
        else:
            # Création d'un nouvel ingrédient
            cursor.execute("""
                INSERT INTO ingredient_price_catalog
                (ingredient_name_fr, ingredient_name_jp, unit_fr, unit_jp, price_eur, price_jpy, qty)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ingredient_name_fr, ingredient_name_jp, unit_fr, unit_jp,
                  price_eur, price_jpy, qty))

            new_id = cursor.lastrowid
            return JSONResponse(content={"success": True, "id": new_id})


# ============================================================================
# Routes pour l'organisation des événements multi-jours
# ============================================================================

@router.get("/events/{event_id}/organization")
async def event_organization_view(request: Request, event_id: int, lang: str = "fr"):
    """
    Affiche l'organisation des recettes par jour (lecture seule)
    """
    event = db.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")

    # Récupérer la planification par jour
    planning_by_date = db.get_recipe_planning(event_id, lang)

    return templates.TemplateResponse(
        "event_organization.html",
        {
            "request": request,
            "lang": lang,
            "event": event,
            "planning_by_date": planning_by_date
        }
    )


@router.get("/events/{event_id}/planning")
async def event_planning_edit(request: Request, event_id: int, lang: str = "fr"):
    """
    Écran de planification avec drag & drop des recettes vers les dates
    """
    event = db.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")

    # Récupérer les recettes de l'événement
    recipes = db.get_event_recipes(event_id, lang)

    # Récupérer les dates sélectionnées de l'événement
    event_dates = db.get_event_dates(event_id)
    # Filtrer seulement les dates sélectionnées
    selected_dates = [d for d in event_dates if d['is_selected']]

    # Récupérer la planification existante
    planning_by_date = db.get_recipe_planning(event_id, lang)

    return templates.TemplateResponse(
        "event_planning.html",
        {
            "request": request,
            "lang": lang,
            "event": event,
            "recipes": recipes,
            "selected_dates": selected_dates,
            "planning_by_date": planning_by_date
        }
    )


@router.post("/events/{event_id}/planning/save")
async def event_planning_save(
    request: Request,
    event_id: int,
    lang: str = Form("fr")
):
    """
    Sauvegarde la planification des recettes par jour
    """
    form_data = await request.form()

    # Parser les données de planification
    planning_data = []
    i = 0
    while f"planning[{i}][recipe_id]" in form_data:
        planning_data.append({
            'recipe_id': int(form_data[f"planning[{i}][recipe_id]"]),
            'event_date_id': int(form_data[f"planning[{i}][event_date_id]"]),
            'position': int(form_data[f"planning[{i}][position]"])
        })
        i += 1

    # Sauvegarder la planification
    db.save_recipe_planning(event_id, planning_data)

    return RedirectResponse(
        url=f"/events/{event_id}/organization?lang={lang}",
        status_code=303
    )
