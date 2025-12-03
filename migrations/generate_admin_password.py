#!/usr/bin/env python3
"""
Script pour générer le hash du mot de passe admin avec passlib
"""
from passlib.hash import pbkdf2_sha256

# Mot de passe par défaut
password = "admin123"

# Générer le hash
password_hash = pbkdf2_sha256.hash(password)

print("Hash généré pour le mot de passe 'admin123' :")
print(password_hash)
print()
print("Copier ce hash dans le fichier migrations/add_user_system.sql")
