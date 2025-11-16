#!/bin/bash
# Script de démarrage pour Recette sur Synology DS213+

# Chemin de base de l'application
APP_DIR="$HOME/recette"

# Activer l'environnement virtuel
source $APP_DIR/venv/bin/activate

# Démarrer l'application (sans --workers pour compatibilité)
cd $APP_DIR
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 >> logs/recette.log 2>&1 &

# Sauvegarder le PID
echo $! > $APP_DIR/recette.pid

echo "✅ Recette démarrée (PID: $(cat $APP_DIR/recette.pid))"
