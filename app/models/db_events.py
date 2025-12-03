"""
Module de gestion des événements
"""
from .db_core import get_db


def list_event_types():
    """
    Liste tous les types d'événements (version bilingual)

    Returns:
        Liste des types d'événements avec noms FR et JP
    """
    with get_db() as con:
        sql = """
            SELECT id, name_fr, name_jp, description_fr, description_jp, created_at
            FROM event_type
            ORDER BY name_fr
        """
        rows = con.execute(sql).fetchall()
        return [dict(row) for row in rows]


def get_all_event_types():
    """Récupère tous les types d'événements triés par nom avec le nombre d'événements"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                et.id,
                et.name_fr,
                et.name_jp,
                et.description_fr,
                et.description_jp,
                COUNT(e.id) as event_count
            FROM event_type et
            LEFT JOIN event e ON et.id = e.event_type_id
            GROUP BY et.id, et.name_fr, et.name_jp, et.description_fr, et.description_jp
            ORDER BY et.name_fr
        """)
        return [dict(row) for row in cursor.fetchall()]


def create_event_type(name_fr: str, name_jp: str, description_fr: str = None,
                      description_jp: str = None):
    """Crée un nouveau type d'événement"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO event_type (name_fr, name_jp, description_fr, description_jp)
            VALUES (?, ?, ?, ?)
        """, (name_fr, name_jp, description_fr, description_jp))
        conn.commit()
        return cursor.lastrowid


