"""Service de gestion des images de recettes - Version sans Pillow"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Tuple, Optional

# Configuration
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}

# Chemins des répertoires d'images
BASE_DIR = Path(__file__).resolve().parent.parent.parent
IMAGES_DIR = BASE_DIR / "static" / "images" / "recipes"
THUMBNAILS_DIR = BASE_DIR / "static" / "images" / "recipes" / "thumbnails"

# Créer les répertoires s'ils n'existent pas
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)


def is_allowed_file(filename: str) -> bool:
    """
    Vérifie si l'extension du fichier est autorisée

    Args:
        filename: Nom du fichier

    Returns:
        True si l'extension est autorisée
    """
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def save_recipe_image(file_data: bytes, filename: str) -> Tuple[str, str]:
    """
    Sauvegarde une image de recette (version simple sans redimensionnement)

    Args:
        file_data: Données du fichier image
        filename: Nom original du fichier

    Returns:
        Tuple (url_image, url_thumbnail) - URLs relatives pour la base de données
        Note: Dans cette version, thumbnail = image (même fichier)

    Raises:
        ValueError: Si le fichier est invalide
    """
    # Vérifier l'extension
    if not is_allowed_file(filename):
        raise ValueError(f"Extension de fichier non autorisée. Formats acceptés: {', '.join(ALLOWED_EXTENSIONS)}")

    # Vérifier la taille
    if len(file_data) > MAX_FILE_SIZE:
        raise ValueError(f"Fichier trop volumineux. Taille maximale: {MAX_FILE_SIZE // (1024*1024)}MB")

    # Générer un nom de fichier unique
    unique_id = uuid.uuid4().hex[:12]
    file_extension = Path(filename).suffix.lower()
    image_filename = f"{unique_id}{file_extension}"

    # Chemins complets
    image_path = IMAGES_DIR / image_filename

    try:
        # Sauvegarder l'image telle quelle
        with open(image_path, 'wb') as f:
            f.write(file_data)

        # Retourner les URLs relatives (pour stocker dans la DB)
        # Note: pas de thumbnail séparé dans cette version simplifiée
        image_url = f"/static/images/recipes/{image_filename}"
        thumbnail_url = image_url  # Même URL pour le thumbnail

        return image_url, thumbnail_url

    except Exception as e:
        # Nettoyer en cas d'erreur
        if image_path.exists():
            image_path.unlink()
        raise ValueError(f"Erreur lors de la sauvegarde de l'image: {str(e)}")


def delete_recipe_image(image_url: Optional[str], thumbnail_url: Optional[str]):
    """
    Supprime les fichiers image d'une recette

    Args:
        image_url: URL de l'image principale
        thumbnail_url: URL du thumbnail (ignoré dans cette version)
    """
    if image_url:
        image_path = BASE_DIR / image_url.lstrip('/')
        if image_path.exists():
            image_path.unlink()


def get_default_image_url() -> str:
    """
    Retourne l'URL de l'image par défaut

    Returns:
        URL de l'image placeholder
    """
    return "/static/images/recipe-placeholder.jpg"
