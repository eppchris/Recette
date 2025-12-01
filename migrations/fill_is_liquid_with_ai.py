#!/usr/bin/env python3
"""
Script pour remplir le champ conversion_category du catalogue de prix avec l'IA
Catégories possibles: 'volume', 'poids', 'unite'
"""

import sys
import os
import sqlite3
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.translation_service import TranslationService

def fill_conversion_category():
    """Remplit le champ conversion_category pour les ingrédients non définis"""

    # Initialiser le service IA
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("❌ Erreur: GROQ_API_KEY non défini dans .env")
        return

    ai_service = TranslationService(api_key)

    # Vérifier que l'API fonctionne
    if not ai_service.check_api_status():
        print("❌ Erreur: API Groq non disponible")
        return

    print("✅ Service IA initialisé\n")

    # Connexion à la base de données
    db_path = 'data/recette.sqlite3'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Récupérer les ingrédients non définis
    cursor.execute("""
        SELECT id, ingredient_name_fr, ingredient_name_jp, unit_fr
        FROM ingredient_price_catalog
        WHERE conversion_category IS NULL
        ORDER BY ingredient_name_fr
    """)

    ingredients = cursor.fetchall()
    total = len(ingredients)

    if total == 0:
        print("✅ Tous les ingrédients ont déjà une valeur conversion_category définie")
        conn.close()
        return

    print(f"📊 {total} ingrédients à analyser\n")
    print("Catégories possibles:")
    print("  💧 volume  - Liquides (eau, huile, lait...)")
    print("  🧂 poids   - Solides mesurables au poids (sucre, farine, viande...)")
    print("  🔢 unite   - Achetés à l'unité (oeufs, sachets, feuilles...)\n")

    success_count = 0
    error_count = 0
    counts = {'volume': 0, 'poids': 0, 'unite': 0}

    for i, ing in enumerate(ingredients, 1):
        ing_id = ing['id']
        name_fr = ing['ingredient_name_fr']
        name_jp = ing['ingredient_name_jp']
        unit_fr = ing['unit_fr']

        print(f"[{i}/{total}] {name_fr} ({name_jp or 'N/A'}) - unité: {unit_fr or 'N/A'}", end=" ... ")

        # Appeler l'IA pour déterminer la catégorie (3 valeurs possibles)
        category = ai_service.determine_ingredient_category(name_fr, name_jp, unit_fr)

        if category in ['volume', 'poids', 'unite']:
            # Mettre à jour la base de données
            cursor.execute("""
                UPDATE ingredient_price_catalog
                SET conversion_category = ?
                WHERE id = ?
            """, (category, ing_id))
            conn.commit()

            emoji_map = {
                'volume': '💧 VOLUME',
                'poids': '🧂 POIDS',
                'unite': '🔢 UNITE'
            }
            print(f"{emoji_map[category]} ✓")
            success_count += 1
            counts[category] += 1
        else:
            print("❌ ERREUR")
            error_count += 1

    print(f"\n📊 Résumé:")
    print(f"  💧 Volume: {counts['volume']}")
    print(f"  🧂 Poids:  {counts['poids']}")
    print(f"  🔢 Unité:  {counts['unite']}")
    print(f"  ❌ Erreurs: {error_count}")
    print(f"  📈 Total: {total}")

    conn.close()

if __name__ == "__main__":
    print("🤖 Remplissage automatique du champ conversion_category avec l'IA\n")
    fill_conversion_category()
    print("\n✅ Terminé!")
