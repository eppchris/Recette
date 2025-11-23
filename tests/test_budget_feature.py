#!/usr/bin/env python3
"""
Script de test pour vérifier que les fonctionnalités budget sont disponibles
"""
import sys
import os

# Ajouter le chemin du projet au PYTHONPATH
sys.path.insert(0, os.path.dirname(__file__))

from app.models import db

def test_budget_functions():
    """Teste que toutes les fonctions budgétaires sont disponibles"""

    print("🧪 Test des fonctions budgétaires\n")

    # Liste des fonctions à vérifier
    functions_to_test = [
        'get_event_budget_planned',
        'update_event_budget_planned',
        'list_expense_categories',
        'create_expense_category',
        'update_expense_category',
        'delete_expense_category',
        'get_event_expenses',
        'create_event_expense',
        'update_event_expense',
        'delete_event_expense',
        'get_event_budget_summary',
        'get_ingredient_price_suggestions',
        'update_ingredient_price_from_shopping_list',
    ]

    missing = []
    available = []

    for func_name in functions_to_test:
        if hasattr(db, func_name):
            available.append(func_name)
            print(f"  ✓ {func_name}")
        else:
            missing.append(func_name)
            print(f"  ✗ {func_name} - MANQUANTE")

    print(f"\n📊 Résultat:")
    print(f"  Disponibles: {len(available)}/{len(functions_to_test)}")
    print(f"  Manquantes: {len(missing)}/{len(functions_to_test)}")

    if missing:
        print(f"\n⚠️  Fonctions manquantes: {', '.join(missing)}")
        return False

    print("\n✅ Toutes les fonctions budgétaires sont disponibles!")
    return True


def test_expense_categories():
    """Teste la récupération des catégories de dépenses"""
    print("\n🧪 Test de récupération des catégories\n")

    try:
        categories_fr = db.list_expense_categories('fr')
        categories_jp = db.list_expense_categories('jp')

        print(f"  Catégories FR trouvées: {len(categories_fr)}")
        for cat in categories_fr:
            print(f"    {cat.get('icon', '📋')} {cat.get('name', 'N/A')}")

        print(f"\n  Catégories JP trouvées: {len(categories_jp)}")
        for cat in categories_jp:
            print(f"    {cat.get('icon', '📋')} {cat.get('name', 'N/A')}")

        if len(categories_fr) == 0:
            print("\n⚠️  Aucune catégorie trouvée - vérifier que la migration a bien été appliquée")
            return False

        print("\n✅ Catégories récupérées avec succès!")
        return True

    except Exception as e:
        print(f"\n❌ Erreur lors de la récupération des catégories: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_budget_summary():
    """Teste le calcul du résumé budgétaire"""
    print("\n🧪 Test du résumé budgétaire\n")

    try:
        # Tester avec un événement inexistant (devrait retourner des valeurs nulles)
        summary = db.get_event_budget_summary(99999)

        print(f"  Résumé pour événement inexistant:")
        print(f"    Total prévu: {summary.get('total_planned', 0)}")
        print(f"    Total réel: {summary.get('total_actual', 0)}")
        print(f"    Ingredients prévu: {summary.get('ingredients_planned', 0)}")
        print(f"    Ingredients réel: {summary.get('ingredients_actual', 0)}")

        print("\n✅ Fonction de résumé budgétaire opérationnelle!")
        return True

    except Exception as e:
        print(f"\n❌ Erreur lors du test du résumé: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Test des fonctionnalités budgétaires")
    print("=" * 60)

    results = []

    # Test 1: Vérifier que les fonctions existent
    results.append(test_budget_functions())

    # Test 2: Vérifier les catégories
    results.append(test_expense_categories())

    # Test 3: Vérifier le résumé budgétaire
    results.append(test_budget_summary())

    print("\n" + "=" * 60)
    if all(results):
        print("✅ Tous les tests sont passés avec succès!")
        print("\n💡 Vous pouvez maintenant tester l'interface web:")
        print("   1. Démarrer le serveur: uvicorn app.main:app --reload")
        print("   2. Accéder à un événement")
        print("   3. Cliquer sur le bouton '💰 Gérer le budget'")
        sys.exit(0)
    else:
        print("❌ Certains tests ont échoué")
        sys.exit(1)
