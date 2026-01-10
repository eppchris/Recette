#!/usr/bin/env python3
"""
Test de création automatique de conversion spécifique (ISC)
Cas de test : ingrédient avec prix dans catalogue mais sans conversion
"""

import sqlite3
from app.services.cost_calculator import compute_estimated_cost_for_ingredient

def test_auto_isc_creation():
    """Test la création automatique d'ISC quand aucune conversion n'existe"""

    print("=" * 80)
    print("TEST: Création automatique de conversion spécifique (ISC)")
    print("=" * 80)

    conn = sqlite3.connect('data/recette.sqlite3')
    conn.row_factory = sqlite3.Row

    # Scénario : Pomme de terre
    # - Catalogue : prix en kg
    # - Recette : utilise "pièce"
    # - Pas de conversion ISC existante
    # → Le système doit créer une ISC automatiquement avec factor=1.0

    ingredient_name = "pomme de terre"
    recipe_qty = 2.0
    recipe_unit = "pièce"
    currency = "EUR"

    print(f"\n📋 Données du test:")
    print(f"   Ingrédient: {ingredient_name}")
    print(f"   Quantité recette: {recipe_qty} {recipe_unit}")
    print(f"   Devise: {currency}")

    # Vérifier si ISC existe déjà
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM ingredient_specific_conversions
        WHERE LOWER(ingredient_name_fr) = LOWER(?)
          AND LOWER(from_unit) = LOWER(?)
    """, (ingredient_name, recipe_unit))

    existing_isc = cursor.fetchone()

    if existing_isc:
        print(f"\n⚠️  ISC existante trouvée, suppression pour le test...")
        cursor.execute("""
            DELETE FROM ingredient_specific_conversions
            WHERE id = ?
        """, (existing_isc['id'],))
        conn.commit()

    # Vérifier le catalogue
    cursor.execute("""
        SELECT ingredient_name_fr, unit_fr, price_eur, qty, conversion_category
        FROM ingredient_price_catalog
        WHERE LOWER(ingredient_name_fr) = LOWER(?)
    """, (ingredient_name,))

    ipc = cursor.fetchone()

    if not ipc:
        print(f"\n❌ Pas de prix dans le catalogue pour '{ingredient_name}'")
        print("   Ajout d'un prix de test...")
        cursor.execute("""
            INSERT INTO ingredient_price_catalog
            (ingredient_name_fr, ingredient_name_jp, unit_fr, unit_jp, price_eur, qty, conversion_category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (ingredient_name, ingredient_name, 'kg', 'kg', 3.50, 1.0, 'poids'))
        conn.commit()
        print("   ✅ Prix ajouté : 3.50€/kg")
    else:
        print(f"\n✅ Catalogue des prix:")
        print(f"   - {ipc['unit_fr']}: {ipc['price_eur']}€ pour {ipc['qty']} {ipc['unit_fr']}")
        print(f"   - Catégorie: {ipc['conversion_category']}")

    # Premier calcul : doit créer l'ISC automatiquement
    print(f"\n🧮 Premier calcul (ISC n'existe pas):")

    result = compute_estimated_cost_for_ingredient(
        conn=conn,
        ingredient_name_fr=ingredient_name,
        recipe_qty=recipe_qty,
        recipe_unit=recipe_unit,
        currency=currency
    )

    print(f"\n   Résultat: {result.cost:.2f} {currency}")
    print(f"   Statut: {result.status}")
    print(f"   Chemin: {' → '.join(result.debug.get('path', []))}")

    if 'warning' in result.debug:
        print(f"   ⚠️  {result.debug['warning']}")

    # Vérifier que l'ISC a bien été créée
    cursor.execute("""
        SELECT * FROM ingredient_specific_conversions
        WHERE LOWER(ingredient_name_fr) = LOWER(?)
          AND LOWER(from_unit) = LOWER(?)
    """, (ingredient_name, recipe_unit))

    created_isc = cursor.fetchone()

    if created_isc:
        print(f"\n✅ ISC créée automatiquement:")
        print(f"   - De: {created_isc['from_unit']}")
        print(f"   - Vers: {created_isc['to_unit']}")
        print(f"   - Facteur: {created_isc['factor']}")
        print(f"   - Notes: {created_isc['notes']}")
    else:
        print(f"\n❌ Aucune ISC créée !")

    # Deuxième calcul : doit utiliser l'ISC créée
    print(f"\n🧮 Deuxième calcul (ISC existe maintenant):")

    result2 = compute_estimated_cost_for_ingredient(
        conn=conn,
        ingredient_name_fr=ingredient_name,
        recipe_qty=recipe_qty,
        recipe_unit=recipe_unit,
        currency=currency
    )

    print(f"\n   Résultat: {result2.cost:.2f} {currency}")
    print(f"   Statut: {result2.status}")
    print(f"   Chemin: {' → '.join(result2.debug.get('path', []))}")

    # Vérification
    print(f"\n📊 Résumé:")

    if result.status == "isc_created":
        print(f"   ✅ Premier calcul : ISC créée automatiquement")
    else:
        print(f"   ❌ Premier calcul : ISC NON créée (status={result.status})")

    if result2.status == "ok" and "isc" in result2.debug.get('path', []):
        print(f"   ✅ Deuxième calcul : ISC utilisée")
    else:
        print(f"   ❌ Deuxième calcul : ISC NON utilisée")

    # Afficher un avertissement pour l'utilisateur
    print(f"\n⚠️  IMPORTANT:")
    print(f"   La conversion automatique utilise un facteur par défaut de 1.0")
    print(f"   Cela signifie: 1 {recipe_unit} = 1 {created_isc['to_unit'] if created_isc else '?'}")
    print(f"   Vous DEVEZ ajuster ce facteur dans l'interface de gestion des conversions !")
    print(f"   Exemple réaliste pour pomme de terre: 1 pièce ≈ 0.15 kg (150g)")

    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_auto_isc_creation()
