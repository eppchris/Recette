#!/usr/bin/env python3
"""
Test pour reproduire le bug JPY
Le calcul fonctionne en EUR mais pas en JPY
"""

import sqlite3
from app.services.cost_calculator import compute_estimated_cost_for_ingredient

def test_jpy_calculation():
    """Test du calcul en JPY vs EUR"""

    print("=" * 80)
    print("TEST: Calcul JPY vs EUR")
    print("=" * 80)

    conn = sqlite3.connect('data/recette.sqlite3')
    conn.row_factory = sqlite3.Row

    # Test avec tofu
    ingredient_name = "tofu"
    recipe_qty = 1.0
    recipe_unit = "pièce"

    print(f"\n📋 Ingrédient testé: {ingredient_name}")
    print(f"   Recette: {recipe_qty} {recipe_unit}")

    # Vérifier le catalogue
    cursor = conn.execute("""
        SELECT ingredient_name_fr, unit_fr, unit_jp, price_eur, price_jpy, conversion_category
        FROM ingredient_price_catalog
        WHERE LOWER(ingredient_name_fr) = LOWER(?)
    """, (ingredient_name,))
    ipc = cursor.fetchone()

    if ipc:
        print(f"\n   Catalogue:")
        print(f"   - Unité FR: {ipc['unit_fr']}, Prix: {ipc['price_eur']}€")
        print(f"   - Unité JP: {ipc['unit_jp']}, Prix: {ipc['price_jpy']}¥")
        print(f"   - Catégorie: {ipc['conversion_category']}")

    # Calcul EUR
    print(f"\n🧮 Calcul en EUR:")
    result_eur = compute_estimated_cost_for_ingredient(
        conn=conn,
        ingredient_name_fr=ingredient_name,
        recipe_qty=recipe_qty,
        recipe_unit=recipe_unit,
        currency="EUR",
        lang="fr"
    )
    print(f"   Résultat: {result_eur.cost:.4f} EUR")
    print(f"   Statut: {result_eur.status}")
    print(f"   Chemin: {' → '.join(result_eur.debug.get('path', []))}")
    if 'ipc_unit' in result_eur.debug:
        print(f"   IPC unit: {result_eur.debug['ipc_unit']}")

    # Calcul JPY
    print(f"\n🧮 Calcul en JPY:")
    result_jpy = compute_estimated_cost_for_ingredient(
        conn=conn,
        ingredient_name_fr=ingredient_name,
        recipe_qty=recipe_qty,
        recipe_unit=recipe_unit,
        currency="JPY",
        lang="jp"
    )
    print(f"   Résultat: {result_jpy.cost:.4f} JPY")
    print(f"   Statut: {result_jpy.status}")
    print(f"   Chemin: {' → '.join(result_jpy.debug.get('path', []))}")
    if 'ipc_unit' in result_jpy.debug:
        print(f"   IPC unit: {result_jpy.debug['ipc_unit']}")

    # Debug complet pour JPY
    print(f"\n   📊 Debug JPY:")
    for key, value in result_jpy.debug.items():
        if key not in ['path']:
            print(f"      - {key}: {value}")

    # Comparaison
    print(f"\n📊 Comparaison:")
    print(f"   EUR: {result_eur.cost:.2f}€ (status={result_eur.status})")
    print(f"   JPY: {result_jpy.cost:.2f}¥ (status={result_jpy.status})")

    if result_eur.cost > 0 and result_jpy.cost == 0:
        print(f"\n❌ BUG CONFIRMÉ !")
        print(f"   Le calcul EUR fonctionne mais pas le JPY")
    elif result_eur.cost > 0 and result_jpy.cost > 0:
        print(f"\n✅ Les deux calculs fonctionnent")
    else:
        print(f"\n⚠️  Problème avec les deux calculs")

    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_jpy_calculation()
