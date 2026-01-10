#!/usr/bin/env python3
"""
Test du système d'authentification
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.models import authenticate_user, create_user, get_user_by_username

def test_auth():
    """Test l'authentification"""
    print("\n" + "="*80)
    print("TEST DU SYSTÈME D'AUTHENTIFICATION")
    print("="*80)

    # Test 1: Login avec l'admin existant
    print("\n1️⃣  Test de connexion avec admin existant")
    user = authenticate_user("admin", "admin123")
    if user:
        print(f"   ✅ Connexion réussie : {user['username']} (ID: {user['id']})")
        print(f"   📧 Email : {user['email']}")
        print(f"   👤 Nom : {user['display_name']}")
        print(f"   ⭐ Admin : {user['is_admin']}")
    else:
        print("   ❌ Échec de connexion")
        return False

    # Test 2: Login avec email
    print("\n2️⃣  Test de connexion avec email")
    user = authenticate_user("admin@recette.local", "admin123")
    if user:
        print(f"   ✅ Connexion réussie avec email : {user['username']}")
    else:
        print("   ❌ Échec de connexion avec email")
        return False

    # Test 3: Login avec mauvais mot de passe
    print("\n3️⃣  Test de connexion avec mauvais mot de passe")
    user = authenticate_user("admin", "wrongpassword")
    if not user:
        print("   ✅ Connexion refusée correctement")
    else:
        print("   ❌ ERREUR : Connexion acceptée avec mauvais mot de passe !")
        return False

    # Test 4: Créer un nouvel utilisateur
    print("\n4️⃣  Test de création d'utilisateur")
    try:
        # Vérifier si l'utilisateur existe déjà
        existing = get_user_by_username("testuser")
        if existing:
            print("   ℹ️  L'utilisateur testuser existe déjà")
        else:
            user_id = create_user(
                username="testuser",
                email="test@example.com",
                password="testpass123",
                display_name="Test User",
                is_admin=False
            )
            print(f"   ✅ Utilisateur créé : ID {user_id}")

        # Test de connexion avec le nouvel utilisateur
        user = authenticate_user("testuser", "testpass123")
        if user:
            print(f"   ✅ Connexion réussie avec testuser")
        else:
            print("   ❌ Échec de connexion avec testuser")
            return False

    except ValueError as e:
        print(f"   ℹ️  Utilisateur existe déjà : {e}")

    print("\n" + "="*80)
    print("✅ TOUS LES TESTS SONT PASSÉS !")
    print("="*80)
    print("\n📝 Vous pouvez maintenant :")
    print("   • Vous connecter sur http://127.0.0.1:8000/login")
    print("   • Username: admin")
    print("   • Password: admin123")
    print("   • Ou créer un nouveau compte via /register\n")

    return True


if __name__ == "__main__":
    try:
        success = test_auth()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
