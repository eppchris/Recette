"""
Module de fournisseurs de prix externes
OPTIONNEL - N'affecte pas le fonctionnement normal de l'application
"""

from .base import PriceProvider, PriceData

__all__ = ['PriceProvider', 'PriceData']
