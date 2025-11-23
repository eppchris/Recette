#!/usr/bin/env python3
"""
Test rapide pour vérifier que les templates se chargent sans erreur
"""
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os

# Configuration Jinja2
template_dir = os.path.join(os.path.dirname(__file__), "app", "templates")
env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(['html', 'xml'])
)

def test_template(template_name, context):
    """Teste le chargement d'un template"""
    try:
        template = env.get_template(template_name)
        # Essayer de rendre le template
        html = template.render(**context)
        print(f"  ✓ {template_name} - OK ({len(html)} caractères)")
        return True
    except Exception as e:
        print(f"  ✗ {template_name} - ERREUR: {e}")
        return False

def main():
    print("🧪 Test des templates modifiés\n")

    # Contexte de test minimal
    event = {
        'id': 1,
        'name': 'Test Event',
        'event_date': '2025-11-17',
        'location': 'Test Location',
        'attendees': 10,
        'event_type_name': 'PRO',
        'budget_planned': 1000.0
    }

    budget_summary = {
        'budget_planned': 1000.0,
        'total_planned': 500.0,
        'total_actual': 450.0,
        'expenses_planned': 300.0,
        'expenses_actual': 280.0,
        'ingredients_planned': 200.0,
        'ingredients_actual': 170.0,
        'remaining': 550.0,
        'variance': -50.0
    }

    categories = [
        {'id': 1, 'name': 'Location', 'icon': '🏠', 'is_system': 1},
        {'id': 2, 'name': 'Décoration', 'icon': '🎨', 'is_system': 1}
    ]

    expenses = [
        {
            'id': 1,
            'event_id': 1,
            'category_id': 1,
            'category_name': 'Location',
            'category_icon': '🏠',
            'description': 'Salle de réception',
            'planned_amount': 300.0,
            'actual_amount': 280.0,
            'is_paid': 1,
            'paid_date': '2025-11-17',
            'notes': 'Test note'
        }
    ]

    # Mock de la classe Request
    class MockRequest:
        def __init__(self):
            self.url = type('obj', (object,), {'path': '/test'})

    results = []

    # Test event_budget.html
    print("Test: event_budget.html")
    for lang in ['fr', 'jp']:
        print(f"  Langue: {lang}")
        context = {
            'request': MockRequest(),
            'lang': lang,
            'event': event,
            'categories': categories,
            'expenses': expenses,
            'budget_summary': budget_summary
        }
        results.append(test_template('event_budget.html', context))

    # Test shopping_list.html
    print("\nTest: shopping_list.html")

    # Fonction S pour les traductions (mock)
    def mock_S(key):
        translations = {
            'back': 'Retour',
            'shopping_list': 'Liste de courses',
            'event_date': 'Date',
            'event_location': 'Lieu',
            'event_attendees': 'Convives',
            'servings': 'portions',
            'generate_shopping_list': 'Générer la liste'
        }
        return translations.get(key, key)

    recipes = [
        {
            'recipe_id': 1,
            'recipe_name': 'Test Recipe',
            'recipe_slug': 'test-recipe',
            'servings_multiplier': 1.0
        }
    ]

    ingredients = [
        {
            'id': 1,
            'ingredient_name': 'Œufs',
            'purchase_quantity': 12,
            'purchase_unit': 'unités',
            'is_checked': 0,
            'planned_unit_price': 0.30,
            'actual_unit_price': 0.28,
            'is_purchased': 0,
            'source_recipes': [
                {'recipe_name': 'Test Recipe', 'quantity': 6, 'unit': 'unités'}
            ]
        }
    ]

    for lang in ['fr', 'jp']:
        print(f"  Langue: {lang}")
        context = {
            'request': MockRequest(),
            'lang': lang,
            'event': event,
            'recipes': recipes,
            'ingredients': ingredients,
            'S': mock_S
        }
        results.append(test_template('shopping_list.html', context))

    print("\n" + "=" * 60)
    if all(results):
        print("✅ Tous les templates se chargent correctement!")
        print("\n💡 Vous pouvez maintenant tester l'interface web:")
        print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return 0
    else:
        print("❌ Certains templates ont des erreurs")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
