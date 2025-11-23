#!/usr/bin/env python3
"""
Script pour appliquer la migration de gestion budgétaire
"""
import sqlite3
import os
import sys

# Chemin vers la base de données
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "recette.sqlite3")
MIGRATION_FILE = os.path.join(os.path.dirname(__file__), "migrations", "add_budget_management.sql")

def apply_migration():
    """Applique la migration budgétaire"""
    print("📊 Application de la migration budgétaire...")
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

        # Activer les clés étrangères
        cursor.execute("PRAGMA foreign_keys = ON")

        print("🔧 Exécution de la migration...\n")

        # Exécuter le script complet (SQLite peut gérer plusieurs statements)
        try:
            conn.executescript(migration_sql)
            conn.commit()
            print("✓ Migration exécutée avec succès\n")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e) or "already exists" in str(e):
                print(f"⚠️  Certaines tables/colonnes existent déjà (migration déjà appliquée?)\n")
                conn.rollback()
                # Continuer quand même pour vérifier
            else:
                raise

        # Vérifications
        print("🔍 Vérification des modifications...\n")

        # Vérifier les tables créées
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            AND name IN ('expense_category', 'expense_category_translation', 'event_expense', 'ingredient_price_history')
        """)
        tables = [t[0] for t in cursor.fetchall()]

        expected_tables = ['expense_category', 'expense_category_translation', 'event_expense', 'ingredient_price_history']
        for table in expected_tables:
            if table in tables:
                print(f"  ✓ Table '{table}' créée")
            else:
                print(f"  ❌ Table '{table}' manquante")

        # Vérifier les colonnes ajoutées à event
        cursor.execute("PRAGMA table_info(event)")
        event_columns = [col[1] for col in cursor.fetchall()]
        if 'budget_planned' in event_columns:
            print(f"  ✓ Colonne 'budget_planned' ajoutée à 'event'")
        else:
            print(f"  ❌ Colonne 'budget_planned' manquante dans 'event'")

        # Vérifier les colonnes ajoutées à shopping_list_item
        cursor.execute("PRAGMA table_info(shopping_list_item)")
        shopping_columns = [col[1] for col in cursor.fetchall()]
        new_columns = ['planned_unit_price', 'actual_unit_price', 'is_purchased']
        for col in new_columns:
            if col in shopping_columns:
                print(f"  ✓ Colonne '{col}' ajoutée à 'shopping_list_item'")
            else:
                print(f"  ❌ Colonne '{col}' manquante dans 'shopping_list_item'")

        # Compter les catégories par défaut
        cursor.execute("SELECT COUNT(*) FROM expense_category")
        cat_count = cursor.fetchone()[0]
        print(f"\n  ✓ {cat_count} catégories de dépenses")

        # Vérifier les traductions
        cursor.execute("SELECT COUNT(*) FROM expense_category_translation WHERE lang = 'fr'")
        fr_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM expense_category_translation WHERE lang = 'jp'")
        jp_count = cursor.fetchone()[0]
        print(f"  ✓ {fr_count} traductions FR, {jp_count} traductions JP")

        # Afficher les catégories
        print("\n📋 Catégories disponibles:")
        cursor.execute("""
            SELECT c.id, c.icon, t_fr.name as name_fr, t_jp.name as name_jp
            FROM expense_category c
            LEFT JOIN expense_category_translation t_fr ON t_fr.category_id = c.id AND t_fr.lang = 'fr'
            LEFT JOIN expense_category_translation t_jp ON t_jp.category_id = c.id AND t_jp.lang = 'jp'
            WHERE c.is_system = 1
            ORDER BY c.id
        """)
        for row in cursor.fetchall():
            print(f"  {row[1]} {row[2]} / {row[3]}")

        conn.close()

        print("\n✅ Migration appliquée avec succès!")
        print("\n💡 Prochaines étapes:")
        print("   1. Redémarrer le serveur FastAPI")
        print("   2. Les fonctions DB budget sont maintenant disponibles")
        print("   3. Il reste à créer les routes API et l'interface utilisateur")

        return True

    except Exception as e:
        print(f"\n❌ Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)
