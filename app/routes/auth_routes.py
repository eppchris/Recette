"""Routes d'authentification"""

from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from app.middleware.auth import check_password
from app.template_config import templates, TRANSLATIONS

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request, lang: str = Query("fr")):
    """Affiche le formulaire de connexion"""
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "lang": lang, "error": None}
    )


@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    password: str = Form(...),
    lang: str = Query("fr")
):
    """Traite la tentative de connexion"""

    # Récupérer le mot de passe configuré depuis l'app state
    shared_password = request.app.state.shared_password

    # Vérifier le mot de passe
    if check_password(password, shared_password):
        # Mot de passe correct : créer la session
        request.session["authenticated"] = True

        # Rediriger vers la page d'accueil
        return RedirectResponse(url=f"/recipes?lang={lang}", status_code=303)
    else:
        # Mot de passe incorrect : afficher l'erreur
        error = TRANSLATIONS[lang]["login_error"]
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "lang": lang, "error": error}
        )


@router.get("/logout")
async def logout(request: Request, lang: str = Query("fr")):
    """Déconnexion de l'utilisateur"""
    request.session.clear()
    return RedirectResponse(url=f"/login?lang={lang}", status_code=303)
