#!/usr/bin/env python3
"""
Script pour reconstruire le catalogue de prix à partir des recettes
Utile après une migration qui a vidé la table ingredient_price_catalog
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import db

def rebuild_catalog():
    """Reconstruit le catalogue de prix à partir des recettes existantes"""

    print("🔧 Reconstruction du catalogue de prix à partir des recettes\n")

    # Récupérer toutes les recettes
    recipes = db.get_all_recipes()
    print(f"📊 {len(recipes)} recettes trouvées")

    ingredients_added = set()

    for recipe in recipes:
        recipe_id = recipe['id']

        # Récupérer les ingrédients de cette recette
        ingredients = db.get_recipe_ingredients_with_translations(recipe_id, 'fr')

        for ing in ingredients:
            ingredient_name_fr = ing.get('ingredient_name_fr')
            ingredient_name_jp = ing.get('ingredient_name_jp')
            unit_fr = ing.get('unit_fr')
            unit_jp = ing.get('unit_jp')

            # Clé unique pour éviter les doublons
            key = (ingredient_name_fr, unit_fr)

            if key not in ingredients_added:
                # Ajouter au catalogue
                try:
                    db.add_ingredient_to_catalog(
                        ingredient_name_fr=ingredient_name_fr,
                        ingredient_name_jp=ingredient_name_jp,
                        unit_fr=unit_fr,
                        unit_jp=unit_jp,
                        price_eur=None,  # Prix à remplir manuellement
                        price_jpy=None,  # Prix à remplir manuellement
                        qty=1.0
                    )
                    print(f"  ✅ {ingredient_name_fr} ({unit_fr})")
                    ingredients_added.add(key)
                except Exception as e:
                    # Ignorer si déjà existe
                    if "UNIQUE constraint failed" not in str(e):
                        print(f"  ⚠️  {ingredient_name_fr}: {e}")

    print(f"\n📊 Résumé:")
    print(f"  ✅ {len(ingredients_added)} ingrédients ajoutés au catalogue")
    print(f"\n💡 Les prix sont à NULL - vous devrez les remplir manuellement")
    print(f"💡 Le champ conversion_category est à NULL - utilisez fill_is_liquid_with_ai.py")

if __name__ == "__main__":
    rebuild_catalog()
    print("\n✅ Terminé!")
