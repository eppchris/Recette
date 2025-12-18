#!/usr/bin/env python3
"""
Test du calcul de coût d'une recette en japonais
Vérifier que le nom français est bien utilisé pour chercher dans le catalogue
"""

from app.models.db_recipes import calculate_recipe_cost

def test_recipe_cost_japanese():
    """Test le calcul de coût d'une recette en japonais"""

    print("=" * 80)
    print("TEST: Calcul coût recette en japonais")
    print("=" * 80)

    # Tester la recette de tofu (slug = 3)
    slug = "3"
    lang = "jp"
    servings = 4

    print(f"\n📋 Recette: {slug}")
    print(f"   Langue: {lang}")
    print(f"   Portions: {servings}")

    # Calcul en japonais
    result_jp = calculate_recipe_cost(slug, lang, servings)

    if not result_jp:
        print(f"\n❌ Recette non trouvée !")
        return

    print(f"\n💴 Résultat JPY:")
    print(f"   Total: {result_jp['total_planned']:.2f} ¥")
    print(f"   Devise: {result_jp['currency']}")

    # Vérifier quelques ingrédients
    print(f"\n📊 Détail des ingrédients (JPY):")
    for ing in result_jp['ingredients'][:5]:
        status_icon = "✅" if ing['cost_status'] == "ok" else "❌"
        print(f"   {status_icon} {ing['name']}: {ing['planned_total']:.2f} ¥ (status={ing['cost_status']})")

    # Calcul en français pour comparer
    result_fr = calculate_recipe_cost(slug, "fr", servings)

    print(f"\n💶 Résultat EUR (comparaison):")
    print(f"   Total: {result_fr['total_planned']:.2f} €")

    print(f"\n📊 Détail des ingrédients (EUR):")
    for ing in result_fr['ingredients'][:5]:
        status_icon = "✅" if ing['cost_status'] == "ok" else "❌"
        print(f"   {status_icon} {ing['name']}: {ing['planned_total']:.2f} € (status={ing['cost_status']})")

    # Vérification
    print(f"\n📋 Vérification:")
    jp_has_costs = any(ing['planned_total'] > 0 for ing in result_jp['ingredients'])
    fr_has_costs = any(ing['planned_total'] > 0 for ing in result_fr['ingredients'])

    if jp_has_costs and fr_has_costs:
        print(f"   ✅ Les deux versions ont des coûts calculés")
        print(f"   EUR total: {result_fr['total_planned']:.2f}€")
        print(f"   JPY total: {result_jp['total_planned']:.2f}¥")
    elif fr_has_costs and not jp_has_costs:
        print(f"   ❌ EUR fonctionne mais pas JPY (bug !)")
    elif jp_has_costs and not fr_has_costs:
        print(f"   ⚠️  JPY fonctionne mais pas EUR")
    else:
        print(f"   ❌ Aucun coût calculé dans les deux langues")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_recipe_cost_japanese()
