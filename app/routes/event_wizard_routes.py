# app/routes/event_wizard_routes.py
"""
Parcours guidé de création d'événement, pensé pour être très simple :
  1. Nom, nombre de personnes, type
  2. Dates
  3. Recettes
  4. Quelle recette quel jour
  5. Liste de courses

Les événements créés ici sont des événements normaux, modifiables
ensuite avec les écrans existants (/events/{id}).
"""
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from app.models import db
from app.routes.event_routes import _check_event_access, ensure_shopping_list
from app.template_config import templates

router = APIRouter()

MAX_DAYS = 60


def _get_event_or_404(event_id: int, request: Request) -> dict:
    event = db.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")
    _check_event_access(event, request)
    return event


def _date_range(date_debut: str, date_fin: str) -> list:
    """Liste des dates ISO entre début et fin (inversées si besoin, bornées à MAX_DAYS)."""
    start = date.fromisoformat(date_debut)
    end = date.fromisoformat(date_fin) if date_fin else start
    if end < start:
        start, end = end, start
    nb_days = min((end - start).days + 1, MAX_DAYS)
    return [(start + timedelta(days=i)).isoformat() for i in range(nb_days)]


_WEEKDAYS = {
    'fr': ['lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.', 'dim.'],
    'jp': ['月', '火', '水', '木', '金', '土', '日'],
}


def _day_label(iso_date: str, lang: str) -> str:
    """'sam. 14/11' en français, '11/14(土)' en japonais."""
    d = date.fromisoformat(iso_date)
    if lang == 'jp':
        return f"{d.month}/{d.day}({_WEEKDAYS['jp'][d.weekday()]})"
    return f"{_WEEKDAYS['fr'][d.weekday()]} {d.day:02d}/{d.month:02d}"


def _parse_days(days: str, dates: list, default_attendees: int) -> dict:
    """
    'YYYY-MM-DD:8,YYYY-MM-DD:12' -> {date: convives} pour chaque date de l'événement.
    None quand le jour a le même nombre que l'événement.
    """
    values = {}
    for part in days.split(","):
        day, _, count = part.partition(":")
        if count.isdigit() and int(count) > 0:
            values[day.strip()] = int(count)
    return {
        d: (values[d] if values.get(d, default_attendees) != default_attendees else None)
        for d in dates
    }


def _sync_servings(event_id: int, lang: str, force_refresh: bool = False):
    """
    Portions de chaque recette = convives du jour où elle est prévue
    (somme si plusieurs jours, convives de l'événement si aucun jour).

    La liste de courses calcule déjà (convives événement / portions recette)
    × servings_multiplier : servings_multiplier est donc le rapport
    convives du jour / convives de l'événement.
    """
    event = db.get_event_by_id(event_id)
    dates = {d['id']: d for d in db.get_event_dates(event_id) if d['is_selected']}
    people_by_recipe = {}
    for day in db.get_recipe_planning(event_id, lang).values():
        day_people = dates[day['event_date_id']]['attendees'] or event['attendees']
        for recipe in day['recipes']:
            people_by_recipe[recipe['id']] = people_by_recipe.get(recipe['id'], 0) + day_people

    changed = False
    for recipe in db.get_event_recipes(event_id, lang):
        multiplier = round(people_by_recipe.get(recipe['id'], event['attendees']) / event['attendees'], 3)
        if abs(multiplier - recipe['servings_multiplier']) > 0.001:
            db.update_event_recipe_servings(event_id, recipe['id'], multiplier)
            changed = True
    if changed or force_refresh:
        # Liste de courses recalculée, en gardant les ingrédients retirés
        # et les quantités modifiées à la main
        db.refresh_shopping_list(event_id, lang)


def _people_by_day(event: dict, lang: str) -> list:
    """[(libellé du jour, convives)] pour les jours de l'événement."""
    return [
        (_day_label(d['date'], lang), d['attendees'] or event['attendees'])
        for d in db.get_event_dates(event['id']) if d['is_selected']
    ]


