# -*- coding: utf-8 -*-
"""
Routes pour le calendrier de planification des repas.
"""

from fastapi import APIRouter, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import datetime

from app.models import (
    get_calendar_data,
    get_day_detail,
    add_meal,
    delete_meal,
    get_todo_recipes,
    get_db,
)
from app.template_config import templates

router = APIRouter()


def _require_user(request: Request, lang: str = "fr"):
    """Retourne (user_id, None) ou (None, RedirectResponse)."""
    user_id = request.session.get('user_id')
    if not user_id:
        return None, RedirectResponse(f"/login?lang={lang}", status_code=302)
    return user_id, None


# ---------------------------------------------------------------------------
# Page principale du calendrier
# ---------------------------------------------------------------------------

@router.get("/calendar")
async def calendar_page(request: Request, lang: str = "fr"):
    user_id, redirect = _require_user(request, lang)
    if redirect:
        return redirect

    today = datetime.date.today()
    return templates.TemplateResponse("calendar.html", {
        "request": request,
        "lang": lang,
        "today_year": today.year,
        "today_month": today.month,
        "today_day": today.day,
    })


# ---------------------------------------------------------------------------
# API : données d'un mois
# ---------------------------------------------------------------------------

@router.get("/api/calendar/month")
async def api_calendar_month(
    request: Request,
    year: int = Query(None),
    month: int = Query(None),
    lang: str = Query("fr"),
):
    user_id, redirect = _require_user(request, lang)
    if redirect:
        return JSONResponse({"error": "unauthenticated"}, status_code=401)

    today = datetime.date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month

    data = get_calendar_data(year, month, lang, user_id)
    return JSONResponse(data)


# ---------------------------------------------------------------------------
# API : détail d'un jour
# ---------------------------------------------------------------------------

@router.get("/api/calendar/day")
async def api_calendar_day(
    request: Request,
    date: str = Query(...),
    lang: str = Query("fr"),
):
    user_id, redirect = _require_user(request, lang)
    if redirect:
        return JSONResponse({"error": "unauthenticated"}, status_code=401)

    detail = get_day_detail(date, lang, user_id)
    return JSONResponse(detail)


# ---------------------------------------------------------------------------
# API : recherche de recettes pour le calendrier (autocomplete)
# Cherche dans recipe_translation.name — plus fiable que search_recipes_by_filters
# ---------------------------------------------------------------------------

@router.get("/api/calendar/recipes/search")
async def api_calendar_recipe_search(
    request: Request,
    q: str = Query(""),
    lang: str = Query("fr"),
):
    user_id, redirect = _require_user(request, lang)
    if redirect:
        return JSONResponse({"error": "unauthenticated"}, status_code=401)

    if not q or len(q) < 2:
        return JSONResponse([])

    with get_db() as con:
        rows = con.execute(
            """
            SELECT r.id, r.slug, r.thumbnail_url, rt.name
            FROM recipe r
            JOIN recipe_translation rt ON rt.recipe_id = r.id AND rt.lang = ?
            WHERE LOWER(rt.name) LIKE LOWER(?)
            ORDER BY rt.name
            LIMIT 10
            """,
            (lang, f"%{q}%")
        ).fetchall()

    return JSONResponse([
        {
            "id": row["id"],
            "slug": row["slug"],
            "thumbnail_url": row["thumbnail_url"],
            "name": row["name"],
        }
        for row in rows
    ])


# ---------------------------------------------------------------------------
# API : liste des repas libres (recettes à créer)
# ---------------------------------------------------------------------------

@router.get("/api/calendar/todo-recipes")
async def api_todo_recipes(request: Request, lang: str = Query("fr")):
    user_id, redirect = _require_user(request, lang)
    if redirect:
        return JSONResponse({"error": "unauthenticated"}, status_code=401)

    todos = get_todo_recipes(user_id)
    return JSONResponse(todos)


# ---------------------------------------------------------------------------
# API : ajouter un repas
# ---------------------------------------------------------------------------

class MealPlanCreate(BaseModel):
    date: str
    meal_type: str = "dinner"
    recipe_id: Optional[int] = None
    free_text: Optional[str] = None
    notes: Optional[str] = None


@router.post("/api/meal-plan")
async def api_add_meal(request: Request, body: MealPlanCreate, lang: str = Query("fr")):
    user_id, redirect = _require_user(request, lang)
    if redirect:
        return JSONResponse({"error": "unauthenticated"}, status_code=401)

    if not body.recipe_id and not body.free_text:
        return JSONResponse({"error": "recipe_id ou free_text requis"}, status_code=400)

    meal_id = add_meal(
        user_id=user_id,
        date=body.date,
        meal_type=body.meal_type,
        recipe_id=body.recipe_id,
        free_text=body.free_text,
        notes=body.notes,
    )
    return JSONResponse({"id": meal_id})


# ---------------------------------------------------------------------------
# API : supprimer un repas personnel
# ---------------------------------------------------------------------------

@router.delete("/api/meal-plan/{meal_id}")
async def api_delete_meal(request: Request, meal_id: int, lang: str = Query("fr")):
    user_id, redirect = _require_user(request, lang)
    if redirect:
        return JSONResponse({"error": "unauthenticated"}, status_code=401)

    ok = delete_meal(meal_id, user_id)
    if not ok:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse({"ok": True})
