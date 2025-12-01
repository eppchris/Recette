#!/usr/bin/env python3
"""
Script pour importer les conversions d'unités depuis le CSV dans la base de données
"""
import sqlite3
import csv
from pathlib import Path

def import_unit_conversions():
    # Chemins
    db_path = Path(__file__).parent / "data" / "recette.sqlite3"
    csv_path = Path(__file__).parent / "data" / "Unit_conversion.csv"

    # Connexion à la base de données
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Supprimer toutes les conversions existantes
    print("Suppression des conversions existantes...")
    cursor.execute("DELETE FROM unit_conversion")
    conn.commit()
    print(f"  {cursor.rowcount} conversions supprimées")

    # Lire le CSV et insérer les nouvelles données
    print(f"\nImport depuis {csv_path}...")
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        count = 0

        for row in reader:
            cursor.execute("""
                INSERT INTO unit_conversion
                (id, from_unit, to_unit, factor, category, notes, created_at,
                 from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                int(row['id']),
                row['from_unit'],
                row['to_unit'],
                float(row['factor']),
                row['category'] if row['category'] else None,
                row['notes'] if row['notes'] else None,
                row['created_at'],
                row['from_unit_fr'],
                row['to_unit_fr'],
                row['from_unit_jp'],
                row['to_unit_jp']
            ))
            count += 1
            print(f"  Importé: {row['from_unit']} → {row['to_unit']} (factor: {row['factor']})")

    conn.commit()
    print(f"\n✅ {count} conversions importées avec succès!")

    # Vérifier les conversions importées par catégorie
    print("\nRésumé par catégorie:")
    cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM unit_conversion
        GROUP BY category
        ORDER BY category
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} conversions")

    conn.close()

if __name__ == "__main__":
    import_unit_conversions()
