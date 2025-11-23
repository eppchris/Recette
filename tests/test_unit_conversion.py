#!/usr/bin/env python3
"""
Test du système de conversion d'unités
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.models import db

def test_basic_conversions():
    """Test des conversions de base"""
    print("\n=== Test des conversions de base ===\n")

    # Test 1: ml → L
    result = db.convert_unit(500, 'ml', 'L')
    print(f"500 ml → L = {result} L (attendu: 0.5 L)")

    # Test 2: L → ml
    result = db.convert_unit(1.5, 'L', 'ml')
    print(f"1.5 L → ml = {result} ml (attendu: 1500 ml)")

    # Test 3: c.s. → ml
    result = db.convert_unit(3, 'c.s.', 'ml')
    print(f"3 c.s. → ml = {result} ml (attendu: 45 ml)")

    # Test 4: g → kg
    result = db.convert_unit(250, 'g', 'kg')
    print(f"250 g → kg = {result} kg (attendu: 0.25 kg)")

    # Test 5: Unités identiques
    result = db.convert_unit(100, 'ml', 'ml')
    print(f"100 ml → ml = {result} ml (attendu: 100 ml)")

    # Test 6: Conversion impossible
    result = db.convert_unit(10, 'g', 'L')
    print(f"10 g → L = {result} (attendu: None)")


def test_convertible_units():
    """Test de la liste des conversions disponibles"""
    print("\n=== Conversions disponibles depuis 'c.s.' ===\n")

    conversions = db.get_convertible_units('c.s.')
    for conv in conversions:
        print(f"  c.s. → {conv['to_unit']}: facteur {conv['factor']} ({conv['category']})")


def test_price_calculation():
    """Test du calcul de prix avec conversion automatique"""
    print("\n=== Test calcul de prix avec conversion ===\n")

    # D'abord, vérifier s'il y a des ingrédients dans le catalogue
    with db.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ingredient_name_fr, price_eur, unit_fr, price_jpy, unit_jp
            FROM ingredient_price_catalog
            LIMIT 5
        """)
        catalog_items = cursor.fetchall()

    if not catalog_items:
        print("  ⚠️  Aucun ingrédient dans le catalogue pour tester")
        return

    print("  Ingrédients disponibles dans le catalogue:")
    for item in catalog_items:
        print(f"    - {item['ingredient_name_fr']}: {item['price_eur']}€/{item['unit_fr']} ou {item['price_jpy']}¥/{item['unit_jp']}")

    # Test avec le premier ingrédient
    if catalog_items:
        ing = catalog_items[0]
        ingredient_name = ing['ingredient_name_fr']

        # Test 1: Même unité
        print(f"\n  Test: 2 {ing['unit_fr']} de {ingredient_name}")
        result = db.calculate_ingredient_price(ingredient_name, 2, ing['unit_fr'], 'EUR')
        if result:
            print(f"    Prix total: {result['total_price']:.2f} €")
            print(f"    Prix unitaire: {result['unit_price']:.2f} €/{result['catalog_unit']}")

        # Test 2: Avec conversion (si possible)
        # Essayer de tester une conversion ml → L ou g → kg
        if ing['unit_fr'].lower() == 'l':
            print(f"\n  Test: 500 ml de {ingredient_name} (prix catalogue en L)")
            result = db.calculate_ingredient_price(ingredient_name, 500, 'ml', 'EUR')
            if result:
                print(f"    Quantité recette: {result['recipe_quantity']} {result['recipe_unit']}")
                print(f"    Quantité convertie: {result['converted_quantity']} {result['catalog_unit']}")
                print(f"    Prix total: {result['total_price']:.2f} €")
                if 'warning' in result:
                    print(f"    ⚠️  {result['warning']}")
        elif ing['unit_fr'].lower() == 'kg':
            print(f"\n  Test: 250 g de {ingredient_name} (prix catalogue en kg)")
            result = db.calculate_ingredient_price(ingredient_name, 250, 'g', 'EUR')
            if result:
                print(f"    Quantité recette: {result['recipe_quantity']} {result['recipe_unit']}")
                print(f"    Quantité convertie: {result['converted_quantity']} {result['catalog_unit']}")
                print(f"    Prix total: {result['total_price']:.2f} €")
                if 'warning' in result:
                    print(f"    ⚠️  {result['warning']}")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  TEST DU SYSTÈME DE CONVERSION D'UNITÉS")
    print("="*60)

    test_basic_conversions()
    test_convertible_units()
    test_price_calculation()

    print("\n" + "="*60)
    print("  FIN DES TESTS")
    print("="*60 + "\n")
