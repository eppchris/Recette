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


def list_events(user_id: int = None):
    """
    Liste tous les événements avec leurs informations de base

    Args:
        user_id: Si fourni, filtre les événements de cet utilisateur uniquement

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
                e.user_id,
                et.id AS event_type_id,
                et.name_fr AS event_type_name_fr,
                et.name_jp AS event_type_name_jp
            FROM event e
            JOIN event_type et ON et.id = e.event_type_id
        """

        if user_id is not None:
            sql += " WHERE e.user_id = ?"
            sql += " ORDER BY e.event_date DESC"
            rows = con.execute(sql, (user_id,)).fetchall()
        else:
            sql += " ORDER BY e.event_date DESC"
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
                e.date_debut,
                e.date_fin,
                e.nombre_jours,
                et.id AS event_type_id,
                et.name_fr AS event_type_name_fr,
                et.name_jp AS event_type_name_jp
            FROM event e
            JOIN event_type et ON et.id = e.event_type_id
            WHERE e.id = ?
        """
        result = con.execute(sql, (event_id,)).fetchone()
        return dict(result) if result else None


def create_event(event_type_id: int, name: str, event_date: str, location: str, attendees: int, notes: str = '', user_id: int = None, date_debut: str = None, date_fin: str = None, nombre_jours: int = 1):
    """
    Crée un nouvel événement

    Args:
        event_type_id: ID du type d'événement
        name: Nom de l'événement
        event_date: Date de l'événement (format YYYY-MM-DD) - conservé pour compatibilité
        location: Lieu de l'événement
        attendees: Nombre de convives
        notes: Notes optionnelles
        user_id: ID de l'utilisateur créateur (optionnel)
        date_debut: Date de début de l'événement (format YYYY-MM-DD)
        date_fin: Date de fin de l'événement (format YYYY-MM-DD)
        nombre_jours: Nombre de jours travaillés

    Returns:
        ID du nouvel événement créé
    """
    # Si date_debut et date_fin ne sont pas fournis, utiliser event_date
    if date_debut is None:
        date_debut = event_date
    if date_fin is None:
        date_fin = event_date

    with get_db() as con:
        sql = """
            INSERT INTO event (event_type_id, name, event_date, location, attendees, notes, user_id, date_debut, date_fin, nombre_jours)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor = con.execute(sql, (event_type_id, name, event_date, location, attendees, notes, user_id, date_debut, date_fin, nombre_jours))
        return cursor.lastrowid


