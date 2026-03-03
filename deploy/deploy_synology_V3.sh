#!/bin/bash
# Script de déploiement pour Synology DS213+
# Version 3.0 - Calendrier repas, temps de préparation, conseils, images d'étapes
#              + Transfert complet DB locale + images (nouvelles recettes ajoutées)
# Usage: ./deploy_synology_V3.sh

SYNOLOGY_USER="admin"
SYNOLOGY_HOST="192.168.1.14"
DEPLOY_PATH="recette"
SYNOLOGY_SSH="${SYNOLOGY_USER}@${SYNOLOGY_HOST}"
LOCAL_DB="data/recette.sqlite3"

echo "🚀 Déploiement de Recette Version 3.0 sur Synology..."
echo "📦 Nouvelles fonctionnalités:"
echo "   📅 Calendrier de planification des repas"
echo "   ⏱️  Temps de préparation et cuisson sur les recettes"
echo "   💡 Conseils (tips) sur les recettes"
echo "   🔗 Liaison ingrédient → sous-recette"
echo "   📷 Images dans les étapes de recettes"
echo "   🗂️  Admin : édition des utilisateurs"
echo "   🎫 Ticket de caisse : chemin du fichier PDF stocké"
echo ""
echo "⚠️  TRANSFERT COMPLET : code + base de données locale + images"
echo "   (la base locale contient des nouvelles recettes)"
echo ""
echo "📍 Destination: ${DEPLOY_PATH}"
echo ""

