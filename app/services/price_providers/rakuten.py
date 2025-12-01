"""
Fournisseur de prix Rakuten Ichiba (Japon)
Documentation API: https://webservice.rakuten.co.jp/documentation/
"""

import os
import requests
from typing import Optional
from datetime import datetime
from .base import PriceProvider, PriceData


class RakutenProvider(PriceProvider):
    """Recherche de prix via l'API Rakuten Ichiba"""

    def __init__(self, app_id: str = None):
        """
        Initialise le provider Rakuten

        Args:
            app_id: Rakuten Application ID (ou via env RAKUTEN_APP_ID)
        """
        self.app_id = app_id or os.getenv('RAKUTEN_APP_ID')
        self.base_url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"

    def get_provider_name(self) -> str:
        return "Rakuten Ichiba"

    def is_available(self) -> bool:
        """Vérifie si l'API key est configurée"""
        return bool(self.app_id)

    def search_price(self, ingredient_name: str, unit: str = None, lang: str = "jp") -> Optional[PriceData]:
        """
        Recherche le prix sur Rakuten

        Args:
            ingredient_name: Nom de l'ingrédient (japonais de préférence)
            unit: Unité (optionnel, aide à filtrer)
            lang: Langue ('jp' recommandé)

        Returns:
            PriceData avec le prix le moins cher trouvé
        """
        if not self.is_available():
            return None

        try:
            # Paramètres de recherche Rakuten
            params = {
                'applicationId': self.app_id,
                'keyword': ingredient_name,
                'hits': 10,  # Nombre de résultats
                'sort': '+itemPrice',  # Tri par prix croissant
                'genreId': '100227',  # Catégorie "食品" (alimentation)
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Vérifier si des résultats existent
            if 'Items' not in data or len(data['Items']) == 0:
                return None

            # Prendre le premier résultat (le moins cher)
            item = data['Items'][0]['Item']

            # Extraire les données
            price_jpy = float(item['itemPrice'])
            product_name = item['itemName']
            product_url = item['itemUrl']

            # Taux de change approximatif JPY → EUR (à ajuster ou récupérer d'une API)
            EUR_TO_JPY = 160.0
            price_eur = price_jpy / EUR_TO_JPY

            return PriceData(
                price_eur=round(price_eur, 2),
                price_jpy=price_jpy,
                unit=unit or "unité",
                quantity=1.0,
                source="Rakuten Ichiba",
                confidence=0.7,  # Confiance moyenne (prix réel mais pas forcément exact)
                updated_at=datetime.now(),
                product_url=product_url,
                notes=f"Produit: {product_name}"
            )

        except requests.exceptions.RequestException as e:
            print(f"Erreur Rakuten API: {e}")
            return None
        except (KeyError, ValueError, IndexError) as e:
            print(f"Erreur parsing Rakuten: {e}")
            return None
