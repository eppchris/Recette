"""
Service orchestrateur pour la recherche de prix
OPTIONNEL - N'est utilisé QUE si explicitement appelé
Ne modifie JAMAIS automatiquement la base de données
"""

from typing import List, Optional
from .price_providers.base import PriceProvider, PriceData
from .price_providers.manual import ManualPriceProvider
from .price_providers.rakuten import RakutenProvider
from .price_providers.openfoodfacts import OpenFoodFactsProvider


class PriceService:
    """
    Orchestrateur de recherche de prix multi-sources
    Utilisation: Uniquement sur demande explicite de l'utilisateur
    """

    def __init__(self, enable_external: bool = False):
        """
        Initialise le service de prix

        Args:
            enable_external: Si True, active les APIs externes (Rakuten, etc.)
                           Si False, utilise uniquement la base locale
        """
        self.providers: List[PriceProvider] = []

        # TOUJOURS disponible : base locale
        self.providers.append(ManualPriceProvider())

        # APIs externes : UNIQUEMENT si explicitement activé
        if enable_external:
            # Rakuten (Japon) - Si API key configurée
            rakuten = RakutenProvider()
            if rakuten.is_available():
                self.providers.append(rakuten)
                print(f"✅ {rakuten.get_provider_name()} activé")

            # Open Food Facts (France/International) - Toujours disponible mais limité
            self.providers.append(OpenFoodFactsProvider())
            print(f"✅ {OpenFoodFactsProvider().get_provider_name()} activé")

    def search_price(
        self,
        ingredient_name: str,
        unit: str = None,
        lang: str = "fr",
        prefer_local: bool = True
    ) -> Optional[PriceData]:
        """
        Recherche le prix d'un ingrédient via les différentes sources

        Args:
            ingredient_name: Nom de l'ingrédient
            unit: Unité de mesure
            lang: Langue de recherche ('fr' ou 'jp')
            prefer_local: Si True, privilégie les prix locaux (confiance maximale)

        Returns:
            PriceData du meilleur résultat trouvé (selon confidence)
        """
        results: List[PriceData] = []

        # Rechercher dans tous les providers
        for provider in self.providers:
            if not provider.is_available():
                continue

            try:
                price_data = provider.search_price(ingredient_name, unit, lang)
                if price_data:
                    results.append(price_data)
                    print(f"  ✓ {provider.get_provider_name()}: {price_data.price_eur}€ / {price_data.price_jpy}¥")
            except Exception as e:
                print(f"  ✗ Erreur {provider.get_provider_name()}: {e}")

        if not results:
            return None

        # Trier par confiance (décroissant)
        results.sort(key=lambda x: x.confidence, reverse=True)

        # Si prefer_local, toujours retourner le prix local s'il existe
        if prefer_local:
            local_result = next((r for r in results if r.source == "Base de données locale"), None)
            if local_result:
                return local_result

        # Sinon, retourner le meilleur résultat
        return results[0]

    def get_all_results(
        self,
        ingredient_name: str,
        unit: str = None,
        lang: str = "fr"
    ) -> List[PriceData]:
        """
        Recherche dans TOUTES les sources et retourne tous les résultats
        Utile pour comparer les prix

        Args:
            ingredient_name: Nom de l'ingrédient
            unit: Unité de mesure
            lang: Langue de recherche

        Returns:
            Liste de tous les PriceData trouvés
        """
        results: List[PriceData] = []

        for provider in self.providers:
            if not provider.is_available():
                continue

            try:
                price_data = provider.search_price(ingredient_name, unit, lang)
                if price_data:
                    results.append(price_data)
            except Exception as e:
                print(f"Erreur {provider.get_provider_name()}: {e}")

        return results


# Instance globale OPTIONNELLE
# N'est créée QUE si explicitement demandé
price_service: Optional[PriceService] = None


def init_price_service(enable_external: bool = False):
    """
    Initialise le service de prix global (optionnel)

    Args:
        enable_external: Active les APIs externes (Rakuten, Open Food Facts)
    """
    global price_service
    price_service = PriceService(enable_external=enable_external)
    print(f"✅ Service de prix initialisé (APIs externes: {'ON' if enable_external else 'OFF'})")
