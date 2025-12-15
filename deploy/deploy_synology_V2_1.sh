#!/bin/bash
# Script de déploiement pour Synology DS213+
# Version 2.1 - Gestion des participants et groupes multi-utilisateurs
# Usage: ./deploy_synology_V2_1.sh

SYNOLOGY_USER="admin"
SYNOLOGY_HOST="192.168.1.14"
DEPLOY_PATH="recette"
SYNOLOGY_SSH="${SYNOLOGY_USER}@${SYNOLOGY_HOST}"

echo "🚀 Déploiement de Recette Version 2.1 sur Synology..."
echo "📦 Nouvelles fonctionnalités:"
echo "   • Système de gestion des participants (non-utilisateurs)"
echo "   • Système de groupes de participants"
echo "   • Association participants ↔ groupes bidirectionnelle"
echo "   • Gestion multi-utilisateurs des participants/groupes"
echo "   • Interface modal dual-list pour les événements"
echo "   • Nouveau template de connexion moderne (recette_connexion.html)"
echo "   • Persistance des filtres dans l'URL (recipes_list)"
echo "   • Option d'import par URL pour les recettes"
echo ""
echo "📍 Destination: ${DEPLOY_PATH}"
echo ""

# Vérifier que les fichiers nécessaires existent
echo "🔍 Vérification des fichiers..."
REQUIRED_FILES=(
    "requirements.txt"
    "app/models/db_participants.py"
    "app/routes/participant_routes.py"
    "app/templates/recette_connexion.html"
    "app/templates/event_detail.html"
    "app/templates/participants_index.html"
    "app/templates/participant_detail.html"
    "app/templates/group_detail.html"
    "migrations/add_participants_and_groups.sql"
    "migrations/add_user_id_to_participants.sql"
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
tar czf /tmp/recette_v2_1_deploy.tar.gz \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='venv' \
    --exclude='data/*.sqlite3' \
    --exclude='data/*.db' \
    --exclude='data/*.csv' \
    --exclude='data/recette.sqlite3-shm' \
    --exclude='data/recette.sqlite3-wal' \
    --exclude='data/recette_dev.sqlite3*' \
    --exclude='data/recette_prod.sqlite3*' \
    --exclude='data/OLD/' \
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
    --exclude='.pytest_cache' \
    --exclude='htmlcov' \
    --exclude='.coverage' \
    app/ static/ requirements.txt config.py main.py migrations/ \
    .env.example

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de la création de l'archive"
    exit 1
fi

ARCHIVE_SIZE=$(du -h /tmp/recette_v2_1_deploy.tar.gz | cut -f1)
echo "✅ Archive créée (${ARCHIVE_SIZE})"

# 2. Transférer via SSH
echo ""
echo "🔗 Étape 2/8 : Transfert vers le NAS..."
cat /tmp/recette_v2_1_deploy.tar.gz | ssh $SYNOLOGY_SSH "cat > ${DEPLOY_PATH}/recette_v2_1_deploy.tar.gz"

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du transfert"
    rm /tmp/recette_v2_1_deploy.tar.gz
    exit 1
fi
echo "✅ Archive transférée"

# 3. Backup de la base de données
echo ""
echo "💾 Étape 3/8 : Backup de la base de données..."
ssh $SYNOLOGY_SSH << 'ENDSSH'
cd recette
mkdir -p backups

if [ -f "data/recette.sqlite3" ]; then
    BACKUP_FILE="backups/recette_pre_v2_1_$(date +%Y%m%d_%H%M%S).sqlite3"
    cp data/recette.sqlite3 "$BACKUP_FILE"
    echo "✅ Backup créé: $BACKUP_FILE"

    # Vérifier l'intégrité du backup
    sqlite3 "$BACKUP_FILE" "PRAGMA integrity_check;" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Intégrité du backup vérifiée"
    else
        echo "❌ Erreur: Backup corrompu"
        exit 1
    fi
else
    echo "⚠️  Pas de base de données existante"
fi
ENDSSH

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du backup"
    exit 1
fi

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
tar xzf recette_v2_1_deploy.tar.gz
rm recette_v2_1_deploy.tar.gz

# Création du .env si nécessaire
[ ! -f ".env" ] && cp .env.example .env

echo "✅ Fichiers déployés"
ENDSSH

# 6. Installation des dépendances
echo ""
echo "📚 Étape 6/8 : Installation des dépendances..."
ssh $SYNOLOGY_SSH << 'ENDSSH'
cd recette
source venv/bin/activate

echo "  🔄 Mise à jour de pip..."
pip install --upgrade pip -q

echo "  📦 Installation des dépendances..."
pip install -r requirements.txt -q

echo "✅ Toutes les dépendances sont installées"
ENDSSH

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de l'installation des dépendances"
    exit 1
fi

# 7. Migration de la base de données
echo ""
echo "🔄 Étape 7/8 : Migration de la base de données..."
echo "⚠️  Ajout des tables participants et groupes + colonnes user_id"
ssh $SYNOLOGY_SSH << 'ENDSSH'
cd recette
source venv/bin/activate

echo "  🔧 Migration 1/2 : Création tables participants et groupes..."
sqlite3 data/recette.sqlite3 < migrations/add_participants_and_groups.sql

if [ $? -eq 0 ]; then
    echo "  ✅ Tables créées avec succès"
else
    echo "  ❌ Erreur lors de la création des tables"
    echo "  ⚠️  Restauration de la sauvegarde..."
    LATEST_BACKUP=$(ls -t backups/recette_pre_v2_1_*.sqlite3 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        cp "$LATEST_BACKUP" data/recette.sqlite3
        echo "  ✅ Base de données restaurée depuis $LATEST_BACKUP"
    fi
    exit 1
fi

echo "  🔧 Migration 2/2 : Ajout colonnes user_id..."
sqlite3 data/recette.sqlite3 < migrations/add_user_id_to_participants.sql

if [ $? -eq 0 ]; then
    echo "  ✅ Migration SQL terminée avec succès"
else
    echo "  ❌ Erreur lors de la migration user_id"
    echo "  ⚠️  Restauration de la sauvegarde..."
    LATEST_BACKUP=$(ls -t backups/recette_pre_v2_1_*.sqlite3 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        cp "$LATEST_BACKUP" data/recette.sqlite3
        echo "  ✅ Base de données restaurée depuis $LATEST_BACKUP"
    fi
    exit 1
fi

# Vérification post-migration
echo "  🔍 Vérification de l'intégrité..."

# Vérifier que les tables existent
for table in participant participant_group participant_group_member event_participant; do
    COUNT=$(sqlite3 data/recette.sqlite3 "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='$table';" 2>/dev/null)
    if [ "$COUNT" = "1" ]; then
        echo "  ✅ Table $table créée"
    else
        echo "  ❌ Erreur : Table $table manquante"
        exit 1
    fi
done

# Vérifier que les colonnes user_id existent
PARTICIPANT_COLS=$(sqlite3 data/recette.sqlite3 "PRAGMA table_info(participant);" | grep user_id)
if [ -n "$PARTICIPANT_COLS" ]; then
    echo "  ✅ Colonne participant.user_id ajoutée"
else
    echo "  ❌ Erreur : Colonne participant.user_id manquante"
    exit 1
fi

GROUP_COLS=$(sqlite3 data/recette.sqlite3 "PRAGMA table_info(participant_group);" | grep user_id)
if [ -n "$GROUP_COLS" ]; then
    echo "  ✅ Colonne participant_group.user_id ajoutée"
else
    echo "  ❌ Erreur : Colonne participant_group.user_id manquante"
    exit 1
fi

# Vérifier les index
INDEX_COUNT=$(sqlite3 data/recette.sqlite3 "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%participant%';" 2>/dev/null)
echo "  ✅ $INDEX_COUNT index créés pour les participants/groupes"

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
rm /tmp/recette_v2_1_deploy.tar.gz

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Déploiement Version 2.1 terminé !"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 URL: http://192.168.1.14:8000"
echo "📍 URL publique: http://recipe.e2pc.fr"
echo ""
echo "✨ Nouvelles fonctionnalités disponibles:"
echo "   • Gestion des participants : http://recipe.e2pc.fr/participants"
echo "   • Création de groupes de participants"
echo "   • Ajout de participants aux événements (individuel ou par groupe)"
echo "   • Isolation multi-utilisateurs (chaque user a ses participants/groupes)"
echo "   • Nouveau design page de connexion"
echo "   • Persistance des filtres de recettes dans l'URL"
echo "   • Import de recettes par URL"
echo ""
echo "✅ Tests à effectuer:"
echo "   1. Se connecter avec votre compte"
echo "   2. Aller sur /participants et créer un participant"
echo "   3. Créer un groupe et y ajouter des participants"
echo "   4. Ouvrir un événement existant"
echo "   5. Cliquer sur 'Participants' et ajouter via groupe ou individuellement"
echo "   6. Vérifier que les participants s'affichent correctement"
echo "   7. Vérifier l'isolation : créer un 2e compte et vérifier qu'il ne voit pas les participants du 1er"
echo "   8. Tester les filtres de recettes et vérifier qu'ils persistent dans l'URL"
echo ""
echo "📚 Documentation:"
echo "   • docs/PARTICIPANTS_GROUPS_SYSTEM.md - Documentation complète du système"
echo "   • deploy/NOTES_DEPLOIEMENT_V2_1.md - Notes de cette version"
echo ""
echo "🔄 En cas de problème:"
echo "   Restaurer depuis le backup : ~/recette/backups/recette_pre_v2_1_*.sqlite3"
echo ""
echo "💡 Commits inclus dans cette version:"
echo "   8d7d3ad - Fix: Utilisation correcte de la session (user_id au lieu de user)"
echo "   148c581 - Feature: Gestion multi-utilisateurs participants et groupes"
echo "   985adb4 - Fix: Ajout Alpine.js et Tailwind + Améliorations UX participants"
echo "   bea628a - Amélioration UI: Interface dual-list pour sélection groupes/participants"
echo "   7cdfb73 - Frontend: Gestion bidirectionnelle participants ↔ groupes dans les modales"
echo "   e7d7676 - Backend: Ajout gestion bidirectionnelle participants ↔ groupes"
echo "   d9ddfbb - Ajout de la gestion des participants et groupes (V1.12 - Base)"
echo ""
