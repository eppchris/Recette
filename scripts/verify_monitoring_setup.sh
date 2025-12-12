#!/bin/bash
# Script de vérification de l'installation du monitoring de performance
# Usage: ./scripts/verify_monitoring_setup.sh

set -e

DB_PATH="data/recette.sqlite3"
SUCCESS_COUNT=0
ERROR_COUNT=0
WARNING_COUNT=0

echo "=================================="
echo "🔍 Vérification Monitoring V1.9"
echo "=================================="
echo ""

# Fonction pour afficher les résultats
check_pass() {
    echo "✅ $1"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
}

check_fail() {
    echo "❌ $1"
    ERROR_COUNT=$((ERROR_COUNT + 1))
}

check_warn() {
    echo "⚠️  $1"
    WARNING_COUNT=$((WARNING_COUNT + 1))
}

# 1. Vérifier les fichiers Python
echo "📦 Vérification des fichiers Python..."
echo ""

if [ -f "app/middleware/access_logger.py" ]; then
    if grep -q "response_size_bytes" app/middleware/access_logger.py; then
        check_pass "Middleware capture la taille des réponses"
    else
        check_fail "Middleware ne capture pas la taille des réponses"
    fi
else
    check_fail "Fichier app/middleware/access_logger.py manquant"
fi

if [ -f "app/models/db_logging.py" ]; then
    if grep -q "log_client_performance" app/models/db_logging.py; then
        check_pass "Fonction log_client_performance existe"
    else
        check_fail "Fonction log_client_performance manquante"
    fi
else
    check_fail "Fichier app/models/db_logging.py manquant"
fi

if [ -f "app/routes/monitoring_routes.py" ]; then
    check_pass "Router monitoring existe"
else
    check_fail "Fichier app/routes/monitoring_routes.py manquant"
fi

if grep -q "monitoring_routes" main.py; then
    if grep -q "app.include_router(monitoring_router)" main.py; then
        check_pass "Main.py importe et enregistre monitoring_routes"
    else
        check_warn "Main.py importe monitoring_routes mais ne l'enregistre pas"
    fi
else
    check_fail "Main.py n'importe pas monitoring_routes"
fi

echo ""

# 2. Vérifier les fichiers JavaScript
echo "📜 Vérification des fichiers JavaScript..."
echo ""

if [ -f "app/static/js/performance_monitor.js" ]; then
    if grep -q "window.performance.timing" app/static/js/performance_monitor.js; then
        check_pass "Script performance_monitor.js existe et utilise l'API"
    else
        check_warn "Script existe mais n'utilise pas l'API correctement"
    fi
else
    check_fail "Fichier app/static/js/performance_monitor.js manquant"
fi

if [ -f "app/templates/base.html" ]; then
    if grep -q "performance_monitor.js" app/templates/base.html; then
        check_pass "base.html inclut performance_monitor.js"
    else
        check_fail "base.html n'inclut pas performance_monitor.js"
    fi
else
    check_fail "Fichier app/templates/base.html manquant"
fi

echo ""

# 3. Vérifier les templates
echo "🎨 Vérification des templates..."
echo ""

if [ -f "app/templates/access_logs.html" ]; then
    if grep -q "Taille (KB)" app/templates/access_logs.html; then
        check_pass "Template access_logs.html affiche la taille"
    else
        check_fail "Template access_logs.html n'affiche pas la taille"
    fi

    if grep -q "Performance Client vs Serveur" app/templates/access_logs.html; then
        check_pass "Template access_logs.html affiche perf client/serveur"
    else
        check_fail "Template access_logs.html n'affiche pas perf client/serveur"
    fi
else
    check_fail "Fichier app/templates/access_logs.html manquant"
fi

echo ""

# 4. Vérifier les migrations
echo "📊 Vérification des fichiers de migration..."
echo ""

if [ -f "migrations/add_response_size_to_access_log.sql" ]; then
    check_pass "Migration add_response_size_to_access_log.sql existe"
else
    check_fail "Migration add_response_size_to_access_log.sql manquante"
fi

if [ -f "migrations/add_client_performance_log.sql" ]; then
    check_pass "Migration add_client_performance_log.sql existe"
else
    check_fail "Migration add_client_performance_log.sql manquante"
fi

echo ""

# 5. Vérifier la base de données
echo "🗄️  Vérification de la base de données..."
echo ""

if [ ! -f "$DB_PATH" ]; then
    check_fail "Base de données $DB_PATH n'existe pas"
    echo ""
    echo "⚠️  Impossible de continuer les vérifications de la base de données"
