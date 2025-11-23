#!/bin/bash
# Script de déploiement avec BASE DE DONNÉES pour Synology DS213+
# Version 1.3 - Inclut la base de données de développement
# Usage: ./deploy_synology.sh

SYNOLOGY_USER="admin"
SYNOLOGY_HOST="192.168.1.14"
DEPLOY_PATH="recette"
SYNOLOGY_SSH="${SYNOLOGY_USER}@${SYNOLOGY_HOST}"

echo "🚀 Déploiement de Recette Version 1.3 sur Synology (avec base de données)..."
echo "📍 Destination: ${DEPLOY_PATH}"
echo ""

# Vérifier que la base de données existe
if [ ! -f "data/recette.sqlite3" ]; then
    echo "❌ Erreur: Base de données data/recette.sqlite3 introuvable"
    exit 1
fi

echo "📊 Base de données trouvée: data/recette.sqlite3"
DB_SIZE=$(du -h data/recette.sqlite3 | cut -f1)
echo "   Taille: ${DB_SIZE}"
echo ""

# 1. Créer l'archive temporaire en local (AVEC la base de données)
echo "📦 Étape 1/6 : Préparation de l'archive..."
tar czf /tmp/recette_v1_3_deploy.tar.gz \
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
    --exclude='migrations' \
    --exclude='recipes.db' \
    app/ static/ data/recette.sqlite3 requirements.txt config.py main.py init_db.py \
    .env.example

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de la création de l'archive"
    exit 1
fi

ARCHIVE_SIZE=$(du -h /tmp/recette_v1_3_deploy.tar.gz | cut -f1)
echo "✅ Archive créée (${ARCHIVE_SIZE})"

# 2. Transférer via SSH
echo "🔗 Étape 2/6 : Transfert vers le NAS..."
cat /tmp/recette_v1_3_deploy.tar.gz | ssh $SYNOLOGY_SSH "cat > ${DEPLOY_PATH}/recette_v1_3_deploy.tar.gz"

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du transfert"
    rm /tmp/recette_v1_3_deploy.tar.gz
    exit 1
fi
echo "✅ Archive transférée"

# 3. Déploiement sur le NAS
echo "🔧 Étape 3/6 : Déploiement..."
ssh $SYNOLOGY_SSH bash stop_recette.sh 2>/dev/null || true
sleep 2

ssh $SYNOLOGY_SSH << 'ENDSSH'
cd recette
mkdir -p backups data logs
BACKUP_DIR="backups/backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
[ -f "data/recette.sqlite3" ] && cp data/recette.sqlite3 "$BACKUP_DIR/"
tar xzf recette_v1_3_deploy.tar.gz
rm recette_v1_3_deploy.tar.gz
[ ! -f ".env" ] && cp .env.example .env
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
ENDSSH

echo "✅ Déploiement réussi"

# 4. Vérifier la base
echo "🗄️  Étape 4/6 : Vérification..."
ssh $SYNOLOGY_SSH << 'ENDSSH'
cd recette
RECIPE_COUNT=$(sqlite3 data/recette.sqlite3 "SELECT COUNT(*) FROM recipe;" 2>/dev/null)
echo "  📊 $RECIPE_COUNT recettes"
ENDSSH

# 5. Redémarrer
echo "▶️  Étape 5/6 : Redémarrage..."
ssh $SYNOLOGY_SSH bash recette/start_recette.sh

# 6. Vérifier
echo "🔍 Étape 6/6 : Vérification..."
sleep 3
ssh $SYNOLOGY_SSH "ps aux | grep '[u]vicorn'" > /dev/null && echo "✅ Application OK"

rm /tmp/recette_v1_3_deploy.tar.gz

echo ""
echo "🎉 Déploiement terminé !"
echo "📍 URL: http://192.168.1.14:8000"
echo ""