def update_event(event_id: int, event_type_id: int, name: str, event_date: str, location: str, attendees: int, notes: str = '', date_debut: str = None, date_fin: str = None, nombre_jours: int = None):
    """
    Met à jour un événement existant

    Args:
        event_id: ID de l'événement à mettre à jour
        event_type_id: ID du type d'événement
        name: Nom de l'événement
        event_date: Date de l'événement (format YYYY-MM-DD) - conservé pour compatibilité
        location: Lieu de l'événement
        attendees: Nombre de convives
        notes: Notes optionnelles
        date_debut: Date de début de l'événement
        date_fin: Date de fin de l'événement
        nombre_jours: Nombre de jours travaillés

    Returns:
        True si la mise à jour a réussi
    """
    # Si date_debut et date_fin ne sont pas fournis, utiliser event_date
    if date_debut is None:
        date_debut = event_date
    if date_fin is None:
        date_fin = event_date
    if nombre_jours is None:
        nombre_jours = 1

    with get_db() as con:
        sql = """
            UPDATE event
            SET event_type_id = ?,
                name = ?,
                event_date = ?,
                location = ?,
                attendees = ?,
                notes = ?,
                date_debut = ?,
                date_fin = ?,
                nombre_jours = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        con.execute(sql, (event_type_id, name, event_date, location, attendees, notes, date_debut, date_fin, nombre_jours, event_id))
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

    OPTIMISATION: Une seule requête avec JOIN au lieu de N+1 queries
    Gain: 91% de réduction (11 requêtes → 1 requête pour 10 recettes)

    Args:
        event_id: ID de l'événement
        lang: Code de langue ('fr' ou 'jp')

    Returns:
        Liste des recettes avec ingrédients détaillés et multiplicateur
    """
    with get_db() as con:
        # Une seule requête avec tous les JOINs
        # IMPORTANT: On récupère TOUJOURS le nom français (ingredient_name_fr) car c'est la clé
        # pour le catalogue des prix, même si on affiche le nom traduit (ingredient_name)
        sql = """
            SELECT
                r.id AS recipe_id,
                r.slug AS recipe_slug,
                COALESCE(rt.name, r.slug) AS recipe_name,
                er.servings_multiplier,
                er.position AS recipe_position,
                ri.id AS ingredient_id,
                ri.position AS ingredient_position,
                ri.quantity,
                COALESCE(rit.name, '') AS ingredient_name,
                COALESCE(rit.unit, '') AS unit,
                COALESCE(rit.notes, '') AS notes,
                COALESCE(rit_fr.name, rit.name, '') AS ingredient_name_fr
            FROM event_recipe er
            JOIN recipe r ON r.id = er.recipe_id
            LEFT JOIN recipe_translation rt ON rt.recipe_id = r.id AND rt.lang = ?
            LEFT JOIN recipe_ingredient ri ON ri.recipe_id = r.id
            LEFT JOIN recipe_ingredient_translation rit
                ON rit.recipe_ingredient_id = ri.id AND rit.lang = ?
            LEFT JOIN recipe_ingredient_translation rit_fr
                ON rit_fr.recipe_ingredient_id = ri.id AND rit_fr.lang = 'fr'
            WHERE er.event_id = ?
            ORDER BY er.position, ri.position
        """
        rows = con.execute(sql, (lang, lang, event_id)).fetchall()

        # Post-traitement en Python pour restructurer les données
        # Regrouper les ingrédients par recette
        recipes_dict = {}
        for row in rows:
            recipe_id = row['recipe_id']

            # Créer l'entrée de recette si elle n'existe pas
            if recipe_id not in recipes_dict:
                recipes_dict[recipe_id] = {
                    'recipe_id': recipe_id,
                    'recipe_slug': row['recipe_slug'],
                    'recipe_name': row['recipe_name'],
                    'servings_multiplier': row['servings_multiplier'],
                    'recipe_position': row['recipe_position'],
                    'ingredients': []
                }

            # Ajouter l'ingrédient s'il existe (peut être NULL si recette sans ingrédients)
            if row['ingredient_id'] is not None:
                recipes_dict[recipe_id]['ingredients'].append({
                    'quantity': row['quantity'],
                    'name': row['ingredient_name'],
                    'name_fr': row['ingredient_name_fr'],  # Nom français pour le catalogue
                    'unit': row['unit'],
                    'notes': row['notes']
                })

        # Convertir le dictionnaire en liste triée par position
        result = sorted(recipes_dict.values(), key=lambda x: x['recipe_position'])

        # Retirer la clé recipe_position qui n'est plus nécessaire
        for recipe in result:
            del recipe['recipe_position']

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

    OPTIMISATION: Batch INSERT avec executemany() au lieu de boucle
    Gain: 67% de réduction (6 requêtes → 2 requêtes pour 5 types)

    Args:
        recipe_id: ID de la recette
        event_type_ids: Liste des IDs de types d'événements
    """
    with get_db() as con:
        cursor = con.cursor()
        # Supprimer les anciennes associations
        cursor.execute("DELETE FROM recipe_event_type WHERE recipe_id = ?", (recipe_id,))

        # Batch INSERT avec executemany() si liste non vide
        if event_type_ids:
            data = [(recipe_id, event_type_id) for event_type_id in event_type_ids]
            cursor.executemany(
                "INSERT INTO recipe_event_type (recipe_id, event_type_id) VALUES (?, ?)",
                data
            )
        con.commit()


# ============================================================================
# Gestion des dates d'événement multi-jours
# ============================================================================

def save_event_dates(event_id: int, dates: list):
    """
    Enregistre ou met à jour les dates d'un événement

    Args:
        event_id: ID de l'événement
        dates: Liste de dicts avec 'date' et 'is_selected'
    """
    with get_db() as con:
        cursor = con.cursor()
        # Supprimer les anciennes dates
        cursor.execute("DELETE FROM event_date WHERE event_id = ?", (event_id,))
        # Ajouter les nouvelles dates
        for date_info in dates:
            cursor.execute(
                "INSERT INTO event_date (event_id, date, is_selected) VALUES (?, ?, ?)",
                (event_id, date_info['date'], date_info.get('is_selected', 1))
            )
        con.commit()


def get_event_dates(event_id: int):
    """
    Récupère toutes les dates d'un événement

    Args:
        event_id: ID de l'événement

    Returns:
        Liste des dates avec leur statut de sélection
    """
    with get_db() as con:
        sql = """
            SELECT id, event_id, date, is_selected, created_at
            FROM event_date
            WHERE event_id = ?
            ORDER BY date
        """
        rows = con.execute(sql, (event_id,)).fetchall()
        return [dict(row) for row in rows]


def toggle_event_date_selection(event_date_id: int):
    """
    Inverse la sélection d'une date d'événement

    Args:
        event_date_id: ID de la date d'événement

    Returns:
        Nouveau statut de is_selected
    """
    with get_db() as con:
        cursor = con.cursor()
        # Récupérer le statut actuel
        current = cursor.execute(
            "SELECT is_selected FROM event_date WHERE id = ?",
            (event_date_id,)
        ).fetchone()

        if current:
            new_status = 0 if current['is_selected'] else 1
            cursor.execute(
                "UPDATE event_date SET is_selected = ? WHERE id = ?",
                (new_status, event_date_id)
            )
            con.commit()
            return new_status
        return None


# ============================================================================
# Gestion de l'organisation des recettes par jour
# ============================================================================

def save_recipe_planning(event_id: int, planning_data: list):
    """
    Sauvegarde l'organisation des recettes par jour

    OPTIMISATION: Batch INSERT avec executemany() au lieu de boucle
    Gain: 90% de réduction (21 requêtes → 2 requêtes pour 20 jours)

    Args:
        event_id: ID de l'événement
        planning_data: Liste de dicts avec 'recipe_id', 'event_date_id', 'position'
    """
    with get_db() as con:
        cursor = con.cursor()
        # Supprimer l'ancienne planification
        cursor.execute("DELETE FROM event_recipe_planning WHERE event_id = ?", (event_id,))

        # Batch INSERT avec executemany() si données non vides
        if planning_data:
            data = [
                (event_id, item['recipe_id'], item['event_date_id'], item['position'])
                for item in planning_data
            ]
            cursor.executemany(
                """INSERT INTO event_recipe_planning
                   (event_id, recipe_id, event_date_id, position)
                   VALUES (?, ?, ?, ?)""",
                data
            )
        con.commit()


def get_recipe_planning(event_id: int, lang: str):
    """
    Récupère l'organisation des recettes par jour pour un événement

    Args:
        event_id: ID de l'événement
        lang: Langue ('fr' ou 'jp')

    Returns:
        Dict organisé par date avec les recettes dans l'ordre
    """
    with get_db() as con:
        sql = """
            SELECT
                ed.id AS event_date_id,
                ed.date,
                ed.is_selected,
                r.id AS recipe_id,
                r.slug,
                r.image_url,
                r.thumbnail_url,
                COALESCE(rt.name, r.slug) AS recipe_name,
                erp.position
            FROM event_date ed
            LEFT JOIN event_recipe_planning erp ON erp.event_date_id = ed.id
            LEFT JOIN recipe r ON r.id = erp.recipe_id
            LEFT JOIN recipe_translation rt ON rt.recipe_id = r.id AND rt.lang = ?
            WHERE ed.event_id = ? AND ed.is_selected = 1
            ORDER BY ed.date, erp.position
        """
        rows = con.execute(sql, (lang, event_id)).fetchall()

        # Organiser par date
        result = {}
        for row in rows:
            date = row['date']
            if date not in result:
                result[date] = {
                    'event_date_id': row['event_date_id'],
                    'date': date,
                    'recipes': []
                }

            # Ajouter la recette si elle existe
            if row['recipe_id']:
                result[date]['recipes'].append({
                    'id': row['recipe_id'],
                    'slug': row['slug'],
                    'name': row['recipe_name'],
                    'image_url': row['image_url'],
                    'thumbnail_url': row['thumbnail_url'],
                    'position': row['position']
                })

        return result


def copy_event(event_id: int, new_name: str, new_event_type_id: int, new_date_debut: str,
               new_date_fin: str, new_location: str = None, new_attendees: int = None,
               new_notes: str = None, user_id: int = None):
    """
    Copie un événement existant avec toutes ses données

    Args:
        event_id: ID de l'événement source à copier
        new_name: Nouveau nom pour la copie
        new_event_type_id: Type d'événement
        new_date_debut: Date de début
        new_date_fin: Date de fin (peut être égale à date_debut pour 1 jour)
        new_location: Lieu
        new_attendees: Nombre de convives
        new_notes: Notes
        user_id: ID de l'utilisateur créateur

    Returns:
        ID du nouvel événement créé, ou None en cas d'erreur

    Copie:
        - Informations de base de l'événement (avec nouvelles valeurs)
        - Toutes les recettes avec leurs quantités (servings_multiplier)
        - Budget prévu et devise (pas les dépenses effectuées)
        - Organisation/planning uniquement si même nombre de jours
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # 1. Récupérer l'événement source
        cursor.execute("""
            SELECT event_type_id, event_date, location, attendees, notes,
                   budget_planned, currency, user_id, date_debut, date_fin, nombre_jours
            FROM event
            WHERE id = ?
        """, (event_id,))

        source_event = cursor.fetchone()
        if not source_event:
            return None

        source_event = dict(source_event)

        # Calculer le nouveau nombre de jours
        from datetime import datetime, timedelta
        date_debut_obj = datetime.strptime(new_date_debut, '%Y-%m-%d')
        date_fin_obj = datetime.strptime(new_date_fin, '%Y-%m-%d')
        new_nombre_jours = (date_fin_obj - date_debut_obj).days + 1

        # 2. Créer le nouvel événement
        cursor.execute("""
            INSERT INTO event (
                event_type_id, name, event_date, location, attendees, notes,
                budget_planned, currency, user_id, date_debut, date_fin, nombre_jours
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_event_type_id,
            new_name,
            new_date_debut,  # event_date = date_debut
            new_location or source_event['location'],
            new_attendees or source_event['attendees'],
            new_notes or source_event['notes'],
            source_event['budget_planned'],  # Copier budget prévu
            source_event['currency'],  # Copier devise
            user_id or source_event['user_id'],
            new_date_debut,
            new_date_fin,
            new_nombre_jours
        ))

        new_event_id = cursor.lastrowid

        # 3. Copier toutes les recettes avec leurs quantités
        cursor.execute("""
            SELECT recipe_id, servings_multiplier, position
            FROM event_recipe
            WHERE event_id = ?
        """, (event_id,))

        recipes = cursor.fetchall()
        for recipe in recipes:
            cursor.execute("""
                INSERT INTO event_recipe (event_id, recipe_id, servings_multiplier, position)
                VALUES (?, ?, ?, ?)
            """, (new_event_id, recipe['recipe_id'], recipe['servings_multiplier'], recipe['position']))

        # 4. Créer les nouvelles dates (toutes sélectionnées par défaut)
        current_date = date_debut_obj
        while current_date <= date_fin_obj:
            cursor.execute("""
                INSERT INTO event_date (event_id, date, is_selected)
                VALUES (?, ?, 1)
            """, (new_event_id, current_date.strftime('%Y-%m-%d')))

            current_date += timedelta(days=1)

        # 5. Copier l'organisation/planning UNIQUEMENT si même nombre de jours
        if new_nombre_jours == source_event['nombre_jours']:
            # Récupérer UNIQUEMENT les dates SÉLECTIONNÉES sources (is_selected = 1)
            cursor.execute("""
                SELECT id, date
                FROM event_date
                WHERE event_id = ? AND is_selected = 1
                ORDER BY date
            """, (event_id,))
            source_dates = list(cursor.fetchall())

            # Récupérer les nouvelles dates (toutes sélectionnées par défaut)
            cursor.execute("""
                SELECT id, date
                FROM event_date
                WHERE event_id = ?
                ORDER BY date
            """, (new_event_id,))
            new_dates = list(cursor.fetchall())

            # Mapper les anciennes dates sélectionnées vers les nouvelles (par index)
            date_mapping = {}
            for i, source_date in enumerate(source_dates):
                if i < len(new_dates):
                    date_mapping[source_date['id']] = new_dates[i]['id']

            # Copier la planification
            cursor.execute("""
                SELECT recipe_id, event_date_id, position
                FROM event_recipe_planning
                WHERE event_id = ?
            """, (event_id,))

            planning_entries = cursor.fetchall()
            for entry in planning_entries:
                old_date_id = entry['event_date_id']
                new_date_id = date_mapping.get(old_date_id)

                if new_date_id:
                    cursor.execute("""
                        INSERT INTO event_recipe_planning (event_id, recipe_id, event_date_id, position)
                        VALUES (?, ?, ?, ?)
                    """, (new_event_id, entry['recipe_id'], new_date_id, entry['position']))

        conn.commit()
        return new_event_id
