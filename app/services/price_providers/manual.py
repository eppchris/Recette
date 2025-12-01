"""
Fournisseur de prix manuel (fallback)
Utilise les prix déjà saisis dans la base de données
"""

from typing import Optional
from datetime import datetime
from .base import PriceProvider, PriceData


class ManualPriceProvider(PriceProvider):
    """
    Récupère les prix depuis la base de données locale
    C'est le fallback de confiance maximale
    """

    def __init__(self, db_connection=None):
        """
        Initialise le provider manuel

        Args:
            db_connection: Connexion à la base de données (optionnel)
        """
        self.db = db_connection

    def get_provider_name(self) -> str:
        return "Base de données locale"

    def is_available(self) -> bool:
        """Toujours disponible"""
        return True

    def search_price(self, ingredient_name: str, unit: str = None, lang: str = "fr") -> Optional[PriceData]:
        """
        Recherche le prix dans la base de données locale

        Args:
            ingredient_name: Nom de l'ingrédient
            unit: Unité de mesure
            lang: Langue ('fr' ou 'jp')

        Returns:
            PriceData depuis la base locale
        """
        from app.models import db

        try:
            # Récupérer depuis le catalogue
            ingredient = db.get_ingredient_from_catalog(ingredient_name)

            if not ingredient:
                return None

            # Vérifier l'unité si fournie
            if unit and ingredient.get('unit_fr', '').lower() != unit.lower():
                return None

            return PriceData(
                price_eur=ingredient.get('price_eur'),
                price_jpy=ingredient.get('price_jpy'),
                unit=ingredient.get('unit_fr'),
                quantity=ingredient.get('qty', 1.0),
                source="Base de données locale",
                confidence=1.0,  # Confiance maximale (prix saisi manuellement)
                updated_at=datetime.fromisoformat(ingredient['updated_at']) if ingredient.get('updated_at') else None,
                product_url=None,
                notes="Prix saisi manuellement"
            )

        except Exception as e:
            print(f"Erreur recherche prix local: {e}")
            return None
