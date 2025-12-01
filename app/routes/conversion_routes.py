# app/routes/conversion_routes.py
"""Routes pour la gestion des conversions spécifiques par ingrédient"""

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from app.models import db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/ingredient-specific-conversions", response_class=HTMLResponse)
async def ingredient_specific_conversions_page(request: Request, lang: str = "fr"):
    """
    Page de gestion des conversions spécifiques par ingrédient
    """
    # Récupérer toutes les conversions
    conversions = db.get_all_specific_conversions()

    # Récupérer tous les ingrédients du catalogue pour le formulaire
    all_ingredients = db.get_all_ingredients_from_catalog()

    return templates.TemplateResponse("ingredient_specific_conversions.html", {
        "request": request,
        "lang": lang,
        "conversions": conversions,
        "ingredients": all_ingredients
    })


@router.post("/ingredient-specific-conversions/add")
async def add_specific_conversion(
    request: Request,
    lang: str = Form("fr"),
    ingredient_name_fr: str = Form(...),
    from_unit: str = Form(...),
    to_unit: str = Form(...),
    factor: float = Form(...),
    notes: Optional[str] = Form(None)
):
    """
    Ajoute une conversion spécifique
    """
    try:
        db.add_specific_conversion(ingredient_name_fr, from_unit, to_unit, factor, notes)

        return RedirectResponse(
            url=f"/ingredient-specific-conversions?lang={lang}",
            status_code=303
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingredient-specific-conversions/{conversion_id}/update")
async def update_specific_conversion(
    conversion_id: int,
    lang: str = Form("fr"),
    from_unit: str = Form(...),
    to_unit: str = Form(...),
    factor: float = Form(...),
    notes: Optional[str] = Form(None)
):
    """
    Met à jour une conversion spécifique
    """
    try:
        db.update_specific_conversion(conversion_id, from_unit, to_unit, factor, notes)

        return RedirectResponse(
            url=f"/ingredient-specific-conversions?lang={lang}",
            status_code=303
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingredient-specific-conversions/{conversion_id}/delete")
async def delete_specific_conversion(
    conversion_id: int,
    lang: str = Form("fr")
):
    """
    Supprime une conversion spécifique
    """
    try:
        db.delete_specific_conversion(conversion_id)

        return RedirectResponse(
            url=f"/ingredient-specific-conversions?lang={lang}",
            status_code=303
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingredient-specific-conversions/suggest-with-ai")
async def suggest_conversion_with_ai(
    ingredient_name_fr: str = Form(...),
    from_unit: str = Form(...),
    to_unit: str = Form(...)
):
    """
    Suggère un facteur de conversion en utilisant l'IA
    """
    from app.services.translation_service import translation_service

    if not translation_service:
        return JSONResponse(
            content={"success": False, "error": "Service IA non disponible"},
            status_code=500
        )

    try:
        # Prompt pour l'IA
        prompt = f"""Calcule le facteur de conversion approximatif pour cet ingrédient culinaire.

Ingrédient: {ingredient_name_fr}
Unité source: {from_unit}
Unité cible: {to_unit}

Question: Combien fait 1 {from_unit} de {ingredient_name_fr} en {to_unit} ?

Donne UNIQUEMENT le facteur de conversion (nombre décimal).
Par exemple, si 1 ml de sucre = 1.6 g, réponds "1.6"

Réponds UNIQUEMENT avec le nombre, rien d'autre."""

        response = translation_service.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=translation_service.model,
            temperature=0.1,
            max_tokens=20
        )

        result = response.choices[0].message.content.strip()

        # Extraire le nombre
        import re
        match = re.search(r'\d+\.?\d*', result)
        if match:
            factor = float(match.group())
            return JSONResponse(content={
                "success": True,
                "factor": factor,
                "explanation": f"1 {from_unit} de {ingredient_name_fr} ≈ {factor} {to_unit}"
            })
        else:
            return JSONResponse(
                content={"success": False, "error": "L'IA n'a pas pu calculer le facteur"},
                status_code=400
            )

    except Exception as e:
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )
