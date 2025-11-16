"""Service de conversion de quantités avec IA pour les listes de courses"""

from typing import Dict, List, Tuple, Optional
import re
from groq import Groq
import os


# Table de conversion d'unités de base (multiplicateur pour convertir vers l'unité de base)
UNIT_CONVERSIONS = {
    # Poids
    "kg": 1000,  # vers grammes
    "g": 1,
    "mg": 0.001,

    # Volume
    "l": 1000,  # vers millilitres
    "ml": 1,
    "cl": 10,
    "dl": 100,

    # Cuillères et tasses (approximatif)
    "cuillère à soupe": 15,  # ml
    "cuillère à café": 5,    # ml
    "c. à soupe": 15,
    "c. à café": 5,
    "cs": 15,
    "cc": 5,
    "tasse": 250,  # ml

    # Japonais
    "大さじ": 15,  # cuillère à soupe
    "小さじ": 5,   # cuillère à café
    "カップ": 200,  # tasse japonaise
}

# Unités considérées comme unités de poids
WEIGHT_UNITS = {"kg", "g", "mg"}

# Unités considérées comme unités de volume
VOLUME_UNITS = {"l", "ml", "cl", "dl", "cuillère à soupe", "cuillère à café", "c. à soupe", "c. à café", "cs", "cc", "tasse", "大さじ", "小さじ", "カップ"}


