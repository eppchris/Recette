#!/bin/bash
# Script de synchronisation PRODUCTION → DEV
# Copie la base de données, les images et les tickets de caisse de production vers l'environnement de dev local
# Usage: ./scripts/sync_prod_to_dev.sh

PROD_SERVER="prod-server"
PROD_PATH="apps/recette"
LOCAL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOCAL_DB="${LOCAL_ROOT}/data/recette.sqlite3"
LOCAL_IMAGES="${LOCAL_ROOT}/static/images"
LOCAL_RECEIPTS="${LOCAL_ROOT}/data/receipts"

echo "🔄 Synchronisation PRODUCTION → DEV"
echo "======================================"
echo ""

# Backup local avant synchronisation
echo "💾 Étape 1/5 : Backup de la base locale actuelle..."
mkdir -p "${LOCAL_ROOT}/backups"
if [ -f "${LOCAL_DB}" ]; then
    BACKUP_FILE="${LOCAL_ROOT}/backups/recette_dev_backup_$(date +%Y%m%d_%H%M%S).sqlite3"
    cp "${LOCAL_DB}" "${BACKUP_FILE}"
    echo "   ✅ Backup local créé : ${BACKUP_FILE}"
else
    echo "   ⚠️  Aucune base locale à sauvegarder"
fi
echo ""

# Téléchargement de la base de production
echo "📥 Étape 2/5 : Téléchargement de la base de production..."
scp ${PROD_SERVER}:${PROD_PATH}/data/recette.sqlite3 "${LOCAL_DB}"

if [ $? -eq 0 ]; then
    DB_SIZE=$(du -h "${LOCAL_DB}" | cut -f1)
    RECIPE_COUNT=$(sqlite3 "${LOCAL_DB}" "SELECT COUNT(*) FROM recipe;" 2>/dev/null)
    echo "   ✅ Base de données téléchargée (${DB_SIZE}, ${RECIPE_COUNT} recettes)"
else
    echo "   ❌ Erreur lors du téléchargement de la base"
    exit 1
fi
echo ""

# Synchronisation des images de recettes
echo "🖼️  Étape 3/5 : Synchronisation des images de recettes..."
mkdir -p "${LOCAL_IMAGES}/recipes/thumbnails" "${LOCAL_IMAGES}/steps"

rsync -a --progress \
    ${PROD_SERVER}:~/${PROD_PATH}/static/images/recipes/ \
    "${LOCAL_IMAGES}/recipes/"
NB_RECIPES=$(find "${LOCAL_IMAGES}/recipes/" -maxdepth 1 -type f 2>/dev/null | wc -l | tr -d ' ')
NB_THUMBS=$(find "${LOCAL_IMAGES}/recipes/thumbnails/" -type f 2>/dev/null | wc -l | tr -d ' ')
echo "   ✅ Images recettes      : ${NB_RECIPES} fichiers"
echo "   ✅ Thumbnails recettes  : ${NB_THUMBS} fichiers"

rsync -a --progress \
    ${PROD_SERVER}:~/${PROD_PATH}/static/images/steps/ \
    "${LOCAL_IMAGES}/steps/"
NB_STEPS=$(find "${LOCAL_IMAGES}/steps/" -type f 2>/dev/null | wc -l | tr -d ' ')
echo "   ✅ Images étapes        : ${NB_STEPS} fichiers"
echo ""

# Synchronisation des tickets de caisse
echo "🧾 Étape 4/5 : Synchronisation des tickets de caisse..."
mkdir -p "${LOCAL_RECEIPTS}"

rsync -a --progress \
    ${PROD_SERVER}:~/${PROD_PATH}/data/receipts/ \
    "${LOCAL_RECEIPTS}/"

if [ $? -eq 0 ]; then
    NB_RECEIPTS=$(find "${LOCAL_RECEIPTS}" -type f 2>/dev/null | wc -l | tr -d ' ')
    echo "   ✅ Tickets de caisse : ${NB_RECEIPTS} fichiers"
else
    echo "   ⚠️  Erreur lors de la sync des tickets (dossier peut-être vide)"
fi
echo ""

# Vérification finale
echo "🔍 Étape 5/5 : Vérification de l'intégrité..."
INTEGRITY=$(sqlite3 "${LOCAL_DB}" "PRAGMA integrity_check;" 2>/dev/null)
if [ "$INTEGRITY" = "ok" ]; then
    echo "   ✅ Base de données OK"
else
    echo "   ❌ Base de données corrompue : ${INTEGRITY}"
    exit 1
fi

echo ""
echo "✅ ========================================"
echo "✅ Synchronisation terminée avec succès !"
echo "✅ ========================================"
echo ""
echo "📊 Résumé :"
echo "   • Base de données      : ${DB_SIZE} (${RECIPE_COUNT} recettes)"
echo "   • Images recettes      : ${NB_RECIPES} fichiers"
echo "   • Thumbnails recettes  : ${NB_THUMBS} fichiers"
echo "   • Images étapes        : ${NB_STEPS} fichiers"
echo "   • Tickets de caisse    : ${NB_RECEIPTS} fichiers"
echo ""
echo "💡 Pour démarrer l'app en dev :"
echo "   uvicorn main:app --reload --port 8000"
echo ""
