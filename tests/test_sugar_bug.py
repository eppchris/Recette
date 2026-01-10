#!/usr/bin/env python3
"""
Test pour reproduire le bug du sucre
Cas : 1 cs de sucre avec UC existante (cs → kg = 0.015) mais ISC auto-créée (factor=1.0)
"""

import sqlite3
from app.services.cost_calculator import compute_estimated_cost_for_ingredient

def test_sugar_bug():
    """Test du bug avec le sucre"""

    print("=" * 80)
    print("TEST: Bug calcul sucre (1 cs)")
    print("=" * 80)

    conn = sqlite3.connect('data/recette.sqlite3')
    conn.row_factory = sqlite3.Row

    ingredient_name = "Sucre"
    recipe_qty = 1.0
    recipe_unit = "cs"
    currency = "EUR"

    print(f"\n📋 Données du test:")
    print(f"   Ingrédient: {ingredient_name}")
    print(f"   Quantité recette: {recipe_qty} {recipe_unit}")

    # Vérifier les données
    print(f"\n🔍 Données en base:")

    # Catalogue
    cursor = conn.execute("""
        SELECT unit_fr, price_eur, qty, conversion_category
        FROM ingredient_price_catalog
        WHERE LOWER(ingredient_name_fr) = LOWER(?)
    """, (ingredient_name,))
    ipc = cursor.fetchone()
    print(f"\n   Catalogue (IPC):")
    print(f"   - Unité: {ipc['unit_fr']}")
    print(f"   - Prix: {ipc['price_eur']}€ pour {ipc['qty']} {ipc['unit_fr']}")
    print(f"   - Catégorie: {ipc['conversion_category']}")

    # UC
    cursor = conn.execute("""
        SELECT from_unit, to_unit, factor, notes
        FROM unit_conversion
        WHERE category = ?
          AND LOWER(from_unit) = LOWER(?)
    """, (ipc['conversion_category'], recipe_unit))
    uc = cursor.fetchone()
    if uc:
        print(f"\n   Conversion Standard (UC):")
        print(f"   - {uc['from_unit']} → {uc['to_unit']} (factor={uc['factor']})")
        print(f"   - Notes: {uc['notes']}")

    # ISC
    cursor = conn.execute("""
        SELECT from_unit, to_unit, factor, notes
        FROM ingredient_specific_conversions
        WHERE LOWER(ingredient_name_fr) = LOWER(?)
          AND LOWER(from_unit) = LOWER(?)
    """, (ingredient_name, recipe_unit))
    isc = cursor.fetchone()
    if isc:
        print(f"\n   Conversion Spécifique (ISC):")
        print(f"   - {isc['from_unit']} → {isc['to_unit']} (factor={isc['factor']})")
        print(f"   - Notes: {isc['notes']}")

    # Calcul
    print(f"\n🧮 Calcul du coût:")
    result = compute_estimated_cost_for_ingredient(
        conn=conn,
        ingredient_name_fr=ingredient_name,
        recipe_qty=recipe_qty,
        recipe_unit=recipe_unit,
        currency=currency
    )

    print(f"\n   Résultat: {result.cost:.4f} {currency}")
    print(f"   Statut: {result.status}")
    print(f"   Chemin: {' → '.join(result.debug.get('path', []))}")

    # Détails debug
    print(f"\n   📊 Détails:")
    for key, value in result.debug.items():
        if key != 'path':
            print(f"      - {key}: {value}")

    # Vérification
    print(f"\n✅ Résultat ATTENDU:")
    print(f"   - Conversion UC: 1 cs × 0.015 = 0.015 kg")
    print(f"   - Prix: 0.015 × 3.00€ = 0.045€")
    print(f"   - Chemin: ['uc', 'ipc']")

    print(f"\n❌ Résultat OBTENU:")
    print(f"   - Coût: {result.cost:.4f}€")
    print(f"   - Chemin: {' → '.join(result.debug.get('path', []))}")

    if result.cost > 0.1:
        print(f"\n🐛 BUG CONFIRMÉ !")
        print(f"   L'ISC (factor=1.0) a été utilisée au lieu de la UC (factor=0.015)")
        print(f"   L'algorithme devrait utiliser UC en priorité sur ISC")
    else:
        print(f"\n✅ Pas de bug")

    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_sugar_bug()
