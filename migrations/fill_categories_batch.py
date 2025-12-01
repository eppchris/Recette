#!/usr/bin/env python3
"""
Script alternatif pour remplir conversion_category
Utilise des batchs pour éviter les erreurs I/O
"""

import sys
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.translation_service import TranslationService

def fill_in_batch(batch_size=20):
    """Remplit par batch de 20 pour éviter les I/O errors"""

    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("❌ Erreur: GROQ_API_KEY non défini")
        return

    ai_service = TranslationService(api_key)

    if not ai_service.check_api_status():
        print("❌ Erreur: API Groq non disponible")
        return

    print("✅ Service IA initialisé\n")

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
        print("✅ Tous les ingrédients ont déjà une catégorie")
        conn.close()
        return

    print(f"📊 {total} ingrédients à analyser\n")

    counts = {'volume': 0, 'poids': 0, 'unite': 0}
    updates = []  # Liste des mises à jour à faire

    for i, ing in enumerate(ingredients, 1):
        ing_id = ing['id']
        name_fr = ing['ingredient_name_fr']
        name_jp = ing['ingredient_name_jp']
        unit_fr = ing['unit_fr']

        print(f"[{i}/{total}] {name_fr} ({name_jp or 'N/A'})", end=" ... ")

        # Appeler l'IA
        category = ai_service.determine_ingredient_category(name_fr, name_jp, unit_fr)

        if category in ['volume', 'poids', 'unite']:
            updates.append((category, ing_id))
            emoji_map = {'volume': '💧', 'poids': '🧂', 'unite': '🔢'}
            print(f"{emoji_map[category]} {category.upper()} ✓")
            counts[category] += 1

            # Commit par batch
            if len(updates) >= batch_size:
                cursor.executemany("""
                    UPDATE ingredient_price_catalog
                    SET conversion_category = ?
                    WHERE id = ?
                """, updates)
                conn.commit()
                print(f"  💾 Batch de {len(updates)} sauvegardé")
                updates = []
        else:
            print("❌ ERREUR")

    # Sauvegarder le reste
    if updates:
        cursor.executemany("""
            UPDATE ingredient_price_catalog
            SET conversion_category = ?
            WHERE id = ?
        """, updates)
        conn.commit()
        print(f"\n💾 Dernier batch de {len(updates)} sauvegardé")

    print(f"\n📊 Résumé:")
    print(f"  💧 Volume: {counts['volume']}")
    print(f"  🧂 Poids:  {counts['poids']}")
    print(f"  🔢 Unité:  {counts['unite']}")
    print(f"  📈 Total: {sum(counts.values())}")

    conn.close()

if __name__ == "__main__":
    print("🤖 Remplissage par batch (évite erreurs I/O)\n")
    fill_in_batch(batch_size=20)
    print("\n✅ Terminé!")
