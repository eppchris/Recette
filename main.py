# main.py
"""Point d'entrée unifié pour tous les environnements"""

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import logging
from logging.handlers import RotatingFileHandler
import os

from config import Config
from app.services.translation_service import init_translation_service
from app.services.conversion_service import init_conversion_service
from app.middleware.auth import AuthMiddleware
from app.template_config import templates

# Configuration du logging
if Config.ENV == "prod":
    handler = RotatingFileHandler(
        Config.LOG_PATH,
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL.upper()),
        handlers=[handler, logging.StreamHandler()]
    )
else:
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

logger = logging.getLogger(__name__)

# Créer l'application FastAPI
app_title = f"Recette FR/JP - {Config.ENV.upper()}"
app = FastAPI(title=app_title)

# Stocker les paramètres dans app.state pour les rendre accessibles
app.state.shared_password = Config.SHARED_PASSWORD

# IMPORTANT : L'ordre d'ajout des middlewares est inversé en FastAPI
# Le dernier ajouté s'exécute en PREMIER
# Donc : ajouter AuthMiddleware AVANT SessionMiddleware

# Ajouter le middleware d'authentification si activé
if Config.REQUIRE_PASSWORD:
    app.add_middleware(
        AuthMiddleware,
        require_password=Config.REQUIRE_PASSWORD,
        shared_password=Config.SHARED_PASSWORD
    )
    logger.info("🔒 Protection par mot de passe activée")
else:
    logger.info(f"⚠️  Protection par mot de passe désactivée ({Config.ENV})")

# Ajouter le middleware de session
app.add_middleware(
    SessionMiddleware,
    secret_key=Config.SECRET_KEY,
    session_cookie="recette_session",
    max_age=86400,  # 24 heures
)

# Initialiser le service de traduction si la clé API est configurée
if Config.GROQ_API_KEY:
    init_translation_service(Config.GROQ_API_KEY)
    logger.info("✅ Service de traduction Groq initialisé")
else:
    logger.warning("⚠️  Clé API Groq non configurée - la traduction automatique est désactivée")

# Initialiser le service de conversion si la clé API est configurée
if Config.GROQ_API_KEY:
    init_conversion_service(Config.GROQ_API_KEY)
    logger.info("✅ Service de conversion initialisé")
else:
    logger.warning("⚠️  Service de conversion initialisé sans IA (clé API manquante)")

# Montage des fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# Import et montage des routes
from app.routes.recipe_routes import router as recipe_router
from app.routes.auth_routes import router as auth_router
from app.routes.event_routes import router as event_router

app.include_router(auth_router)
app.include_router(recipe_router)
app.include_router(event_router)

# Page d'accueil : redirection vers la liste des recettes
@app.get("/")
async def root():
    return RedirectResponse(url="/recipes?lang=fr")

# Health check endpoint pour monitoring
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "environment": Config.ENV,
        "debug": Config.DEBUG
    }


# Point d'entrée pour le développement
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG
    )
