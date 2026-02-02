#!/bin/bash
# Script de déploiement pour Synology DS213+
# Version 2.7 - Maintenance catalogue (doublons) + Responsive mobile
# Usage: ./deploy_synology_V2_7.sh

SYNOLOGY_USER="admin"
SYNOLOGY_HOST="192.168.1.14"
DEPLOY_PATH="recette"
SYNOLOGY_SSH="${SYNOLOGY_USER}@${SYNOLOGY_HOST}"

echo "🚀 Déploiement de Recette Version 2.7 sur Synology..."
echo "📦 Nouvelles fonctionnalités:"
echo "   🔧 Outil de maintenance du catalogue (détection et fusion des doublons)"
echo "   📱 Améliorations responsive mobile (recette détail)"
echo ""
echo "📍 Destination: ${DEPLOY_PATH}"
echo ""

# Vérifier que les fichiers nécessaires existent
echo "🔍 Vérification des fichiers modifiés..."
REQUIRED_FILES=(
    "app/models/__init__.py"
    "app/models/db_catalog_maintenance.py"
    "app/routes/catalog_routes.py"
    "app/templates/ingredient_catalog.html"
    "app/templates/ingredient_catalog_maintenance.html"
    "app/templates/recipe_detail.html"
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
echo "📦 Étape 1/6 : Préparation de l'archive..."
tar czf /tmp/recette_v2_7_deploy.tar.gz \
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
    --exclude='test_*.py' \
    --exclude='scripts' \
    --exclude='.claude' \
    --exclude='.DS_Store' \
    --exclude='recipes.db' \
    --exclude='recette.db' \
    --exclude='.pytest_cache' \
    --exclude='htmlcov' \
    --exclude='.coverage' \
    app/ static/ requirements.txt config.py main.py migrations/ \
    .env.example docs/

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de la création de l'archive"
    exit 1
fi

ARCHIVE_SIZE=$(du -h /tmp/recette_v2_7_deploy.tar.gz | cut -f1)
echo "✅ Archive créée (${ARCHIVE_SIZE})"

# 2. Transférer via SSH
echo ""
echo "🔗 Étape 2/6 : Transfert vers le NAS..."
cat /tmp/recette_v2_7_deploy.tar.gz | ssh $SYNOLOGY_SSH "cat > ${DEPLOY_PATH}/recette_v2_7_deploy.tar.gz"

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du transfert"
    rm /tmp/recette_v2_7_deploy.tar.gz
    exit 1
fi
echo "✅ Archive transférée"

# 3. Backup de la base de données
echo ""
echo "💾 Étape 3/6 : Backup de la base de données..."
ssh $SYNOLOGY_SSH << 'ENDSSH'
cd recette
mkdir -p backups

if [ -f "data/recette.sqlite3" ]; then
    BACKUP_FILE="backups/recette_pre_v2_7_$(date +%Y%m%d_%H%M%S).sqlite3"
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
echo "⏸️  Étape 4/6 : Arrêt de l'application..."
ssh $SYNOLOGY_SSH "cd ${DEPLOY_PATH} && bash stop_recette.sh" 2>/dev/null || true
sleep 2

# 5. Déploiement sur le NAS
echo ""
echo "🔧 Étape 5/6 : Déploiement des fichiers..."
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
tar xzf recette_v2_7_deploy.tar.gz
rm recette_v2_7_deploy.tar.gz

# Supprimer le cache Python pour forcer la recompilation
echo "  🧹 Suppression du cache Python..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Création du .env si nécessaire
[ ! -f ".env" ] && cp .env.example .env

echo "✅ Fichiers déployés (cache Python nettoyé)"
ENDSSH

# 6. Redémarrage de l'application
echo ""
echo "▶️  Étape 6/6 : Redémarrage de l'application..."
ssh $SYNOLOGY_SSH "cd ${DEPLOY_PATH} && bash start_recette.sh"

# Vérification
echo ""
echo "🔍 Vérification du démarrage..."
sleep 3
ssh $SYNOLOGY_SSH "ps aux | grep '[u]vicorn'" > /dev/null && echo "✅ Application démarrée avec succès"

# Nettoyage local
rm /tmp/recette_v2_7_deploy.tar.gz

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Déploiement Version 2.7 terminé !"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 URL: http://192.168.1.14:8000"
echo "📍 URL publique: http://recipe.e2pc.fr"
echo ""
echo "✨ Nouvelles fonctionnalités:"
echo ""
echo "🔧 MAINTENANCE DU CATALOGUE - DÉTECTION ET FUSION DES DOUBLONS:"
echo "   • Nouvelle page: /ingredient-catalog/maintenance"
echo "   • Bouton 'Maintenance' orange dans le catalogue"
echo "   • Détection automatique des doublons via 3 règles:"
echo "     - Règle A: Même nom normalisé (Oignon = oignon)"
echo "     - Règle B: Levenshtein ≤ 1 (noms > 5 chars)"
echo "     - Règle C: Même nom sans articles (cuisse de poulet = cuisse poulet)"
echo "   • Sélection du 'Prix de référence' (radio bouton par membre)"
echo "   • L'utilisateur choisit quel ingrédient garde ses prix"
echo "   • Nom canonique éditable (FR + JP)"
echo "   • Fusion atomique: mise à jour des recettes + catalogue + conversions"
echo "   • Affichage des prix avec quantité/unité (EUR: 3/1kg)"
echo ""
echo "📱 RESPONSIVE MOBILE - PAGE RECETTE DÉTAIL:"
echo "   • Tableau ingrédients: colonne Commentaire masquée sur mobile"
echo "   • Notes affichées sous le nom de l'ingrédient sur mobile"
echo "   • Section conversion: layout 2 lignes sur mobile"
echo "   • Modal édition: padding réduit, grille 1 colonne"
echo "   • Édition ingrédients: layout empilé sur mobile (nom, qté+unité, notes)"
echo "   • Boutons d'action: pleine largeur sur mobile, empilés verticalement"
echo ""
echo "📁 FICHIERS MODIFIÉS/CRÉÉS:"
echo "   • app/models/db_catalog_maintenance.py (NOUVEAU - 385 lignes)"
echo "   • app/templates/ingredient_catalog_maintenance.html (NOUVEAU - 327 lignes)"
echo "   • app/models/__init__.py (ajout exports maintenance)"
echo "   • app/routes/catalog_routes.py (2 routes: GET + POST maintenance)"
echo "   • app/templates/ingredient_catalog.html (bouton Maintenance)"
echo "   • app/templates/recipe_detail.html (responsive mobile)"
echo ""
echo "📊 STATISTIQUES:"
echo "   • 2 fichiers créés, 4 fichiers modifiés"
echo "   • +712 lignes (nouveaux fichiers)"
echo "   • ~260 lignes modifiées (fichiers existants)"
echo ""
echo "✅ TESTS À EFFECTUER:"
echo "   1. 🔧 Maintenance du catalogue:"
echo "      • Aller sur /ingredient-catalog?lang=fr"
echo "      • Cliquer sur le bouton orange 'Maintenance'"
echo "      • Vérifier que les groupes de doublons s'affichent"
echo "      • Sélectionner un 'Prix ref.' différent et voir le résumé changer"
echo "      • Modifier le nom canonique si nécessaire"
echo "      • Cliquer 'Fusionner' et confirmer"
echo "      • Vérifier que le groupe disparaît après fusion"
echo "      • Vérifier dans le catalogue que les doublons sont supprimés"
echo "      • Vérifier dans les recettes que le nom est mis à jour"
echo ""
echo "   2. 📱 Responsive mobile:"
echo "      • Ouvrir une recette sur smartphone"
echo "      • Vérifier que le tableau ingrédients est lisible"
echo "      • Vérifier que le modal d'édition est utilisable"
echo "      • Vérifier les boutons d'action en pleine largeur"
echo ""
echo "🔄 EN CAS DE PROBLÈME:"
echo "   1. Vérifier les logs: tail -f ~/recette/logs/recette.log"
echo "   2. Restaurer la base: cp backups/recette_pre_v2_7_*.sqlite3 data/recette.sqlite3"
echo "   3. Redémarrer: cd ~/recette && bash stop_recette.sh && bash start_recette.sh"
echo ""
