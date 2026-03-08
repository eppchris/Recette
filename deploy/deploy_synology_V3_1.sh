#!/bin/bash
# Script de déploiement pour Synology DS213+
# Version 3.1 - Import de recettes depuis texte libre (IA)
#              + Transfert complet DB locale + images
# Usage: ./deploy_synology_V3_1.sh

SYNOLOGY_USER="admin"
SYNOLOGY_HOST="192.168.1.14"
DEPLOY_PATH="recette"
SYNOLOGY_SSH="${SYNOLOGY_USER}@${SYNOLOGY_HOST}"
LOCAL_DB="data/recette.sqlite3"

echo "🚀 Déploiement de Recette Version 3.1 sur Synology..."
echo "📦 Nouvelles fonctionnalités:"
echo "   📋 Import de recettes depuis texte libre (copier/coller)"
echo "   🤖 Analyse intelligente par IA (Groq)"
echo "   🔍 Vérification/édition avant sauvegarde"
echo ""
echo "⚠️  TRANSFERT COMPLET : code + base de données locale + images"
echo ""
echo "📍 Destination: ${DEPLOY_PATH}"
echo ""

# ─── Vérification des fichiers requis ──────────────────────────────────────
echo "🔍 Vérification des fichiers modifiés..."
REQUIRED_FILES=(
    "app/routes/recipe_routes.py"
    "app/templates/import_text.html"
    "app/templates/import_recipes.html"
    "app/templates/recipes_list.html"
    "app/templates/base.html"
    "app/template_config.py"
    "${LOCAL_DB}"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Erreur: Fichier manquant: $file"
        exit 1
    fi
done
echo "✅ Tous les fichiers requis sont présents"
echo ""

# ─── Vérification intégrité DB locale ──────────────────────────────────────
echo "🗄️  Vérification de la base de données locale..."
INTEGRITY=$(sqlite3 "${LOCAL_DB}" "PRAGMA integrity_check;")
if [ "$INTEGRITY" != "ok" ]; then
    echo "❌ Erreur: La base locale est corrompue ($INTEGRITY)"
    exit 1
fi
NB_RECIPES=$(sqlite3 "${LOCAL_DB}" "SELECT COUNT(*) FROM recipe;")
echo "✅ Base locale OK — ${NB_RECIPES} recettes"
echo ""

# ─── Étape 1 : Création de l'archive de code ───────────────────────────────
echo "📦 Étape 1/8 : Préparation de l'archive de code..."
ARCHIVE="/tmp/recette_v3_1_deploy.tar.gz"

tar czf "$ARCHIVE" \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='venv' \
    --exclude='data' \
    --exclude='logs/*' \
    --exclude='*.log' \
    --exclude='*.tar.gz' \
    --exclude='deploy' \
    --exclude='tests' \
    --exclude='test_*.py' \
    --exclude='scripts' \
    --exclude='.claude' \
    --exclude='.DS_Store' \
    --exclude='recette.db' \
    --exclude='.pytest_cache' \
    --exclude='htmlcov' \
    --exclude='.coverage' \
    --exclude='static/images/steps' \
    --exclude='static/images/recipes' \
    app/ static/ requirements.txt config.py main.py migrations/ \
    .env.example docs/

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de la création de l'archive de code"
    exit 1
fi

ARCHIVE_SIZE=$(du -h "$ARCHIVE" | cut -f1)
echo "✅ Archive code créée (${ARCHIVE_SIZE})"
echo ""

# ─── Étape 2 : Transfert de l'archive de code ──────────────────────────────
echo "🔗 Étape 2/8 : Transfert de l'archive vers le NAS..."
cat "$ARCHIVE" | ssh $SYNOLOGY_SSH "cat > ${DEPLOY_PATH}/recette_v3_1_deploy.tar.gz"

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du transfert de l'archive"
    rm "$ARCHIVE"
    exit 1
fi
echo "✅ Archive transférée"
echo ""

# ─── Étape 3 : Backup de la base de production ─────────────────────────────
echo "💾 Étape 3/8 : Backup de la base de données de production..."
ssh $SYNOLOGY_SSH << 'ENDSSH'
cd recette
mkdir -p backups

if [ -f "data/recette.sqlite3" ]; then
    BACKUP_FILE="backups/recette_pre_v3_1_$(date +%Y%m%d_%H%M%S).sqlite3"
    cp data/recette.sqlite3 "$BACKUP_FILE"
    echo "✅ Backup créé: $BACKUP_FILE"

    sqlite3 "$BACKUP_FILE" "PRAGMA integrity_check;" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Intégrité du backup vérifiée"
    else
        echo "❌ Erreur: Backup corrompu — abandon"
        exit 1
    fi
    NB=$(sqlite3 "$BACKUP_FILE" "SELECT COUNT(*) FROM recipe;")
    echo "   Recettes en production avant déploiement: $NB"
else
    echo "⚠️  Pas de base de données existante en production"
fi
ENDSSH

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du backup de production"
    exit 1
fi
echo ""

# ─── Étape 4 : Arrêt de l'application ──────────────────────────────────────
echo "⏸️  Étape 4/8 : Arrêt de l'application..."
ssh $SYNOLOGY_SSH "cd ${DEPLOY_PATH} && bash stop_recette.sh" 2>/dev/null || true
sleep 2
echo ""

# ─── Étape 5 : Déploiement du code ─────────────────────────────────────────
echo "🔧 Étape 5/8 : Déploiement des fichiers de code..."
ssh $SYNOLOGY_SSH << 'ENDSSH'
cd recette
mkdir -p backups data logs static/images/steps static/images/recipes

# Backup du code existant
if [ -d "app" ]; then
    BACKUP_DIR="backups/code_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    cp -r app "$BACKUP_DIR/" 2>/dev/null || true
    echo "  📦 Code sauvegardé dans $BACKUP_DIR"
fi

# Extraction de l'archive
tar xzf recette_v3_1_deploy.tar.gz
rm recette_v3_1_deploy.tar.gz

# Nettoyage du cache Python
echo "  🧹 Nettoyage du cache Python..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo "✅ Code déployé (cache Python nettoyé)"
ENDSSH

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du déploiement du code"
    exit 1
fi
echo ""

# ─── Étape 6 : Transfert de la base de données locale ──────────────────────
echo "🗄️  Étape 6/8 : Transfert de la base de données locale → NAS..."
echo "   (${NB_RECIPES} recettes)"

cat "${LOCAL_DB}" | ssh $SYNOLOGY_SSH "cat > ${DEPLOY_PATH}/data/recette.sqlite3"

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du transfert de la base de données"
    echo "⚠️  Le backup est disponible sur le NAS: backups/recette_pre_v3_1_*.sqlite3"
    exit 1
fi
echo "✅ Base de données transférée"
echo ""

# ─── Étape 7 : Transfert des images ────────────────────────────────────────
echo "🖼️  Étape 7/8 : Transfert des images..."

NB_RECIPE_IMAGES=$(ls static/images/recipes/ 2>/dev/null | wc -l | tr -d ' ')
echo "  📸 Images recettes: ${NB_RECIPE_IMAGES} fichiers"

if [ "$NB_RECIPE_IMAGES" -gt 0 ]; then
    tar czf /tmp/recette_v3_1_images_recipes.tar.gz -C static/images recipes/
    cat /tmp/recette_v3_1_images_recipes.tar.gz | ssh $SYNOLOGY_SSH \
        "cd ${DEPLOY_PATH}/static/images && tar xzf -"
    if [ $? -ne 0 ]; then
        echo "⚠️  Erreur lors du transfert des images recettes"
    else
        echo "✅ Images recettes transférées"
    fi
    rm /tmp/recette_v3_1_images_recipes.tar.gz
fi

NB_STEP_IMAGES=$(ls static/images/steps/ 2>/dev/null | wc -l | tr -d ' ')
echo "  📷 Images étapes: ${NB_STEP_IMAGES} fichiers"

if [ "$NB_STEP_IMAGES" -gt 0 ]; then
    tar czf /tmp/recette_v3_1_images_steps.tar.gz -C static/images steps/
    cat /tmp/recette_v3_1_images_steps.tar.gz | ssh $SYNOLOGY_SSH \
        "cd ${DEPLOY_PATH}/static/images && tar xzf -"
    if [ $? -ne 0 ]; then
        echo "⚠️  Erreur lors du transfert des images d'étapes"
    else
        echo "✅ Images d'étapes transférées"
    fi
    rm /tmp/recette_v3_1_images_steps.tar.gz
fi
echo ""

# ─── Étape 8 : Redémarrage de l'application ────────────────────────────────
echo "▶️  Étape 8/8 : Redémarrage de l'application..."
ssh $SYNOLOGY_SSH "cd ${DEPLOY_PATH} && bash start_recette.sh"

echo ""
echo "🔍 Vérification du démarrage..."
sleep 3
ssh $SYNOLOGY_SSH "ps aux | grep '[u]vicorn'" > /dev/null && echo "✅ Application démarrée avec succès"

# Vérification finale de la base de données
echo ""
echo "🔍 Vérification finale de la base de données sur le NAS..."
ssh $SYNOLOGY_SSH << 'ENDSSH'
cd recette
NB=$(sqlite3 data/recette.sqlite3 "SELECT COUNT(*) FROM recipe;" 2>/dev/null)
echo "   Recettes en production après déploiement: $NB"
ENDSSH

# Nettoyage local
rm "$ARCHIVE"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Déploiement Version 3.1 terminé !"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 URL: http://192.168.1.14:8000"
echo "📍 URL publique: http://recipe.e2pc.fr"
echo ""
echo "✨ Nouvelles fonctionnalités V3.1:"
echo ""
echo "📋 IMPORT RECETTE DEPUIS TEXTE:"
echo "   • Nouvelle page /import-text"
echo "   • Copier/coller n'importe quel texte (livre, site, notes...)"
echo "   • Extraction intelligente par IA (Groq llama-3.3-70b)"
echo "   • Traduction automatique si la langue diffère"
echo "   • Vérification et édition avant sauvegarde"
echo "   • Intégré dans le menu Importer (4 options: CSV / PDF / URL / Texte)"
echo "   • Intégré dans le dropdown de la liste des recettes"
echo ""
echo "🗄️  BASE DE DONNÉES:"
echo "   ⚠️  La base locale a été transférée en production"
echo "   • Backup disponible sur le NAS: backups/recette_pre_v3_1_*.sqlite3"
echo "   • ${NB_RECIPES} recettes déployées"
echo ""
echo "✅ TESTS À EFFECTUER:"
echo "   1. 📋 Import texte: /import-text — coller un texte, vérifier extraction IA"
echo "   2. 🔍 Page import: /import — vérifier la 4ème carte 'Import Texte'"
echo "   3. 📋 Dropdown liste: /recipes — vérifier l'option dans le bouton Importer"
echo "   4. 💾 Sauvegarde: vérifier que la recette importée apparaît dans la liste"
echo ""
echo "🔄 EN CAS DE PROBLÈME:"
echo "   1. Logs:    tail -f ~/recette/logs/recette.log"
echo "   2. Restaurer la base:"
echo "      cp ~/recette/backups/recette_pre_v3_1_*.sqlite3 ~/recette/data/recette.sqlite3"
echo "   3. Redémarrer:"
echo "      cd ~/recette && bash stop_recette.sh && bash start_recette.sh"
echo ""
