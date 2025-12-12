"""
Module de gestion des participants et groupes
"""
from .db_core import get_db


# ============================================================================
# Gestion des participants
# ============================================================================

def list_participants():
    """
    Liste tous les participants triés par nom

    Returns:
        Liste des participants avec leurs informations
    """
    with get_db() as con:
        sql = """
            SELECT id, nom, prenom, role, telephone, email, adresse, created_at, updated_at
            FROM participant
            ORDER BY nom, prenom
        """
        rows = con.execute(sql).fetchall()
        return [dict(row) for row in rows]


def get_participant_by_id(participant_id: int):
    """
    Récupère un participant par son ID

    Args:
        participant_id: ID du participant

    Returns:
        Dict avec les informations du participant ou None si non trouvé
    """
    with get_db() as con:
        sql = """
            SELECT id, nom, prenom, role, telephone, email, adresse, created_at, updated_at
            FROM participant
            WHERE id = ?
        """
        result = con.execute(sql, (participant_id,)).fetchone()
        return dict(result) if result else None


def create_participant(nom: str, prenom: str = None, role: str = None,
                      telephone: str = None, email: str = None, adresse: str = None):
    """
    Crée un nouveau participant

    Args:
        nom: Nom du participant (obligatoire)
        prenom: Prénom (optionnel)
        role: Rôle texte libre (optionnel)
        telephone: Téléphone (optionnel)
        email: Email (optionnel)
        adresse: Adresse (optionnel)

    Returns:
        ID du nouveau participant créé
    """
    with get_db() as con:
        sql = """
            INSERT INTO participant (nom, prenom, role, telephone, email, adresse)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor = con.execute(sql, (nom, prenom, role, telephone, email, adresse))
        return cursor.lastrowid


def update_participant(participant_id: int, nom: str = None, prenom: str = None,
                      role: str = None, telephone: str = None, email: str = None,
                      adresse: str = None):
    """
    Met à jour un participant existant

    Args:
        participant_id: ID du participant à mettre à jour
        nom: Nom (obligatoire si fourni)
        prenom: Prénom (optionnel)
        role: Rôle (optionnel)
        telephone: Téléphone (optionnel)
        email: Email (optionnel)
        adresse: Adresse (optionnel)

    Returns:
        True si la mise à jour a réussi
    """
    with get_db() as con:
        cursor = con.cursor()

        # Vérifier que le participant existe
        cursor.execute("SELECT id FROM participant WHERE id = ?", (participant_id,))
        if not cursor.fetchone():
            return False

        # Mise à jour complète (tous les champs)
        sql = """
            UPDATE participant
            SET nom = ?, prenom = ?, role = ?, telephone = ?, email = ?, adresse = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        cursor.execute(sql, (nom, prenom, role, telephone, email, adresse, participant_id))
        con.commit()
        return True


def delete_participant(participant_id: int):
    """
    Supprime un participant et toutes ses associations

    Args:
        participant_id: ID du participant à supprimer

    Returns:
        True si la suppression a réussi
    """
    with get_db() as con:
        sql = "DELETE FROM participant WHERE id = ?"
        con.execute(sql, (participant_id,))
        return True


# ============================================================================
# Gestion des groupes
# ============================================================================

def list_groups():
    """
    Liste tous les groupes avec le nombre de participants

    Returns:
        Liste des groupes avec le nombre de membres
    """
    with get_db() as con:
        sql = """
            SELECT
                pg.id,
                pg.nom,
                pg.description,
                pg.created_at,
                pg.updated_at,
                COUNT(pgm.participant_id) as member_count
            FROM participant_group pg
            LEFT JOIN participant_group_member pgm ON pgm.group_id = pg.id
            GROUP BY pg.id, pg.nom, pg.description, pg.created_at, pg.updated_at
            ORDER BY pg.nom
        """
        rows = con.execute(sql).fetchall()
        return [dict(row) for row in rows]


def get_group_by_id(group_id: int):
    """
    Récupère un groupe par son ID avec le nombre de participants

    Args:
        group_id: ID du groupe

    Returns:
        Dict avec les informations du groupe ou None si non trouvé
    """
    with get_db() as con:
        sql = """
            SELECT
                pg.id,
                pg.nom,
                pg.description,
                pg.created_at,
                pg.updated_at,
                COUNT(pgm.participant_id) as member_count
            FROM participant_group pg
            LEFT JOIN participant_group_member pgm ON pgm.group_id = pg.id
            WHERE pg.id = ?
            GROUP BY pg.id, pg.nom, pg.description, pg.created_at, pg.updated_at
        """
        result = con.execute(sql, (group_id,)).fetchone()
        return dict(result) if result else None


