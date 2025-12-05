#!/bin/bash
# Script de déploiement pour Synology DS213+
# Version 1.7 - Aide modifiable par admin
# Usage: ./deploy_synology_V1_7.sh

SYNOLOGY_USER="admin"
SYNOLOGY_HOST="192.168.1.14"
DEPLOY_PATH="recette"
SYNOLOGY_SSH="${SYNOLOGY_USER}@${SYNOLOGY_HOST}"

echo "🚀 Déploiement de Recette Version 1.7 sur Synology..."
echo "📦 Nouvelles fonctionnalités:"
echo "   • Aide modifiable par les administrateurs via interface web"
echo "   • Éditeur Markdown avec preview en temps réel"
echo "   • Bouton retour dans la page d'aide"
echo "   • Contenu bilingue (FR/JP) éditable séparément"
echo "   • Modifications sans redéploiement"
echo ""
echo "📍 Destination: ${DEPLOY_PATH}"
echo ""

# Vérifier que les fichiers nécessaires existent
echo "🔍 Vérification des fichiers..."
REQUIRED_FILES=(
    "requirements.txt"
    "app/routes/auth_routes.py"
    "app/templates/help.html"
    "app/templates/admin_help_edit.html"
    "docs/help/content/help_fr.md"
    "docs/help/content/help_jp.md"
    "app/models/__init__.py"
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
tar czf /tmp/recette_v1_7_deploy.tar.gz \
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
    --exclude='scripts' \
    --exclude='.claude' \
    --exclude='.DS_Store' \
    --exclude='recipes.db' \
    --exclude='data/recette.sqlite3' \
    --exclude='.pytest_cache' \
    --exclude='htmlcov' \
    --exclude='.coverage' \
    app/ static/ requirements.txt config.py main.py init_db.py migrations/ docs/help/ \
    .env.example

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de la création de l'archive"
    exit 1
fi

ARCHIVE_SIZE=$(du -h /tmp/recette_v1_7_deploy.tar.gz | cut -f1)
echo "✅ Archive créée (${ARCHIVE_SIZE})"

# 2. Transférer via SSH
echo ""
echo "🔗 Étape 2/8 : Transfert vers le NAS..."
cat /tmp/recette_v1_7_deploy.tar.gz | ssh $SYNOLOGY_SSH "cat > ${DEPLOY_PATH}/recette_v1_7_deploy.tar.gz"

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du transfert"
    rm /tmp/recette_v1_7_deploy.tar.gz
    exit 1
fi
echo "✅ Archive transférée"

# 3. Backup de la base de données
echo ""
echo "💾 Étape 3/8 : Backup de la base de données..."
ssh $SYNOLOGY_SSH << 'EOF'
cd recette
BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="${BACKUP_DIR}/recette_pre_v1_7_$(date +%Y%m%d_%H%M%S).sqlite3"

if [ -f "data/recette.sqlite3" ]; then
    cp data/recette.sqlite3 "$BACKUP_FILE"
    echo "✅ Backup créé: $BACKUP_FILE"
else
    echo "⚠️  Aucune base de données à sauvegarder"
fi
EOF

# 4. Arrêt de l'application
echo ""
echo "🛑 Étape 4/8 : Arrêt de l'application..."
ssh $SYNOLOGY_SSH "pkill -f 'uvicorn.*recette' || true"
sleep 2
echo "✅ Application arrêtée"

# 5. Déploiement des fichiers
echo ""
echo "📂 Étape 5/8 : Déploiement des fichiers..."
ssh $SYNOLOGY_SSH << 'EOF'
cd recette

# Extraction
tar xzf recette_v1_7_deploy.tar.gz
if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de l'extraction"
    exit 1
fi

# Nettoyage
rm recette_v1_7_deploy.tar.gz

# Vérifier permissions
chmod -R 755 app/
chmod 644 requirements.txt

echo "✅ Fichiers déployés"
EOF

# 6. Installation des dépendances
echo ""
echo "📚 Étape 6/8 : Installation des dépendances Python..."
ssh $SYNOLOGY_SSH << 'EOF'
cd recette

# Vérifier que le venv existe
if [ ! -d "venv" ]; then
    echo "⚠️  Création de l'environnement virtuel..."
    /usr/local/bin/python3 -m venv venv
fi

# Activer et installer
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de l'installation des dépendances"
    exit 1
fi

echo "✅ Dépendances installées"

# Vérifier que markdown est installé
python3 -c "import markdown" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Bibliothèque markdown installée"
else
    echo "❌ Erreur: markdown non installé"
    exit 1
fi
EOF

# 7. Pas de migration BDD pour V1.7
echo ""
echo "🗄️  Étape 7/8 : Migrations..."
echo "ℹ️  Aucune migration nécessaire pour V1.7"

# 8. Démarrage de l'application
echo ""
echo "▶️  Étape 8/8 : Démarrage de l'application..."
ssh $SYNOLOGY_SSH << 'EOF'
cd recette

# Vérifier que le port 8000 est libre
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8000 occupé, nettoyage..."
    pkill -f 'uvicorn.*recette'
    sleep 2
fi

# Démarrer en arrière-plan
nohup venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/app.log 2>&1 &

# Attendre démarrage
sleep 5

# Vérifier que l'app répond
curl -s http://localhost:8000/recipes > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Application démarrée avec succès"
else
    echo "❌ Erreur: L'application ne répond pas"
    tail -n 20 logs/app.log
    exit 1
fi
EOF

# Nettoyage local
rm /tmp/recette_v1_7_deploy.tar.gz

echo ""
echo "✅ ============================================="
echo "✅ Déploiement V1.7 terminé avec succès!"
echo "✅ ============================================="
echo ""
echo "🌐 Application accessible sur:"
echo "   • Local: http://192.168.1.14:8000"
echo "   • Public: http://recipe.e2pc.fr"
echo ""
echo "📝 Nouveautés V1.7:"
echo "   1. Bouton retour dans la page d'aide"
echo "   2. Aide modifiable via /admin/help/edit (admins uniquement)"
echo "   3. Éditeur Markdown avec preview en temps réel"
echo "   4. Contenu stocké dans docs/help/content/help_{lang}.md"
echo "   5. Modifications sans redéploiement"
echo ""
echo "🔧 Tests à effectuer:"
echo "   1. Se connecter en tant qu'admin"
echo "   2. Accéder à la page d'aide (icône ❓)"
echo "   3. Cliquer sur 'Éditer l'aide'"
echo "   4. Modifier le contenu Markdown"
echo "   5. Basculer sur 'Aperçu' pour voir le rendu"
echo "   6. Enregistrer et vérifier que les modifications apparaissent"
echo "   7. Tester en FR et JP"
echo "   8. Vérifier le bouton retour"
echo ""
echo "📊 Commits inclus dans cette version:"
echo "   • 999e324 - Aide modifiable par admin en Markdown"
echo "   • bac34f6 - Ajout bouton retour dans l'aide"
echo ""
echo "🆘 En cas de problème:"
echo "   • Logs: ssh admin@192.168.1.14 'tail -f recette/logs/app.log'"
echo "   • Rollback: Restaurer depuis backups/recette_pre_v1_7_*.sqlite3"
echo ""
