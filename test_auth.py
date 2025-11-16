"""Script de test rapide pour vérifier la configuration de l'authentification"""

import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

print("=== Test de Configuration d'Authentification ===\n")

# Vérifier les variables d'environnement
require_password = os.getenv("REQUIRE_PASSWORD", "False")
shared_password = os.getenv("SHARED_PASSWORD", "")
secret_key = os.getenv("SECRET_KEY", "")

print(f"REQUIRE_PASSWORD: {require_password}")
print(f"SHARED_PASSWORD: {'***' + shared_password[-4:] if shared_password else 'NON DÉFINI'}")
print(f"SECRET_KEY: {'***' + secret_key[-8:] if secret_key else 'NON DÉFINI'}")

print("\n=== Résultat ===\n")

if require_password.lower() == "true":
    print("✅ Protection par mot de passe ACTIVÉE")

    if not shared_password:
        print("❌ ERREUR: SHARED_PASSWORD n'est pas défini dans .env")
    elif len(shared_password) < 8:
        print("⚠️  ATTENTION: Le mot de passe est trop court (recommandé: 8+ caractères)")
    else:
        print(f"✅ Mot de passe défini ({len(shared_password)} caractères)")

    if not secret_key:
        print("❌ ERREUR: SECRET_KEY n'est pas définie dans .env")
    elif secret_key in ["dev-secret-key-change-me", "dev-secret-key-for-sessions"]:
        print("⚠️  ATTENTION: Vous utilisez une clé secrète par défaut (changez-la en production!)")
    else:
        print(f"✅ Clé secrète définie ({len(secret_key)} caractères)")

else:
    print("⚠️  Protection par mot de passe DÉSACTIVÉE")
    print("   → Pour activer: REQUIRE_PASSWORD=True dans .env")

print("\n=== Imports Python ===\n")

try:
    from starlette.middleware.sessions import SessionMiddleware
    print("✅ starlette.middleware.sessions importé")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")

try:
    from app.middleware.auth import AuthMiddleware, check_password
    print("✅ app.middleware.auth importé")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")

try:
    from app.routes.auth_routes import router
    print("✅ app.routes.auth_routes importé")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")

print("\n=== Test de vérification de mot de passe ===\n")

try:
    from app.middleware.auth import check_password

    test_password = "RecipeTakachan2026"
    result = check_password(test_password, shared_password)

    if result:
        print(f"✅ Fonction check_password fonctionne correctement")
    else:
        print(f"⚠️  Le mot de passe de test ne correspond pas à SHARED_PASSWORD")

except Exception as e:
    print(f"❌ Erreur lors du test: {e}")

print("\n=== Fin du test ===\n")
