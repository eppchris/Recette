# -*- coding: utf-8 -*-
"""
Gestion de la planification des repas quotidiens.
"""

from .db_core import get_db


def get_calendar_data(year: int, month: int, lang: str, user_id: int) -> dict:
    """
    Retourne les données de repas pour un mois donné.
    Structure : {date_str: {personal: [...], events: [...]}}

    personal = repas planifiés manuellement (meal_plan)
    events   = repas liés à des événements via "Organiser"
    """
    month_prefix = f"{year:04d}-{month:02d}-%"
    result = {}

    with get_db() as con:
        # --- Repas personnels ---
        personal_rows = con.execute(
            """
            SELECT
                mp.id, mp.date, mp.meal_type,
                mp.free_text,
                mp.notes,
                r.id AS recipe_id,
                r.slug,
                r.thumbnail_url,
                r.country,
                rt.name
            FROM meal_plan mp
            LEFT JOIN recipe r ON r.id = mp.recipe_id
            LEFT JOIN recipe_translation rt ON rt.recipe_id = r.id AND rt.lang = ?
            WHERE mp.date LIKE ?
              AND mp.user_id = ?
            ORDER BY mp.date, mp.meal_type, mp.id
            """,
            (lang, month_prefix, user_id)
        ).fetchall()

        for row in personal_rows:
            d = row['date']
            if d not in result:
                result[d] = {'personal': [], 'events': []}
            result[d]['personal'].append({
                'id': row['id'],
                'meal_type': row['meal_type'],
                'recipe_id': row['recipe_id'],
                'slug': row['slug'],
                'thumbnail_url': row['thumbnail_url'],
                'country': row['country'] or '',
                'name': row['name'] or row['free_text'] or '',
                'free_text': row['free_text'],
                'is_free_text': row['free_text'] is not None and row['recipe_id'] is None,
                'notes': row['notes'],
            })

        # --- Repas liés aux événements (via "Organiser") ---
        # Toutes les dates sélectionnées de l'événement apparaissent,
        # même si aucune recette n'est encore assignée (LEFT JOIN).
        event_rows = con.execute(
            """
            -- Dates avec planification explicite (event_recipe_planning)
            SELECT
                ed.date,
                e.id AS event_id,
                e.name AS event_name,
                r.id AS recipe_id,
                r.slug,
                r.thumbnail_url,
                r.country,
                rt.name AS recipe_name,
                erp.position
            FROM event_date ed
            JOIN event e ON e.id = ed.event_id
            LEFT JOIN event_recipe_planning erp ON erp.event_date_id = ed.id
            LEFT JOIN recipe r ON r.id = erp.recipe_id
            LEFT JOIN recipe_translation rt ON rt.recipe_id = r.id AND rt.lang = ?
            WHERE ed.date LIKE ?
              AND ed.is_selected = 1
              AND e.user_id = ?

            UNION ALL

            -- Événements SANS aucune planification : afficher les recettes globales sur toutes les dates
            SELECT
                ed.date,
                e.id AS event_id,
                e.name AS event_name,
                r.id AS recipe_id,
                r.slug,
                r.thumbnail_url,
                r.country,
                rt.name AS recipe_name,
                er.position
            FROM event_date ed
            JOIN event e ON e.id = ed.event_id
            JOIN event_recipe er ON er.event_id = e.id
            JOIN recipe r ON r.id = er.recipe_id
            LEFT JOIN recipe_translation rt ON rt.recipe_id = r.id AND rt.lang = ?
            WHERE ed.date LIKE ?
              AND ed.is_selected = 1
              AND e.user_id = ?
              AND NOT EXISTS (
                  SELECT 1 FROM event_recipe_planning erp2
                  WHERE erp2.event_id = e.id
              )

            ORDER BY date, event_id, position
            """,
            (lang, month_prefix, user_id, lang, month_prefix, user_id)
        ).fetchall()

        # Déduplique : une seule entrée par (date, event_id) si pas de recette
        seen_date_event = set()
        for row in event_rows:
            d = row['date']
            if d not in result:
                result[d] = {'personal': [], 'events': []}
            key = (d, row['event_id'], row['recipe_id'])
            if key in seen_date_event:
                continue
            seen_date_event.add(key)
            result[d]['events'].append({
                'event_id': row['event_id'],
                'event_name': row['event_name'],
                'recipe_id': row['recipe_id'],
                'slug': row['slug'],
                'thumbnail_url': row['thumbnail_url'],
                'country': row['country'] or '',
                'name': row['recipe_name'] or '',
            })

    return result


