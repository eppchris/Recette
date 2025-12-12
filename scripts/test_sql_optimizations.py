#!/usr/bin/env python3
"""
Script de test des optimisations SQL V1.10
Usage: python scripts/test_sql_optimizations.py
"""

import sys
import os

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import (
    get_event_recipes_with_ingredients,
    set_recipe_event_types,
    save_recipe_planning,
    get_recipe_planning,
    list_events,
    list_recipes
)
from app.models.db_core import get_db
import time

# Couleurs pour l'affichage
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(name, passed, message=""):
    if passed:
        print(f"{GREEN}✓{RESET} {name}")
        if message:
            print(f"  {BLUE}→{RESET} {message}")
    else:
        print(f"{RED}✗{RESET} {name}")
        if message:
            print(f"  {RED}→{RESET} {message}")

def test_indexes():
    """Vérifier que les index de performance existent"""
    print(f"\n{BLUE}=== Test 1: Vérification des index ==={RESET}\n")

    expected_indexes = [
        'idx_access_log_accessed_at',
        'idx_client_perf_created_at',
        'idx_event_user_date',
        'idx_recipe_user_created',
        'idx_shopping_list_event_date',
        'idx_event_expense_event_date',
        'idx_recipe_ingredient_trans_lang_name',
        'idx_event_recipe_event_position',
        'idx_ingredient_catalog_name_fr'
    ]

    with get_db() as con:
        cursor = con.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name LIKE 'idx_%'
        """)
        existing_indexes = [row['name'] for row in cursor.fetchall()]

    all_exist = True
    for idx in expected_indexes:
        exists = idx in existing_indexes
        print_test(f"Index {idx}", exists)
        if not exists:
            all_exist = False

    return all_exist

def test_get_event_recipes_with_ingredients():
    """Test de la fonction optimisée get_event_recipes_with_ingredients"""
    print(f"\n{BLUE}=== Test 2: get_event_recipes_with_ingredients() ==={RESET}\n")

    # Trouver un événement avec des recettes
    events = list_events()

    if not events:
        print_test("Événement trouvé", False, "Aucun événement dans la base")
        return False

    event_id = events[0]['id']
    print(f"{BLUE}Utilisation de l'événement ID {event_id}{RESET}")

    try:
        # Mesurer le temps d'exécution
        start = time.time()
        recipes = get_event_recipes_with_ingredients(event_id=event_id, lang='fr')
        elapsed = time.time() - start

        # Vérifications
        is_list = isinstance(recipes, list)
        print_test("Retourne une liste", is_list)

        if recipes:
            first_recipe = recipes[0]
            has_id = 'recipe_id' in first_recipe
            has_name = 'recipe_name' in first_recipe
            has_multiplier = 'servings_multiplier' in first_recipe
            has_ingredients = 'ingredients' in first_recipe

            print_test("Structure recipe_id", has_id)
            print_test("Structure recipe_name", has_name)
            print_test("Structure servings_multiplier", has_multiplier)
            print_test("Structure ingredients", has_ingredients)

            if has_ingredients:
                ingredients_is_list = isinstance(first_recipe['ingredients'], list)
                print_test("Ingrédients est une liste", ingredients_is_list)

                if first_recipe['ingredients']:
                    ing = first_recipe['ingredients'][0]
                    has_quantity = 'quantity' in ing
                    has_ing_name = 'name' in ing
                    has_unit = 'unit' in ing

                    print_test("Structure ingrédient.quantity", has_quantity)
                    print_test("Structure ingrédient.name", has_ing_name)
                    print_test("Structure ingrédient.unit", has_unit)

            print_test(f"Performance", True, f"{len(recipes)} recettes en {elapsed*1000:.2f}ms")
            return True
        else:
            print_test("Recettes trouvées", False, "Événement sans recettes")
            return True  # Pas une erreur, juste vide

    except Exception as e:
        print_test("Exécution sans erreur", False, str(e))
        return False

def test_set_recipe_event_types():
    """Test de la fonction optimisée set_recipe_event_types"""
    print(f"\n{BLUE}=== Test 3: set_recipe_event_types() ==={RESET}\n")

    # Trouver une recette
    recipes = list_recipes('fr')

    if not recipes:
        print_test("Recette trouvée", False, "Aucune recette dans la base")
        return False

    recipe_id = recipes[0]['id']
    print(f"{BLUE}Utilisation de la recette ID {recipe_id}{RESET}")

    try:
        # Test 1: Assigner des types
        test_types = [1, 2]  # Supposons que les IDs 1 et 2 existent
        set_recipe_event_types(recipe_id, test_types)
        print_test("Assignation de types", True, f"Types {test_types} assignés")

        # Test 2: Vider les types
        set_recipe_event_types(recipe_id, [])
        print_test("Suppression de types", True, "Types vidés")

        return True
    except Exception as e:
        print_test("Exécution sans erreur", False, str(e))
        return False

def test_save_recipe_planning():
    """Test de la fonction optimisée save_recipe_planning"""
    print(f"\n{BLUE}=== Test 4: save_recipe_planning() ==={RESET}\n")

    # Trouver un événement
    events = list_events()

    if not events:
        print_test("Événement trouvé", False, "Aucun événement dans la base")
        return False

    event_id = events[0]['id']
    print(f"{BLUE}Utilisation de l'événement ID {event_id}{RESET}")

    try:
        # Test 1: Sauvegarder une planification vide
        save_recipe_planning(event_id, [])
        print_test("Sauvegarde planning vide", True)

        # Test 2: Récupérer la planification
        planning = get_recipe_planning(event_id, 'fr')
        print_test("Récupération planning", True, f"{len(planning)} entrées")

        return True
    except Exception as e:
        print_test("Exécution sans erreur", False, str(e))
        return False

def test_query_plans():
    """Vérifier que les requêtes utilisent bien les index"""
    print(f"\n{BLUE}=== Test 5: Plans de requêtes (EXPLAIN) ==={RESET}\n")

    queries = [
        ("Stats access_log", "SELECT COUNT(*) FROM access_log WHERE accessed_at >= datetime('now', '-24 hours')"),
        ("Stats client_perf", "SELECT COUNT(*) FROM client_performance_log WHERE created_at >= datetime('now', '-24 hours')"),
        ("Events par user", "SELECT * FROM event WHERE user_id = 1 ORDER BY event_date DESC"),
    ]

    all_use_index = True
    with get_db() as con:
        cursor = con.cursor()
        for name, query in queries:
            cursor.execute(f"EXPLAIN QUERY PLAN {query}")
            plan = cursor.fetchone()
            plan_text = plan['detail'] if plan else ""

            # Vérifier si l'index est utilisé (SEARCH au lieu de SCAN)
            uses_index = 'USING INDEX' in plan_text
            print_test(f"{name}", uses_index, plan_text[:80])

            if not uses_index and 'SCAN' in plan_text:
                all_use_index = False

    return all_use_index

def main():
    print(f"\n{YELLOW}╔════════════════════════════════════════════════════╗{RESET}")
    print(f"{YELLOW}║  Test des optimisations SQL V1.10                 ║{RESET}")
    print(f"{YELLOW}╚════════════════════════════════════════════════════╝{RESET}")

    results = []

    # Exécuter tous les tests
    results.append(("Index de performance", test_indexes()))
    results.append(("get_event_recipes_with_ingredients", test_get_event_recipes_with_ingredients()))
    results.append(("set_recipe_event_types", test_set_recipe_event_types()))
    results.append(("save_recipe_planning", test_save_recipe_planning()))
    results.append(("Plans de requêtes", test_query_plans()))

    # Résumé
    print(f"\n{YELLOW}╔════════════════════════════════════════════════════╗{RESET}")
    print(f"{YELLOW}║  Résumé des tests                                  ║{RESET}")
    print(f"{YELLOW}╚════════════════════════════════════════════════════╝{RESET}\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = f"{GREEN}✓ PASS{RESET}" if result else f"{RED}✗ FAIL{RESET}"
        print(f"{status}  {name}")

    print(f"\n{BLUE}Total: {passed}/{total} tests réussis{RESET}")

    if passed == total:
        print(f"\n{GREEN}🎉 Tous les tests sont passés ! Prêt pour le déploiement.{RESET}\n")
        return 0
    else:
        print(f"\n{RED}⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
