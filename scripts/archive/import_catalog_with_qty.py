#!/usr/bin/env python3
"""Script pour ajouter la colonne qty et importer les prix depuis Excel"""

import sqlite3
import pandas as pd
import sys

DB_PATH = "data/recette.sqlite3"

def add_qty_column():
    """Ajoute la colonne qty si elle n'existe pas"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Vérifier si la colonne existe déjà
    cursor.execute("PRAGMA table_info(ingredient_price_catalog)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'qty' not in columns:
        print("Ajout de la colonne qty...")
        cursor.execute("ALTER TABLE ingredient_price_catalog ADD COLUMN qty REAL DEFAULT 1.0")
        conn.commit()
        print("✓ Colonne qty ajoutée")
    else:
        print("✓ Colonne qty existe déjà")

    conn.close()

def import_from_excel(excel_file):
    """Importe les données depuis le fichier Excel"""
    print(f"\nLecture du fichier Excel: {excel_file}")

    # Lire le fichier Excel
    df = pd.read_excel(excel_file)
    print(f"✓ {len(df)} lignes trouvées")

    # Afficher les colonnes disponibles
    print(f"Colonnes: {list(df.columns)}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    updated = 0
    inserted = 0

    for _, row in df.iterrows():
        ingredient_fr = row.get('ingredient_name_fr')
        ingredient_jp = row.get('ingredient_name_jp')
        price_eur = row.get('price_eur')
        price_jpy = row.get('price_jpy')
        qty = row.get('qty', 1.0)
        unit_fr = row.get('unit_fr', 'kg')
        unit_jp = row.get('unit_jp', unit_fr)

        if pd.isna(ingredient_fr):
            continue

        # Vérifier si l'ingrédient existe
        cursor.execute(
            "SELECT id FROM ingredient_price_catalog WHERE ingredient_name_fr = ?",
            (ingredient_fr,)
        )
        existing = cursor.fetchone()

        if existing:
            # Mise à jour
            cursor.execute("""
                UPDATE ingredient_price_catalog
                SET price_eur = ?, price_jpy = ?, qty = ?,
                    unit_fr = ?, unit_jp = ?, ingredient_name_jp = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE ingredient_name_fr = ?
            """, (price_eur, price_jpy, qty, unit_fr, unit_jp, ingredient_jp, ingredient_fr))
            updated += 1
        else:
            # Insertion
            cursor.execute("""
                INSERT INTO ingredient_price_catalog
                (ingredient_name_fr, ingredient_name_jp, price_eur, price_jpy, qty, unit_fr, unit_jp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ingredient_fr, ingredient_jp, price_eur, price_jpy, qty, unit_fr, unit_jp))
            inserted += 1

    conn.commit()
    conn.close()

    print(f"\n✓ Import terminé:")
    print(f"  - {inserted} ingrédients insérés")
    print(f"  - {updated} ingrédients mis à jour")

if __name__ == "__main__":
    print("=== Migration: Ajout de la colonne qty ===\n")

    # Étape 1: Ajouter la colonne
    add_qty_column()

    # Étape 2: Importer depuis Excel si un fichier est fourni
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
        import_from_excel(excel_file)
    else:
        print("\nPour importer depuis Excel:")
        print("  python import_catalog_with_qty.py <fichier.xlsx>")