def _redirect(next_url: str, default_url: str) -> RedirectResponse:
    """Redirige vers next_url (navigation dans le parcours) sinon vers l'étape suivante."""
    if next_url.startswith("/event-wizard/") or next_url.startswith("/events/"):
        return RedirectResponse(url=next_url, status_code=303)
    return RedirectResponse(url=default_url, status_code=303)


def _ctx(request: Request, lang: str, step: int, **extra) -> dict:
    return {"request": request, "lang": lang, "step": step, **extra}


# ============================================================================
# Étape 1 : nom, nombre de personnes, type
# ============================================================================

@router.get("/event-wizard", response_class=HTMLResponse)
async def wizard_info(
    request: Request,
    lang: str = "fr",
    name: str = "",
    attendees: int = 10,
    event_type_id: int = 0,
    date_debut: str = "",
    date_fin: str = "",
    days: str = ""
):
    """Étape 1 d'un nouvel événement (paramètres présents = retour depuis l'étape 2)."""
    if not name:
        # Nouveau parcours : oublier l'événement du parcours précédent
        request.session.pop('wizard_event_id', None)
    return templates.TemplateResponse(
        "event_wizard/step_info.html",
        _ctx(request, lang, 1,
             event=None, name=name, attendees=attendees, event_type_id=event_type_id,
             date_debut=date_debut, date_fin=date_fin, days=days,
             event_types=db.list_event_types())
    )


@router.get("/event-wizard/{event_id}/info", response_class=HTMLResponse)
async def wizard_info_edit(request: Request, event_id: int, lang: str = "fr"):
    """Étape 1 d'un événement déjà créé."""
    event = _get_event_or_404(event_id, request)
    return templates.TemplateResponse(
        "event_wizard/step_info.html",
        _ctx(request, lang, 1,
             event=event, name=event['name'], attendees=event['attendees'],
             event_type_id=event['event_type_id'], date_debut="", date_fin="", days="",
             event_types=db.list_event_types())
    )


@router.post("/event-wizard/{event_id}/info")
async def wizard_info_save(
    request: Request,
    event_id: int,
    lang: str = Form("fr"),
    name: str = Form(...),
    attendees: int = Form(...),
    event_type_id: int = Form(...),
    next: str = Form("")
):
    event = _get_event_or_404(event_id, request)
    attendees = max(attendees, 1)
    db.update_event(
        event_id=event_id,
        event_type_id=event_type_id,
        name=name.strip() or event['name'],
        event_date=event['event_date'],
        location=event['location'] or "",
        attendees=attendees,
        notes=event['notes'] or "",
        date_debut=event['date_debut'],
        date_fin=event['date_fin'],
        nombre_jours=event['nombre_jours']
    )
    # Les jours sans nombre propre suivent le nouveau nombre de l'événement ;
    # la liste de courses dépend directement du nombre de convives
    _sync_servings(event_id, lang, force_refresh=attendees != event['attendees'])
    return _redirect(next, f"/event-wizard/{event_id}/dates?lang={lang}")


# ============================================================================
# Étape 2 : dates
# ============================================================================

@router.get("/event-wizard/dates", response_class=HTMLResponse)
async def wizard_dates_new(
    request: Request,
    lang: str = "fr",
    name: str = "",
    attendees: int = 10,
    event_type_id: int = 0,
    date_debut: str = "",
    date_fin: str = "",
    days: str = ""
):
    """Dates d'un événement pas encore créé (données de l'étape 1 transmises)."""
    if not name.strip() or not event_type_id:
        return RedirectResponse(url=f"/event-wizard?lang={lang}", status_code=303)
    # Les dates sont ajoutées côté navigateur pour conserver la saisie en cours
    back_url = "/event-wizard?" + urlencode({
        "lang": lang, "name": name, "attendees": attendees, "event_type_id": event_type_id
    })
    date_debut = date_debut or date.today().isoformat()
    attendees = max(attendees, 1)
    date_fin = date_fin or date_debut
    return templates.TemplateResponse(
        "event_wizard/step_dates.html",
        _ctx(request, lang, 2,
             event=None, name=name.strip(), attendees=attendees,
             event_type_id=event_type_id, date_debut=date_debut, date_fin=date_fin,
             day_counts={d: n for d, n in _parse_days(days, _date_range(date_debut, date_fin), attendees).items() if n},
             form_action="/event-wizard/create", back_url=back_url)
    )


