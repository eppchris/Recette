"""
Interface de base pour les fournisseurs de prix
Permet d'ajouter facilement de nouvelles sources sans modifier le code existant
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class PriceData:
    """Données de prix retournées par un fournisseur"""
    price_eur: Optional[float] = None
    price_jpy: Optional[float] = None
    unit: Optional[str] = None
    quantity: float = 1.0
    source: str = "unknown"
    confidence: float = 0.0  # 0.0 à 1.0
    updated_at: Optional[datetime] = None
    product_url: Optional[str] = None
    notes: Optional[str] = None


class PriceProvider(ABC):
    """Interface abstraite pour tous les fournisseurs de prix"""

    @abstractmethod
    def search_price(self, ingredient_name: str, unit: str = None, lang: str = "fr") -> Optional[PriceData]:
        """
        Recherche le prix d'un ingrédient

        Args:
            ingredient_name: Nom de l'ingrédient
            unit: Unité de mesure (optionnel)
            lang: Langue de recherche ('fr' ou 'jp')

        Returns:
            PriceData si trouvé, None sinon
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Retourne le nom du fournisseur"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Vérifie si le fournisseur est disponible (API key configurée, etc.)"""
        pass
