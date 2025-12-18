#!/usr/bin/env python3
"""
Test de régression pour la correction du bug des conversions UC multiples

BUG CORRIGÉ:
Avant, l'algorithme prenait seulement la PREMIÈRE conversion UC trouvée (LIMIT 1)
et s'arrêtait si aucun IPC n'existait pour l'unité cible.

Exemple avec le sucre:
- UC disponibles: cs → g (15.0) et cs → kg (0.015)
- Catalogue: seulement kg (pas de g)
- AVANT: prenait cs → g, ne trouvait pas d'IPC pour g, passait à ISC
- APRÈS: essaie cs → g (échec), puis cs → kg (succès!)

Ce test vérifie que l'algorithme essaie TOUTES les conversions UC possibles.
"""

import sqlite3
from app.services.cost_calculator import compute_estimated_cost_for_ingredient

def test_multiple_uc_conversions():
    """Test que l'algo essaie toutes les UC possibles"""

    print("=" * 80)
    print("TEST: Conversions UC multiples (régression bug sucre)")
    print("=" * 80)

    conn = sqlite3.connect('data/recette.sqlite3')
    conn.row_factory = sqlite3.Row

    # Cas de test: cuillère à soupe de sucre
    # - Recette: 1 cs
    # - UC disponibles: cs → g (15.0) et cs → kg (0.015)
    # - Catalogue: kg seulement (pas de g)
    # → L'algo doit essayer cs → g (échec), puis cs → kg (succès)

    ingredient_name = "Sucre"
    recipe_qty = 1.0
    recipe_unit = "cs"
    currency = "EUR"

    print(f"\n📋 Scénario de test:")
    print(f"   Ingrédient: {ingredient_name}")
    print(f"   Recette: {recipe_qty} {recipe_unit}")
    print(f"   Catalogue: kg à 3.00€")
    print(f"   UC disponibles: cs → g (15.0), cs → kg (0.015)")
    print(f"   L'algo doit utiliser cs → kg car le catalogue n'a pas de 'g'")

    # Vérifier les données
    cursor = conn.execute("""
        SELECT COUNT(*) as count
        FROM unit_conversion
        WHERE category = 'poids' AND LOWER(from_unit) = 'cs'
    """)
    uc_count = cursor.fetchone()['count']
    print(f"\n✓ {uc_count} conversions UC trouvées depuis 'cs'")

    # Calcul
    result = compute_estimated_cost_for_ingredient(
        conn=conn,
        ingredient_name_fr=ingredient_name,
        recipe_qty=recipe_qty,
        recipe_unit=recipe_unit,
        currency=currency
    )

    # Vérifications
    print(f"\n📊 Résultat:")
    print(f"   Coût: {result.cost:.4f}€")
    print(f"   Statut: {result.status}")
    print(f"   Chemin: {' → '.join(result.debug.get('path', []))}")
    print(f"   UC utilisée: {result.debug.get('uc_from')} → {result.debug.get('uc_to')} (factor={result.debug.get('uc_factor')})")

    # Assertions
    expected_cost = 0.045  # 1 cs × 0.015 = 0.015 kg → 0.015 × 3.00€ = 0.045€
    assert result.status == "ok", f"Status devrait être 'ok', obtenu '{result.status}'"
    assert abs(result.cost - expected_cost) < 0.001, f"Coût devrait être {expected_cost}€, obtenu {result.cost}€"
    assert result.debug.get('uc_to') == 'kg', "L'UC devrait convertir vers 'kg'"
    assert result.debug.get('uc_factor') == 0.015, "Le facteur UC devrait être 0.015"

    print(f"\n✅ TEST RÉUSSI!")
    print(f"   L'algorithme a correctement essayé toutes les UC disponibles")
    print(f"   et a utilisé cs → kg (0.015) au lieu de s'arrêter à cs → g")

    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_multiple_uc_conversions()
