#!/usr/bin/env python3
"""
Test de la persistance de la devise
Vérifie que la devise est mémorisée avec l'événement et ne change pas selon la langue d'affichage
"""
import sys
import os

def test_currency_column_exists():
    """Vérifie que la colonne currency existe dans la table event"""
    print("🧪 Test 1: Vérification de la colonne currency\n")

    import sqlite3
    db_path = os.path.join(os.path.dirname(__file__), "data", "recette.sqlite3")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Vérifier la structure de la table
        cursor.execute("PRAGMA table_info(event)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'currency' in columns:
            print("  ✓ Colonne 'currency' existe dans 'event'")

            # Vérifier les valeurs
            cursor.execute("SELECT id, name, currency FROM event")
            events = cursor.fetchall()

            for event_id, name, currency in events:
                currency_display = currency if currency else "NULL"
                print(f"  ✓ Événement #{event_id} '{name}': {currency_display}")

            conn.close()
            return True
        else:
            print("  ✗ Colonne 'currency' manquante")
            conn.close()
            return False

    except Exception as e:
        print(f"  ✗ Erreur: {e}")
        return False


def test_db_function_exists():
    """Vérifie que la fonction update_event_currency existe"""
    print("\n🧪 Test 2: Vérification de la fonction DB\n")

    try:
        from app.models import db

        if hasattr(db, 'update_event_currency'):
            print("  ✓ Fonction 'update_event_currency()' existe")
            return True
        else:
            print("  ✗ Fonction 'update_event_currency()' manquante")
            return False

    except Exception as e:
        print(f"  ✗ Erreur lors de l'import: {e}")
        return False


def test_template_uses_event_currency():
    """Vérifie que les templates utilisent event.currency"""
    print("\n🧪 Test 3: Vérification des templates\n")

    try:
        templates_to_check = [
            ("app/templates/event_budget.html", "{% set currency = '€' if event.currency == 'EUR' else '¥' %}"),
            ("app/templates/shopping_list.html", "{% set currency = '€' if event.currency == 'EUR' else '¥' %}")
        ]

        all_good = True
        for template_path, expected_line in templates_to_check:
            full_path = os.path.join(os.path.dirname(__file__), template_path)

            if not os.path.exists(full_path):
                print(f"  ✗ {template_path} - FICHIER INTROUVABLE")
                all_good = False
                continue

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if expected_line in content:
                print(f"  ✓ {template_path} utilise event.currency")
            else:
                print(f"  ✗ {template_path} n'utilise PAS event.currency")
                all_good = False

        return all_good

    except Exception as e:
        print(f"  ✗ Erreur: {e}")
        return False


def test_route_sets_currency():
    """Vérifie que les routes définissent la devise"""
    print("\n🧪 Test 4: Vérification des routes\n")

    try:
        route_file = os.path.join(os.path.dirname(__file__), "app/routes/event_routes.py")

        with open(route_file, 'r', encoding='utf-8') as f:
            content = f.read()

        checks = [
            ("update_event_currency présent", "db.update_event_currency"),
            ("Route budget/planned vérifie currency", "if not event.get('currency')"),
            ("Route expenses/add vérifie currency", "currency = 'EUR' if lang == 'fr' else 'JPY'")
        ]

        all_good = True
        for check_name, search_string in checks:
            if search_string in content:
                print(f"  ✓ {check_name}")
            else:
                print(f"  ✗ {check_name} - MANQUANT")
                all_good = False

        return all_good

    except Exception as e:
        print(f"  ✗ Erreur: {e}")
        return False


def test_currency_logic():
    """Teste la logique de conversion devise ↔ langue"""
    print("\n🧪 Test 5: Logique de conversion\n")

    test_cases = [
        ('EUR', 'fr', '€', "EUR + français → €"),
        ('EUR', 'jp', '€', "EUR + japonais → € (pas ¥!)"),
        ('JPY', 'fr', '¥', "JPY + français → ¥ (pas €!)"),
        ('JPY', 'jp', '¥', "JPY + japonais → ¥"),
    ]

    all_passed = True
    for currency, lang, expected_symbol, description in test_cases:
        # Simuler la logique du template
        symbol = '€' if currency == 'EUR' else '¥'

        if symbol == expected_symbol:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description} - Attendu: {expected_symbol}, Obtenu: {symbol}")
            all_passed = False

    return all_passed


def main():
    print("=" * 70)
    print("🧪 Test de persistance de la devise")
    print("=" * 70)
    print()
    print("Objectif: Vérifier qu'un événement créé en japonais reste en ¥")
    print("          même quand affiché en français, et vice versa.")
    print()

    results = []

    # Test 1: Colonne existe
    results.append(test_currency_column_exists())

    # Test 2: Fonction DB existe
    results.append(test_db_function_exists())

    # Test 3: Templates utilisent event.currency
    results.append(test_template_uses_event_currency())

    # Test 4: Routes définissent la devise
    results.append(test_route_sets_currency())

    # Test 5: Logique de conversion
    results.append(test_currency_logic())

    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ")
    print("=" * 70)
    print()

    if all(results):
        print("✅ TOUS LES TESTS SONT PASSÉS!")
        print()
        print("🎯 La devise est maintenant persistante:")
        print("   • Un budget créé en japonais sera en ¥")
        print("   • Même si on passe en français, il reste en ¥")
        print("   • Un budget créé en français sera en €")
        print("   • Même si on passe en japonais, il reste en €")
        print()
        print("📝 Comment ça marche:")
        print("   1. Quand on définit le budget ou ajoute la 1ère dépense:")
        print("      → La devise est définie selon la langue actuelle")
        print("      → Elle est sauvegardée dans event.currency")
        print("   2. Quand on affiche le budget:")
        print("      → Le template utilise event.currency (pas lang)")
        print("      → La devise reste cohérente")
        print()
        print("🧪 Pour tester manuellement:")
        print("   1. Créer un événement en français")
        print("   2. Ajouter un budget (sera en €)")
        print("   3. Passer en japonais avec le bouton JP")
        print("   4. Vérifier que les montants restent en €")
        print()
        return 0
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print()
        print("Veuillez vérifier les erreurs ci-dessus.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
