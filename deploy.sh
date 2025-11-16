#!/bin/bash

# Script de déploiement Recette - Version 1.2
# Ce script synchronise les fichiers locaux vers le serveur de production

set -e  # Arrêter en cas d'erreur

echo "🚀 Déploiement de Recette v1.2 vers la production"
echo "================================================="

# Configuration
PROD_USER="christianepp"
PROD_HOST="192.168.1.95"
PROD_PATH="/volume1/homes/christianepp/recette"
LOCAL_PATH="."

# Vérifier la connexion SSH
echo "📡 Vérification de la connexion au serveur..."
if ! ssh -q $PROD_USER@$PROD_HOST exit; then
    echo "❌ Impossible de se connecter au serveur $PROD_HOST"
    exit 1
fi
echo "✅ Connexion au serveur OK"

# Arrêter l'application en production
echo "⏸️  Arrêt de l'application..."
ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && ./stop_recette.sh" || echo "⚠️  L'application n'était peut-être pas démarrée"

# Synchroniser les fichiers (exclure certains dossiers)
echo "📦 Synchronisation des fichiers..."
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='venv' \
    --exclude='.env' \
    --exclude='data/*.sqlite3' \
    --exclude='data/*.sqlite3-wal' \
    --exclude='data/*.sqlite3-shm' \
    --exclude='logs/*.log' \
    --exclude='.DS_Store' \
    --exclude='deploy.sh' \
    $LOCAL_PATH/ $PROD_USER@$PROD_HOST:$PROD_PATH/

echo "✅ Fichiers synchronisés"

# Installer/mettre à jour les dépendances
echo "📚 Mise à jour des dépendances..."
ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && source venv/bin/activate && pip install -r requirements.txt -q"
echo "✅ Dépendances à jour"

# Redémarrer l'application
echo "▶️  Démarrage de l'application..."
ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && ./start_recette.sh"

# Attendre un peu pour que l'application démarre
sleep 3

# Vérifier que l'application est bien démarrée
echo "🔍 Vérification du démarrage..."
if ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && test -f recette.pid && kill -0 \$(cat recette.pid) 2>/dev/null"; then
    echo "✅ Application démarrée avec succès!"
    echo ""
    echo "🎉 Déploiement terminé!"
    echo "📍 URL: http://$PROD_HOST:8000"
    echo ""
    echo "📋 Nouvelles fonctionnalités V1.2:"
    echo "   • Filtre par type de recette dans la liste"
    echo "   • Bouton 'Ajouter toutes les recettes' par type d'événement"
    echo "   • Traduction automatique des types de recette"
    echo "   • Amélioration de la robustesse des traductions (API Groq)"
    echo "   • Format d'impression optimisé pour les listes de courses"
    echo "   • Affichage des recettes sources dans la liste de courses"
    echo "   • Auto-régénération de la liste en cas de changement de langue"
else
    echo "❌ Erreur: L'application ne semble pas démarrée"
    echo "Consultez les logs: ssh $PROD_USER@$PROD_HOST 'tail -50 $PROD_PATH/logs/recette.log'"
    exit 1
fi
