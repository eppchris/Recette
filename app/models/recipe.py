# app/models/recipe.py
from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String

from .db import BaseModel

class Recipe(BaseModel):
    """
    Représente une recette.
    Champs explicites pour faciliter la lecture du code.
    """
    __tablename__ = "recipe"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipe_name: Mapped[str] = mapped_column(String(255), nullable=False)
    recipe_type: Mapped[str] = mapped_column(String(50), nullable=False)  # PRO, MASTER, PERSO, AUTRE…
    country: Mapped[str] = mapped_column(String(80), nullable=True)       # Pays d'origine (optionnel)
    servings_default: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    owner_id: Mapped[int] = mapped_column(Integer, nullable=True)         # référence future vers table owner
    photo_path: Mapped[str] = mapped_column(String(300), nullable=True)   # chemin relatif vers /data/uploads
