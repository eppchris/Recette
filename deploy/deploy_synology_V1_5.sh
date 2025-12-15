#!/bin/bash
# Script de déploiement pour Synology DS213+
# Version 1.5 - Système d'authentification multi-utilisateur + Refactoring
# Usage: ./deploy_synology_V1_5.sh

SYNOLOGY_USER="admin"
SYNOLOGY_HOST="192.168.1.14"
DEPLOY_PATH="recette"
SYNOLOGY_SSH="${SYNOLOGY_USER}@${SYNOLOGY_HOST}"

echo "🚀 Déploiement de Recette Version 1.5 sur Synology..."
echo "📦 Nouvelles fonctionnalités:"
echo "   • Système d'authentification multi-utilisateur (login/register/profil)"
echo "   • Refactoring: db.py (3114 lignes) → 10 modules spécialisés"
echo "   • Infrastructure de tests unitaires avec pytest"
echo "   • Hash sécurisé des mots de passe avec bcrypt"
echo "   • Gestion des rôles (admin/utilisateur standard)"
echo ""
echo "📍 Destination: ${DEPLOY_PATH}"
echo ""

# Vérifier que les fichiers nécessaires existent
echo "🔍 Vérification des fichiers..."
REQUIRED_FILES=(
    "requirements.txt"
    "app/models/__init__.py"
    "app/models/db_users.py"
    "app/routes/auth_routes.py"
    "app/templates/recette_connexion.html"
    "app/templates/register.html"
    "migrations/add_user_system.sql"
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
tar czf /tmp/recette_v1_5_deploy.tar.gz \
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

ARCHIVE_SIZE=$(du -h /tmp/recette_v1_5_deploy.tar.gz | cut -f1)
echo "✅ Archive créée (${ARCHIVE_SIZE})"

# 2. Transférer via SSH
echo ""
echo "🔗 Étape 2/8 : Transfert vers le NAS..."
cat /tmp/recette_v1_5_deploy.tar.gz | ssh $SYNOLOGY_SSH "cat > ${DEPLOY_PATH}/recette_v1_5_deploy.tar.gz"

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du transfert"
    rm /tmp/recette_v1_5_deploy.tar.gz
    exit 1
fi
echo "✅ Archive transférée"

# 3. Backup de la base de données (si pas déjà fait)
echo ""
echo "💾 Étape 3/8 : Vérification du backup..."
ssh $SYNOLOGY_SSH << 'ENDSSH'
cd recette
mkdir -p backups

# Vérifier si un backup récent existe (moins de 5 minutes)
RECENT_BACKUP=$(find backups/ -name "recette_*.sqlite3" -mmin -5 2>/dev/null | head -1)

if [ -n "$RECENT_BACKUP" ]; then
    echo "✅ Backup récent trouvé: $RECENT_BACKUP"
    echo "   (Vous avez indiqué avoir déjà copié la base)"
else
    echo "⚠️  Aucun backup récent trouvé"
    if [ -f "data/recette.sqlite3" ]; then
        BACKUP_FILE="backups/recette_$(date +%Y%m%d_%H%M%S).sqlite3"
        cp data/recette.sqlite3 "$BACKUP_FILE"
        echo "✅ Backup de sécurité créé: $BACKUP_FILE"
    else
        echo "⚠️  Pas de base de données existante"
    fi
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
tar xzf recette_v1_5_deploy.tar.gz
rm recette_v1_5_deploy.tar.gz

# Création du .env si nécessaire
[ ! -f ".env" ] && cp .env.example .env

echo "✅ Fichiers déployés"
ENDSSH

# 6. Installation des dépendances
echo ""
echo "📚 Étape 6/8 : Installation des dépendances..."
echo "   (Installation de passlib - pure Python, pas de compilation)"
ssh $SYNOLOGY_SSH << 'ENDSSH'
cd recette
source venv/bin/activate

echo "  🔄 Mise à jour de pip..."
pip install --upgrade pip -q

echo "  📦 Installation des dépendances..."
echo "     • passlib (hash des mots de passe - pure Python)"
echo "     • pytest (tests unitaires)"
echo "     • Autres dépendances..."
pip install -r requirements.txt

echo "✅ Toutes les dépendances sont installées"
ENDSSH

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de l'installation des dépendances"
    exit 1
fi

# 7. Migration de la base de données
echo ""
echo "🔄 Étape 7/8 : Migration de la base de données..."
echo "⚠️  Ajout du système d'authentification (table user + colonnes user_id)"
ssh $SYNOLOGY_SSH << 'ENDSSH'
cd recette
source venv/bin/activate

echo "  🔧 Exécution du script SQL..."
sqlite3 data/recette.sqlite3 < migrations/add_user_system.sql

if [ $? -eq 0 ]; then
    echo "✅ Migration SQL terminée avec succès"
else
    echo "❌ Erreur lors de la migration SQL"
    echo "⚠️  Restauration de la sauvegarde..."
    LATEST_BACKUP=$(ls -t backups/recette_*.sqlite3 | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        cp "$LATEST_BACKUP" data/recette.sqlite3
        echo "✅ Base de données restaurée depuis $LATEST_BACKUP"
    fi
    exit 1
fi

# Vérification post-migration
echo "  🔍 Vérification de l'intégrité..."

# Vérifier que la table user existe
USER_COUNT=$(sqlite3 data/recette.sqlite3 "SELECT COUNT(*) FROM user;" 2>/dev/null)
if [ -n "$USER_COUNT" ] && [ "$USER_COUNT" -ge 1 ]; then
    echo "  ✅ Table user créée : $USER_COUNT utilisateur(s)"
else
    echo "  ❌ Erreur : Table user invalide"
    exit 1
fi

# Vérifier que la colonne user_id existe dans recipe
RECIPE_COLUMNS=$(sqlite3 data/recette.sqlite3 "PRAGMA table_info(recipe);" | grep user_id)
if [ -n "$RECIPE_COLUMNS" ]; then
    echo "  ✅ Colonne recipe.user_id ajoutée"
else
    echo "  ⚠️  Attention : Colonne recipe.user_id non trouvée"
fi

# Vérifier que la colonne user_id existe dans event
EVENT_COLUMNS=$(sqlite3 data/recette.sqlite3 "PRAGMA table_info(event);" | grep user_id)
if [ -n "$EVENT_COLUMNS" ]; then
    echo "  ✅ Colonne event.user_id ajoutée"
else
    echo "  ⚠️  Attention : Colonne event.user_id non trouvée"
fi

# Vérifier l'utilisateur admin
ADMIN_USER=$(sqlite3 data/recette.sqlite3 "SELECT username FROM user WHERE id = 1;" 2>/dev/null)
if [ "$ADMIN_USER" = "admin" ]; then
    echo "  ✅ Utilisateur admin créé (username: admin, password: admin123)"
else
    echo "  ⚠️  Attention : Utilisateur admin non trouvé"
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
rm /tmp/recette_v1_5_deploy.tar.gz

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Déploiement Version 1.5 terminé !"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 URL: http://192.168.1.14:8000"
echo "📍 URL publique: http://recipe.e2pc.fr"
echo ""
echo "🔐 Connexion par défaut:"
echo "   Username: admin"
echo "   Password: admin123"
echo "   ⚠️  IMPORTANT: Changer ce mot de passe immédiatement !"
echo ""
echo "✨ Nouvelles fonctionnalités disponibles:"
echo "   • Page de connexion : http://recipe.e2pc.fr/login"
echo "   • Page d'inscription : http://recipe.e2pc.fr/register"
echo "   • Profil utilisateur : http://recipe.e2pc.fr/profile"
echo "   • Architecture modulaire : db.py → 10 modules"
echo ""
echo "✅ Tests à effectuer:"
echo "   1. Se connecter avec admin/admin123"
echo "   2. Vérifier que le profil s'affiche correctement"
echo "   3. Créer un nouveau compte utilisateur"
echo "   4. Vérifier que les recettes et événements sont accessibles"
echo "   5. ⚠️  CHANGER LE MOT DE PASSE ADMIN"
echo ""
echo "📚 Documentation complète:"
echo "   • deploy/NOTES_DEPLOIEMENT_V1_5.md"
echo "   • docs/AUTH_SYSTEM.md"
echo ""
echo "🔑 Prochaine étape IMPORTANTE:"
echo "   Générer une SECRET_KEY unique pour les sessions :"
echo "   python3 -c \"import secrets; print(secrets.token_hex(32))\""
echo "   Puis l'ajouter dans ~/recette/.env"
echo ""
