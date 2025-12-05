#!/bin/bash
# Script de déploiement pour Synology DS213+
# Version 1.6 - Recherche par ingrédients + Événements multi-jours
# Usage: ./deploy_synology_V1_6.sh

SYNOLOGY_USER="admin"
SYNOLOGY_HOST="192.168.1.14"
DEPLOY_PATH="recette"
SYNOLOGY_SSH="${SYNOLOGY_USER}@${SYNOLOGY_HOST}"

echo "🚀 Déploiement de Recette Version 1.6 sur Synology..."
echo "📦 Nouvelles fonctionnalités:"
echo "   • Recherche de recettes par ingrédients multiples"
echo "   • Gestion événements multi-jours avec sélection de dates"
echo "   • Organisation et planification des recettes par jour"
echo "   • Interface drag & drop pour la planification"
echo "   • Page d'aide complète bilingue (FR/JP)"
echo "   • Auto-génération liste de courses si vide"
echo ""
echo "📍 Destination: ${DEPLOY_PATH}"
echo ""

# Vérifier que les fichiers nécessaires existent
echo "🔍 Vérification des fichiers..."
REQUIRED_FILES=(
    "requirements.txt"
    "app/models/__init__.py"
    "app/models/db_recipes.py"
    "app/models/db_events.py"
    "app/routes/recipe_routes.py"
    "app/routes/event_routes.py"
    "app/routes/auth_routes.py"
    "app/templates/recipes_list.html"
    "app/templates/event_form.html"
    "app/templates/event_organization.html"
    "app/templates/event_planning.html"
    "app/templates/help.html"
    "app/templates/base.html"
    "migrations/add_event_multi_days.sql"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Erreur: Fichier manquant: $file"
        exit 1
    fi
done
echo "✅ Tous les fichiers requis sont présents"
echo ""

# 1. Créer l'archive temporaire en local
echo "📦 Étape 1/8 : Préparation de l'archive..."
tar czf /tmp/recette_v1_6_deploy.tar.gz \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='venv' \
    --exclude='data/recette.sqlite3-shm' \
    --exclude='data/recette.sqlite3-wal' \
    --exclude='data/recette_dev.sqlite3*' \
    --exclude='data/recette_prod.sqlite3*' \
    --exclude='logs/*' \
    --exclude='*.log' \
    --exclude='*.tar.gz' \
    --exclude='deploy' \
    --exclude='tests' \
    --exclude='docs' \
    --exclude='scripts' \
    --exclude='.claude' \
    --exclude='.DS_Store' \
    --exclude='recipes.db' \
    --exclude='data/recette.sqlite3' \
    --exclude='.pytest_cache' \
    --exclude='htmlcov' \
    --exclude='.coverage' \
    app/ static/ requirements.txt config.py main.py init_db.py migrations/ \
    .env.example

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de la création de l'archive"
    exit 1
fi

ARCHIVE_SIZE=$(du -h /tmp/recette_v1_6_deploy.tar.gz | cut -f1)
echo "✅ Archive créée (${ARCHIVE_SIZE})"

# 2. Transférer via SSH
echo ""
echo "🔗 Étape 2/8 : Transfert vers le NAS..."
cat /tmp/recette_v1_6_deploy.tar.gz | ssh $SYNOLOGY_SSH "cat > ${DEPLOY_PATH}/recette_v1_6_deploy.tar.gz"

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du transfert"
    rm /tmp/recette_v1_6_deploy.tar.gz
    exit 1
fi
echo "✅ Archive transférée"

# 3. Backup de la base de données
echo ""
echo "💾 Étape 3/8 : Backup de la base de données..."
ssh $SYNOLOGY_SSH << 'ENDSSH'
cd recette
mkdir -p backups

# Créer un backup avec horodatage
if [ -f "data/recette.sqlite3" ]; then
    BACKUP_FILE="backups/recette_pre_v1_6_$(date +%Y%m%d_%H%M%S).sqlite3"
    cp data/recette.sqlite3 "$BACKUP_FILE"
    echo "✅ Backup créé: $BACKUP_FILE"
else
    echo "⚠️  Pas de base de données existante"
fi
ENDSSH

# 4. Arrêt de l'application
echo ""
echo "⏸️  Étape 4/8 : Arrêt de l'application..."
ssh $SYNOLOGY_SSH "cd ${DEPLOY_PATH} && bash stop_recette.sh" 2>/dev/null || true
sleep 2

# 5. Déploiement sur le NAS
echo ""
echo "🔧 Étape 5/8 : Déploiement des fichiers..."
ssh $SYNOLOGY_SSH << 'ENDSSH'
cd recette
mkdir -p backups data logs

# Backup des anciens fichiers si ils existent
if [ -d "app" ]; then
    BACKUP_DIR="backups/code_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    cp -r app "$BACKUP_DIR/" 2>/dev/null || true
    echo "  📦 Code sauvegardé dans $BACKUP_DIR"
fi

# Extraction
tar xzf recette_v1_6_deploy.tar.gz
rm recette_v1_6_deploy.tar.gz

# Création du .env si nécessaire
[ ! -f ".env" ] && cp .env.example .env

echo "✅ Fichiers déployés"
ENDSSH

# 6. Installation des dépendances (si nouvelles)
echo ""
echo "📚 Étape 6/8 : Vérification des dépendances..."
ssh $SYNOLOGY_SSH << 'ENDSSH'
cd recette
source venv/bin/activate

echo "  🔄 Mise à jour de pip..."
pip install --upgrade pip -q

echo "  📦 Installation/mise à jour des dépendances..."
pip install -r requirements.txt -q

echo "✅ Dépendances à jour"
ENDSSH

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de l'installation des dépendances"
    exit 1
fi

# 7. Migration de la base de données
echo ""
echo "🔄 Étape 7/8 : Migration de la base de données..."
echo "⚠️  Ajout des tables pour événements multi-jours"
ssh $SYNOLOGY_SSH << 'ENDSSH'
cd recette
source venv/bin/activate

echo "  🔧 Exécution du script SQL..."
sqlite3 data/recette.sqlite3 < migrations/add_event_multi_days.sql

if [ $? -eq 0 ]; then
    echo "✅ Migration SQL terminée avec succès"
else
    echo "❌ Erreur lors de la migration SQL"
    echo "⚠️  Restauration de la sauvegarde..."
    LATEST_BACKUP=$(ls -t backups/recette_pre_v1_6_*.sqlite3 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        cp "$LATEST_BACKUP" data/recette.sqlite3
        echo "✅ Base de données restaurée depuis $LATEST_BACKUP"
    fi
    exit 1
fi

# Vérification post-migration
echo "  🔍 Vérification de l'intégrité..."

# Vérifier que la colonne date_debut existe dans event
EVENT_COLUMNS=$(sqlite3 data/recette.sqlite3 "PRAGMA table_info(event);" | grep date_debut)
if [ -n "$EVENT_COLUMNS" ]; then
    echo "  ✅ Colonne event.date_debut ajoutée"
else
    echo "  ⚠️  Attention : Colonne event.date_debut non trouvée"
fi

# Vérifier que la colonne date_fin existe dans event
EVENT_COLUMNS=$(sqlite3 data/recette.sqlite3 "PRAGMA table_info(event);" | grep date_fin)
if [ -n "$EVENT_COLUMNS" ]; then
    echo "  ✅ Colonne event.date_fin ajoutée"
else
    echo "  ⚠️  Attention : Colonne event.date_fin non trouvée"
fi

# Vérifier que la colonne nombre_jours existe dans event
EVENT_COLUMNS=$(sqlite3 data/recette.sqlite3 "PRAGMA table_info(event);" | grep nombre_jours)
if [ -n "$EVENT_COLUMNS" ]; then
    echo "  ✅ Colonne event.nombre_jours ajoutée"
else
    echo "  ⚠️  Attention : Colonne event.nombre_jours non trouvée"
fi

# Vérifier que la table event_date existe
EVENT_DATE_EXISTS=$(sqlite3 data/recette.sqlite3 "SELECT name FROM sqlite_master WHERE type='table' AND name='event_date';" 2>/dev/null)
if [ "$EVENT_DATE_EXISTS" = "event_date" ]; then
    echo "  ✅ Table event_date créée"
else
    echo "  ⚠️  Attention : Table event_date non trouvée"
fi

# Vérifier que la table event_recipe_planning existe
PLANNING_EXISTS=$(sqlite3 data/recette.sqlite3 "SELECT name FROM sqlite_master WHERE type='table' AND name='event_recipe_planning';" 2>/dev/null)
if [ "$PLANNING_EXISTS" = "event_recipe_planning" ]; then
    echo "  ✅ Table event_recipe_planning créée"
else
    echo "  ⚠️  Attention : Table event_recipe_planning non trouvée"
fi
ENDSSH

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de la migration"
    exit 1
fi

# 8. Redémarrage de l'application
echo ""
echo "▶️  Étape 8/8 : Redémarrage de l'application..."
ssh $SYNOLOGY_SSH "cd ${DEPLOY_PATH} && bash start_recette.sh"

# Vérification
echo ""
echo "🔍 Vérification du démarrage..."
sleep 3
ssh $SYNOLOGY_SSH "ps aux | grep '[u]vicorn'" > /dev/null && echo "✅ Application démarrée avec succès"

# Nettoyage local
rm /tmp/recette_v1_6_deploy.tar.gz

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Déploiement Version 1.6 terminé !"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 URL: http://192.168.1.14:8000"
echo "📍 URL publique: http://recipe.e2pc.fr"
echo ""
echo "✨ Nouvelles fonctionnalités disponibles:"
echo ""
echo "🥕 Recherche par ingrédients:"
echo "   • Interface dans la liste des recettes"
echo "   • Support multi-ingrédients (ex: tomate, basilic, mozzarella)"
echo "   • Logique ET (trouve les recettes avec TOUS les ingrédients)"
echo ""
echo "📅 Événements multi-jours:"
echo "   • Dates de début et de fin"
echo "   • Sélection des jours travaillés (désélectionner week-ends)"
echo "   • Organisation : Voir les recettes par jour"
echo "   • Planification : Drag & drop des recettes vers les dates"
echo "   • Défilement indépendant des colonnes"
echo ""
echo "❓ Page d'aide:"
echo "   • Accessible depuis la sidebar (icône ❓)"
echo "   • Bilingue FR/JP avec mode clair/sombre"
echo "   • Documentation complète de toutes les fonctions"
echo "   • FAQ interactive"
echo ""
echo "✅ Tests à effectuer:"
echo "   1. Page recettes : Tester la recherche par ingrédients"
echo "   2. Créer un événement multi-jours (ex: 5 jours)"
echo "   3. Désélectionner des jours (ex: week-end)"
echo "   4. Ajouter des recettes à l'événement"
echo "   5. Aller dans 'Organisation' pour voir la planification"
echo "   6. Aller dans 'Planification' pour drag & drop"
echo "   7. Vérifier que la liste de courses se génère automatiquement"
echo "   8. Cliquer sur 'Aide' (❓) dans la sidebar"
echo ""
echo "📝 Commits inclus:"
echo "   • 8fe57aa - Recherche par ingrédients et gestion événements multi-jours"
echo "   • 21318f5 - Page d'aide complète et documentation déploiement V1.6"
echo ""
echo "🔄 Base de données:"
echo "   • Backup: ~/recette/backups/recette_pre_v1_6_*.sqlite3"
echo "   • Migration: add_event_multi_days.sql"
echo "   • Nouvelles tables: event_date, event_recipe_planning"
echo "   • Nouvelles colonnes: date_debut, date_fin, nombre_jours"
echo ""
