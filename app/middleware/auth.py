"""Middleware d'authentification pour FastAPI"""

from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
import os


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware pour protéger les routes avec un mot de passe partagé"""

    def __init__(self, app, require_password: bool, shared_password: str):
        super().__init__(app)
        self.require_password = require_password
        self.shared_password = shared_password

        # Routes publiques (accessibles sans authentification)
        self.public_paths = [
            "/login",
            "/static",
            "/health",
        ]

    async def dispatch(self, request: Request, call_next):
        """Vérifie l'authentification avant de traiter la requête"""

        # Si la protection n'est pas activée, laisser passer
        if not self.require_password:
            return await call_next(request)

        # Vérifier si la route est publique
        path = request.url.path
        if any(path.startswith(public_path) for public_path in self.public_paths):
            return await call_next(request)

        # Vérifier la session
        authenticated = request.session.get("authenticated", False)

        if not authenticated:
            # Rediriger vers la page de login
            lang = request.query_params.get("lang", "fr")
            return RedirectResponse(url=f"/login?lang={lang}", status_code=303)

        # Utilisateur authentifié, continuer
        return await call_next(request)


def check_password(password: str, shared_password: str) -> bool:
    """Vérifie si le mot de passe est correct"""
    return password == shared_password
