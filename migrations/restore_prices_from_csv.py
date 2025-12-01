#!/usr/bin/env python3
"""
Script pour restaurer les prix depuis le fichier CSV
"""

import csv
import sqlite3
import sys
import os

def restore_prices_from_csv():
    """Restaure les prix depuis data/Prix ingrédient.csv"""

    csv_path = 'data/Prix ingrédient.csv'
    db_path = 'data/recette.sqlite3'

    if not os.path.exists(csv_path):
        print(f"❌ Fichier CSV non trouvé: {csv_path}")
        return

    print("📥 Restauration des prix depuis le CSV\n")

    # Connexion à la base de données
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Lire le CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        # Détecter le délimiteur (point-virgule)
        reader = csv.DictReader(f, delimiter=';')

        updated_count = 0
        created_count = 0
        error_count = 0

        for row in reader:
            ingredient_name_fr = row['ingredient_name_fr']
            ingredient_name_jp = row.get('ingredient_name_jp', '')
            unit_fr = row['unit_fr']
            unit_jp = row.get('unit_jp', '')
            price_eur = float(row['price_eur']) if row['price_eur'] else None
            price_jpy = float(row['price_jpy']) if row['price_jpy'] else None
            qty = float(row['qty']) if row.get('qty') else 1.0
            conversion_category = row.get('conversion_category', '').strip() or None

            try:
                # Vérifier si l'ingrédient existe déjà
                cursor.execute("""
                    SELECT id FROM ingredient_price_catalog
                    WHERE LOWER(ingredient_name_fr) = LOWER(?)
                    AND LOWER(unit_fr) = LOWER(?)
                """, (ingredient_name_fr, unit_fr))

                existing = cursor.fetchone()

                if existing:
                    # Mise à jour
                    cursor.execute("""
                        UPDATE ingredient_price_catalog
                        SET ingredient_name_jp = ?,
                            unit_jp = ?,
                            price_eur = ?,
                            price_jpy = ?,
                            qty = ?,
                            conversion_category = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (ingredient_name_jp, unit_jp, price_eur, price_jpy, qty,
                          conversion_category, existing['id']))

                    print(f"  ✅ Mis à jour: {ingredient_name_fr} ({unit_fr}) - {price_eur}€ / {price_jpy}¥")
                    updated_count += 1
                else:
                    # Création
                    cursor.execute("""
                        INSERT INTO ingredient_price_catalog
                        (ingredient_name_fr, ingredient_name_jp, unit_fr, unit_jp,
                         price_eur, price_jpy, qty, conversion_category)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (ingredient_name_fr, ingredient_name_jp, unit_fr, unit_jp,
                          price_eur, price_jpy, qty, conversion_category))

                    print(f"  ➕ Créé: {ingredient_name_fr} ({unit_fr}) - {price_eur}€ / {price_jpy}¥")
                    created_count += 1

                conn.commit()

            except Exception as e:
                print(f"  ❌ Erreur pour {ingredient_name_fr}: {e}")
                error_count += 1

    print(f"\n📊 Résumé:")
    print(f"  ✅ Mis à jour: {updated_count}")
    print(f"  ➕ Créés: {created_count}")
    print(f"  ❌ Erreurs: {error_count}")
    print(f"  📈 Total traité: {updated_count + created_count}")

    conn.close()

if __name__ == "__main__":
    print("🔄 Restauration des prix depuis le CSV\n")
    restore_prices_from_csv()
    print("\n✅ Terminé!")
