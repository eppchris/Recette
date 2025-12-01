"""Service d'agrégation d'ingrédients pour les listes de courses d'événements"""

from typing import List, Dict, Optional
from collections import defaultdict
import re
import unicodedata


class IngredientAggregator:
    """Service pour agréger les ingrédients de plusieurs recettes"""

    def __init__(self):
        """Initialise l'agrégateur avec un cache pour les conversions"""
        self._conversion_cache = None
        self._cache_timestamp = None

        # Liste d'ingrédients connus comme liquides
        self.LIQUID_INGREDIENTS = {
            'eau', 'water', 'huile', 'oil', 'lait', 'milk',
            'sauce soja', 'soy sauce', 'vinaigre', 'vinegar',
            'vin', 'wine', 'bouillon', 'broth', 'stock',
            'jus', 'juice', 'sake', 'mirin', '水', '油',
            'しょうゆ', '醤油', '酢', 'みりん', '酒'
        }

    def _load_unit_conversions(self) -> Dict:
        """
        Charge les conversions d'unités depuis la base de données

        Returns:
            Dictionnaire {from_unit: [(to_unit, factor, category), ...]}
        """
        from app.models import db
        import time

        # Cache les conversions pendant 5 minutes
        current_time = time.time()
        if self._conversion_cache is None or (current_time - (self._cache_timestamp or 0)) > 300:
            conversions = db.get_all_unit_conversions()

            # Construire un dictionnaire de conversions
            # On crée une structure: {from_unit_lower: [(to_unit, factor, category), ...]}
            conv_dict = defaultdict(list)

            for conv in conversions:
                from_unit = conv['from_unit'].lower().strip()
                to_unit = conv['to_unit'].lower().strip()
                factor = conv['factor']
                category = conv.get('category', '')  # 'volume' ou 'poids'

                # Ajouter aussi les variantes FR et JP
                if conv.get('from_unit_fr'):
                    from_fr = conv['from_unit_fr'].lower().strip()
                    conv_dict[from_fr].append((to_unit, factor, category))

                if conv.get('from_unit_jp'):
                    from_jp = conv['from_unit_jp'].lower().strip()
                    conv_dict[from_jp].append((to_unit, factor, category))

                # Ajouter la conversion principale
                conv_dict[from_unit].append((to_unit, factor, category))

            self._conversion_cache = dict(conv_dict)
            self._cache_timestamp = current_time

        return self._conversion_cache

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

    def choose_display_name(self, original_names: set) -> str:
        """
        Choisit le meilleur nom à afficher parmi les variantes

        Args:
            original_names: Set des noms originaux trouvés

        Returns:
            Le nom le plus approprié pour l'affichage
        """
        if not original_names:
            return ""

        # Convertir en liste pour trier
        names = list(original_names)

        # Trier par ordre de préférence:
        # 1. Les noms avec ligatures (Œ) avant ceux sans (Oe)
        # 2. Les noms commençant par une majuscule
        # 3. Le plus court (sans parenthèses)
        def sort_key(name):
            has_ligature = 'œ' in name.lower() or 'æ' in name.lower()
            has_capital = name[0].isupper() if name else False
            has_parentheses = '(' in name
            return (
                not has_ligature,  # False (ligature) vient avant True (pas de ligature)
                not has_capital,   # False (majuscule) vient avant True (minuscule)
                has_parentheses,   # False (sans parenthèses) vient avant True
                len(name)          # Plus court en premier
            )

        names.sort(key=sort_key)
        return names[0]

    def normalize_ingredient_name(self, name: str) -> str:
        """
        Normalise le nom d'un ingrédient pour l'agrégation

        Args:
            name: Nom original de l'ingrédient

        Returns:
            Nom normalisé (minuscules, sans accents superflus, formes Unicode normalisées)
        """
        # Remplacer les ligatures courantes avant la normalisation
        name = name.replace('œ', 'oe').replace('Œ', 'oe')
        name = name.replace('æ', 'ae').replace('Æ', 'ae')

        # Normaliser Unicode (convertir é en e, etc.)
        # NFD décompose les caractères (é -> e + ´), puis on retire les accents
        normalized = unicodedata.normalize('NFD', name)
        # Garder seulement les caractères non-diacritiques
        normalized = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')

        # Minuscules
        normalized = normalized.lower().strip()

        # Suppression des variations communes
        normalized = normalized.replace("d'", "de ")
        normalized = normalized.replace("l'", "le ")
        normalized = re.sub(r'\s+', ' ', normalized)

        return normalized

    def _is_liquid_ingredient(self, ingredient_name: str) -> bool:
        """
        Détermine si un ingrédient est liquide

        Args:
            ingredient_name: Nom de l'ingrédient

        Returns:
            True si l'ingrédient est identifié comme liquide
        """
        name_lower = ingredient_name.lower().strip()
        return any(liquid in name_lower for liquid in self.LIQUID_INGREDIENTS)

    def convert_to_standard_unit(self, quantity: float, unit: str, ingredient_name: str = "") -> tuple:
        """
        Convertit une quantité vers l'unité standard (L pour liquides, kg pour solides)
        en utilisant la catégorie de l'ingrédient depuis le catalogue

        Args:
            quantity: Quantité à convertir
            unit: Unité d'origine
            ingredient_name: Nom de l'ingrédient

        Returns:
            Tuple (quantité_convertie, unité_standard)
        """
        from app.models import db

        if not unit:
            return (quantity, unit)

        unit_lower = unit.lower().strip()
        conversions = self._load_unit_conversions()

        # Si l'unité n'a pas de conversion disponible, on la garde telle quelle
        if unit_lower not in conversions:
            return (quantity, unit)

        # 1. Récupérer conversion_category depuis le catalogue
        catalog = db.get_ingredient_from_catalog(ingredient_name)

        if catalog and catalog.get('conversion_category'):
            category = catalog['conversion_category']  # 'volume' ou 'poids'
        else:
            # Fallback: utiliser l'ancienne méthode
            is_liquid = self._is_liquid_ingredient(ingredient_name)
            category = 'volume' if is_liquid else 'poids'

        # 2. Déduire l'unité standard cible
        standard_unit = 'l' if category == 'volume' else 'kg'

        # 3. Filtrer les conversions par catégorie
        possible_conversions = conversions[unit_lower]
        category_conversions = [
            (to_unit, factor)
            for to_unit, factor, conv_cat in possible_conversions
            if conv_cat == category
        ]

        # 4. Chercher conversion directe vers l'unité standard
        for to_unit, factor in category_conversions:
            if to_unit == standard_unit:
                return (quantity * factor, to_unit)

        # 5. Conversion en chaîne (ex: cs → g → kg)
        for to_unit, factor in category_conversions:
            if to_unit in conversions:
                # Récursion avec l'unité intermédiaire
                converted_qty = quantity * factor
                return self.convert_to_standard_unit(converted_qty, to_unit, ingredient_name)

        # 6. Chercher dans ingredient_specific_conversions
        specific = db.get_specific_conversion(ingredient_name, unit_lower)
        if specific:
            converted_qty = quantity * specific['factor']
            to_unit = specific['to_unit']

            # Continuer la conversion si nécessaire
            if to_unit != standard_unit and to_unit in conversions:
                return self.convert_to_standard_unit(converted_qty, to_unit, ingredient_name)
            else:
                return (converted_qty, to_unit)

        # 7. Pas de conversion trouvée → garder tel quel
        return (quantity, unit)

    def convert_to_purchase_unit(self, quantity: float, standard_unit: str) -> tuple:
        """
        Convertit vers une unité d'achat appropriée
        Règle: < 500 → unité de base, ≥ 500 → unité supérieure

        Args:
            quantity: Quantité en unité standard (L ou kg)
            standard_unit: Unité standard (l ou kg)

        Returns:
            Tuple (quantité, unité_achat)
        """
        unit_lower = standard_unit.lower().strip()

        # Pour les liquides: L → ml si < 0.5L
        if unit_lower == "l":
            if quantity < 0.5:
                return (round(quantity * 1000, 1), "ml")
            else:
                return (round(quantity, 2), "L")

        # Pour les solides: kg → g si < 0.5kg (500g)
        elif unit_lower == "kg":
            if quantity < 0.5:
                return (round(quantity * 1000, 1), "g")
            else:
                return (round(quantity, 2), "kg")

        # Autres unités: garder tel quel
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

                # Convertir en float si c'est une chaîne
                if isinstance(quantity, str):
                    try:
                        quantity = float(quantity)
                    except (ValueError, TypeError):
                        quantity = None

                if quantity is None or quantity == 0:
                    # Ingrédient sans quantité précise
                    aggregated[normalized_name]["original_names"].add(ingredient["name"])
                    # Traduire l'unité dans la langue demandée
                    unit = ingredient.get("unit", "")
                    translated_unit = self.translate_unit(unit, lang) if unit else ""
                    aggregated[normalized_name]["source_recipes"].append({
                        "recipe_id": recipe_id,
                        "recipe_name": recipe_name,
                        "quantity": None,
                        "unit": translated_unit
                    })
                    if ingredient.get("notes"):
                        aggregated[normalized_name]["notes"].append(ingredient["notes"])
                    continue

                adjusted_quantity = quantity * multiplier
                unit = ingredient.get("unit", "").strip()

                # Convertir vers unité standard (en passant le nom pour déterminer si liquide/solide)
                std_quantity, std_unit = self.convert_to_standard_unit(
                    adjusted_quantity, unit, ingredient["name"]
                )

                # Agréger
                agg = aggregated[normalized_name]
                agg["original_names"].add(ingredient["name"])

                # Vérifier la compatibilité des unités
                if agg["standard_unit"] is None:
                    agg["standard_unit"] = std_unit
                elif agg["standard_unit"] != std_unit:
                    # Unités incompatibles (ex: g et ml) - on garde séparé
                    # Pour l'instant, on ajoute quand même mais on note le problème
                    pass

                agg["total_quantity_standard"] += std_quantity
                # Traduire l'unité dans la langue demandée
                translated_unit = self.translate_unit(unit, lang)
                agg["source_recipes"].append({
                    "recipe_id": recipe_id,
                    "recipe_name": recipe_name,
                    "quantity": adjusted_quantity,
                    "unit": translated_unit
                })

                if ingredient.get("notes"):
                    agg["notes"].append(ingredient["notes"])

        # Convertir en liste de résultats
        result = []
        for normalized_name, data in aggregated.items():
            # Choisir le meilleur nom à afficher parmi les variantes
            display_name = self.choose_display_name(data["original_names"])

            # Convertir vers unité d'achat
            if data["total_quantity_standard"] > 0:
                if data["standard_unit"]:
                    purchase_qty, purchase_unit = self.convert_to_purchase_unit(
                        data["total_quantity_standard"],
                        data["standard_unit"]
                    )
                    # Traduire l'unité dans la langue demandée
                    purchase_unit = self.translate_unit(purchase_unit, lang)
                else:
                    # Ingrédient sans unité (ex: œufs, nombre d'items)
                    purchase_qty = round(data["total_quantity_standard"], 1)
                    purchase_unit = ""
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
                "ingredient_name": display_name,
                "total_quantity": purchase_qty,
                "purchase_unit": purchase_unit,
                "source_recipes": translated_sources,
                "notes": "; ".join(data["notes"]) if data["notes"] else ""
            })

        # Trier par nom (insensible à la casse)
        result.sort(key=lambda x: x["ingredient_name"].lower())

        return result


# Instance globale
_ingredient_aggregator = IngredientAggregator()


def get_ingredient_aggregator() -> IngredientAggregator:
    """Retourne l'instance du service d'agrégation"""
    return _ingredient_aggregator
