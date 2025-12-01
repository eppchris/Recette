#!/usr/bin/env python3
"""
Script de test pour vérifier les conversions d'unités
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ingredient_aggregator import IngredientAggregator

def test_conversion(ingredient, quantity, unit):
    """Teste une conversion"""
    aggregator = IngredientAggregator()

    print(f"\n{'='*60}")
    print(f"Test: {quantity} {unit} de {ingredient}")
    print(f"{'='*60}")

    result_qty, result_unit = aggregator.convert_to_standard_unit(quantity, unit, ingredient)

    print(f"  Résultat: {result_qty} {result_unit}")

    # Convertir vers unité d'achat
    purchase_qty, purchase_unit = aggregator.convert_to_purchase_unit(result_qty, result_unit)
    print(f"  Unité d'achat: {purchase_qty} {purchase_unit}")

    return result_qty, result_unit

def main():
    print("🧪 Test des Conversions d'Unités\n")

    # Tests pour ingrédients SOLIDES
    print("\n" + "="*60)
    print("INGRÉDIENTS SOLIDES (conversion_category = 'poids')")
    print("="*60)

    test_conversion("Sucre", 1, "大")      # 1 大さじ de sucre → 15g → 0.015kg
    test_conversion("Sucre", 50, "g")      # 50g de sucre → 0.05kg
    test_conversion("Riz", 1, "カップ")    # 1 カップ de riz → 180g → 0.18kg
    test_conversion("Riz", 200, "g")       # 200g de riz → 0.2kg

    # Tests pour ingrédients LIQUIDES
    print("\n" + "="*60)
    print("INGRÉDIENTS LIQUIDES (conversion_category = 'volume')")
    print("="*60)

    test_conversion("Eau", 1, "大")        # 1 大さじ d'eau → 15ml → 0.015L
    test_conversion("Eau", 250, "ml")      # 250ml d'eau → 0.25L
    test_conversion("Huile", 1, "カップ")  # 1 カップ d'huile → 200ml → 0.2L
    test_conversion("Huile", 500, "ml")    # 500ml d'huile → 0.5L

    print("\n" + "="*60)
    print("✅ Tests terminés !")
    print("="*60)

if __name__ == "__main__":
    main()
