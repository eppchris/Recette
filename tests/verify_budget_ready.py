#!/usr/bin/env python3
"""
Script de vérification finale avant mise en production
"""
import sys
import os

def check_files_exist():
    """Vérifie que tous les fichiers nécessaires existent"""
    print("📁 Vérification des fichiers...\n")

    files = [
        "migrations/add_budget_management.sql",
        "apply_budget_migration.py",
        "app/models/db.py",
        "app/routes/event_routes.py",
        "app/templates/event_budget.html",
        "app/templates/event_detail.html",
        "app/templates/shopping_list.html",
        "BUDGET_IMPLEMENTATION.md"
    ]

    missing = []
    for file_path in files:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} - MANQUANT")
            missing.append(file_path)

    if missing:
        print(f"\n⚠️  {len(missing)} fichier(s) manquant(s)")
        return False

    print(f"\n✅ Tous les fichiers sont présents")
    return True


def check_database_migration():
    """Vérifie que la migration a été appliquée"""
    print("\n🗄️  Vérification de la base de données...\n")

    import sqlite3
    db_path = os.path.join(os.path.dirname(__file__), "data", "recette.sqlite3")

    if not os.path.exists(db_path):
        print(f"  ⚠️  Base de données non trouvée: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Vérifier les tables
        tables = ['expense_category', 'expense_category_translation',
                  'event_expense', 'ingredient_price_history']

        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if cursor.fetchone():
                print(f"  ✓ Table '{table}' existe")
            else:
                print(f"  ✗ Table '{table}' manquante")
                conn.close()
                return False

        # Vérifier les colonnes
        cursor.execute("PRAGMA table_info(event)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'budget_planned' in columns:
            print(f"  ✓ Colonne 'budget_planned' ajoutée à 'event'")
        else:
            print(f"  ✗ Colonne 'budget_planned' manquante dans 'event'")
            conn.close()
            return False

        cursor.execute("PRAGMA table_info(shopping_list_item)")
        columns = [col[1] for col in cursor.fetchall()]
        required_cols = ['planned_unit_price', 'actual_unit_price', 'is_purchased']
        for col in required_cols:
            if col in columns:
                print(f"  ✓ Colonne '{col}' ajoutée à 'shopping_list_item'")
            else:
                print(f"  ✗ Colonne '{col}' manquante dans 'shopping_list_item'")
                conn.close()
                return False

        # Vérifier les catégories
        cursor.execute("SELECT COUNT(*) FROM expense_category")
        cat_count = cursor.fetchone()[0]
        print(f"  ✓ {cat_count} catégories de dépenses disponibles")

        conn.close()
        print("\n✅ Base de données correctement migrée")
        return True

    except Exception as e:
        print(f"\n❌ Erreur lors de la vérification: {e}")
        return False


def check_functions_available():
    """Vérifie que les fonctions DB sont disponibles"""
    print("\n🔧 Vérification des fonctions...\n")

    try:
        from app.models import db

        functions = [
            'list_expense_categories',
            'get_event_expenses',
            'get_event_budget_summary',
            'get_ingredient_price_suggestions'
        ]

        for func_name in functions:
            if hasattr(db, func_name):
                print(f"  ✓ {func_name}()")
            else:
                print(f"  ✗ {func_name}() - MANQUANTE")
                return False

        print("\n✅ Toutes les fonctions sont disponibles")
        return True

    except Exception as e:
        print(f"\n❌ Erreur lors de l'import: {e}")
        return False


def check_routes_configured():
    """Vérifie que les routes sont configurées"""
    print("\n🛣️  Vérification des routes...\n")

    try:
        # Import main pour déclencher l'enregistrement des routes
        import main
        from app.routes import event_routes

        # Vérifier que le router a les bonnes routes
        routes = [route.path for route in event_routes.router.routes]

        required_routes = [
            '/events/{event_id}/budget',
            '/events/{event_id}/budget/planned',
            '/events/{event_id}/expenses/add'
        ]

        all_present = True
        for route_path in required_routes:
            if route_path in routes:
                print(f"  ✓ {route_path}")
            else:
                print(f"  ✗ {route_path} - MANQUANTE")
                all_present = False

        if all_present:
            print("\n✅ Toutes les routes sont configurées")
            return True
        else:
            return False

    except Exception as e:
        print(f"\n❌ Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_templates_valid():
    """Vérifie que les templates sont valides"""
    print("\n📄 Vérification des templates...\n")

    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape

        template_dir = os.path.join(os.path.dirname(__file__), "app", "templates")
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

        templates = ['event_budget.html', 'shopping_list.html']

        for template_name in templates:
            try:
                env.get_template(template_name)
                print(f"  ✓ {template_name}")
            except Exception as e:
                print(f"  ✗ {template_name} - ERREUR: {e}")
                return False

        print("\n✅ Tous les templates sont valides")
        return True

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return False


def main():
    print("=" * 70)
    print("🔍 VÉRIFICATION FINALE - Fonctionnalité Budget")
    print("=" * 70)
    print()

    checks = [
        ("Fichiers", check_files_exist),
        ("Base de données", check_database_migration),
        ("Fonctions", check_functions_available),
        ("Routes", check_routes_configured),
        ("Templates", check_templates_valid)
    ]

    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Erreur lors de '{check_name}': {e}")
            results.append(False)

    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ")
    print("=" * 70)
    print()

    for i, (check_name, _) in enumerate(checks):
        status = "✅ OK" if results[i] else "❌ ÉCHEC"
        print(f"  {status} - {check_name}")

    print()

    if all(results):
        print("🎉 TOUTES LES VÉRIFICATIONS SONT PASSÉES !")
        print()
        print("✅ La fonctionnalité budget est prête pour les tests en dev")
        print()
        print("🚀 Prochaines étapes :")
        print("   1. Démarrer le serveur: uvicorn main:app --reload")
        print("   2. Accéder à un événement")
        print("   3. Cliquer sur '💰 Gérer le budget'")
        print("   4. Tester toutes les fonctionnalités")
        print("   5. Vérifier en FR et en JP")
        print()
        print("📖 Documentation complète : BUDGET_IMPLEMENTATION.md")
        print()
        return 0
    else:
        print("⚠️  CERTAINES VÉRIFICATIONS ONT ÉCHOUÉ")
        print()
        print("Veuillez corriger les problèmes avant de continuer.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