def get_day_detail(date: str, lang: str, user_id: int) -> dict:
    """
    Retourne le détail complet des repas pour un jour donné.
    """
    with get_db() as con:
        personal_rows = con.execute(
            """
            SELECT
                mp.id, mp.date, mp.meal_type,
                mp.free_text, mp.notes,
                r.id AS recipe_id,
                r.slug,
                r.thumbnail_url,
                r.country,
                rt.name
            FROM meal_plan mp
            LEFT JOIN recipe r ON r.id = mp.recipe_id
            LEFT JOIN recipe_translation rt ON rt.recipe_id = r.id AND rt.lang = ?
            WHERE mp.date = ?
              AND mp.user_id = ?
            ORDER BY mp.meal_type, mp.id
            """,
            (lang, date, user_id)
        ).fetchall()

        event_rows = con.execute(
            """
            -- Dates avec planification explicite (event_recipe_planning)
            SELECT
                e.id AS event_id,
                e.name AS event_name,
                r.id AS recipe_id,
                r.slug,
                r.thumbnail_url,
                r.country,
                rt.name AS recipe_name,
                erp.position
            FROM event_date ed
            JOIN event e ON e.id = ed.event_id
            LEFT JOIN event_recipe_planning erp ON erp.event_date_id = ed.id
            LEFT JOIN recipe r ON r.id = erp.recipe_id
            LEFT JOIN recipe_translation rt ON rt.recipe_id = r.id AND rt.lang = ?
            WHERE ed.date = ?
              AND ed.is_selected = 1
              AND e.user_id = ?

            UNION ALL

            -- Événements SANS aucune planification : afficher les recettes globales sur toutes les dates
            SELECT
                e.id AS event_id,
                e.name AS event_name,
                r.id AS recipe_id,
                r.slug,
                r.thumbnail_url,
                r.country,
                rt.name AS recipe_name,
                er.position
            FROM event_date ed
            JOIN event e ON e.id = ed.event_id
            JOIN event_recipe er ON er.event_id = e.id
            JOIN recipe r ON r.id = er.recipe_id
            LEFT JOIN recipe_translation rt ON rt.recipe_id = r.id AND rt.lang = ?
            WHERE ed.date = ?
              AND ed.is_selected = 1
              AND e.user_id = ?
              AND NOT EXISTS (
                  SELECT 1 FROM event_recipe_planning erp2
                  WHERE erp2.event_id = e.id
              )

            ORDER BY event_id, position
            """,
            (lang, date, user_id, lang, date, user_id)
        ).fetchall()

    personal = [
        {
            'id': r['id'],
            'meal_type': r['meal_type'],
            'recipe_id': r['recipe_id'],
            'slug': r['slug'],
            'thumbnail_url': r['thumbnail_url'],
            'country': r['country'] or '',
            'name': r['name'] or r['free_text'] or '',
            'free_text': r['free_text'],
            'is_free_text': r['free_text'] is not None and r['recipe_id'] is None,
            'notes': r['notes'],
        }
        for r in personal_rows
    ]

    seen = set()
    events = []
    for r in event_rows:
        key = (r['event_id'], r['recipe_id'])
        if key in seen:
            continue
        seen.add(key)
        events.append({
            'event_id': r['event_id'],
            'event_name': r['event_name'],
            'recipe_id': r['recipe_id'],
            'slug': r['slug'],
            'thumbnail_url': r['thumbnail_url'],
            'country': r['country'] or '' if r['country'] is not None else '',
            'name': r['recipe_name'] or '',
        })

    return {'personal': personal, 'events': events}


def add_meal(user_id: int, date: str, meal_type: str, recipe_id=None, free_text: str = None, notes: str = None) -> int:
    """
    Ajoute un repas à la planification.
    Requiert recipe_id OU free_text.
    Retourne l'id du repas créé.
    """
    if not recipe_id and not free_text:
        raise ValueError("recipe_id ou free_text requis")

    with get_db() as con:
        cursor = con.execute(
            """
            INSERT INTO meal_plan (user_id, date, meal_type, recipe_id, free_text, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, date, meal_type, recipe_id or None, free_text or None, notes or None)
        )
        return cursor.lastrowid


def delete_meal(meal_id: int, user_id: int) -> bool:
    """
    Supprime un repas personnel.
    Vérifie que l'utilisateur est bien propriétaire.
    """
    with get_db() as con:
        row = con.execute(
            "SELECT id FROM meal_plan WHERE id = ? AND user_id = ?",
            (meal_id, user_id)
        ).fetchone()
        if not row:
            return False
        con.execute("DELETE FROM meal_plan WHERE id = ?", (meal_id,))
    return True


def get_todo_recipes(user_id: int) -> list:
    """
    Retourne la liste des repas planifiés en texte libre (sans recette liée),
    triés par date — constitue la liste des recettes à créer.
    """
    with get_db() as con:
        rows = con.execute(
            """
            SELECT id, date, meal_type, free_text, notes
            FROM meal_plan
            WHERE user_id = ?
              AND recipe_id IS NULL
              AND free_text IS NOT NULL
            ORDER BY date
            """,
            (user_id,)
        ).fetchall()

    return [dict(r) for r in rows]
