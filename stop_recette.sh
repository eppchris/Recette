#!/bin/bash
# Script d'arrêt pour Recette sur Synology DS213+
# À placer dans /volume1/web/recette/stop_recette.sh

APP_DIR="/volume1/web/recette"
PID_FILE="$APP_DIR/recette.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)

    if ps -p $PID > /dev/null 2>&1; then
        echo "🛑 Arrêt de Recette (PID: $PID)..."
        kill $PID
        rm $PID_FILE
        echo "✅ Recette arrêtée"
    else
        echo "⚠️  Processus $PID non trouvé"
        rm $PID_FILE
    fi
else
    echo "⚠️  Fichier PID non trouvé. Recherche du processus..."
    pkill -f "uvicorn main_prod:app"
    echo "✅ Processus arrêté"
fi
