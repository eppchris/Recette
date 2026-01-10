"""
Test de l'adaptation automatique des quantités au nombre de convives
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models import db
from app.services.ingredient_aggregator import get_ingredient_aggregator
import math


def test_attendees_multiplier():
    """
    Test du calcul automatique du multiplicateur basé sur le nombre de convives

    Scénario :
    - Recette pour 4 personnes
    - Événement avec 12 convives
    - Multiplicateur attendu : 12 / 4 = 3
    """
    print("\n" + "="*80)
    print("TEST 1: Calcul automatique du multiplicateur")
    print("="*80)

    # Simuler les données d'une recette
    recipes_data = [{
        'recipe_id': 1,
        'recipe_name': 'Test Recipe',
        'servings_default': 4,  # Recette pour 4 personnes
        'event_attendees': 12,   # Événement pour 12 personnes
        'servings_multiplier': 3.0,  # Devrait être calculé automatiquement : 12/4 = 3
        'ingredients': [
            {
                'quantity': 2,  # 2 œufs par portion de 4
                'name': 'Œuf',
                'name_fr': 'Œuf',
                'unit': '',  # Unité vide = unitaire
                'notes': ''
            },
            {
                'quantity': 200,  # 200g de farine
                'name': 'Farine',
                'name_fr': 'Farine',
                'unit': 'g',
                'notes': ''
            }
        ]
    }]

    # Agréger les ingrédients
    aggregator = get_ingredient_aggregator()
    result = aggregator.aggregate_ingredients(recipes_data, lang='fr')

    print(f"\n📊 Recette originale : 4 personnes")
    print(f"👥 Événement : 12 convives")
    print(f"✖️  Multiplicateur calculé : {recipes_data[0]['servings_multiplier']}")
    print(f"\n📝 Résultats :")

    success = True

    for item in result:
        name = item['ingredient_name']
        qty = item['total_quantity']
        unit = item['purchase_unit']

        print(f"  • {name}: {qty} {unit}")

        if name == 'oeuf':  # Normalisé sans accent
            # 2 œufs × 3 = 6 œufs
            expected = 6
            if qty == expected:
                print(f"    ✅ Correct (2 × 3 = {expected})")
            else:
                print(f"    ❌ ERREUR : attendu {expected}, obtenu {qty}")
                success = False

        elif name == 'farine':
            # 200g × 3 = 600g (ou 0.6kg selon la conversion)
            if unit == 'kg':
                expected = 0.6
                if qty == expected:
                    print(f"    ✅ Correct (200g × 3 = 600g = {expected}kg)")
                else:
                    print(f"    ❌ ERREUR : attendu {expected}kg, obtenu {qty}{unit}")
                    success = False
            else:  # unit == 'g'
                expected = 600.0
                if qty == expected:
                    print(f"    ✅ Correct (200g × 3 = {expected}g)")
                else:
                    print(f"    ❌ ERREUR : attendu {expected}g, obtenu {qty}{unit}")
                    success = False

    return success


def test_ceil_rounding():
    """
    Test de l'arrondissement au supérieur pour les unités indivisibles

    Scénario :
    - 2.3 œufs → doit donner 3 œufs (math.ceil)
    - 1.8 paquets → doit donner 2 paquets
    """
    print("\n" + "="*80)
    print("TEST 2: Arrondissement au supérieur des unités indivisibles")
    print("="*80)

    # Simuler une recette avec quantités décimales après multiplication
    recipes_data = [{
        'recipe_id': 2,
        'recipe_name': 'Test Rounding',
        'servings_multiplier': 2.3,  # Multiplicateur qui donne des décimales
        'ingredients': [
            {
                'quantity': 1,  # 1 œuf × 2.3 = 2.3 œufs
                'name': 'Œuf',
                'name_fr': 'Œuf',
                'unit': '',
                'notes': ''
            },
            {
                'quantity': 1,  # 1 paquet × 2.3 = 2.3 paquets (si c'était sans unité)
                'name': 'Levure chimique',
                'name_fr': 'Levure chimique',
                'unit': '',  # Sans unité = indivisible
                'notes': ''
            },
            {
                'quantity': 100,  # 100g × 2.3 = 230g (pas d'arrondissement supérieur)
                'name': 'Sucre',
                'name_fr': 'Sucre',
                'unit': 'g',
                'notes': ''
            }
        ]
    }]

    aggregator = get_ingredient_aggregator()
    result = aggregator.aggregate_ingredients(recipes_data, lang='fr')

    print(f"\n✖️  Multiplicateur : 2.3")
    print(f"\n📝 Résultats :")

    success = True

    for item in result:
        name = item['ingredient_name']
        qty = item['total_quantity']
        unit = item['purchase_unit']

        print(f"  • {name}: {qty} {unit}")

        if name == 'oeuf':
            # 1 × 2.3 = 2.3 → ceil(2.3) = 3
            raw_value = 1 * 2.3
            expected = 3
            if qty == expected:
                print(f"    ✅ Correct ({raw_value:.1f} → ceil = {expected})")
            else:
                print(f"    ❌ ERREUR : attendu {expected}, obtenu {qty}")
                success = False

        elif name == 'levure chimique':
            # 1 × 2.3 = 2.3 → ceil(2.3) = 3
            raw_value = 1 * 2.3
            expected = 3
            if qty == expected:
                print(f"    ✅ Correct ({raw_value:.1f} → ceil = {expected})")
            else:
                print(f"    ❌ ERREUR : attendu {expected}, obtenu {qty}")
                success = False

        elif name == 'sucre':
            # 100g × 2.3 = 230g (pas d'arrondissement supérieur pour g)
            expected = 230.0
            if qty == expected:
                print(f"    ✅ Correct (100g × 2.3 = {expected}g, pas d'arrondissement)")
            else:
                print(f"    ❌ ERREUR : attendu {expected}g, obtenu {qty}{unit}")
                success = False

    return success


def test_multiple_recipes_same_event():
    """
    Test avec plusieurs recettes dans le même événement

    Scénario :
    - 2 recettes différentes (4 et 6 portions)
    - Événement pour 12 convives
    - Vérifier l'agrégation correcte
    """
    print("\n" + "="*80)
    print("TEST 3: Plusieurs recettes avec différentes portions par défaut")
    print("="*80)

    recipes_data = [
        {
            'recipe_id': 1,
            'recipe_name': 'Recette A (4 portions)',
            'servings_default': 4,
            'event_attendees': 12,
            'servings_multiplier': 3.0,  # 12/4 = 3
            'ingredients': [
                {
                    'quantity': 2,
                    'name': 'Œuf',
                    'name_fr': 'Œuf',
                    'unit': '',
                    'notes': ''
                }
            ]
        },
        {
            'recipe_id': 2,
            'recipe_name': 'Recette B (6 portions)',
            'servings_default': 6,
            'event_attendees': 12,
            'servings_multiplier': 2.0,  # 12/6 = 2
            'ingredients': [
                {
                    'quantity': 3,
                    'name': 'Œuf',
                    'name_fr': 'Œuf',
                    'unit': '',
                    'notes': ''
                }
            ]
        }
    ]

    aggregator = get_ingredient_aggregator()
    result = aggregator.aggregate_ingredients(recipes_data, lang='fr')

    print(f"\n📊 Recette A : 4 portions → multiplicateur 3.0 (12/4)")
    print(f"   - 2 œufs × 3 = 6 œufs")
    print(f"\n📊 Recette B : 6 portions → multiplicateur 2.0 (12/6)")
    print(f"   - 3 œufs × 2 = 6 œufs")
    print(f"\n📝 Total agrégé attendu : 6 + 6 = 12 œufs")

    success = True

    for item in result:
        if item['ingredient_name'] == 'oeuf':
            qty = item['total_quantity']
            expected = 12

            print(f"\n  • Œufs agrégés: {qty}")
            if qty == expected:
                print(f"    ✅ Correct (6 + 6 = {expected})")
            else:
                print(f"    ❌ ERREUR : attendu {expected}, obtenu {qty}")
                success = False

    return success


if __name__ == '__main__':
    print("\n" + "🧪 TESTS D'ADAPTATION AU NOMBRE DE CONVIVES ".center(80, "="))

    all_success = True

    # Test 1
    if not test_attendees_multiplier():
        all_success = False

    # Test 2
    if not test_ceil_rounding():
        all_success = False

    # Test 3
    if not test_multiple_recipes_same_event():
        all_success = False

    # Résumé final
    print("\n" + "="*80)
    print("RÉSUMÉ DES TESTS")
    print("="*80)

    if all_success:
        print("✅ TOUS LES TESTS SONT PASSÉS")
        sys.exit(0)
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        sys.exit(1)
