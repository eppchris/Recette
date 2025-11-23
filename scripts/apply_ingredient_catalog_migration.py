#!/usr/bin/env python3
"""
Script pour appliquer la migration du catalogue des ingrédients
"""
import sqlite3
import os
import sys

# Chemin vers la base de données
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "recette.sqlite3")
MIGRATION_FILE = os.path.join(os.path.dirname(__file__), "migrations", "add_ingredient_catalog.sql")

def apply_migration():
    """Applique la migration du catalogue des ingrédients"""
    print("🍅 Application de la migration du catalogue des ingrédients...")
    print(f"Database: {DB_PATH}")
    print(f"Migration file: {MIGRATION_FILE}")
    print()

    if not os.path.exists(DB_PATH):
        print(f"❌ Erreur: La base de données n'existe pas: {DB_PATH}")
        return False

    if not os.path.exists(MIGRATION_FILE):
        print(f"❌ Erreur: Le fichier de migration n'existe pas: {MIGRATION_FILE}")
        return False

    try:
        # Lire le fichier SQL
        with open(MIGRATION_FILE, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # Se connecter à la base de données
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        print("🔧 Exécution de la migration...\n")

        # Exécuter le script
        try:
            conn.executescript(migration_sql)
            conn.commit()
            print("✓ Migration exécutée avec succès\n")
        except sqlite3.OperationalError as e:
            if "already exists" in str(e).lower():
                print(f"⚠️  Les tables existent déjà (migration déjà appliquée)\n")
                conn.rollback()
            else:
                raise

        # Vérifications
        print("🔍 Vérification des modifications...\n")

        # Vérifier la table ingredient_price_catalog
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ingredient_price_catalog'")
        if cursor.fetchone():
            print(f"  ✓ Table 'ingredient_price_catalog' créée")

            # Compter les ingrédients
            cursor.execute("SELECT COUNT(*) as count FROM ingredient_price_catalog")
            count = cursor.fetchone()['count']
            print(f"  ✓ {count} ingrédient(s) dans le catalogue")

            # Afficher quelques exemples
            if count > 0:
                cursor.execute("SELECT ingredient_name, price_eur, price_jpy, unit FROM ingredient_price_catalog LIMIT 5")
                print(f"\n  📋 Exemples d'ingrédients:")
                for row in cursor.fetchall():
                    price_eur = f"{row['price_eur']}€" if row['price_eur'] else "-"
                    price_jpy = f"{row['price_jpy']}¥" if row['price_jpy'] else "-"
                    print(f"     • {row['ingredient_name']} ({row['unit']}): {price_eur} / {price_jpy}")
        else:
            print(f"  ❌ Table 'ingredient_price_catalog' manquante")
            conn.close()
            return False

        # Vérifier la table expense_ingredient_detail
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='expense_ingredient_detail'")
        if cursor.fetchone():
            print(f"\n  ✓ Table 'expense_ingredient_detail' créée")
        else:
            print(f"\n  ❌ Table 'expense_ingredient_detail' manquante")
            conn.close()
            return False

        # Vérifier le trigger
        cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name='update_catalog_after_actual_price'")
        if cursor.fetchone():
            print(f"  ✓ Trigger 'update_catalog_after_actual_price' créé")
        else:
            print(f"  ⚠️  Trigger 'update_catalog_after_actual_price' manquant")

        conn.close()

        print("\n✅ Migration appliquée avec succès!")
        print("\n💡 Prochaines étapes:")
        print("   1. Les ingrédients de vos recettes sont dans le catalogue (sans prix)")
        print("   2. Vous pouvez maintenant gérer les prix via la page 'Catalogue des prix'")
        print("   3. Lors de la création d'une dépense 'Ingrédients', les prix seront pré-remplis")
        print("   4. Les prix réels mettront à jour automatiquement le catalogue")

        return True

    except Exception as e:
        print(f"\n❌ Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)
