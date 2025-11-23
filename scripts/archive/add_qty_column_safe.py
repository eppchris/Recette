#!/usr/bin/env python3
"""Script pour ajouter la colonne qty de manière sûre"""

import sqlite3
import time

DB_PATH = "data/recette.sqlite3"

def wait_and_add_column():
    """Attend que la base soit disponible et ajoute la colonne"""
    max_retries = 10
    retry = 0

    while retry < max_retries:
        try:
            conn = sqlite3.connect(DB_PATH, timeout=30.0)
            cursor = conn.cursor()

            # Vérifier si la colonne existe déjà
            cursor.execute("PRAGMA table_info(ingredient_price_catalog)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'qty' not in columns:
                print("Ajout de la colonne qty...")
                cursor.execute("ALTER TABLE ingredient_price_catalog ADD COLUMN qty REAL DEFAULT 1.0")
                conn.commit()
                print("✓ Colonne qty ajoutée avec succès")
            else:
                print("✓ Colonne qty existe déjà")

            # Vérifier le résultat
            cursor.execute("PRAGMA table_info(ingredient_price_catalog)")
            print("\nStructure de la table:")
            for row in cursor.fetchall():
                print(f"  {row[1]}: {row[2]}")

            conn.close()
            return True

        except sqlite3.OperationalError as e:
            if "locked" in str(e):
                retry += 1
                print(f"Base de données verrouillée, tentative {retry}/{max_retries}...")
                time.sleep(2)
            else:
                print(f"Erreur: {e}")
                return False
        except Exception as e:
            print(f"Erreur inattendue: {e}")
            return False

    print("Échec: base de données toujours verrouillée après plusieurs tentatives")
    return False

if __name__ == "__main__":
    print("=== Ajout de la colonne qty ===\n")
    success = wait_and_add_column()
    exit(0 if success else 1)
