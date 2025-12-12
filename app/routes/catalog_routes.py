"""
Routes pour la gestion du catalogue des prix des ingrédients
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.models import db
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/ingredient-catalog")
async def ingredient_catalog(
    request: Request,
    lang: str = "fr",
    search: Optional[str] = None
):
    """
    Page de gestion du catalogue des prix des ingrédients
    """
    ingredients = db.list_ingredient_catalog(search, lang)

    return templates.TemplateResponse("ingredient_catalog.html", {
        "request": request,
        "lang": lang,
        "ingredients": ingredients,
        "search": search or ""
    })


@router.post("/ingredient-catalog/sync")
async def sync_catalog(lang: str = Form("fr")):
    """
    Synchronise le catalogue avec les ingrédients des recettes
    """
    count = db.sync_ingredients_from_recipes()
    # TODO: Ajouter un message flash pour afficher "{count} ingrédients ajoutés"
    return RedirectResponse(f"/ingredient-catalog?lang={lang}", status_code=303)




@router.post("/ingredient-catalog/{ingredient_id}/update")
async def update_ingredient_price(
    ingredient_id: int,
    lang: str = Form("fr"),
    price_eur: Optional[str] = Form(None),
    price_jpy: Optional[str] = Form(None),
    qty: Optional[str] = Form(None),
    unit: str = Form(...)
):
    """
    Met à jour les prix d'un ingrédient
    """
    # Convertir les prix (gérer les chaînes vides)
    eur = None
    if price_eur and price_eur.strip():
        try:
            eur = float(price_eur)
        except ValueError:
            pass

    jpy = None
    if price_jpy and price_jpy.strip():
        try:
            jpy = float(price_jpy)
        except ValueError:
            pass

    # Convertir la quantité
    quantity = None
    if qty and qty.strip():
        try:
            quantity = float(qty)
        except ValueError:
            pass

    # Mettre à jour l'unité selon la langue affichée
    if lang == 'jp':
        db.update_ingredient_catalog_price(ingredient_id, eur, jpy, unit_jp=unit, qty=quantity)
    else:
        db.update_ingredient_catalog_price(ingredient_id, eur, jpy, unit_fr=unit, qty=quantity)

    return RedirectResponse(f"/ingredient-catalog?lang={lang}", status_code=303)


@router.post("/ingredient-catalog/{ingredient_id}/delete")
async def delete_ingredient_from_catalog(
    ingredient_id: int,
    lang: str = Form("fr")
):
    """
    Supprime un ingrédient du catalogue
    """
    db.delete_ingredient_from_catalog(ingredient_id)
    return RedirectResponse(f"/ingredient-catalog?lang={lang}", status_code=303)


# ============================================================================
# GESTION DES CONVERSIONS D'UNITÉS
# ============================================================================

@router.get("/unit-conversions")
async def unit_conversions(
    request: Request,
    lang: str = "fr",
    search: Optional[str] = None
):
    """
    Page de gestion des conversions d'unités
    """
    conversions = db.get_all_unit_conversions(search)

    return templates.TemplateResponse("unit_conversions.html", {
        "request": request,
        "lang": lang,
        "conversions": conversions,
        "search": search or ""
    })


@router.post("/unit-conversions/add")
async def add_unit_conversion(
    request: Request,
    lang: str = Form("fr"),
    from_unit: str = Form(...),
    to_unit: str = Form(...),
    factor: float = Form(...),
    category: Optional[str] = Form(None),
    notes: Optional[str] = Form(None)
):
    """
    Ajoute une nouvelle conversion d'unité
    """
    try:
        db.add_unit_conversion(from_unit, to_unit, factor, category, notes)
        return RedirectResponse(f"/unit-conversions?lang={lang}", status_code=303)
    except Exception as e:
        # Si c'est une erreur de contrainte UNIQUE
        if "UNIQUE constraint failed" in str(e):
            error_msg = {
                "fr": f"Erreur : Une conversion de {from_unit} vers {to_unit} existe déjà. Chaque paire d'unités doit être unique.",
                "jp": f"エラー：{from_unit}から{to_unit}への変換は既に存在します。各単位ペアは一意である必要があります。"
            }
            # Récupérer toutes les conversions pour réafficher la page avec l'erreur
            conversions = db.get_all_unit_conversions()
            return templates.TemplateResponse(
                "unit_conversions.html",
                {
                    "request": request,
                    "lang": lang,
                    "conversions": conversions,
                    "error": error_msg.get(lang, error_msg["fr"])
                }
            )
        else:
            # Autre erreur, la relancer
            raise


@router.post("/unit-conversions/{conversion_id}/update")
async def update_unit_conversion(
    request: Request,
    conversion_id: int,
    lang: str = Form("fr"),
    from_unit: str = Form(...),
    to_unit: str = Form(...),
    factor: float = Form(...),
    category: Optional[str] = Form(None),
    notes: Optional[str] = Form(None)
):
    """
    Met à jour une conversion existante
    """
    try:
        db.update_unit_conversion(conversion_id, from_unit, to_unit, factor, category, notes)
        return RedirectResponse(f"/unit-conversions?lang={lang}", status_code=303)
    except Exception as e:
        # Si c'est une erreur de contrainte UNIQUE
        if "UNIQUE constraint failed" in str(e):
            error_msg = {
                "fr": f"Erreur : Une conversion de {from_unit} vers {to_unit} existe déjà. Chaque paire d'unités doit être unique.",
                "jp": f"エラー：{from_unit}から{to_unit}への変換は既に存在します。各単位ペアは一意である必要があります。"
            }
            # Récupérer toutes les conversions pour réafficher la page avec l'erreur
            conversions = db.get_all_unit_conversions()
            return templates.TemplateResponse(
                "unit_conversions.html",
                {
                    "request": request,
                    "lang": lang,
                    "conversions": conversions,
                    "error": error_msg.get(lang, error_msg["fr"])
                }
            )
        else:
            # Autre erreur, la relancer
            raise


@router.post("/unit-conversions/{conversion_id}/delete")
async def delete_unit_conversion(
    conversion_id: int,
    lang: str = Form("fr")
):
    """
    Supprime une conversion d'unité
    """
    db.delete_unit_conversion(conversion_id)
    return RedirectResponse(f"/unit-conversions?lang={lang}", status_code=303)


# ============================================================================
# VISUALISATION DES LOGS D'ACCÈS
# ============================================================================

@router.get("/access-logs")
async def access_logs(
    request: Request,
    lang: str = "fr",
    time_range: int = 24
):
    """
    Page de visualisation des logs d'accès
    """
    # Récupérer les statistiques pour la période demandée
    stats = db.get_access_stats(hours=time_range)

    # Récupérer les 50 derniers logs de la période
    recent_logs = db.get_recent_access_logs(limit=50, hours=time_range)

    # Récupérer les statistiques de performance côté client
    # DÉSACTIVÉ: Nécessite table client_performance_log (migration non appliquée en prod)
    client_stats = {}  # db.get_client_performance_stats(hours=time_range)

    # Calculer le temps de réponse moyen
    avg_response_time = None
    if stats['slow_pages']:
        total_time = sum(page['avg_time'] * page['count'] for page in stats['slow_pages'])
        total_count = sum(page['count'] for page in stats['slow_pages'])
        if total_count > 0:
            avg_response_time = total_time / total_count

    return templates.TemplateResponse("access_logs.html", {
        "request": request,
        "lang": lang,
        "time_range": time_range,
        "stats": stats,
        "client_stats": client_stats,
        "recent_logs": recent_logs,
        "avg_response_time": avg_response_time
    })
