#!/usr/bin/env python3
"""
Test de création automatique de conversion en japonais
"""

import sqlite3
from app.services.cost_calculator import compute_estimated_cost_for_ingredient

def test_japanese_isc():
    """Test la création automatique d'ISC en japonais"""

    print("=" * 80)
    print("TEST: Création automatique ISC en japonais")
    print("=" * 80)

    conn = sqlite3.connect('data/recette.sqlite3')
    conn.row_factory = sqlite3.Row

    # Test avec langue japonaise
    ingredient_name = "pomme de terre"
    recipe_qty = 2.0
    recipe_unit = "pièce"
    currency = "JPY"
    lang = "jp"

    print(f"\n📋 Test avec langue={lang}")

    # Premier calcul : doit créer l'ISC en japonais
    result = compute_estimated_cost_for_ingredient(
        conn=conn,
        ingredient_name_fr=ingredient_name,
        recipe_qty=recipe_qty,
        recipe_unit=recipe_unit,
        currency=currency,
        lang=lang
    )

    print(f"\n   Résultat: {result.cost:.2f} {currency}")
    print(f"   Statut: {result.status}")

    # Vérifier l'ISC créée
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM ingredient_specific_conversions
        WHERE ingredient_name_fr = ? AND from_unit = ?
    """, (ingredient_name, recipe_unit))

    isc = cursor.fetchone()

    if isc:
        print(f"\n✅ ISC créée:")
        print(f"   Notes: {isc['notes']}")

        if '自動作成' in isc['notes']:
            print(f"   ✅ Notes en japonais !")
        else:
            print(f"   ❌ Notes pas en japonais !")
    else:
        print(f"\n❌ Aucune ISC créée")

    # Test avec langue française
    print(f"\n" + "=" * 80)
    print("TEST: Création automatique ISC en français")
    print("=" * 80)

    # Supprimer l'ISC précédente
    cursor.execute("DELETE FROM ingredient_specific_conversions WHERE ingredient_name_fr = ?", (ingredient_name,))
    conn.commit()

    lang_fr = "fr"
    print(f"\n📋 Test avec langue={lang_fr}")

    result_fr = compute_estimated_cost_for_ingredient(
        conn=conn,
        ingredient_name_fr=ingredient_name,
        recipe_qty=recipe_qty,
        recipe_unit=recipe_unit,
        currency="EUR",
        lang=lang_fr
    )

    print(f"\n   Résultat: {result_fr.cost:.2f} EUR")
    print(f"   Statut: {result_fr.status}")

    cursor.execute("""
        SELECT * FROM ingredient_specific_conversions
        WHERE ingredient_name_fr = ? AND from_unit = ?
    """, (ingredient_name, recipe_unit))

    isc_fr = cursor.fetchone()

    if isc_fr:
        print(f"\n✅ ISC créée:")
        print(f"   Notes: {isc_fr['notes']}")

        if 'Conversion automatique' in isc_fr['notes']:
            print(f"   ✅ Notes en français !")
        else:
            print(f"   ❌ Notes pas en français !")
    else:
        print(f"\n❌ Aucune ISC créée")

    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_japanese_isc()
