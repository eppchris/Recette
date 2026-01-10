#!/bin/bash
# Script pour lancer l'application en mode test mobile
# Permet l'accès depuis un smartphone sur le même réseau WiFi

echo "🔍 Détection de votre adresse IP locale..."
IP_ADDRESS=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)

if [ -z "$IP_ADDRESS" ]; then
    echo "❌ Impossible de détecter l'adresse IP locale"
    exit 1
fi

echo "✅ Adresse IP détectée: $IP_ADDRESS"
echo ""
echo "📱 Instructions pour tester sur votre smartphone:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Assurez-vous que votre smartphone et cet ordinateur"
echo "   sont sur le MÊME réseau WiFi"
echo ""
echo "2. Sur votre smartphone, ouvrez le navigateur et accédez à:"
echo ""
echo "   👉  http://$IP_ADDRESS:8000"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Conseils de test:"
echo "   • Testez le menu hamburger (navigation mobile)"
echo "   • Vérifiez que tous les tableaux sont scrollables"
echo "   • Testez les formulaires et la saisie tactile"
echo "   • Vérifiez le mode sombre/clair"
echo "   • Testez la rotation portrait/paysage"
echo ""
echo "🚀 Démarrage du serveur sur 0.0.0.0:8000..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Activer l'environnement virtuel si présent
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Lancer le serveur accessible depuis le réseau local
# 0.0.0.0 permet l'accès depuis d'autres machines du réseau
export HOST=0.0.0.0
export PORT=8000
python main.py
