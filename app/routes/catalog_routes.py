"""
Routes pour la gestion du catalogue des prix des ingrédients
"""
from fastapi import APIRouter, Request, Form, UploadFile
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
    unit: str = Form(...),
    conversion_category: Optional[str] = Form(None)
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
        db.update_ingredient_catalog_price(ingredient_id, eur, jpy, unit_jp=unit, qty=quantity, conversion_category=conversion_category)
    else:
        db.update_ingredient_catalog_price(ingredient_id, eur, jpy, unit_fr=unit, qty=quantity, conversion_category=conversion_category)

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


# ============================================================================
# GESTION DES TICKETS DE CAISSE (RECEIPT UPLOAD)
# ============================================================================

@router.get("/receipt-list")
async def receipt_list(
    request: Request,
    lang: str = "fr"
):
    """
    Page de liste de tous les tickets de caisse uploadés
    """
    receipts = db.list_all_receipts(lang=lang, limit=100)

    return templates.TemplateResponse("receipt_list.html", {
        "request": request,
        "lang": lang,
        "receipts": receipts
    })


@router.get("/receipt-upload")
async def receipt_upload_form(
    request: Request,
    lang: str = "fr"
):
    """
    Page d'upload d'un ticket de caisse PDF
    """
    return templates.TemplateResponse("receipt_upload.html", {
        "request": request,
        "lang": lang
    })


@router.post("/receipt-upload")
async def receipt_upload_process(
    request: Request,
    lang: str = Form("fr"),
    receipt_name: Optional[str] = Form(None),
    pdf_file: UploadFile = None
):
    """
    Traite l'upload d'un ticket de caisse PDF
    """
    import tempfile
    import os
    from app.services.receipt_extractor import get_receipt_extractor
    from app.services.ingredient_matcher import get_ingredient_matcher

    if not pdf_file:
        return templates.TemplateResponse("receipt_upload.html", {
            "request": request,
            "lang": lang,
            "error": "Aucun fichier sélectionné" if lang == "fr" else "ファイルが選択されていません"
        })

    # Sauvegarder temporairement le fichier PDF
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await pdf_file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # Extraire le contenu du PDF
        extractor = get_receipt_extractor()
        currency_hint = "JPY" if lang == "jp" else "EUR"
        receipt_data = extractor.extract_receipt_from_pdf(temp_path, currency_hint)

        # Nettoyer le fichier temporaire
        os.unlink(temp_path)

        if not receipt_data:
            return templates.TemplateResponse("receipt_upload.html", {
                "request": request,
                "lang": lang,
                "error": "Impossible d'extraire les données du PDF" if lang == "fr" else "PDFからデータを抽出できません"
            })

        # Créer l'enregistrement du receipt
        receipt_id = db.create_receipt_upload(
            filename=pdf_file.filename,
            receipt_name=receipt_name if receipt_name and receipt_name.strip() else None,
            store_name=receipt_data.get('store_name'),
            receipt_date=receipt_data.get('date'),
            currency=receipt_data.get('currency', currency_hint),
            user_id=None  # TODO: récupérer user_id de la session
        )

        # Matcher les ingrédients
        matcher = get_ingredient_matcher()
        matched_items = matcher.match_all_items(receipt_data['items'], lang)

        # Sauvegarder les items matchés
        db.save_receipt_items(receipt_id, matched_items)

        # Mettre à jour le statut
        db.update_receipt_status(receipt_id, 'pending')

        # Rediriger vers la page de révision
        return RedirectResponse(f"/receipt-review/{receipt_id}?lang={lang}", status_code=303)

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors du traitement du ticket: {e}", exc_info=True)

        # Nettoyer le fichier temporaire en cas d'erreur
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)

        return templates.TemplateResponse("receipt_upload.html", {
            "request": request,
            "lang": lang,
            "error": f"Erreur: {str(e)}" if lang == "fr" else f"エラー: {str(e)}"
        })


@router.get("/receipt-review/{receipt_id}")
async def receipt_review(
    request: Request,
    receipt_id: int,
    lang: str = "fr"
):
    """
    Page de révision et validation des matches d'ingrédients
    """
    receipt = db.get_receipt_with_matches(receipt_id, lang)

    if not receipt:
        return templates.TemplateResponse(
            "not_found.html",
            {"request": request, "lang": lang, "message": "Ticket introuvable"},
            status_code=404
        )

    # Récupérer tous les ingrédients du catalogue pour le dropdown
    all_ingredients = db.get_all_catalog_ingredients_for_dropdown(lang)

    return templates.TemplateResponse("receipt_review.html", {
        "request": request,
        "lang": lang,
        "receipt": receipt,
        "all_ingredients": all_ingredients
    })


