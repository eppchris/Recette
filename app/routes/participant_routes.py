# app/routes/participant_routes.py
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from typing import Optional

from app.models import db
from app.template_config import templates

router = APIRouter()


# ============================================================================
# Page principale de gestion des participants et groupes
# ============================================================================

@router.get("/participants", response_class=HTMLResponse)
async def participants_index(request: Request, lang: str = "fr"):
    """
    Page principale de gestion des participants et des groupes
    Affiche les deux listes côte à côte
    """
    participants = db.list_participants()
    groups = db.list_groups()

    return templates.TemplateResponse(
        "participants_index.html",
        {
            "request": request,
            "lang": lang,
            "participants": participants,
            "groups": groups
        }
    )


# ============================================================================
# Routes pour la gestion des participants
# ============================================================================

@router.get("/participants/{participant_id}", response_class=HTMLResponse)
async def participant_detail(request: Request, participant_id: int, lang: str = "fr"):
    """
    Affiche les détails d'un participant avec ses groupes et événements
    """
    participant = db.get_participant_by_id(participant_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant non trouvé")

    groups = db.get_participant_groups(participant_id)
    events = db.get_participant_events(participant_id)

    return templates.TemplateResponse(
        "participant_detail.html",
        {
            "request": request,
            "lang": lang,
            "participant": participant,
            "groups": groups,
            "events": events
        }
    )


@router.post("/participants/create")
async def participant_create(
    request: Request,
    lang: str = Form("fr"),
    nom: str = Form(...),
    prenom: str = Form(""),
    role: str = Form(""),
    telephone: str = Form(""),
    email: str = Form(""),
    adresse: str = Form("")
):
    """
    Crée un nouveau participant
    """
    participant_id = db.create_participant(
        nom=nom,
        prenom=prenom if prenom else None,
        role=role if role else None,
        telephone=telephone if telephone else None,
        email=email if email else None,
        adresse=adresse if adresse else None
    )

    return RedirectResponse(
        url=f"/participants?lang={lang}",
        status_code=303
    )


@router.post("/participants/{participant_id}/update")
async def participant_update(
    request: Request,
    participant_id: int,
    lang: str = Form("fr"),
    nom: str = Form(...),
    prenom: str = Form(""),
    role: str = Form(""),
    telephone: str = Form(""),
    email: str = Form(""),
    adresse: str = Form("")
):
    """
    Met à jour un participant existant
    """
    success = db.update_participant(
        participant_id=participant_id,
        nom=nom,
        prenom=prenom if prenom else None,
        role=role if role else None,
        telephone=telephone if telephone else None,
        email=email if email else None,
        adresse=adresse if adresse else None
    )

    if not success:
        raise HTTPException(status_code=404, detail="Participant non trouvé")

    return RedirectResponse(
        url=f"/participants?lang={lang}",
        status_code=303
    )


@router.post("/participants/{participant_id}/delete")
async def participant_delete(
    request: Request,
    participant_id: int,
    lang: str = Form("fr")
):
    """
    Supprime un participant
    """
    db.delete_participant(participant_id)

    return RedirectResponse(
        url=f"/participants?lang={lang}",
        status_code=303
    )


# ============================================================================
# Routes pour la gestion des groupes
# ============================================================================

@router.get("/participants/groups/{group_id}", response_class=HTMLResponse)
async def group_detail(request: Request, group_id: int, lang: str = "fr"):
    """
    Affiche les détails d'un groupe avec ses membres
    """
    group = db.get_group_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Groupe non trouvé")

    members = db.get_group_members(group_id)
    all_participants = db.list_participants()

    return templates.TemplateResponse(
        "group_detail.html",
        {
            "request": request,
            "lang": lang,
            "group": group,
            "members": members,
            "all_participants": all_participants
        }
    )


@router.post("/participants/groups/create")
async def group_create(
    request: Request,
    lang: str = Form("fr"),
    nom: str = Form(...),
    description: str = Form("")
):
    """
    Crée un nouveau groupe
    """
    group_id = db.create_group(
        nom=nom,
        description=description if description else None
    )

    return RedirectResponse(
        url=f"/participants?lang={lang}",
        status_code=303
    )


@router.post("/participants/groups/{group_id}/update")
async def group_update(
    request: Request,
    group_id: int,
    lang: str = Form("fr"),
    nom: str = Form(...),
    description: str = Form("")
):
    """
    Met à jour un groupe existant
    """
    success = db.update_group(
        group_id=group_id,
        nom=nom,
        description=description if description else None
    )

    if not success:
        raise HTTPException(status_code=404, detail="Groupe non trouvé")

    return RedirectResponse(
        url=f"/participants?lang={lang}",
        status_code=303
    )


@router.post("/participants/groups/{group_id}/delete")
async def group_delete(
    request: Request,
    group_id: int,
    lang: str = Form("fr")
):
    """
    Supprime un groupe
    """
    db.delete_group(group_id)

    return RedirectResponse(
        url=f"/participants?lang={lang}",
        status_code=303
    )


# ============================================================================
# Routes pour la gestion de l'appartenance aux groupes
# ============================================================================

@router.post("/participants/groups/{group_id}/members/add")
async def group_add_member(
    request: Request,
    group_id: int,
    lang: str = Form("fr"),
    participant_id: int = Form(...)
):
    """
    Ajoute un participant à un groupe
    """
    db.add_participant_to_group(participant_id, group_id)

    return RedirectResponse(
        url=f"/participants/groups/{group_id}?lang={lang}",
        status_code=303
    )


@router.post("/participants/groups/{group_id}/members/{participant_id}/remove")
async def group_remove_member(
    request: Request,
    group_id: int,
    participant_id: int,
    lang: str = Form("fr")
):
    """
    Retire un participant d'un groupe
    """
    db.remove_participant_from_group(participant_id, group_id)

    return RedirectResponse(
        url=f"/participants/groups/{group_id}?lang={lang}",
        status_code=303
    )


# ============================================================================
# Routes API pour la liaison événement ↔ participants
# ============================================================================

@router.get("/api/events/{event_id}/participants")
async def api_get_event_participants(event_id: int):
    """
    API: Récupère les participants d'un événement
    """
    participants = db.get_event_participants(event_id)
    return JSONResponse(content=participants)


@router.post("/api/events/{event_id}/participants/add")
async def api_add_participant_to_event(
    event_id: int,
    participant_id: int = Form(...)
):
    """
    API: Ajoute un participant individuel à un événement
    """
    result = db.add_participant_to_event(event_id, participant_id)

    if result is None:
        return JSONResponse(
            content={"success": False, "message": "Participant déjà lié à l'événement"},
            status_code=400
        )

    return JSONResponse(content={"success": True, "id": result})


@router.post("/api/events/{event_id}/participants/add-group")
async def api_add_group_to_event(
    event_id: int,
    group_id: int = Form(...)
):
    """
    API: Ajoute tous les participants d'un groupe à un événement
    """
    added_count = db.add_group_to_event(event_id, group_id)

    return JSONResponse(content={
        "success": True,
        "added_count": added_count
    })


@router.post("/api/events/{event_id}/participants/{participant_id}/remove")
async def api_remove_participant_from_event(
    event_id: int,
    participant_id: int
):
    """
    API: Retire un participant d'un événement
    """
    db.remove_participant_from_event(event_id, participant_id)

    return JSONResponse(content={"success": True})