def create_group(nom: str, description: str = None):
    """
    Crée un nouveau groupe

    Args:
        nom: Nom du groupe (obligatoire et unique)
        description: Description optionnelle

    Returns:
        ID du nouveau groupe créé
    """
    with get_db() as con:
        sql = """
            INSERT INTO participant_group (nom, description)
            VALUES (?, ?)
        """
        cursor = con.execute(sql, (nom, description))
        return cursor.lastrowid


def update_group(group_id: int, nom: str = None, description: str = None):
    """
    Met à jour un groupe existant

    Args:
        group_id: ID du groupe à mettre à jour
        nom: Nom (obligatoire si fourni)
        description: Description (optionnel)

    Returns:
        True si la mise à jour a réussi
    """
    with get_db() as con:
        cursor = con.cursor()

        # Vérifier que le groupe existe
        cursor.execute("SELECT id FROM participant_group WHERE id = ?", (group_id,))
        if not cursor.fetchone():
            return False

        # Mise à jour complète (tous les champs)
        sql = """
            UPDATE participant_group
            SET nom = ?, description = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        cursor.execute(sql, (nom, description, group_id))
        con.commit()
        return True


def delete_group(group_id: int):
    """
    Supprime un groupe et toutes ses associations

    Args:
        group_id: ID du groupe à supprimer

    Returns:
        True si la suppression a réussi
    """
    with get_db() as con:
        sql = "DELETE FROM participant_group WHERE id = ?"
        con.execute(sql, (group_id,))
        return True


# ============================================================================
# Gestion de l'appartenance aux groupes
# ============================================================================

def get_group_members(group_id: int):
    """
    Récupère tous les participants d'un groupe

    Args:
        group_id: ID du groupe

    Returns:
        Liste des participants membres du groupe
    """
    with get_db() as con:
        sql = """
            SELECT
                p.id,
                p.nom,
                p.prenom,
                p.role,
                p.telephone,
                p.email,
                p.adresse,
                pgm.created_at as added_at
            FROM participant p
            JOIN participant_group_member pgm ON pgm.participant_id = p.id
            WHERE pgm.group_id = ?
            ORDER BY p.nom, p.prenom
        """
        rows = con.execute(sql, (group_id,)).fetchall()
        return [dict(row) for row in rows]


def get_participant_groups(participant_id: int):
    """
    Récupère tous les groupes auxquels appartient un participant

    Args:
        participant_id: ID du participant

    Returns:
        Liste des groupes du participant
    """
    with get_db() as con:
        sql = """
            SELECT
                pg.id,
                pg.nom,
                pg.description,
                pgm.created_at as added_at
            FROM participant_group pg
            JOIN participant_group_member pgm ON pgm.group_id = pg.id
            WHERE pgm.participant_id = ?
            ORDER BY pg.nom
        """
        rows = con.execute(sql, (participant_id,)).fetchall()
        return [dict(row) for row in rows]


def add_participant_to_group(participant_id: int, group_id: int):
    """
    Ajoute un participant à un groupe

    Args:
        participant_id: ID du participant
        group_id: ID du groupe

    Returns:
        ID de l'association créée ou None si déjà existante
    """
    with get_db() as con:
        try:
            sql = """
                INSERT INTO participant_group_member (participant_id, group_id)
                VALUES (?, ?)
            """
            cursor = con.execute(sql, (participant_id, group_id))
            con.commit()  # Commit explicite
            return cursor.lastrowid
        except Exception as e:
            # L'association existe déjà (UNIQUE constraint)
            print(f"Error adding participant to group: {e}")
            return None


def remove_participant_from_group(participant_id: int, group_id: int):
    """
    Retire un participant d'un groupe

    Args:
        participant_id: ID du participant
        group_id: ID du groupe

    Returns:
        True si la suppression a réussi
    """
    with get_db() as con:
        sql = """
            DELETE FROM participant_group_member
            WHERE participant_id = ? AND group_id = ?
        """
        con.execute(sql, (participant_id, group_id))
        return True


def set_participant_groups(participant_id: int, group_ids: list):
    """
    Définit les groupes d'un participant (remplace les anciens)

    Args:
        participant_id: ID du participant
        group_ids: Liste des IDs de groupes
    """
    with get_db() as con:
        cursor = con.cursor()
        # Supprimer les anciennes associations
        cursor.execute("DELETE FROM participant_group_member WHERE participant_id = ?", (participant_id,))

        # Ajouter les nouvelles associations
        if group_ids:
            for group_id in group_ids:
                cursor.execute(
                    "INSERT INTO participant_group_member (participant_id, group_id) VALUES (?, ?)",
                    (participant_id, group_id)
                )
        con.commit()


def set_group_members(group_id: int, participant_ids: list):
    """
    Définit les membres d'un groupe (remplace les anciens)

    Args:
        group_id: ID du groupe
        participant_ids: Liste des IDs de participants
    """
    with get_db() as con:
        cursor = con.cursor()
        # Supprimer les anciennes associations
        cursor.execute("DELETE FROM participant_group_member WHERE group_id = ?", (group_id,))

        # Ajouter les nouvelles associations
        if participant_ids:
            for participant_id in participant_ids:
                cursor.execute(
                    "INSERT INTO participant_group_member (participant_id, group_id) VALUES (?, ?)",
                    (participant_id, group_id)
                )
        con.commit()


# ============================================================================
# Gestion de la liaison événement ↔ participants
# ============================================================================

def get_event_participants(event_id: int):
    """
    Récupère tous les participants d'un événement

    Args:
        event_id: ID de l'événement

    Returns:
        Liste des participants avec informations sur le groupe source si applicable
    """
    with get_db() as con:
        sql = """
            SELECT
                p.id,
                p.nom,
                p.prenom,
                p.role,
                p.telephone,
                p.email,
                p.adresse,
                ep.added_via_group_id,
                pg.nom as group_name,
                ep.created_at as added_at
            FROM participant p
            JOIN event_participant ep ON ep.participant_id = p.id
            LEFT JOIN participant_group pg ON pg.id = ep.added_via_group_id
            WHERE ep.event_id = ?
            ORDER BY p.nom, p.prenom
        """
        rows = con.execute(sql, (event_id,)).fetchall()
        return [dict(row) for row in rows]


def add_participant_to_event(event_id: int, participant_id: int, added_via_group_id: int = None):
    """
    Ajoute un participant à un événement

    Args:
        event_id: ID de l'événement
        participant_id: ID du participant
        added_via_group_id: ID du groupe source (None si ajout manuel)

    Returns:
        ID de l'association créée ou None si déjà existante
    """
    with get_db() as con:
        try:
            sql = """
                INSERT INTO event_participant (event_id, participant_id, added_via_group_id)
                VALUES (?, ?, ?)
            """
            cursor = con.execute(sql, (event_id, participant_id, added_via_group_id))
            return cursor.lastrowid
        except Exception:
            # L'association existe déjà (UNIQUE constraint)
            return None


def add_group_to_event(event_id: int, group_id: int):
    """
    Ajoute tous les participants d'un groupe à un événement

    Args:
        event_id: ID de l'événement
        group_id: ID du groupe

    Returns:
        Nombre de participants ajoutés
    """
    members = get_group_members(group_id)
    added_count = 0

    for member in members:
        result = add_participant_to_event(event_id, member['id'], group_id)
        if result is not None:
            added_count += 1

    return added_count


def remove_participant_from_event(event_id: int, participant_id: int):
    """
    Retire un participant d'un événement

    Args:
        event_id: ID de l'événement
        participant_id: ID du participant

    Returns:
        True si la suppression a réussi
    """
    with get_db() as con:
        sql = """
            DELETE FROM event_participant
            WHERE event_id = ? AND participant_id = ?
        """
        con.execute(sql, (event_id, participant_id))
        return True


def get_participant_events(participant_id: int):
    """
    Récupère tous les événements auxquels participe un participant

    Args:
        participant_id: ID du participant

    Returns:
        Liste des événements
    """
    with get_db() as con:
        sql = """
            SELECT
                e.id,
                e.name,
                e.event_date,
                e.location,
                et.name_fr as event_type_name_fr,
                et.name_jp as event_type_name_jp,
                ep.added_via_group_id,
                pg.nom as group_name
            FROM event e
            JOIN event_participant ep ON ep.event_id = e.id
            JOIN event_type et ON et.id = e.event_type_id
            LEFT JOIN participant_group pg ON pg.id = ep.added_via_group_id
            WHERE ep.participant_id = ?
            ORDER BY e.event_date DESC
        """
        rows = con.execute(sql, (participant_id,)).fetchall()
        return [dict(row) for row in rows]
