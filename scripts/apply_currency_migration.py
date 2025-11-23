#!/usr/bin/env python3
"""
Script pour appliquer la migration de devise
"""
import sqlite3
import os
import sys

# Chemin vers la base de données
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "recette.sqlite3")
MIGRATION_FILE = os.path.join(os.path.dirname(__file__), "migrations", "add_event_currency.sql")

def apply_migration():
    """Applique la migration de devise"""
    print("💱 Application de la migration de devise...")
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
            if "duplicate column" in str(e):
                print(f"⚠️  La colonne existe déjà (migration déjà appliquée)\n")
                conn.rollback()
            else:
                raise

        # Vérifications
        print("🔍 Vérification des modifications...\n")

        # Vérifier la colonne ajoutée
        cursor.execute("PRAGMA table_info(event)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'currency' in columns:
            print(f"  ✓ Colonne 'currency' ajoutée à 'event'")
        else:
            print(f"  ❌ Colonne 'currency' manquante dans 'event'")
            conn.close()
            return False

        # Vérifier les valeurs
        cursor.execute("SELECT COUNT(*) as total, currency FROM event GROUP BY currency")
        for row in cursor.fetchall():
            print(f"  ✓ {row['total']} événement(s) avec devise '{row['currency']}'")

        conn.close()

        print("\n✅ Migration appliquée avec succès!")
        print("\n💡 La devise est maintenant mémorisée pour chaque événement")
        print("   - Les événements existants sont en EUR par défaut")
        print("   - Les nouveaux événements mémoriseront la devise de création")

        return True

    except Exception as e:
        print(f"\n❌ Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)