class ConversionService:
    """Service de conversion de quantités d'ingrédients"""

    def __init__(self, groq_api_key: Optional[str] = None):
        """
        Initialise le service de conversion

        Args:
            groq_api_key: Clé API Groq (optionnelle si déjà dans l'environnement)
        """
        self.api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def convert_recipe_servings(
        self,
        ingredients: List[Dict],
        original_servings: int,
        target_servings: int,
        lang: str = "fr"
    ) -> List[Dict]:
        """
        Convertit les quantités d'ingrédients pour un nombre de personnes différent

        Args:
            ingredients: Liste des ingrédients avec quantity, unit, name
            original_servings: Nombre de personnes de la recette originale
            target_servings: Nombre de personnes souhaité
            lang: Langue de la recette

        Returns:
            Liste des ingrédients avec quantités converties
        """
        ratio = target_servings / original_servings
        converted_ingredients = []

        for ing in ingredients:
            converted = self._convert_ingredient(ing, ratio, lang)
            converted_ingredients.append(converted)

        return converted_ingredients

    def _convert_ingredient(
        self,
        ingredient: Dict,
        ratio: float,
        lang: str
    ) -> Dict:
        """
        Convertit un ingrédient individuel

        Args:
            ingredient: Dict avec quantity, unit, name
            ratio: Ratio de conversion (target/original)
            lang: Langue

        Returns:
            Dict avec les quantités converties
        """
        quantity = ingredient.get("quantity")
        unit = ingredient.get("unit", "").strip()
        name = ingredient.get("name", "")

        # Si pas de quantité, on utilise l'IA
        if quantity is None or quantity == 0:
            return self._convert_with_ai(ingredient, ratio, lang)

        # Conversion simple proportionnelle
        new_quantity = quantity * ratio

        # Arrondir intelligemment
        rounded_quantity, rounded_unit = self._smart_round(new_quantity, unit, name, lang)

        # Vérifier si négligeable
        is_negligible = self._is_negligible(rounded_quantity, rounded_unit)

        # Déterminer l'unité d'achat
        purchase_unit = self._determine_purchase_unit(rounded_quantity, rounded_unit, name, lang)

        return {
            **ingredient,
            "converted_quantity": rounded_quantity,
            "purchase_unit": purchase_unit,
            "is_negligible": is_negligible,
            "conversion_ratio": ratio
        }

    def _smart_round(
        self,
        quantity: float,
        unit: str,
        name: str,
        lang: str
    ) -> Tuple[float, str]:
        """
        Arrondit intelligemment une quantité

        Args:
            quantity: Quantité à arrondir
            unit: Unité
            name: Nom de l'ingrédient
            lang: Langue

        Returns:
            Tuple (quantité arrondie, unité ajustée)
        """
        # Œufs: toujours arrondir à l'entier supérieur
        if "œuf" in name.lower() or "oeuf" in name.lower() or "卵" in name:
            return (int(quantity) + (1 if quantity % 1 > 0 else 0), unit)

        # Pour les petites quantités (< 1), garder 1 décimale
        if quantity < 1:
            return (round(quantity, 1), unit)

        # Pour les quantités moyennes (1-10), arrondir à 0.5
        if quantity < 10:
            return (round(quantity * 2) / 2, unit)

        # Pour les grandes quantités, convertir en unité supérieure si pertinent
        if unit.lower() in {"g", "ml"} and quantity >= 1000:
            if unit.lower() == "g":
                return (round(quantity / 1000, 2), "kg")
            else:
                return (round(quantity / 1000, 2), "L")

        # Sinon, arrondir à l'entier
        return (round(quantity), unit)

    def _is_negligible(self, quantity: float, unit: str) -> bool:
        """
        Détermine si une quantité est négligeable

        Args:
            quantity: Quantité
            unit: Unité

        Returns:
            True si négligeable
        """
        # Moins de 1g ou 1ml est généralement négligeable pour l'achat
        if unit.lower() in WEIGHT_UNITS | VOLUME_UNITS:
            base_quantity = quantity * UNIT_CONVERSIONS.get(unit.lower(), 1)
            return base_quantity < 1

        return False

    def _determine_purchase_unit(
        self,
        quantity: float,
        unit: str,
        name: str,
        lang: str
    ) -> str:
        """
        Détermine l'unité d'achat appropriée

        Args:
            quantity: Quantité
            unit: Unité de la recette
            name: Nom de l'ingrédient
            lang: Langue

        Returns:
            Unité d'achat recommandée
        """
        # Si c'est déjà une bonne unité d'achat, on garde
        good_purchase_units = {"kg", "g", "l", "ml", "pièce", "個", "本"}
        if unit.lower() in good_purchase_units:
            return unit

        # Convertir les cuillères en ml/g
        if unit.lower() in {"cuillère à soupe", "cuillère à café", "c. à soupe", "c. à café", "cs", "cc", "大さじ", "小さじ"}:
            return "ml"

        # Par défaut, retourner l'unité originale
        return unit

    def _convert_with_ai(
        self,
        ingredient: Dict,
        ratio: float,
        lang: str
    ) -> Dict:
        """
        Utilise l'IA pour convertir un ingrédient avec quantité vague

        Args:
            ingredient: Ingrédient à convertir
            ratio: Ratio de conversion
            lang: Langue

        Returns:
            Ingrédient avec quantité convertie
        """
        if not self.client:
            # Pas d'IA disponible, retourner l'ingrédient tel quel
            return {
                **ingredient,
                "converted_quantity": None,
                "purchase_unit": ingredient.get("unit", ""),
                "is_negligible": False,
                "notes": "Conversion IA non disponible"
            }

        # Préparer le prompt pour l'IA
        prompt = self._build_ai_prompt(ingredient, ratio, lang)

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.3,
                max_tokens=200
            )

            # Parser la réponse de l'IA
            ai_response = response.choices[0].message.content
            return self._parse_ai_response(ingredient, ai_response)

        except Exception as e:
            print(f"Erreur lors de la conversion IA: {e}")
            return {
                **ingredient,
                "converted_quantity": None,
                "purchase_unit": ingredient.get("unit", ""),
                "is_negligible": False,
                "notes": f"Erreur de conversion: {str(e)}"
            }

    def _build_ai_prompt(self, ingredient: Dict, ratio: float, lang: str) -> str:
        """Construit le prompt pour l'IA"""
        name = ingredient.get("name", "")
        quantity = ingredient.get("quantity")
        unit = ingredient.get("unit", "")
        notes = ingredient.get("notes", "")

        if lang == "jp":
            return f"""以下の材料を{ratio}倍に換算してください。買い物用の実用的な量と単位で答えてください。

材料: {name}
元の量: {quantity if quantity else '指定なし'} {unit}
備考: {notes}

以下の形式で答えてください:
量: [数値]
単位: [単位]
無視可能: [はい/いいえ]
メモ: [任意]"""
        else:
            return f"""Convertissez l'ingrédient suivant pour un facteur de {ratio}. Donnez une quantité pratique pour faire les courses.

Ingrédient: {name}
Quantité originale: {quantity if quantity else 'non spécifiée'} {unit}
Notes: {notes}

Répondez dans ce format:
Quantité: [nombre]
Unité: [unité]
Négligeable: [oui/non]
Notes: [optionnel]"""

    def _parse_ai_response(self, ingredient: Dict, response: str) -> Dict:
        """Parse la réponse de l'IA"""
        # Extraire la quantité
        quantity_match = re.search(r"(?:Quantité|量)[:\s]+([0-9.]+)", response, re.IGNORECASE)
        quantity = float(quantity_match.group(1)) if quantity_match else None

        # Extraire l'unité
        unit_match = re.search(r"(?:Unité|単位)[:\s]+([^\n]+)", response, re.IGNORECASE)
        unit = unit_match.group(1).strip() if unit_match else ingredient.get("unit", "")

        # Vérifier si négligeable
        negligible_match = re.search(r"(?:Négligeable|無視可能)[:\s]+(?:oui|はい)", response, re.IGNORECASE)
        is_negligible = bool(negligible_match)

        # Extraire les notes
        notes_match = re.search(r"(?:Notes|メモ)[:\s]+([^\n]+)", response, re.IGNORECASE)
        notes = notes_match.group(1).strip() if notes_match else None

        return {
            **ingredient,
            "converted_quantity": quantity,
            "purchase_unit": unit,
            "is_negligible": is_negligible,
            "notes": notes
        }


# Instance globale du service
_conversion_service: Optional[ConversionService] = None


def init_conversion_service(groq_api_key: str):
    """Initialise le service de conversion global"""
    global _conversion_service
    _conversion_service = ConversionService(groq_api_key)


def get_conversion_service() -> Optional[ConversionService]:
    """Retourne l'instance du service de conversion"""
    return _conversion_service