@router.post("/event-wizard/create")
async def wizard_create(
    request: Request,
    lang: str = Form("fr"),
    name: str = Form(...),
    attendees: int = Form(...),
    event_type_id: int = Form(...),
    date_debut: str = Form(...),
    date_fin: str = Form(""),
    days: str = Form("")
):
    # Retour arrière du navigateur jusqu'à l'étape 2 puis « Suivant » :
    # on met à jour l'événement déjà créé par ce parcours au lieu d'en créer un second
    wizard_event_id = request.session.get('wizard_event_id')
    if wizard_event_id and db.get_event_by_id(wizard_event_id):
        event = _get_event_or_404(wizard_event_id, request)
        db.update_event(
            event_id=wizard_event_id, event_type_id=event_type_id, name=name.strip(),
            event_date=event['event_date'], location=event['location'] or "",
            attendees=event['attendees'], notes=event['notes'] or "",
            date_debut=event['date_debut'], date_fin=event['date_fin'],
            nombre_jours=event['nombre_jours']
        )
        return await wizard_dates_save(request, wizard_event_id, lang=lang, date_debut=date_debut,
                                       date_fin=date_fin, days=days, next="")

    dates = _date_range(date_debut, date_fin)
    event_id = db.create_event(
        event_type_id=event_type_id,
        name=name.strip(),
        event_date=dates[0],
        location="",
        attendees=max(attendees, 1),
        user_id=request.session.get('user_id'),
        date_debut=dates[0],
        date_fin=dates[-1],
        nombre_jours=len(dates)
    )
    attendees_by_date = _parse_days(days, dates, max(attendees, 1))
    db.save_event_dates(event_id, [
        {'date': d, 'is_selected': True, 'attendees': attendees_by_date[d]} for d in dates
    ])
    request.session['wizard_event_id'] = event_id
    return RedirectResponse(url=f"/event-wizard/{event_id}/recipes?lang={lang}", status_code=303)


@router.get("/event-wizard/{event_id}/dates", response_class=HTMLResponse)
async def wizard_dates_edit(request: Request, event_id: int, lang: str = "fr"):
    """Retour à l'étape 2 depuis l'étape 3 : modifie les dates de l'événement créé."""
    event = _get_event_or_404(event_id, request)
    return templates.TemplateResponse(
        "event_wizard/step_dates.html",
        _ctx(request, lang, 2,
             event=event, name=event['name'], attendees=event['attendees'],
             event_type_id=event['event_type_id'],
             date_debut=event['date_debut'] or event['event_date'],
             date_fin=event['date_fin'] or event['event_date'],
             day_counts={d['date']: d['attendees'] for d in db.get_event_dates(event_id)
                         if d['is_selected'] and d['attendees']},
             planned_by_date={day['date']: [r['name'] for r in day['recipes']]
                              for day in db.get_recipe_planning(event_id, lang).values() if day['recipes']},
             form_action=f"/event-wizard/{event_id}/dates",
             back_url=f"/event-wizard/{event_id}/info?lang={lang}")
    )