def update_event_type(event_type_id: int, name_fr: str = None, name_jp: str = None,
                      description_fr: str = None, description_jp: str = None) -> bool:
    """Modifier un type d'événement existant"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Vérifier que le type d'événement existe
        cursor.execute("SELECT id FROM event_type WHERE id = ?", (event_type_id,))
        row = cursor.fetchone()
        if not row:
            return False

        # Construire la requête UPDATE dynamiquement
        updates = []
        params = []

        if name_fr is not None:
            updates.append("name_fr = ?")
            params.append(name_fr)
        if name_jp is not None:
            updates.append("name_jp = ?")
            params.append(name_jp)
        if description_fr is not None:
            updates.append("description_fr = ?")
            params.append(description_fr)
        if description_jp is not None:
            updates.append("description_jp = ?")
            params.append(description_jp)

        if not updates:
            return False

        params.append(event_type_id)
        query = f"UPDATE event_type SET {', '.join(updates)} WHERE id = ?"

        cursor.execute(query, params)
        conn.commit()
        return True


def list_events():
    """
    Liste tous les événements avec leurs informations de base

    Returns:
        Liste des événements triés par date décroissante
    """
    with get_db() as con:
        sql = """
            SELECT
                e.id,
                e.name,
                e.event_date,
                e.location,
                e.attendees,
                e.notes,
                e.created_at,
                e.updated_at,
                e.currency,
                e.budget_planned,
                et.id AS event_type_id,
                et.name_fr AS event_type_name_fr,
                et.name_jp AS event_type_name_jp
            FROM event e
            JOIN event_type et ON et.id = e.event_type_id
            ORDER BY e.event_date DESC
        """
        rows = con.execute(sql).fetchall()
        return [dict(row) for row in rows]


def get_event_by_id(event_id: int):
    """
    Récupère un événement par son ID

    Args:
        event_id: ID de l'événement

    Returns:
        Dict avec les informations de l'événement ou None si non trouvé
    """
    with get_db() as con:
        sql = """
            SELECT
                e.id,
                e.name,
                e.event_date,
                e.location,
                e.attendees,
                e.notes,
                e.created_at,
                e.updated_at,
                e.currency,
                e.budget_planned,
                e.ingredients_actual_total,
                et.id AS event_type_id,
                et.name_fr AS event_type_name_fr,
                et.name_jp AS event_type_name_jp
            FROM event e
            JOIN event_type et ON et.id = e.event_type_id
            WHERE e.id = ?
        """
        result = con.execute(sql, (event_id,)).fetchone()
        return dict(result) if result else None


def create_event(event_type_id: int, name: str, event_date: str, location: str, attendees: int, notes: str = '', user_id: int = None):
    """
    Crée un nouvel événement

    Args:
        event_type_id: ID du type d'événement
        name: Nom de l'événement
        event_date: Date de l'événement (format YYYY-MM-DD)
        location: Lieu de l'événement
        attendees: Nombre de convives
        notes: Notes optionnelles
        user_id: ID de l'utilisateur créateur (optionnel)

    Returns:
        ID du nouvel événement créé
    """
    with get_db() as con:
        sql = """
            INSERT INTO event (event_type_id, name, event_date, location, attendees, notes, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor = con.execute(sql, (event_type_id, name, event_date, location, attendees, notes, user_id))
        return cursor.lastrowid


def update_event(event_id: int, event_type_id: int, name: str, event_date: str, location: str, attendees: int, notes: str = ''):
    """
    Met à jour un événement existant

    Args:
        event_id: ID de l'événement à mettre à jour
        event_type_id: ID du type d'événement
        name: Nom de l'événement
        event_date: Date de l'événement (format YYYY-MM-DD)
        location: Lieu de l'événement
        attendees: Nombre de convives
        notes: Notes optionnelles

    Returns:
        True si la mise à jour a réussi
    """
    with get_db() as con:
        sql = """
            UPDATE event
            SET event_type_id = ?,
                name = ?,
                event_date = ?,
                location = ?,
                attendees = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        con.execute(sql, (event_type_id, name, event_date, location, attendees, notes, event_id))
        return True


def delete_event(event_id: int):
    """
    Supprime un événement et toutes ses associations

    Args:
        event_id: ID de l'événement à supprimer

    Returns:
        True si la suppression a réussi
    """
    with get_db() as con:
        sql = "DELETE FROM event WHERE id = ?"
        con.execute(sql, (event_id,))
        return True


def add_recipe_to_event(event_id: int, recipe_id: int, servings_multiplier: float = 1.0):
    """
    Ajoute une recette à un événement

    Args:
        event_id: ID de l'événement
        recipe_id: ID de la recette
        servings_multiplier: Multiplicateur pour adapter aux convives

    Returns:
        ID de l'association créée
    """
    with get_db() as con:
        # Récupérer la position max actuelle
        sql_max_pos = "SELECT COALESCE(MAX(position), -1) as max_pos FROM event_recipe WHERE event_id = ?"
        max_pos = con.execute(sql_max_pos, (event_id,)).fetchone()['max_pos']

        sql = """
            INSERT INTO event_recipe (event_id, recipe_id, servings_multiplier, position)
            VALUES (?, ?, ?, ?)
        """
        cursor = con.execute(sql, (event_id, recipe_id, servings_multiplier, max_pos + 1))
        return cursor.lastrowid


def update_event_recipe_servings(event_id: int, recipe_id: int, servings_multiplier: float):
    """
    Met à jour le multiplicateur de portions pour une recette d'un événement

    Args:
        event_id: ID de l'événement
        recipe_id: ID de la recette
        servings_multiplier: Nouveau multiplicateur

    Returns:
        True si la mise à jour a réussi
    """
    with get_db() as con:
        sql = """
            UPDATE event_recipe
            SET servings_multiplier = ?
            WHERE event_id = ? AND recipe_id = ?
        """
        con.execute(sql, (servings_multiplier, event_id, recipe_id))
        return True


def update_event_recipes_multipliers(event_id: int, ratio: float):
    """
    Multiplie tous les servings_multiplier des recettes d'un événement par un ratio
    Utilisé pour ajuster les quantités quand le nombre de participants change

    Args:
        event_id: ID de l'événement
        ratio: Ratio de multiplication (nouveau_nb_participants / ancien_nb_participants)

    Returns:
        True si la mise à jour a réussi
    """
    with get_db() as con:
        sql = """
            UPDATE event_recipe
            SET servings_multiplier = servings_multiplier * ?
            WHERE event_id = ?
        """
        con.execute(sql, (ratio, event_id))
        return True


def remove_recipe_from_event(event_id: int, recipe_id: int):
    """
    Retire une recette d'un événement

    Args:
        event_id: ID de l'événement
        recipe_id: ID de la recette

    Returns:
        True si la suppression a réussi
    """
    with get_db() as con:
        sql = "DELETE FROM event_recipe WHERE event_id = ? AND recipe_id = ?"
        con.execute(sql, (event_id, recipe_id))
        return True


def get_event_recipes(event_id: int, lang: str):
    """
    Récupère toutes les recettes associées à un événement

    Args:
        event_id: ID de l'événement
        lang: Code de langue ('fr' ou 'jp')

    Returns:
        Liste des recettes avec leurs informations et multiplicateur
    """
    with get_db() as con:
        sql = """
            SELECT
                r.id,
                r.slug,
                r.servings_default,
                r.country,
                r.image_url,
                r.thumbnail_url,
                COALESCE(rt.name, r.slug) AS name,
                rt.recipe_type AS type,
                er.servings_multiplier,
                er.position
            FROM event_recipe er
            JOIN recipe r ON r.id = er.recipe_id
            LEFT JOIN recipe_translation rt ON rt.recipe_id = r.id AND rt.lang = ?
            WHERE er.event_id = ?
            ORDER BY er.position
        """
        rows = con.execute(sql, (lang, event_id)).fetchall()
        return [dict(row) for row in rows]


def get_event_recipes_with_ingredients(event_id: int, lang: str):
    """
    Récupère toutes les recettes d'un événement avec leurs ingrédients
    Pour générer la liste de courses

    Args:
        event_id: ID de l'événement
        lang: Code de langue ('fr' ou 'jp')

    Returns:
        Liste des recettes avec ingrédients détaillés et multiplicateur
    """
    with get_db() as con:
        # Récupérer les recettes
        recipes_sql = """
            SELECT
                r.id,
                r.slug,
                COALESCE(rt.name, r.slug) AS name,
                er.servings_multiplier
            FROM event_recipe er
            JOIN recipe r ON r.id = er.recipe_id
            LEFT JOIN recipe_translation rt ON rt.recipe_id = r.id AND rt.lang = ?
            WHERE er.event_id = ?
            ORDER BY er.position
        """
        recipes = con.execute(recipes_sql, (lang, event_id)).fetchall()

        # Pour chaque recette, récupérer les ingrédients
        result = []
        for recipe in recipes:
            ingredients_sql = """
                SELECT
                    ri.quantity,
                    COALESCE(rit.name, '') AS name,
                    COALESCE(rit.unit, '') AS unit,
                    COALESCE(rit.notes, '') AS notes
                FROM recipe_ingredient ri
                LEFT JOIN recipe_ingredient_translation rit
                    ON rit.recipe_ingredient_id = ri.id AND rit.lang = ?
                WHERE ri.recipe_id = ?
                ORDER BY ri.position
            """
            ingredients = con.execute(ingredients_sql, (lang, recipe['id'])).fetchall()

            result.append({
                'recipe_id': recipe['id'],
                'recipe_slug': recipe['slug'],
                'recipe_name': recipe['name'],
                'servings_multiplier': recipe['servings_multiplier'],
                'ingredients': [dict(ing) for ing in ingredients]
            })

        return result


def get_recipe_event_types(recipe_id: int):
    """
    Récupère les types d'événements associés à une recette

    Args:
        recipe_id: ID de la recette

    Returns:
        Liste des types d'événements (id, name_fr, name_jp)
    """
    with get_db() as con:
        sql = """
            SELECT
                et.id,
                et.name_fr,
                et.name_jp
            FROM event_type et
            JOIN recipe_event_type ret ON ret.event_type_id = et.id
            WHERE ret.recipe_id = ?
            ORDER BY et.name_fr
        """
        rows = con.execute(sql, (recipe_id,)).fetchall()
        return [dict(row) for row in rows]


def set_recipe_event_types(recipe_id: int, event_type_ids: list):
    """
    Définit les types d'événements d'une recette (remplace les anciens)

    Args:
        recipe_id: ID de la recette
        event_type_ids: Liste des IDs de types d'événements
    """
    with get_db() as con:
        cursor = con.cursor()
        # Supprimer les anciennes associations
        cursor.execute("DELETE FROM recipe_event_type WHERE recipe_id = ?", (recipe_id,))
        # Ajouter les nouvelles
        for event_type_id in event_type_ids:
            cursor.execute(
                "INSERT INTO recipe_event_type (recipe_id, event_type_id) VALUES (?, ?)",
                (recipe_id, event_type_id)
            )
        con.commit()
