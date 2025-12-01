"""
Fournisseur de prix Open Food Facts (France & International)
Documentation API: https://openfoodfacts.github.io/api-documentation/
"""

import requests
from typing import Optional
from datetime import datetime
from .base import PriceProvider, PriceData


class OpenFoodFactsProvider(PriceProvider):
    """Recherche de prix via l'API Open Food Facts"""

    def __init__(self):
        """Initialise le provider Open Food Facts (pas d'API key nécessaire)"""
        self.base_url = "https://world.openfoodfacts.org/cgi/search.pl"

    def get_provider_name(self) -> str:
        return "Open Food Facts"

    def is_available(self) -> bool:
        """Toujours disponible (API gratuite sans authentification)"""
        return True

    def search_price(self, ingredient_name: str, unit: str = None, lang: str = "fr") -> Optional[PriceData]:
        """
        Recherche le prix sur Open Food Facts

        Note: Open Food Facts ne contient PAS toujours de prix,
        mais des données nutritionnelles et de produits.
        Les prix doivent être estimés ou complétés manuellement.

        Args:
            ingredient_name: Nom de l'ingrédient
            unit: Unité (optionnel)
            lang: Langue ('fr' ou 'en')

        Returns:
            PriceData si produit trouvé (prix estimé à NULL)
        """
        try:
            # Paramètres de recherche
            params = {
                'search_terms': ingredient_name,
                'search_simple': 1,
                'json': 1,
                'page_size': 5,
                'fields': 'product_name,quantity,brands,stores',
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Vérifier si des résultats existent
            if 'products' not in data or len(data['products']) == 0:
                return None

            # Prendre le premier résultat
            product = data['products'][0]
            product_name = product.get('product_name', ingredient_name)
            quantity = product.get('quantity', '')

            return PriceData(
                price_eur=None,  # Open Food Facts ne fournit pas de prix
                price_jpy=None,
                unit=unit or "unité",
                quantity=1.0,
                source="Open Food Facts",
                confidence=0.3,  # Faible car pas de prix réel
                updated_at=datetime.now(),
                product_url=f"https://world.openfoodfacts.org/product/{product.get('code', '')}",
                notes=f"Produit trouvé: {product_name} ({quantity}). Prix à estimer."
            )

        except requests.exceptions.RequestException as e:
            print(f"Erreur Open Food Facts API: {e}")
            return None
        except (KeyError, ValueError, IndexError) as e:
            print(f"Erreur parsing Open Food Facts: {e}")
            return None