@router.post("/event-wizard/{event_id}/dates")
async def wizard_dates_save(
    request: Request,
    event_id: int,
    lang: str = Form("fr"),
    date_debut: str = Form(...),
    date_fin: str = Form(""),
    days: str = Form(""),
    next: str = Form("")
):
    event = _get_event_or_404(event_id, request)
    dates = _date_range(date_debut, date_fin)
    attendees_by_date = _parse_days(days, dates, event['attendees'])
    old_dates = [d['date'] for d in db.get_event_dates(event_id) if d['is_selected']]
    if dates == old_dates:
        # Mêmes dates : on garde le planning, seuls les convives par jour changent
        db.update_event_dates_attendees(event_id, attendees_by_date)
    else:
        db.update_event(
            event_id=event_id,
            event_type_id=event['event_type_id'],
            name=event['name'],
            event_date=dates[0],
            location=event['location'] or "",
            attendees=event['attendees'],
            notes=event['notes'] or "",
            date_debut=dates[0],
            date_fin=dates[-1],
            nombre_jours=len(dates)
        )
        # Recrée les dates : le planning des jours retirés est supprimé
        db.save_event_dates(event_id, [
            {'date': d, 'is_selected': True, 'attendees': attendees_by_date[d]} for d in dates
        ])
    _sync_servings(event_id, lang)
    return _redirect(next, f"/event-wizard/{event_id}/recipes?lang={lang}")


# ============================================================================
# Étape 3 : recettes
# ============================================================================

@router.get("/event-wizard/{event_id}/recipes", response_class=HTMLResponse)
async def wizard_recipes(request: Request, event_id: int, lang: str = "fr"):
    event = _get_event_or_404(event_id, request)

    suggested_ids = {r['id'] for r in db.list_recipes_by_event_types([event['event_type_id']], lang)}
    recipes = db.list_recipes(lang)
    # Recettes habituelles pour ce type d'événement en premier
    recipes.sort(key=lambda r: (r['id'] not in suggested_ids, (r['name'] or '').lower()))
    selected_ids = [r['id'] for r in db.get_event_recipes(event_id, lang)]
    types_by_recipe = db.get_all_recipe_event_type_ids()
    for recipe in recipes:
        recipe['event_type_ids'] = types_by_recipe.get(recipe['id'], [])

    return templates.TemplateResponse(
        "event_wizard/step_recipes.html",
        _ctx(request, lang, 3,
             event=event, recipes=recipes, event_types=db.list_event_types(),
             suggested_ids=list(suggested_ids), selected_ids=selected_ids,
             # Filtre initial : les recettes déjà choisies (retour sur l'étape),
             # sinon le type de l'événement s'il a des recettes associées
             initial_type_id=-1 if selected_ids else (event['event_type_id'] if suggested_ids else 0))
    )


@router.post("/event-wizard/{event_id}/recipes")
async def wizard_recipes_save(request: Request, event_id: int, lang: str = Form("fr"), next: str = Form("")):
    event = _get_event_or_404(event_id, request)
    form_data = await request.form()
    wanted_ids = {int(v) for v in form_data.getlist("recipe_ids")}

    current_ids = {r['id'] for r in db.get_event_recipes(event_id, lang)}
    to_add = wanted_ids - current_ids
    to_remove = current_ids - wanted_ids

    if to_add:
        existing_ids = {r['id'] for r in db.list_recipes(lang)}
        for recipe_id in to_add & existing_ids:
            db.add_recipe_to_event(event_id, recipe_id, 1.0)
    for recipe_id in to_remove:
        db.remove_recipe_from_event(event_id, recipe_id)

    selected_dates = [d for d in db.get_event_dates(event_id) if d['is_selected']]
    if len(selected_dates) == 1:
        # Un seul jour : pas besoin de demander quelle recette quel jour
        recipes = db.get_event_recipes(event_id, lang)
        db.save_recipe_planning(event_id, [
            {'recipe_id': r['id'], 'event_date_id': selected_dates[0]['id'], 'position': i}
            for i, r in enumerate(recipes)
        ])
    _sync_servings(event_id, lang, force_refresh=bool(to_add or to_remove))
    if len(selected_dates) == 1:
        return _redirect(next, f"/event-wizard/{event_id}/shopping?lang={lang}")
    return _redirect(next, f"/event-wizard/{event_id}/planning?lang={lang}")


# ============================================================================
# Étape 4 : quelle recette quel jour
# ============================================================================

