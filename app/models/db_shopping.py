"""
Module de gestion des listes de courses
"""
from .db_core import get_db


def get_shopping_list_items(event_id: int, lang: str = "fr"):
    """
    Récupère tous les items d'une liste de courses pour un événement

    Args:
        event_id: ID de l'événement
        lang: Langue pour la traduction des noms d'ingrédients ("fr" ou "jp")
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # DEBUG: Vérifier que la table existe et lister ses colonnes
        cursor.execute("PRAGMA table_info(shopping_list_item)")
        columns = cursor.fetchall()
        print(f"DEBUG: shopping_list_item columns: {[col[1] for col in columns]}")

        # Récupérer les items avec traduction depuis le catalogue
        cursor.execute("""
            SELECT
                sli.id,
                sli.event_id,
                sli.ingredient_name,
                CASE
                    WHEN ? = 'jp' AND ipc.ingredient_name_jp IS NOT NULL
                    THEN ipc.ingredient_name_jp
                    ELSE sli.ingredient_name
                END AS ingredient_name_display,
                sli.needed_quantity,
                sli.needed_unit,
                sli.purchase_quantity,
                sli.purchase_unit,
                sli.is_checked,
                sli.notes,
                sli.source_recipes,
                sli.position,
                sli.created_at,
                sli.updated_at,
                sli.planned_unit_price,
                sli.actual_total_price
            FROM shopping_list_item sli
            LEFT JOIN ingredient_price_catalog ipc
                ON LOWER(sli.ingredient_name) = LOWER(ipc.ingredient_name_fr)
            WHERE sli.event_id = ?
            ORDER BY sli.position, sli.ingredient_name
        """, (lang, event_id))

        items = []
        for row in cursor.fetchall():
            item = dict(row)
            # Utiliser le nom traduit pour l'affichage
            item['ingredient_name'] = item['ingredient_name_display']
            del item['ingredient_name_display']

            # Déserialiser le JSON des recettes sources
            if item['source_recipes']:
                import json
                item['source_recipes'] = json.loads(item['source_recipes'])
            items.append(item)

        return items


def save_shopping_list_items(event_id: int, items: list):
    """
    Sauvegarde les items d'une liste de courses (écrase l'existant)
    Cette fonction est appelée lors de la génération initiale de la liste
    """
    import json

    with get_db() as conn:
        cursor = conn.cursor()

        # Supprimer les items existants pour cet événement
        cursor.execute("DELETE FROM shopping_list_item WHERE event_id = ?", (event_id,))

        # Insérer les nouveaux items
        for position, item in enumerate(items):
            # Sérialiser les recettes sources en JSON
            source_recipes_json = json.dumps(item.get('source_recipes', []))

            cursor.execute("""
                INSERT INTO shopping_list_item (
                    event_id, ingredient_name,
                    needed_quantity, needed_unit,
                    purchase_quantity, purchase_unit,
                    is_checked, notes, source_recipes, position
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                item['ingredient_name'],
                item.get('total_quantity'),  # needed_quantity
                item.get('purchase_unit'),    # needed_unit
                item.get('total_quantity'),  # purchase_quantity (initialement = needed)
                item.get('purchase_unit'),    # purchase_unit (initialement = needed)
                False,                        # is_checked
                item.get('notes', ''),
                source_recipes_json,
                position
            ))

        conn.commit()


def update_shopping_list_item(
    item_id: int,
    purchase_quantity=None,
    purchase_unit=None,
    is_checked=None,
    notes=None
):
    """
    Met à jour un item de liste de courses
    """
    updates = []
    params = []

    if purchase_quantity is not None:
        updates.append("purchase_quantity = ?")
        params.append(purchase_quantity)

    if purchase_unit is not None:
        updates.append("purchase_unit = ?")
        params.append(purchase_unit)

    if is_checked is not None:
        updates.append("is_checked = ?")
        params.append(1 if is_checked else 0)

    if notes is not None:
        updates.append("notes = ?")
        params.append(notes)

    if not updates:
        return False

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(item_id)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE shopping_list_item
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)
        conn.commit()

        return cursor.rowcount > 0


def update_shopping_list_item_prices(item_id: int, planned_unit_price=None, actual_total_price=None):
    """
    Met à jour les prix prévus et réels d'un ingrédient dans la liste de courses

    Args:
        item_id: ID de l'item
        planned_unit_price: Prix unitaire prévu
        actual_total_price: Prix total réel payé
    """
    updates = []
    params = []

    if planned_unit_price is not None:
        updates.append("planned_unit_price = ?")
        params.append(planned_unit_price)

    if actual_total_price is not None:
        updates.append("actual_total_price = ?")
        params.append(actual_total_price)

    if not updates:
        return False

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(item_id)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE shopping_list_item
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)
        conn.commit()

        return cursor.rowcount > 0


def update_event_ingredients_actual_total(event_id: int, actual_total: float):
    """
    Met à jour le montant total réel des ingrédients pour un événement

    Args:
        event_id: ID de l'événement
        actual_total: Montant total réel payé pour les ingrédients
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE event
            SET ingredients_actual_total = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (actual_total, event_id))
        conn.commit()
        return cursor.rowcount > 0


def delete_shopping_list_item(item_id: int):
    """
    Supprime un item de liste de courses
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM shopping_list_item WHERE id = ?", (item_id,))
        conn.commit()
        return cursor.rowcount > 0


def delete_all_shopping_list_items(event_id: int):
    """
    Supprime tous les items de la shopping list d'un événement
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM shopping_list_item WHERE event_id = ?", (event_id,))
        conn.commit()
        return cursor.rowcount


def regenerate_shopping_list(event_id: int, lang: str = "fr"):
    """
    Régénère la liste de courses pour un événement
    (utile si l'utilisateur veut recalculer depuis les recettes)
    """
    from app.services.ingredient_aggregator import get_ingredient_aggregator
    from .db_events import get_event_recipes_with_ingredients

    # Récupérer les recettes avec leurs ingrédients
    recipes_data = get_event_recipes_with_ingredients(event_id, lang)

    # Agréger les ingrédients
    aggregator = get_ingredient_aggregator()
    aggregated_ingredients = aggregator.aggregate_ingredients(recipes_data, lang)

    # Sauvegarder dans la base de données
    save_shopping_list_items(event_id, aggregated_ingredients)

    return aggregated_ingredients
