#!/bin/bash
# Script pour appliquer la migration response_size_bytes en production
# Usage: ./scripts/apply_response_size_migration.sh

set -e

DB_PATH="data/recipes.db"
MIGRATION_FILE="migrations/add_response_size_to_access_log.sql"

echo "========================================="
echo "Application de la migration response_size_bytes"
echo "========================================="
echo ""

# Vérifier que la DB existe
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Erreur: Base de données non trouvée: $DB_PATH"
    exit 1
fi

# Vérifier que la migration existe
if [ ! -f "$MIGRATION_FILE" ]; then
    echo "❌ Erreur: Fichier de migration non trouvé: $MIGRATION_FILE"
    exit 1
fi

# Backup de la base
BACKUP_PATH="data/recipes_backup_$(date +%Y%m%d_%H%M%S).db"
echo "📦 Création d'un backup: $BACKUP_PATH"
cp "$DB_PATH" "$BACKUP_PATH"
echo "✅ Backup créé avec succès"
echo ""

# Vérifier si la colonne existe déjà
echo "🔍 Vérification de l'état actuel..."
COLUMN_EXISTS=$(sqlite3 "$DB_PATH" "PRAGMA table_info(access_log)" | grep response_size_bytes || echo "")

if [ -n "$COLUMN_EXISTS" ]; then
    echo "⚠️  La colonne response_size_bytes existe déjà"
    echo "   Aucune action nécessaire"
    exit 0
fi

echo "📝 La colonne response_size_bytes n'existe pas, application de la migration..."
echo ""

# Appliquer la migration
echo "🚀 Application de la migration..."
sqlite3 "$DB_PATH" < "$MIGRATION_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Migration appliquée avec succès!"
    echo ""
    echo "🔍 Vérification post-migration..."
    COLUMN_EXISTS_AFTER=$(sqlite3 "$DB_PATH" "PRAGMA table_info(access_log)" | grep response_size_bytes || echo "")

    if [ -n "$COLUMN_EXISTS_AFTER" ]; then
        echo "✅ Colonne response_size_bytes confirmée dans la table access_log"
        echo ""
        echo "📊 Structure de la table access_log:"
        sqlite3 "$DB_PATH" "PRAGMA table_info(access_log)"
        echo ""
        echo "✅ Migration terminée avec succès!"
        echo "📦 Backup disponible: $BACKUP_PATH"
    else
        echo "❌ Erreur: La colonne n'a pas été créée"
        echo "🔄 Restauration du backup..."
        cp "$BACKUP_PATH" "$DB_PATH"
        echo "✅ Backup restauré"
        exit 1
    fi
else
    echo "❌ Erreur lors de l'application de la migration"
    echo "🔄 Restauration du backup..."
    cp "$BACKUP_PATH" "$DB_PATH"
    echo "✅ Backup restauré"
    exit 1
fi

echo ""
echo "========================================="
echo "✅ TERMINÉ"
echo "========================================="