@router.get("/event-wizard/{event_id}/planning", response_class=HTMLResponse)
async def wizard_planning(request: Request, event_id: int, lang: str = "fr"):
    event = _get_event_or_404(event_id, request)
    recipes = db.get_event_recipes(event_id, lang)
    selected_dates = [
        {**d, 'label': _day_label(d['date'], lang), 'people': d['attendees'] or event['attendees']}
        for d in db.get_event_dates(event_id) if d['is_selected']
    ]

    # Planning existant sous forme "recipe_id:event_date_id"
    planned = [
        f"{r['id']}:{day['event_date_id']}"
        for day in db.get_recipe_planning(event_id, lang).values()
        for r in day['recipes']
    ]

    return templates.TemplateResponse(
        "event_wizard/step_planning.html",
        _ctx(request, lang, 4,
             event=event, recipes=recipes, dates=selected_dates, planned=planned)
    )


@router.post("/event-wizard/{event_id}/planning")
async def wizard_planning_save(request: Request, event_id: int, lang: str = Form("fr"), next: str = Form("")):
    _get_event_or_404(event_id, request)
    form_data = await request.form()

    recipe_order = {r['id']: i for i, r in enumerate(db.get_event_recipes(event_id, lang))}
    valid_date_ids = {d['id'] for d in db.get_event_dates(event_id) if d['is_selected']}

    pairs = []
    for value in form_data.getlist("plan"):
        recipe_id, event_date_id = (int(x) for x in value.split(":"))
        if recipe_id in recipe_order and event_date_id in valid_date_ids:
            pairs.append((recipe_id, event_date_id))
    pairs.sort(key=lambda p: (p[1], recipe_order[p[0]]))

    planning_data = []
    position_by_date = {}
    for recipe_id, event_date_id in pairs:
        position = position_by_date.get(event_date_id, 0)
        position_by_date[event_date_id] = position + 1
        planning_data.append({'recipe_id': recipe_id, 'event_date_id': event_date_id, 'position': position})

    db.save_recipe_planning(event_id, planning_data)
    _sync_servings(event_id, lang)
    return _redirect(next, f"/event-wizard/{event_id}/shopping?lang={lang}")


# ============================================================================
# Étape 5 : liste de courses
# ============================================================================

@router.get("/event-wizard/{event_id}/shopping", response_class=HTMLResponse)
async def wizard_shopping(request: Request, event_id: int, lang: str = "fr"):
    event = _get_event_or_404(event_id, request)
    _sync_servings(event_id, lang)
    recipes, items = ensure_shopping_list(event_id, lang)
    nb_dates = len([d for d in db.get_event_dates(event_id) if d['is_selected']])
    event_recipe_ids = {r['id'] for r in db.get_event_recipes(event_id, lang)}
    # Recettes sans ingrédients en base : absentes de la liste de courses
    empty_recipes = [r['name'] for r in db.list_recipes(lang)
                     if r['id'] in event_recipe_ids and not r['ingredient_count']]

    return templates.TemplateResponse(
        "event_wizard/step_shopping.html",
        _ctx(request, lang, 5,
             event=event, recipes=recipes, items=items, empty_recipes=empty_recipes,
             nb_recipes=len(event_recipe_ids), people_by_day=_people_by_day(event, lang),
             back_url=(f"/event-wizard/{event_id}/planning?lang={lang}" if nb_dates > 1
                       else f"/event-wizard/{event_id}/recipes?lang={lang}"))
    )


@router.post("/event-wizard/{event_id}/shopping/{item_id}")
async def wizard_shopping_item_save(
    request: Request,
    event_id: int,
    item_id: int,
    purchase_quantity: Optional[float] = Form(None),
    purchase_unit: Optional[str] = Form(None),
    excluded: Optional[bool] = Form(None)
):
    """Modification d'une ligne de la liste de courses (enregistrement immédiat)."""
    _get_event_or_404(event_id, request)
    if item_id not in {item['id'] for item in db.get_shopping_list_items(event_id)}:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    db.update_shopping_list_item(
        item_id=item_id,
        purchase_quantity=purchase_quantity,
        purchase_unit=purchase_unit.strip() if purchase_unit is not None else None,
        excluded=excluded
    )
    return JSONResponse(content={"success": True})
