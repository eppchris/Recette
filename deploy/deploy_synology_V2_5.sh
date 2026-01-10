#!/bin/bash
# Script de déploiement pour Synology DS213+
# Version 2.5 - Gestion tickets de caisse, adaptation convives et améliorations mobile
# Usage: ./deploy_synology_V2_5.sh

SYNOLOGY_USER="admin"
SYNOLOGY_HOST="192.168.1.14"
DEPLOY_PATH="recette"
SYNOLOGY_SSH="${SYNOLOGY_USER}@${SYNOLOGY_HOST}"

echo "🚀 Déploiement de Recette Version 2.5 sur Synology..."
echo "📦 Nouvelles fonctionnalités majeures:"
echo "   🎫 Système de tickets de caisse avec OCR (Gemini Vision API)"
echo "   👥 Adaptation automatique au nombre de convives"
echo "   📱 Améliorations interface mobile (mode grille/liste)"
echo "   🐛 Corrections critiques (Jinja2, alignement catalogue)"
echo ""
echo "📍 Destination: ${DEPLOY_PATH}"
echo ""

# Vérifier que les fichiers nécessaires existent
echo "🔍 Vérification des fichiers..."
REQUIRED_FILES=(
    "requirements.txt"
    "app/models/db_receipt.py"
    "app/services/receipt_extractor.py"
    "app/services/ingredient_matcher.py"
    "app/models/db_events.py"
    "app/services/ingredient_aggregator.py"
    "migrations/008_add_receipt_tables.sql"
    "migrations/009_add_receipt_bilingual_columns.sql"
    "migrations/010_add_price_source_tracking.sql"
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
tar czf /tmp/recette_v2_5_deploy.tar.gz \
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

ARCHIVE_SIZE=$(du -h /tmp/recette_v2_5_deploy.tar.gz | cut -f1)
echo "✅ Archive créée (${ARCHIVE_SIZE})"

# 2. Transférer via SSH
echo ""
echo "🔗 Étape 2/8 : Transfert vers le NAS..."
cat /tmp/recette_v2_5_deploy.tar.gz | ssh $SYNOLOGY_SSH "cat > ${DEPLOY_PATH}/recette_v2_5_deploy.tar.gz"

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du transfert"
    rm /tmp/recette_v2_5_deploy.tar.gz
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
    BACKUP_FILE="backups/recette_pre_v2_5_$(date +%Y%m%d_%H%M%S).sqlite3"
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
tar xzf recette_v2_5_deploy.tar.gz
rm recette_v2_5_deploy.tar.gz

# Création du .env si nécessaire
[ ! -f ".env" ] && cp .env.example .env

echo "✅ Fichiers déployés"
ENDSSH

# 6. Application des migrations SQL
echo ""
echo "🗄️  Étape 6/8 : Transfert de la base de données migrée..."
echo ""
echo "⚠️  IMPORTANT : Les migrations SQL ne peuvent pas être appliquées directement sur le NAS"
echo "    à cause de la version ancienne de SQLite (< 3.25.0) qui ne supporte pas"
echo "    certaines commandes comme ALTER TABLE RENAME COLUMN."
echo ""
echo "📋 PROCÉDURE MANUELLE REQUISE :"
echo ""
echo "   1️⃣  Copier la base du NAS vers le poste local :"
echo "       scp admin@192.168.1.14:recette/data/recette.sqlite3 data/recette_nas_backup.sqlite3"
echo ""
echo "   2️⃣  Appliquer les migrations en local :"
echo "       sqlite3 data/recette_nas_backup.sqlite3 < migrations/008_add_receipt_tables.sql"
echo "       sqlite3 data/recette_nas_backup.sqlite3 < migrations/009_add_receipt_bilingual_columns.sql"
echo "       sqlite3 data/recette_nas_backup.sqlite3 < migrations/010_add_price_source_tracking.sql"
echo ""
echo "   3️⃣  Vérifier l'intégrité :"
echo "       sqlite3 data/recette_nas_backup.sqlite3 'PRAGMA integrity_check;'"
echo ""
echo "   4️⃣  Copier la base migrée vers le NAS :"
echo "       scp data/recette_nas_backup.sqlite3 admin@192.168.1.14:recette/data/recette.sqlite3"
echo ""
echo "   5️⃣  Relancer ce script pour déployer le code"
echo ""
echo "❓ Avez-vous déjà effectué la migration manuelle de la base de données ?"
echo "   (Appuyez sur Entrée pour continuer si OUI, ou Ctrl+C pour annuler)"
read -r

echo "✅ Migration de la base supposée effectuée, on continue..."

# 7. Vérification et installation des dépendances
echo ""
echo "📚 Étape 7/8 : Vérification des dépendances..."
ssh $SYNOLOGY_SSH << 'ENDSSH'
cd recette
source venv/bin/activate

# Installer toutes les dépendances depuis requirements.txt
echo "  📦 Installation des dépendances depuis requirements.txt..."
pip install --quiet -r requirements.txt

# Nouvelle dépendance pour Gemini Vision API (V2.5)
echo "  🔍 Installation de google-generativeai..."
pip install --quiet google-generativeai

echo "✅ Dépendances installées"

ENDSSH

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de l'installation des dépendances"
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
rm /tmp/recette_v2_5_deploy.tar.gz

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Déploiement Version 2.5 terminé !"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 URL: http://192.168.1.14:8000"
echo "📍 URL publique: http://recipe.e2pc.fr"
echo ""
echo "✨ Nouvelles fonctionnalités:"
echo ""
echo "🎫 SYSTÈME DE TICKETS DE CAISSE:"
echo "   • Upload de tickets (PDF/images) avec OCR Gemini Vision API"
echo "   • Extraction automatique des articles + prix"
echo "   • Traduction bidirectionnelle FR↔JP automatique"
echo "   • Matching intelligent vers le catalogue (premier mot)"
echo "   • Validation en 1 clic → mise à jour prix catalogue"
echo "   • Badge rouge 🎫 pour identifier prix issus de tickets"
echo "   • Fichiers: db_receipt.py, receipt_extractor.py, ingredient_matcher.py"
echo "   • Routes: /receipt-list, /receipt-upload, /receipt-review"
echo ""
echo "👥 ADAPTATION AUTOMATIQUE AUX CONVIVES:"
echo "   • Calcul auto: (attendees / servings_default) × manual_multiplier"
echo "   • Exemple: événement 12 convives + recette 4 portions = quantités × 3"
echo "   • Arrondissement supérieur pour unités indivisibles (2.3 œufs → 3 œufs)"
echo "   • Précision décimale conservée pour g, kg, ml, L"
echo "   • Fichier: db_events.py (calcul multiplicateur)"
echo "   • Fichier: ingredient_aggregator.py (arrondissement math.ceil)"
echo ""
echo "📱 AMÉLIORATIONS INTERFACE MOBILE:"
echo "   • Mode grille/liste pour les recettes (déjà présent en V2.4)"
echo "   • Préférence sauvegardée dans localStorage"
echo "   • Tableau compact optimisé smartphones"
echo "   • Fichier: recipes_list.html"
echo ""
echo "🐛 CORRECTIONS CRITIQUES:"
echo "   • Fix erreurs Jinja2/Alpine.js dans le catalogue (plantages résolus)"
echo "   • Fix alignement colonnes en mode édition (suppression colspan)"
echo "   • Badge prix ticket 🎫 en rouge vif au lieu de vert"
echo "   • Simplification interface tickets (suppression colonne Statut)"
echo "   • Fichier: ingredient_catalog.html (restructuration tableau)"
echo "   • Fichier: receipt_list.html"
echo ""
echo "🗄️  MODIFICATIONS BASE DE DONNÉES:"
echo "   • Migration 008: Tables receipt_upload_history, receipt_item_match"
echo "   • Migration 009: Colonnes bilingues (receipt_item_text_original, receipt_item_text_fr)"
echo "   • Migration 010: Tracking source prix (price_eur_source, price_eur_last_receipt_date)"
echo "   • Colonnes ajoutées: price_jpy_source, price_jpy_last_receipt_date"
echo ""
echo "📊 STATISTIQUES:"
echo "   • 32 fichiers modifiés"
echo "   • +3 615 lignes ajoutées"
echo "   • -309 lignes supprimées"
echo "   • 13 nouveaux fichiers créés"
echo "   • 3 migrations SQL appliquées"
echo ""
echo "✅ TESTS À EFFECTUER:"
echo "   1. 🎫 Tickets de caisse:"
echo "      • Aller sur /receipt-list"
echo "      • Uploader un ticket (PDF ou image)"
echo "      • Vérifier l'extraction OCR et traduction"
echo "      • Valider un article et vérifier la mise à jour du catalogue"
echo "      • Vérifier le badge 🎫 rouge dans /ingredient-catalog"
echo ""
echo "   2. 👥 Adaptation convives:"
echo "      • Créer un événement avec 12 convives"
echo "      • Ajouter une recette pour 4 personnes"
echo "      • Générer la liste de courses"
echo "      • Vérifier que les quantités sont × 3"
echo "      • Vérifier arrondissement supérieur (ex: œufs)"
echo ""
echo "   3. 🎨 Interface:"
echo "      • Basculer mode grille/liste sur /recipes"
echo "      • Éditer un ingrédient dans /ingredient-catalog"
echo "      • Vérifier l'alignement des colonnes"
echo "      • Tester sur mobile/tablette"
echo ""
echo "⚠️  CONFIGURATION REQUISE:"
echo "   • Ajouter GEMINI_API_KEY dans le fichier .env"
echo "   • Obtenir la clé sur: https://makersuite.google.com/app/apikey"
echo "   • Format: GEMINI_API_KEY=AIza..."
echo ""
echo "🔄 EN CAS DE PROBLÈME:"
echo "   1. Vérifier les logs: tail -f ~/recette/logs/recette.log"
echo "   2. Restaurer la base: cp backups/recette_pre_v2_5_*.sqlite3 data/recette.sqlite3"
echo "   3. Redémarrer: cd ~/recette && bash stop_recette.sh && bash start_recette.sh"
echo ""
echo "💡 COMMIT GITHUB:"
echo "   • Hash: 9fe52b5"
echo "   • Message: feat: Gestion tickets de caisse, adaptation convives et améliorations mobile"
echo ""
echo "📚 DOCUMENTATION:"
echo "   • Tests: tests/test_event_attendees_adaptation.py"
echo "   • Notes: TESTS_MOBILE.md, data/README.md"
echo ""