# ─── Vérification des fichiers requis ──────────────────────────────────────
echo "🔍 Vérification des fichiers modifiés..."
REQUIRED_FILES=(
    "app/models/__init__.py"
    "app/models/db_meal_plan.py"
    "app/models/db_recipes.py"
    "app/models/db_receipt.py"
    "app/models/db_users.py"
    "app/routes/auth_routes.py"
    "app/routes/catalog_routes.py"
    "app/routes/event_routes.py"
    "app/routes/recipe_routes.py"
    "app/routes/calendar_routes.py"
    "app/services/image_service.py"
    "app/services/pdf_recipe_extractor.py"
    "app/services/web_recipe_importer.py"
    "app/templates/calendar.html"
    "app/templates/admin_user_edit.html"
    "app/templates/recipe_detail.html"
    "app/templates/recipes_list.html"
    "app/templates/base.html"
    "config.py"
    "main.py"
    "requirements.txt"
    "migrations/add_meal_plan.sql"
    "migrations/add_recipe_links.sql"
    "migrations/add_recipe_times.sql"
    "migrations/add_recipe_tips.sql"
    "migrations/add_step_images.sql"
    "migrations/010_add_receipt_file_path.sql"
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

# ─── Étape 1 : Application des migrations en local ─────────────────────────
echo "🗄️  Étape 1/9 : Application des migrations sur la base locale..."

apply_migration() {
    local sql_file="$1"
    local label="$2"
    echo "  📋 $label..."
    sqlite3 "${LOCAL_DB}" < "$sql_file" 2>&1 | grep -v "^$" | sed 's/^/     /' || true
}

apply_migration "migrations/add_step_images.sql"     "add_step_images (type + image_url dans step)"
apply_migration "migrations/010_add_receipt_file_path.sql" "010_add_receipt_file_path (file_path dans receipt_upload_history)"
apply_migration "migrations/add_meal_plan.sql"        "add_meal_plan (table meal_plan)"
apply_migration "migrations/add_recipe_links.sql"    "add_recipe_links (linked_recipe_id dans recipe_ingredient)"
apply_migration "migrations/add_recipe_times.sql"    "add_recipe_times (prep_time + cook_time dans recipe)"
apply_migration "migrations/add_recipe_tips.sql"     "add_recipe_tips (tips dans recipe_translation)"

echo ""
echo "  🔍 Vérification de l'intégrité de la base locale..."
INTEGRITY=$(sqlite3 "${LOCAL_DB}" "PRAGMA integrity_check;")
if [ "$INTEGRITY" != "ok" ]; then
    echo "❌ Erreur: La base locale est corrompue ($INTEGRITY)"
    exit 1
fi
NB_RECIPES=$(sqlite3 "${LOCAL_DB}" "SELECT COUNT(*) FROM recipe;")
echo "✅ Base locale OK — ${NB_RECIPES} recettes"
echo ""

# ─── Étape 2 : Création de l'archive de code ───────────────────────────────
echo "📦 Étape 2/9 : Préparation de l'archive de code..."
ARCHIVE="/tmp/recette_v3_deploy.tar.gz"

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

# ─── Étape 3 : Transfert de l'archive de code ──────────────────────────────
echo "🔗 Étape 3/9 : Transfert de l'archive vers le NAS..."
cat "$ARCHIVE" | ssh $SYNOLOGY_SSH "cat > ${DEPLOY_PATH}/recette_v3_deploy.tar.gz"

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du transfert de l'archive"
    rm "$ARCHIVE"
    exit 1
fi
echo "✅ Archive transférée"
echo ""

# ─── Étape 4 : Backup de la base de production ─────────────────────────────
echo "💾 Étape 4/9 : Backup de la base de données de production..."
ssh $SYNOLOGY_SSH << 'ENDSSH'
cd recette
mkdir -p backups

if [ -f "data/recette.sqlite3" ]; then
    BACKUP_FILE="backups/recette_pre_v3_$(date +%Y%m%d_%H%M%S).sqlite3"
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

# ─── Étape 5 : Arrêt de l'application ──────────────────────────────────────
echo "⏸️  Étape 5/9 : Arrêt de l'application..."
ssh $SYNOLOGY_SSH "cd ${DEPLOY_PATH} && bash stop_recette.sh" 2>/dev/null || true
sleep 2
echo ""

# ─── Étape 6 : Déploiement du code ─────────────────────────────────────────
echo "🔧 Étape 6/9 : Déploiement des fichiers de code..."
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
tar xzf recette_v3_deploy.tar.gz
rm recette_v3_deploy.tar.gz

# Nettoyage du cache Python
echo "  🧹 Nettoyage du cache Python..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Création du .env si inexistant
[ ! -f ".env" ] && cp .env.example .env

# Permissions
chmod 755 static/images/steps
chmod 755 static/images/recipes

echo "✅ Code déployé (cache Python nettoyé)"
ENDSSH

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du déploiement du code"
    exit 1
fi
echo ""

# ─── Étape 7 : Transfert de la base de données locale ──────────────────────
echo "🗄️  Étape 7/9 : Transfert de la base de données locale → NAS..."
echo "   (${NB_RECIPES} recettes, base locale avec migrations appliquées)"

cat "${LOCAL_DB}" | ssh $SYNOLOGY_SSH "cat > ${DEPLOY_PATH}/data/recette.sqlite3"

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du transfert de la base de données"
    echo "⚠️  Le backup est disponible sur le NAS: backups/recette_pre_v3_*.sqlite3"
    exit 1
fi
echo "✅ Base de données transférée"
echo ""

# ─── Étape 8 : Transfert des images ────────────────────────────────────────
echo "🖼️  Étape 8/9 : Transfert des images..."

# Images des recettes
NB_RECIPE_IMAGES=$(ls static/images/recipes/ 2>/dev/null | wc -l | tr -d ' ')
echo "  📸 Images recettes: ${NB_RECIPE_IMAGES} fichiers"

if [ "$NB_RECIPE_IMAGES" -gt 0 ]; then
    tar czf /tmp/recette_v3_images_recipes.tar.gz -C static/images recipes/
    cat /tmp/recette_v3_images_recipes.tar.gz | ssh $SYNOLOGY_SSH \
        "cd ${DEPLOY_PATH}/static/images && tar xzf -"
    if [ $? -ne 0 ]; then
        echo "⚠️  Erreur lors du transfert des images recettes"
    else
        echo "✅ Images recettes transférées"
    fi
    rm /tmp/recette_v3_images_recipes.tar.gz
fi

# Images des étapes
NB_STEP_IMAGES=$(ls static/images/steps/ 2>/dev/null | wc -l | tr -d ' ')
echo "  📷 Images étapes: ${NB_STEP_IMAGES} fichiers"

if [ "$NB_STEP_IMAGES" -gt 0 ]; then
    tar czf /tmp/recette_v3_images_steps.tar.gz -C static/images steps/
    cat /tmp/recette_v3_images_steps.tar.gz | ssh $SYNOLOGY_SSH \
        "cd ${DEPLOY_PATH}/static/images && tar xzf -"
    if [ $? -ne 0 ]; then
        echo "⚠️  Erreur lors du transfert des images d'étapes"
    else
        echo "✅ Images d'étapes transférées"
    fi
    rm /tmp/recette_v3_images_steps.tar.gz
fi
echo ""

# ─── Étape 9 : Redémarrage de l'application ────────────────────────────────
echo "▶️  Étape 9/9 : Redémarrage de l'application..."
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
HAS_MEAL_PLAN=$(sqlite3 data/recette.sqlite3 "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='meal_plan';" 2>/dev/null)
[ "$HAS_MEAL_PLAN" = "1" ] && echo "✅ Table meal_plan présente" || echo "⚠️  Table meal_plan absente"
HAS_PREP_TIME=$(sqlite3 data/recette.sqlite3 "PRAGMA table_info(recipe);" | grep prep_time | wc -l)
[ "$HAS_PREP_TIME" -gt 0 ] && echo "✅ Colonnes prep_time/cook_time présentes" || echo "⚠️  Colonnes prep_time/cook_time absentes"
ENDSSH

# Nettoyage local
rm "$ARCHIVE"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Déploiement Version 3.0 terminé !"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 URL: http://192.168.1.14:8000"
echo "📍 URL publique: http://recipe.e2pc.fr"
echo ""
echo "✨ Nouvelles fonctionnalités V3:"
echo ""
echo "📅 CALENDRIER DE PLANIFICATION DES REPAS:"
echo "   • Nouvelle page /calendar — vue mensuelle"
echo "   • Planification jour par jour (petit-dej / déjeuner / dîner)"
echo "   • Liaison de recettes ou texte libre"
echo "   • Affichage des événements 'Organiser' dans le calendrier"
echo "   • Liste des repas libres (recettes à créer)"
echo "   • Routes: /calendar, /api/calendar/*, /api/meal-plan"
echo "   • Migration: migrations/add_meal_plan.sql"
echo ""
echo "⏱️  TEMPS DE PRÉPARATION ET CUISSON:"
echo "   • Champs prep_time et cook_time sur les recettes"
echo "   • Affichage dans la fiche recette"
echo "   • Migration: migrations/add_recipe_times.sql"
echo ""
echo "💡 CONSEILS SUR LES RECETTES:"
echo "   • Champ 'tips' libre sur les traductions de recette"
echo "   • Affiché dans la fiche recette"
echo "   • Migration: migrations/add_recipe_tips.sql"
echo ""
echo "🔗 LIAISON INGRÉDIENT → SOUS-RECETTE:"
echo "   • Un ingrédient peut pointer vers une autre recette"
echo "   • Permet de naviguer vers la recette de base"
echo "   • Migration: migrations/add_recipe_links.sql"
echo ""
echo "📷 IMAGES DANS LES ÉTAPES:"
echo "   • Les étapes peuvent être texte OU photo"
echo "   • Copier-coller d'image (Ctrl+V)"
echo "   • Lightbox pour agrandir"
echo "   • Migration: migrations/add_step_images.sql"
echo ""
echo "🗂️  ADMIN UTILISATEURS:"
echo "   • Nouveau template admin_user_edit.html"
echo "   • Édition des utilisateurs depuis l'interface admin"
echo ""
echo "🗄️  BASE DE DONNÉES:"
echo "   ⚠️  La base locale a été transférée en production"
echo "   • Backup disponible sur le NAS: backups/recette_pre_v3_*.sqlite3"
echo "   • ${NB_RECIPES} recettes déployées"
echo ""
echo "🖼️  IMAGES TRANSFÉRÉES:"
echo "   • static/images/recipes/ : ${NB_RECIPE_IMAGES} images de recettes"
echo "   • static/images/steps/  : ${NB_STEP_IMAGES} images d'étapes"
echo ""
echo "✅ TESTS À EFFECTUER:"
echo "   1. 📅 Calendrier: /calendar — affichage mensuel, ajout d'un repas"
echo "   2. ⏱️  Recette: vérifier temps de préparation/cuisson affiché"
echo "   3. 💡 Recette: vérifier section conseils"
echo "   4. 🖼️  Recettes: vérifier que les photos de recettes s'affichent"
echo "   5. 📷 Étapes: vérifier les images dans les étapes"
echo "   6. 🔐 Auth: vérifier connexion / admin"
echo ""
echo "🔄 EN CAS DE PROBLÈME:"
echo "   1. Logs:    tail -f ~/recette/logs/recette.log"
echo "   2. Restaurer la base:"
echo "      cp ~/recette/backups/recette_pre_v3_*.sqlite3 ~/recette/data/recette.sqlite3"
echo "   3. Redémarrer:"
echo "      cd ~/recette && bash stop_recette.sh && bash start_recette.sh"
echo ""
