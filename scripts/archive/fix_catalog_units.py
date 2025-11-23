#!/usr/bin/env python3
"""Correction des unités dans le catalogue de prix"""

import sqlite3

DB_PATH = "data/recette.sqlite3"

# Corrections à appliquer : (ingredient_fr, nouvelle_unit_fr)
# Les quantités en JPY semblent être en grammes, pas en kg/L
unit_corrections = [
    ("Farine blanche", "g"),
    ("Farine", "g"),
    ("Carotte", "g"),
    ("Champignon de Paris", "g"),
    ("Chou", "g"),
    ("Concombre", "g"),
    ("Courge", "g"),
    ("Courgette", "g"),
    ("Daikon", "g"),
    ("Eau", "ml"),
    ("Huile", "ml"),
    ("Huile de salade", "ml"),
    ("Oignon", "g"),
    ("Panure", "g"),
    ("Sel", "g"),
    ("Sel d'olive", "ml"),
    ("Basilic", "g"),
    ("Jambon", "g"),
]

def fix_units():
    """Corrige les unités dans la base de données"""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    cursor = conn.cursor()

    updated = 0

    for ingredient_fr, correct_unit in unit_corrections:
        try:
            cursor.execute("""
                UPDATE ingredient_price_catalog
                SET unit_fr = ?
                WHERE ingredient_name_fr = ?
            """, (correct_unit, ingredient_fr))

            if cursor.rowcount > 0:
                updated += cursor.rowcount
                print(f"✓ {ingredient_fr}: {correct_unit}")
        except Exception as e:
            print(f"✗ Erreur pour {ingredient_fr}: {e}")

    conn.commit()
    conn.close()

    print(f"\n✓ {updated} ingrédients mis à jour")

if __name__ == "__main__":
    print("=== Correction des unités du catalogue ===\n")
    fix_units()
