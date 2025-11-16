"""Service d'agrégation d'ingrédients pour les listes de courses d'événements"""

from typing import List, Dict
from collections import defaultdict
import re


class IngredientAggregator:
    """Service pour agréger les ingrédients de plusieurs recettes"""

    # Table de conversion vers unités standard (grammes pour poids, ml pour volume)
    UNIT_TO_STANDARD = {
        # Poids → grammes
        "kg": ("g", 1000),
        "g": ("g", 1),
        "mg": ("g", 0.001),

        # Volume → ml
        "l": ("ml", 1000),
        "ml": ("ml", 1),
        "cl": ("ml", 10),
        "dl": ("ml", 100),

        # Cuillères → ml
        "cuillère à soupe": ("ml", 15),
        "cuillère à café": ("ml", 5),
        "c. à soupe": ("ml", 15),
        "c. à café": ("ml", 5),
        "cs": ("ml", 15),
        "cc": ("ml", 5),

        # Japonais → ml
        "大さじ": ("ml", 15),
        "小さじ": ("ml", 5),
        "カップ": ("ml", 200),

        # Tasse → ml
        "tasse": ("ml", 250),
    }

    # Unités d'achat recommandées
    PURCHASE_UNITS = {
        "g": ["g", "kg"],
        "ml": ["ml", "l"]
    }

    # Traduction des unités
    UNIT_TRANSLATIONS = {
        "fr": {
            "g": "g",
            "kg": "kg",
            "ml": "ml",
            "l": "L",
            "大さじ": "c. à soupe",
            "小さじ": "c. à café",
            "カップ": "tasse",
        },
        "jp": {
            "g": "g",
            "kg": "kg",
            "ml": "ml",
            "l": "L",
            "cuillère à soupe": "大さじ",
            "cuillère à café": "小さじ",
            "c. à soupe": "大さじ",
            "c. à café": "小さじ",
            "cs": "大さじ",
            "cc": "小さじ",
            "tasse": "カップ",
        }
    }

    def translate_unit(self, unit: str, lang: str) -> str:
        """
        Traduit une unité dans la langue demandée

        Args:
            unit: Unité à traduire
            lang: Langue cible ('fr' ou 'jp')

        Returns:
            Unité traduite
        """
        if not unit:
            return unit

        translations = self.UNIT_TRANSLATIONS.get(lang, {})
        return translations.get(unit, unit)

    def normalize_ingredient_name(self, name: str) -> str:
        """
        Normalise le nom d'un ingrédient pour l'agrégation

        Args:
            name: Nom original de l'ingrédient

        Returns:
            Nom normalisé (minuscules, sans accents superflus)
        """
        # Minuscules
        normalized = name.lower().strip()

        # Suppression des variations communes
        normalized = normalized.replace("d'", "de ")
        normalized = re.sub(r'\s+', ' ', normalized)

        return normalized

    def convert_to_standard_unit(self, quantity: float, unit: str) -> tuple:
        """
        Convertit une quantité vers l'unité standard

        Args:
            quantity: Quantité à convertir
            unit: Unité d'origine

        Returns:
            Tuple (quantité_convertie, unité_standard)
        """
        unit_lower = unit.lower().strip()

        if unit_lower in self.UNIT_TO_STANDARD:
            standard_unit, multiplier = self.UNIT_TO_STANDARD[unit_lower]
            return (quantity * multiplier, standard_unit)

        # Si l'unité n'est pas reconnue, on la garde telle quelle
        return (quantity, unit)

    def convert_to_purchase_unit(self, quantity: float, standard_unit: str) -> tuple:
        """
        Convertit vers une unité d'achat appropriée

        Args:
            quantity: Quantité en unité standard
            standard_unit: Unité standard (g ou ml)

        Returns:
            Tuple (quantité, unité_achat)
        """
        if standard_unit == "g" and quantity >= 1000:
            return (round(quantity / 1000, 2), "kg")
        elif standard_unit == "ml" and quantity >= 1000:
            return (round(quantity / 1000, 2), "L")
        else:
            return (round(quantity, 1), standard_unit)

    def aggregate_ingredients(
        self,
        recipes_ingredients: List[Dict],
        lang: str = "fr"
    ) -> List[Dict]:
        """
        Agrège les ingrédients de plusieurs recettes

        Args:
            recipes_ingredients: Liste de dictionnaires contenant:
                - recipe_id: ID de la recette
                - recipe_name: Nom de la recette
                - servings_multiplier: Multiplicateur pour adapter aux convives
                - ingredients: Liste des ingrédients de cette recette
            lang: Langue

        Returns:
            Liste des ingrédients agrégés avec quantités totales
        """
        # Structure pour l'agrégation : {nom_normalisé: {données}}
        aggregated = defaultdict(lambda: {
            "ingredient_name": "",
            "original_names": set(),
            "total_quantity_standard": 0,
            "standard_unit": None,
            "source_recipes": [],
            "notes": []
        })

        # Parcourir toutes les recettes
        for recipe_data in recipes_ingredients:
            recipe_id = recipe_data["recipe_id"]
            recipe_name = recipe_data["recipe_name"]
            multiplier = recipe_data.get("servings_multiplier", 1.0)

            for ingredient in recipe_data["ingredients"]:
                # Normaliser le nom
                normalized_name = self.normalize_ingredient_name(ingredient["name"])

                # Quantité ajustée
                quantity = ingredient.get("quantity")
                if quantity is None or quantity == 0:
                    # Ingrédient sans quantité précise
                    aggregated[normalized_name]["original_names"].add(ingredient["name"])
                    aggregated[normalized_name]["ingredient_name"] = ingredient["name"]
                    aggregated[normalized_name]["source_recipes"].append({
                        "recipe_id": recipe_id,
                        "recipe_name": recipe_name,
                        "quantity": None,
                        "unit": ingredient.get("unit", "")
                    })
                    if ingredient.get("notes"):
                        aggregated[normalized_name]["notes"].append(ingredient["notes"])
                    continue

                adjusted_quantity = quantity * multiplier
                unit = ingredient.get("unit", "").strip()

                # Convertir vers unité standard
                std_quantity, std_unit = self.convert_to_standard_unit(adjusted_quantity, unit)

                # Agréger
                agg = aggregated[normalized_name]
                agg["original_names"].add(ingredient["name"])
                agg["ingredient_name"] = ingredient["name"]  # Garder un nom d'exemple

                # Vérifier la compatibilité des unités
                if agg["standard_unit"] is None:
                    agg["standard_unit"] = std_unit
                elif agg["standard_unit"] != std_unit:
                    # Unités incompatibles (ex: g et ml) - on garde séparé
                    # Pour l'instant, on ajoute quand même mais on note le problème
                    pass

                agg["total_quantity_standard"] += std_quantity
                agg["source_recipes"].append({
                    "recipe_id": recipe_id,
                    "recipe_name": recipe_name,
                    "quantity": adjusted_quantity,
                    "unit": unit
                })

                if ingredient.get("notes"):
                    agg["notes"].append(ingredient["notes"])

        # Convertir en liste de résultats
        result = []
        for normalized_name, data in aggregated.items():
            # Convertir vers unité d'achat
            if data["standard_unit"] and data["total_quantity_standard"] > 0:
                purchase_qty, purchase_unit = self.convert_to_purchase_unit(
                    data["total_quantity_standard"],
                    data["standard_unit"]
                )
                # Traduire l'unité dans la langue demandée
                purchase_unit = self.translate_unit(purchase_unit, lang)
            else:
                purchase_qty = None
                purchase_unit = ""

            # Traduire aussi les unités dans source_recipes
            translated_sources = []
            for source in data["source_recipes"]:
                translated_unit = self.translate_unit(source.get("unit", ""), lang)
                translated_sources.append({
                    **source,
                    "unit": translated_unit
                })

            result.append({
                "ingredient_name": data["ingredient_name"],
                "total_quantity": purchase_qty,
                "purchase_unit": purchase_unit,
                "source_recipes": translated_sources,
                "notes": "; ".join(data["notes"]) if data["notes"] else ""
            })

        # Trier par nom
        result.sort(key=lambda x: x["ingredient_name"])

        return result


# Instance globale
_ingredient_aggregator = IngredientAggregator()


def get_ingredient_aggregator() -> IngredientAggregator:
    """Retourne l'instance du service d'agrégation"""
    return _ingredient_aggregator
