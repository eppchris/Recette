#!/bin/bash
# Script de synchronisation DEV → PRODUCTION
# Copie la base de données, les images et les tickets de caisse du dev local vers la production
# Usage: ./scripts/sync_dev_to_prod.sh

PROD_SERVER="prod-server"
PROD_PATH="apps/recette"
LOCAL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOCAL_DB="${LOCAL_ROOT}/data/recette.sqlite3"
LOCAL_IMAGES="${LOCAL_ROOT}/static/images"
LOCAL_RECEIPTS="${LOCAL_ROOT}/data/receipts"
LOCAL_APP="${LOCAL_ROOT}/app"
LOCAL_MAIN="${LOCAL_ROOT}/main.py"

echo "🔄 Synchronisation DEV → PRODUCTION"
echo "======================================"
echo ""
echo "⚠️  ATTENTION : Cette opération va écraser les données de production !"
echo "   Appuie sur Entrée pour continuer ou Ctrl+C pour annuler."
read -r
echo ""

# Backup production avant synchronisation
echo "💾 Étape 1/6 : Backup de la base de production..."
BACKUP_FILE="${PROD_PATH}/data/recette_prod_backup_$(date +%Y%m%d_%H%M%S).sqlite3"
ssh ${PROD_SERVER} "cp ~/${PROD_PATH}/data/recette.sqlite3 ~/${BACKUP_FILE}"

if [ $? -eq 0 ]; then
    echo "   ✅ Backup prod créé : ${BACKUP_FILE}"
else
    echo "   ❌ Erreur lors du backup prod — abandon"
    exit 1
fi
echo ""

# Vérification intégrité de la base locale avant envoi
echo "🔍 Étape 2/6 : Vérification de l'intégrité de la base locale..."
INTEGRITY=$(sqlite3 "${LOCAL_DB}" "PRAGMA integrity_check;" 2>/dev/null)
if [ "$INTEGRITY" = "ok" ]; then
    DB_SIZE=$(du -h "${LOCAL_DB}" | cut -f1)
    RECIPE_COUNT=$(sqlite3 "${LOCAL_DB}" "SELECT COUNT(*) FROM recipe;" 2>/dev/null)
    echo "   ✅ Base de données OK (${DB_SIZE}, ${RECIPE_COUNT} recettes)"
else
    echo "   ❌ Base de données locale corrompue : ${INTEGRITY} — abandon"
    exit 1
fi
echo ""

# Envoi de la base de données
echo "📤 Étape 3/6 : Envoi de la base de données vers la production..."
scp "${LOCAL_DB}" ${PROD_SERVER}:${PROD_PATH}/data/recette.sqlite3

if [ $? -eq 0 ]; then
    echo "   ✅ Base de données envoyée"
else
    echo "   ❌ Erreur lors de l'envoi de la base"
    exit 1
fi
echo ""

# Synchronisation des images
echo "🖼️  Étape 4/6 : Synchronisation des images vers la production..."

rsync -a --progress \
    "${LOCAL_IMAGES}/recipes/" \
    ${PROD_SERVER}:~/${PROD_PATH}/static/images/recipes/
NB_RECIPES=$(find "${LOCAL_IMAGES}/recipes/" -maxdepth 1 -type f 2>/dev/null | wc -l | tr -d ' ')
NB_THUMBS=$(find "${LOCAL_IMAGES}/recipes/thumbnails/" -type f 2>/dev/null | wc -l | tr -d ' ')
echo "   ✅ Images recettes      : ${NB_RECIPES} fichiers"
echo "   ✅ Thumbnails recettes  : ${NB_THUMBS} fichiers"

rsync -a --progress \
    "${LOCAL_IMAGES}/steps/" \
    ${PROD_SERVER}:~/${PROD_PATH}/static/images/steps/
NB_STEPS=$(find "${LOCAL_IMAGES}/steps/" -type f 2>/dev/null | wc -l | tr -d ' ')
echo "   ✅ Images étapes        : ${NB_STEPS} fichiers"
echo ""

# Synchronisation des tickets de caisse
echo "🧾 Étape 5/6 : Synchronisation des tickets de caisse..."
rsync -a --progress \
    "${LOCAL_RECEIPTS}/" \
    ${PROD_SERVER}:~/${PROD_PATH}/data/receipts/

if [ $? -eq 0 ]; then
    NB_RECEIPTS=$(find "${LOCAL_RECEIPTS}" -type f 2>/dev/null | wc -l | tr -d ' ')
    echo "   ✅ Tickets de caisse : ${NB_RECEIPTS} fichiers"
else
    echo "   ⚠️  Erreur lors de la sync des tickets (dossier peut-être vide)"
fi
echo ""

# Synchronisation du code applicatif
echo "💻 Étape 6/6 : Synchronisation du code vers la production..."
rsync -a --delete \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    "${LOCAL_APP}/" \
    ${PROD_SERVER}:~/${PROD_PATH}/app/

rsync -a "${LOCAL_MAIN}" ${PROD_SERVER}:~/${PROD_PATH}/main.py

if [ $? -eq 0 ]; then
    NB_PY=$(find "${LOCAL_APP}" -name "*.py" | wc -l | tr -d ' ')
    NB_HTML=$(find "${LOCAL_APP}/templates" -name "*.html" | wc -l | tr -d ' ')
    echo "   ✅ Code Python    : ${NB_PY} fichiers .py"
    echo "   ✅ Templates HTML : ${NB_HTML} fichiers .html"
    echo "   ✅ main.py"
else
    echo "   ❌ Erreur lors de la sync du code — abandon"
    exit 1
fi
echo ""

# Redémarrage du service
echo "🔁 Redémarrage du service en production..."
ssh ${PROD_SERVER} "sudo systemctl restart recette"
if [ $? -eq 0 ]; then
    echo "   ✅ Service redémarré"
else
    echo "   ⚠️  Erreur lors du redémarrage — vérifie manuellement"
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