else
    # Vérifier la colonne response_size_bytes
    if sqlite3 "$DB_PATH" "PRAGMA table_info(access_log);" | grep -q "response_size_bytes"; then
        check_pass "Colonne response_size_bytes existe dans access_log"
    else
        check_fail "Colonne response_size_bytes manquante dans access_log"
        echo "   💡 Exécuter: sqlite3 $DB_PATH \"ALTER TABLE access_log ADD COLUMN response_size_bytes INTEGER;\""
    fi

    # Vérifier la table client_performance_log
    if sqlite3 "$DB_PATH" ".tables" | grep -q "client_performance_log"; then
        check_pass "Table client_performance_log existe"

        # Vérifier les colonnes de la table
        if sqlite3 "$DB_PATH" "PRAGMA table_info(client_performance_log);" | grep -q "network_time"; then
            check_pass "Table client_performance_log a les bonnes colonnes"
        else
            check_warn "Table client_performance_log existe mais colonnes incorrectes"
        fi
    else
        check_fail "Table client_performance_log manquante"
        echo "   💡 Exécuter: sqlite3 $DB_PATH < migrations/add_client_performance_log.sql"
    fi

    # Vérifier la vue v_popular_pages_24h
    if sqlite3 "$DB_PATH" "SELECT sql FROM sqlite_master WHERE type='view' AND name='v_popular_pages_24h';" | grep -q "avg_response_size"; then
        check_pass "Vue v_popular_pages_24h inclut avg_response_size"
    else
        check_warn "Vue v_popular_pages_24h n'inclut pas avg_response_size"
        echo "   💡 Exécuter la migration 3 pour mettre à jour la vue"
    fi

    # Vérifier la vue v_client_performance_24h
    if sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='view' AND name='v_client_performance_24h';" | grep -q "v_client_performance_24h"; then
        check_pass "Vue v_client_performance_24h existe"
    else
        check_warn "Vue v_client_performance_24h manquante (optionnelle)"
    fi
fi

echo ""

# 6. Vérifier la documentation
echo "📚 Vérification de la documentation..."
echo ""

if [ -f "LIVRAISON_V1.8_MONITORING_PERFORMANCE.md" ]; then
    check_pass "Document de livraison existe"
else
    check_warn "Document de livraison manquant"
fi

if [ -f "docs/MONITORING_PERFORMANCE.md" ]; then
    check_pass "Documentation technique existe"
else
    check_warn "Documentation technique manquante"
fi

if [ -f "docs/USER_GUIDE_MONITORING.md" ]; then
    check_pass "Guide utilisateur existe"
else
    check_warn "Guide utilisateur manquant"
fi

if [ -f "RELEASE_NOTES_V1.9.md" ]; then
    check_pass "Release notes existent"
else
    check_warn "Release notes manquantes"
fi

echo ""

# 7. Vérifier le script de déploiement
echo "🚀 Vérification du script de déploiement..."
echo ""

if [ -f "deploy/deploy_synology_V1_9_monitoring.sh" ]; then
    if [ -x "deploy/deploy_synology_V1_9_monitoring.sh" ]; then
        check_pass "Script de déploiement existe et est exécutable"
    else
        check_warn "Script de déploiement existe mais n'est pas exécutable"
        echo "   💡 Exécuter: chmod +x deploy/deploy_synology_V1_9_monitoring.sh"
    fi
else
    check_fail "Script de déploiement manquant"
fi

echo ""

# Résumé
echo "=================================="
echo "📊 Résumé de la vérification"
echo "=================================="
echo ""
echo "✅ Succès   : $SUCCESS_COUNT"
echo "⚠️  Warnings : $WARNING_COUNT"
echo "❌ Erreurs  : $ERROR_COUNT"
echo ""

if [ $ERROR_COUNT -eq 0 ] && [ $WARNING_COUNT -eq 0 ]; then
    echo "🎉 Tout est parfait ! Prêt pour le déploiement."
    exit 0
elif [ $ERROR_COUNT -eq 0 ]; then
    echo "⚠️  Il y a quelques warnings, mais vous pouvez déployer."
    echo "   Les warnings concernent généralement de la documentation optionnelle."
    exit 0
else
    echo "❌ Il y a des erreurs à corriger avant le déploiement."
    echo ""
    echo "💡 Suggestions :"
    echo "   1. Vérifier que toutes les migrations ont été appliquées"
    echo "   2. Vérifier que tous les fichiers sont présents"
    echo "   3. Vérifier que main.py importe bien monitoring_routes"
    echo ""
    exit 1
fi
