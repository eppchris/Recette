"""
Module de gestion des utilisateurs et authentification
"""
from passlib.hash import pbkdf2_sha256
from datetime import datetime
from .db_core import get_db


def hash_password(password: str) -> str:
    """
    Hash un mot de passe avec PBKDF2-SHA256

    Args:
        password: Mot de passe en clair

    Returns:
        Hash du mot de passe
    """
    return pbkdf2_sha256.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Vérifie un mot de passe contre son hash
    Compatible avec les anciens hash bcrypt ET les nouveaux hash PBKDF2

    Args:
        password: Mot de passe en clair
        password_hash: Hash stocké (bcrypt ou pbkdf2)

    Returns:
        True si le mot de passe correspond
    """
    # Vérifier si c'est un hash bcrypt (commence par $2b$)
    if password_hash.startswith('$2b$') or password_hash.startswith('$2a$'):
        try:
            import bcrypt
            password_bytes = password.encode('utf-8')
            hash_bytes = password_hash.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except ImportError:
            # Si bcrypt n'est pas disponible, impossible de vérifier les anciens hash
            # L'utilisateur devra réinitialiser son mot de passe
            return False

    # Sinon, utiliser pbkdf2_sha256
    return pbkdf2_sha256.verify(password, password_hash)


def create_user(username: str, email: str, password: str, display_name: str = None, is_admin: bool = False) -> int:
    """
    Crée un nouvel utilisateur

    Args:
        username: Nom d'utilisateur unique
        email: Email unique
        password: Mot de passe en clair (sera hashé)
        display_name: Nom d'affichage (optionnel)
        is_admin: Si l'utilisateur est admin

    Returns:
        ID du nouvel utilisateur

    Raises:
        ValueError: Si l'username ou l'email existe déjà
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Vérifier si l'username existe déjà
        cursor.execute("SELECT id FROM user WHERE username = ?", (username,))
        if cursor.fetchone():
            raise ValueError(f"Le nom d'utilisateur '{username}' existe déjà")

        # Vérifier si l'email existe déjà
        cursor.execute("SELECT id FROM user WHERE email = ?", (email,))
        if cursor.fetchone():
            raise ValueError(f"L'email '{email}' existe déjà")

        # Hash du mot de passe
        password_hash = hash_password(password)

        # Créer l'utilisateur
        cursor.execute("""
            INSERT INTO user (username, email, password_hash, display_name, is_admin)
            VALUES (?, ?, ?, ?, ?)
        """, (username, email, password_hash, display_name or username, 1 if is_admin else 0))

        conn.commit()
        return cursor.lastrowid


def get_user_by_username(username: str):
    """
    Récupère un utilisateur par son nom d'utilisateur

    Args:
        username: Nom d'utilisateur

    Returns:
        Dict avec les infos de l'utilisateur ou None
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, email, password_hash, display_name, is_active, is_admin, created_at, last_login
            FROM user
            WHERE username = ?
        """, (username,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_email(email: str):
    """
    Récupère un utilisateur par son email

    Args:
        email: Email de l'utilisateur

    Returns:
        Dict avec les infos de l'utilisateur ou None
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, email, password_hash, display_name, is_active, is_admin, created_at, last_login
            FROM user
            WHERE email = ?
        """, (email,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int):
    """
    Récupère un utilisateur par son ID

    Args:
        user_id: ID de l'utilisateur

    Returns:
        Dict avec les infos de l'utilisateur ou None
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, email, display_name, is_active, is_admin, created_at, last_login
            FROM user
            WHERE id = ?
        """, (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def authenticate_user(username_or_email: str, password: str):
    """
    Authentifie un utilisateur

    Args:
        username_or_email: Nom d'utilisateur ou email
        password: Mot de passe en clair

    Returns:
        Dict avec les infos de l'utilisateur si authentifié, None sinon
    """
    # Essayer d'abord par username
    user = get_user_by_username(username_or_email)

    # Si pas trouvé, essayer par email
    if not user:
        user = get_user_by_email(username_or_email)

    # Si toujours pas trouvé ou inactif
    if not user or not user['is_active']:
        return None

    # Vérifier le mot de passe
    if not verify_password(password, user['password_hash']):
        return None

    # Mettre à jour la date de dernière connexion
    update_last_login(user['id'])

    # Retourner l'utilisateur sans le hash du mot de passe
    user_info = {k: v for k, v in user.items() if k != 'password_hash'}
    return user_info


def update_last_login(user_id: int):
    """
    Met à jour la date de dernière connexion

    Args:
        user_id: ID de l'utilisateur
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE user
            SET last_login = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id,))
        conn.commit()


def list_users():
    """
    Liste tous les utilisateurs

    Returns:
        Liste des utilisateurs (sans les mots de passe)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, email, display_name, is_active, is_admin, created_at, last_login
            FROM user
            ORDER BY username
        """)
        return [dict(row) for row in cursor.fetchall()]


def update_user_password(user_id: int, new_password: str):
    """
    Change le mot de passe d'un utilisateur

    Args:
        user_id: ID de l'utilisateur
        new_password: Nouveau mot de passe en clair
    """
    password_hash = hash_password(new_password)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE user
            SET password_hash = ?
            WHERE id = ?
        """, (password_hash, user_id))
        conn.commit()


def deactivate_user(user_id: int):
    """
    Désactive un utilisateur (soft delete)

    Args:
        user_id: ID de l'utilisateur
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE user
            SET is_active = 0
            WHERE id = ?
        """, (user_id,))
        conn.commit()


def activate_user(user_id: int):
    """
    Réactive un utilisateur

    Args:
        user_id: ID de l'utilisateur
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE user
            SET is_active = 1
            WHERE id = ?
        """, (user_id,))
        conn.commit()
