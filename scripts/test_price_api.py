#!/usr/bin/env python3
"""
Script de TEST pour les APIs de prix externes
N'AFFECTE PAS la base de données
Utilisation: python3 test_price_api.py
"""

import sys
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.price_service import PriceService


def test_price_search():
    """Teste la recherche de prix sans modifier la base"""

    print("🧪 Test de recherche de prix (MODE READ-ONLY)\n")

    # Vérifier les clés API
    rakuten_key = os.getenv('RAKUTEN_APP_ID')
    print(f"📊 Configuration:")
    print(f"  Rakuten API Key: {'✅ Configurée' if rakuten_key else '❌ Non configurée'}")
    print()

    # Créer le service (APIs externes activées)
    print("🔧 Initialisation du service de prix...")
    service = PriceService(enable_external=True)
    print()

    # Liste d'ingrédients à tester
    test_ingredients = [
        ("Riz", "kg", "jp"),      # 米 (kome)
        ("Sucre", "kg", "fr"),
        ("Tomate", "kg", "fr"),
        ("醤油", "ml", "jp"),     # Sauce soja
    ]

    print("=" * 80)
    print("TESTS DE RECHERCHE")
    print("=" * 80)

    for ingredient, unit, lang in test_ingredients:
        print(f"\n🔍 Recherche: {ingredient} ({unit}) - Langue: {lang}")
        print("-" * 80)

        # Recherche avec toutes les sources
        results = service.get_all_results(ingredient, unit, lang)

        if results:
            print(f"✅ {len(results)} résultat(s) trouvé(s):\n")
            for i, result in enumerate(results, 1):
                print(f"  [{i}] Source: {result.source}")
                print(f"      Prix: {result.price_eur}€ / {result.price_jpy}¥")
                print(f"      Unité: {result.unit} (qty: {result.quantity})")
                print(f"      Confiance: {result.confidence * 100:.0f}%")
                if result.product_url:
                    print(f"      URL: {result.product_url}")
                if result.notes:
                    print(f"      Notes: {result.notes}")
                print()
        else:
            print("❌ Aucun résultat trouvé")

        print("-" * 80)

    print("\n" + "=" * 80)
    print("✅ Tests terminés - AUCUNE modification en base de données")
    print("=" * 80)


def show_instructions():
    """Affiche les instructions pour configurer les APIs"""

    print("\n📖 INSTRUCTIONS DE CONFIGURATION\n")

    print("1️⃣  Rakuten API (Japon):")
    print("   - Créer un compte: https://webservice.rakuten.co.jp/app/create")
    print("   - Obtenir une Application ID (gratuit)")
    print("   - Ajouter dans .env: RAKUTEN_APP_ID=votre_app_id")
    print()

    print("2️⃣  Open Food Facts (France):")
    print("   - Pas de configuration nécessaire (API gratuite)")
    print("   - Fonctionne automatiquement")
    print()

    print("3️⃣  Base de données locale:")
    print("   - Toujours active (fallback)")
    print("   - Utilise les prix déjà saisis")
    print()


if __name__ == "__main__":
    print("🤖 Test des APIs de prix externes\n")

    # Afficher les instructions
    show_instructions()

    # Demander confirmation
    response = input("Lancer les tests ? (o/n): ").lower()

    if response == 'o':
        test_price_search()
    else:
        print("❌ Tests annulés")