@router.post("/receipt-match/{match_id}/validate")
async def validate_receipt_match(
    match_id: int,
    lang: str = Form("fr"),
    validated: bool = Form(True),
    notes: Optional[str] = Form(None)
):
    """
    Valide ou rejette un match d'ingrédient
    """
    db.validate_match(match_id, validated, notes)

    # Récupérer le receipt_id pour la redirection
    # On doit faire une requête pour obtenir le receipt_id du match
    from app.models.db_core import get_db as get_db_conn
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT receipt_id FROM receipt_item_match WHERE id = ?", (match_id,))
        result = cursor.fetchone()
        receipt_id = result['receipt_id'] if result else None

    if receipt_id:
        return RedirectResponse(f"/receipt-review/{receipt_id}?lang={lang}", status_code=303)
    else:
        return RedirectResponse(f"/receipt-list?lang={lang}", status_code=303)


@router.post("/receipt-match/{match_id}/validate-and-apply")
async def validate_and_apply_receipt_match(
    match_id: int,
    lang: str = Form("fr")
):
    """
    Valide un match et applique immédiatement le prix au catalogue
    """
    from app.models.db_core import get_db as get_db_conn

    # Récupérer les infos du match
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT receipt_id, matched_ingredient_id, receipt_price, receipt_quantity, receipt_unit
            FROM receipt_item_match WHERE id = ?
        """, (match_id,))
        match = cursor.fetchone()

    if not match or not match['matched_ingredient_id']:
        return RedirectResponse(f"/receipt-list?lang={lang}", status_code=303)

    receipt_id = match['receipt_id']
    ingredient_id = match['matched_ingredient_id']
    price = match['receipt_price']
    quantity = match['receipt_quantity'] if match['receipt_quantity'] else 1.0

    # Récupérer la devise et la date du ticket
    receipt = db.get_receipt_by_id(receipt_id)
    currency = receipt['currency']
    receipt_date = receipt['receipt_date']

    # Mettre à jour le catalogue immédiatement
    with get_db_conn() as conn:
        cursor = conn.cursor()
        if currency == "EUR":
            cursor.execute("""
                UPDATE ingredient_price_catalog
                SET price_eur = ?,
                    qty = ?,
                    price_eur_source = 'receipt',
                    price_eur_last_receipt_date = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (price, quantity, receipt_date, ingredient_id))
        else:  # JPY
            cursor.execute("""
                UPDATE ingredient_price_catalog
                SET price_jpy = ?,
                    qty = ?,
                    price_jpy_source = 'receipt',
                    price_jpy_last_receipt_date = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (price, quantity, receipt_date, ingredient_id))

        # Marquer le match comme appliqué
        cursor.execute("""
            UPDATE receipt_item_match
            SET status = 'applied', validated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (match_id,))

        conn.commit()

    return RedirectResponse(f"/receipt-review/{receipt_id}?lang={lang}", status_code=303)


@router.post("/receipt-match/{match_id}/update-ingredient")
async def update_receipt_match_ingredient(
    match_id: int,
    lang: str = Form("fr"),
    ingredient_id: int = Form(...)
):
    """
    Met à jour l'ingrédient matché pour un item (correction manuelle)
    """
    db.update_match_ingredient(match_id, ingredient_id, confidence_score=1.0)

    # Récupérer le receipt_id pour la redirection
    from app.models.db_core import get_db as get_db_conn
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT receipt_id FROM receipt_item_match WHERE id = ?", (match_id,))
        result = cursor.fetchone()
        receipt_id = result['receipt_id'] if result else None

    if receipt_id:
        return RedirectResponse(f"/receipt-review/{receipt_id}?lang={lang}", status_code=303)
    else:
        return RedirectResponse(f"/receipt-list?lang={lang}", status_code=303)


@router.post("/receipt-apply/{receipt_id}")
async def apply_receipt_prices(
    receipt_id: int,
    lang: str = Form("fr")
):
    """
    Applique tous les prix validés au catalogue
    """
    receipt = db.get_receipt_by_id(receipt_id)

    if not receipt:
        return RedirectResponse(f"/receipt-list?lang={lang}", status_code=303)

    # Appliquer les prix
    count = db.apply_validated_prices(receipt_id, receipt['currency'])

    # TODO: Ajouter un message flash pour afficher "{count} prix mis à jour"

    return RedirectResponse(f"/receipt-list?lang={lang}", status_code=303)


@router.post("/receipt-delete/{receipt_id}")
async def delete_receipt_by_id(
    receipt_id: int,
    lang: str = Form("fr")
):
    """
    Supprime un ticket de caisse
    """
    db.delete_receipt(receipt_id)

    return RedirectResponse(f"/receipt-list?lang={lang}", status_code=303)
