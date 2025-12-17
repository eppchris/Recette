#!/usr/bin/env python3
"""
Script de test pour vérifier le calcul du coût des carottes
Cas de test : 1 pièce de carotte avec conversion pièce → g → kg
"""

import sqlite3
import sys
from app.services.cost_calculator import compute_estimated_cost_for_ingredient

def test_carrot_cost():
    """Test du calcul de coût pour les carottes"""

    print("=" * 80)
    print("TEST: Calcul du coût des carottes")
    print("=" * 80)

    # Connexion à la base de données
    conn = sqlite3.connect('data/recette.sqlite3')
    conn.row_factory = sqlite3.Row

    # Données de test
    ingredient_name = "carotte"
    recipe_qty = 1.0
    recipe_unit = "pièce"
    currency = "EUR"

    print(f"\n📋 Données du test:")
    print(f"   Ingrédient: {ingredient_name}")
    print(f"   Quantité recette: {recipe_qty} {recipe_unit}")
    print(f"   Devise: {currency}")

    # Vérifier les données en base
    print(f"\n🔍 Vérification des données en base:")

    # 1. Catalogue des prix
    cursor = conn.execute("""
        SELECT ingredient_name_fr, unit_fr, price_eur, qty, conversion_category
        FROM ingredient_price_catalog
        WHERE LOWER(ingredient_name_fr) = LOWER(?)
    """, (ingredient_name,))
    ipc_rows = cursor.fetchall()

    if ipc_rows:
        print(f"\n   ✅ Catalogue des prix (ingredient_price_catalog):")
        for row in ipc_rows:
            print(f"      - {row['unit_fr']}: {row['price_eur']}€ pour {row['qty']} {row['unit_fr']}")
            print(f"        Catégorie: {row['conversion_category']}")
    else:
        print(f"   ❌ Pas de prix dans le catalogue pour '{ingredient_name}'")
        return

    category = ipc_rows[0]['conversion_category']

    # 2. Conversion spécifique
    cursor = conn.execute("""
        SELECT from_unit, to_unit, factor, notes
        FROM ingredient_specific_conversions
        WHERE LOWER(ingredient_name_fr) = LOWER(?)
    """, (ingredient_name,))
    isc_rows = cursor.fetchall()

    if isc_rows:
        print(f"\n   ✅ Conversions spécifiques (ingredient_specific_conversions):")
        for row in isc_rows:
            print(f"      - {row['from_unit']} → {row['to_unit']} (facteur: {row['factor']})")
            if row['notes']:
                print(f"        Notes: {row['notes']}")
    else:
        print(f"\n   ⚠️  Pas de conversion spécifique pour '{ingredient_name}'")

    # 3. Conversions standard
    if category:
        cursor = conn.execute("""
            SELECT from_unit, to_unit, factor, notes
            FROM unit_conversion
            WHERE category = ?
            ORDER BY from_unit, to_unit
        """, (category,))
        uc_rows = cursor.fetchall()

        if uc_rows:
            print(f"\n   ✅ Conversions standard (catégorie '{category}'):")
            # Afficher seulement les conversions pertinentes
            relevant = [r for r in uc_rows if r['from_unit'] in ['pièce', 'g', 'kg'] or r['to_unit'] in ['pièce', 'g', 'kg']]
            for row in relevant:
                print(f"      - {row['from_unit']} → {row['to_unit']} (facteur: {row['factor']})")

    # Calcul du coût
    print(f"\n🧮 Calcul du coût:")
    result = compute_estimated_cost_for_ingredient(
        conn=conn,
        ingredient_name_fr=ingredient_name,
        recipe_qty=recipe_qty,
        recipe_unit=recipe_unit,
        currency=currency
    )

    print(f"\n   Résultat: {result.cost:.2f} {currency}")
    print(f"   Statut: {result.status}")
    print(f"\n   📊 Détails du calcul (debug):")
    for key, value in result.debug.items():
        if key == 'path':
            print(f"      - Chemin: {' → '.join(value)}")
        else:
            print(f"      - {key}: {value}")

    # Vérification du résultat attendu
    expected_cost = 0.30
    print(f"\n✅ Résultat attendu: {expected_cost} EUR")

    if result.status == "ok":
        if abs(result.cost - expected_cost) < 0.01:
            print(f"✅ TEST RÉUSSI ! Coût calculé: {result.cost:.2f}€ (attendu: {expected_cost}€)")
        else:
            print(f"❌ TEST ÉCHOUÉ ! Coût calculé: {result.cost:.2f}€ (attendu: {expected_cost}€)")
    else:
        print(f"❌ TEST ÉCHOUÉ ! Statut: {result.status}")
        print(f"\n💡 Suggestions:")
        if result.status == "missing_conversion":
            print("   - Vérifier que la conversion spécifique existe : pièce → g pour 'carotte'")
            print("   - Vérifier que la conversion standard existe : g → kg dans la catégorie 'poids'")
        elif result.status == "missing_data":
            print("   - Vérifier que le prix existe dans ingredient_price_catalog")
        elif result.status == "missing_price":
            print("   - Le prix dans le catalogue est NULL ou 0")

    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_carrot_cost()
