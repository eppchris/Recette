#!/bin/bash
# Script de synchronisation PRODUCTION → DEV
# Copie la base de données et les images de production vers l'environnement de dev local
# Usage: ./scripts/sync_prod_to_dev.sh

SYNOLOGY_USER="admin"
SYNOLOGY_HOST="192.168.1.14"
PROD_PATH="recette"

echo "🔄 Synchronisation PRODUCTION → DEV"
echo "======================================"
echo ""

# Backup local avant synchronisation
echo "💾 Étape 1/4 : Backup de la base locale actuelle..."
BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"
if [ -f "data/recette.sqlite3" ]; then
    BACKUP_FILE="${BACKUP_DIR}/recette_dev_backup_$(date +%Y%m%d_%H%M%S).sqlite3"
    cp data/recette.sqlite3 "$BACKUP_FILE"
    echo "✅ Backup local créé: $BACKUP_FILE"
else
    echo "⚠️  Aucune base locale à sauvegarder"
fi
echo ""

# Téléchargement de la base de production
echo "📥 Étape 2/4 : Téléchargement de la base de production..."
scp ${SYNOLOGY_USER}@${SYNOLOGY_HOST}:${PROD_PATH}/data/recette.sqlite3 data/recette.sqlite3

if [ $? -eq 0 ]; then
    DB_SIZE=$(du -h data/recette.sqlite3 | cut -f1)
    echo "✅ Base de données téléchargée (${DB_SIZE})"
else
    echo "❌ Erreur lors du téléchargement de la base"
    exit 1
fi
echo ""

# Téléchargement des images
echo "🖼️  Étape 3/4 : Synchronisation des images de recettes..."
mkdir -p static/images/recipes

# Compter les images en production
PROD_IMAGE_COUNT=$(ssh ${SYNOLOGY_USER}@${SYNOLOGY_HOST} "ls -1 ${PROD_PATH}/static/images/recipes/*.png 2>/dev/null | wc -l" | tr -d ' ')

if [ "$PROD_IMAGE_COUNT" -gt 0 ]; then
    echo "   → ${PROD_IMAGE_COUNT} images à télécharger..."

    # Télécharger toutes les images
    scp ${SYNOLOGY_USER}@${SYNOLOGY_HOST}:${PROD_PATH}/static/images/recipes/*.png static/images/recipes/ 2>/dev/null

    LOCAL_IMAGE_COUNT=$(ls -1 static/images/recipes/*.png 2>/dev/null | wc -l | tr -d ' ')
    echo "✅ ${LOCAL_IMAGE_COUNT} images synchronisées"
else
    echo "ℹ️  Aucune image en production"
fi
echo ""

# Vérification
echo "🔍 Étape 4/4 : Vérification..."

# Vérifier la base de données
sqlite3 data/recette.sqlite3 "SELECT COUNT(*) FROM recipe;" > /tmp/recipe_count.txt 2>/dev/null
if [ $? -eq 0 ]; then
    RECIPE_COUNT=$(cat /tmp/recipe_count.txt)
    echo "✅ Base de données fonctionnelle"
    echo "   → ${RECIPE_COUNT} recettes en base"
    rm /tmp/recipe_count.txt
else
    echo "❌ Erreur: Base de données corrompue"
    exit 1
fi

# Vérifier les images
LOCAL_IMAGES=$(ls -1 static/images/recipes/*.png 2>/dev/null | wc -l | tr -d ' ')
echo "   → ${LOCAL_IMAGES} images dans static/images/recipes/"

echo ""
echo "✅ ========================================"
echo "✅ Synchronisation terminée avec succès!"
echo "✅ ========================================"
echo ""
echo "📊 Résumé:"
echo "   • Base de données: ${DB_SIZE}"
echo "   • Recettes: ${RECIPE_COUNT}"
echo "   • Images: ${LOCAL_IMAGES}"
echo ""
echo "📁 Backup local disponible dans:"
echo "   → ${BACKUP_DIR}/"
echo ""
echo "💡 Pour démarrer l'app en dev:"
echo "   uvicorn app.main:app --reload --port 8000"
echo ""
