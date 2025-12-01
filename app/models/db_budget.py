"""
Module de gestion du budget des événements
"""
from .db_core import get_db


def get_event_budget_planned(event_id: int):
    """
    Récupère le budget prévisionnel d'un événement
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT budget_planned FROM event WHERE id = ?", (event_id,))
        result = cursor.fetchone()
        return result['budget_planned'] if result else None


def update_event_budget_planned(event_id: int, budget_planned: float):
    """
    Met à jour le budget prévisionnel d'un événement
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE event SET budget_planned = ? WHERE id = ?",
            (budget_planned, event_id)
        )
        conn.commit()
        return cursor.rowcount > 0


def update_event_currency(event_id: int, currency: str):
    """
    Met à jour la devise d'un événement

    Args:
        event_id: ID de l'événement
        currency: Code de devise ('EUR' ou 'JPY')

    Returns:
        True si la mise à jour a réussi, False sinon
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE event SET currency = ? WHERE id = ?",
            (currency, event_id)
        )
        conn.commit()
        return cursor.rowcount > 0


def list_expense_categories(lang: str = 'fr'):
    """
    Liste toutes les catégories de dépenses avec leurs traductions

    Args:
        lang: Code de langue ('fr' ou 'jp')

    Returns:
        Liste des catégories avec nom traduit
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                c.id,
                c.icon,
                c.is_system,
                c.created_at,
                COALESCE(t.name, 'Unknown') AS name
            FROM expense_category c
            LEFT JOIN expense_category_translation t
                ON t.category_id = c.id AND t.lang = ?
            ORDER BY c.is_system DESC, t.name ASC
        """, (lang,))
        return [dict(row) for row in cursor.fetchall()]


def create_expense_category(name_fr: str, name_jp: str, icon: str = '📋'):
    """
    Crée une nouvelle catégorie de dépense personnalisée avec traductions

    Args:
        name_fr: Nom en français
        name_jp: Nom en japonais
        icon: Icône (emoji)

    Returns:
        ID de la catégorie créée
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Créer la catégorie
        cursor.execute(
            "INSERT INTO expense_category (icon, is_system) VALUES (?, 0)",
            (icon,)
        )
        category_id = cursor.lastrowid

        # Ajouter les traductions
        cursor.execute(
            "INSERT INTO expense_category_translation (category_id, lang, name) VALUES (?, 'fr', ?)",
            (category_id, name_fr)
        )
        cursor.execute(
            "INSERT INTO expense_category_translation (category_id, lang, name) VALUES (?, 'jp', ?)",
            (category_id, name_jp)
        )

        conn.commit()
        return category_id


def update_expense_category(category_id: int, name_fr: str = None, name_jp: str = None, icon: str = None):
    """
    Met à jour une catégorie de dépense (uniquement les catégories non-système)

    Args:
        category_id: ID de la catégorie
        name_fr: Nouveau nom en français (optionnel)
        name_jp: Nouveau nom en japonais (optionnel)
        icon: Nouvelle icône (optionnel)

    Returns:
        True si la mise à jour a réussi
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Vérifier que c'est une catégorie non-système
        cursor.execute("SELECT is_system FROM expense_category WHERE id = ?", (category_id,))
        result = cursor.fetchone()
        if not result or result['is_system']:
            return False

        # Mettre à jour l'icône si fournie
        if icon is not None:
            cursor.execute(
                "UPDATE expense_category SET icon = ? WHERE id = ?",
                (icon, category_id)
            )

        # Mettre à jour les traductions si fournies
        if name_fr is not None:
            cursor.execute("""
                INSERT OR REPLACE INTO expense_category_translation (category_id, lang, name)
                VALUES (?, 'fr', ?)
            """, (category_id, name_fr))

        if name_jp is not None:
            cursor.execute("""
                INSERT OR REPLACE INTO expense_category_translation (category_id, lang, name)
                VALUES (?, 'jp', ?)
            """, (category_id, name_jp))

        conn.commit()
        return True


def delete_expense_category(category_id: int):
    """
    Supprime une catégorie de dépense (uniquement les catégories non-système)
    Les traductions sont supprimées automatiquement par CASCADE
    """
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM expense_category WHERE id = ? AND is_system = 0",
                (category_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        except:
            return False


def get_event_expenses(event_id: int, lang: str = 'fr'):
    """
    Récupère toutes les dépenses d'un événement avec noms de catégories traduits

    Args:
        event_id: ID de l'événement
        lang: Code de langue ('fr' ou 'jp')

    Returns:
        Liste des dépenses avec catégories traduites
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                e.id,
                e.event_id,
                e.category_id,
                COALESCE(t.name, 'Unknown') AS category_name,
                c.icon AS category_icon,
                e.description,
                e.planned_amount,
                e.actual_amount,
                e.is_paid,
                e.paid_date,
                e.notes,
                e.created_at,
                e.updated_at
            FROM event_expense e
            JOIN expense_category c ON c.id = e.category_id
            LEFT JOIN expense_category_translation t
                ON t.category_id = c.id AND t.lang = ?
            WHERE e.event_id = ?
            ORDER BY e.created_at DESC
        """, (lang, event_id))
        return [dict(row) for row in cursor.fetchall()]


def create_event_expense(
    event_id: int,
    category_id: int,
    description: str,
    planned_amount: float,
    actual_amount: float = None,
    is_paid: bool = False,
    paid_date: str = None,
    notes: str = ''
):
    """
    Crée une nouvelle dépense pour un événement
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO event_expense (
                event_id, category_id, description,
                planned_amount, actual_amount,
                is_paid, paid_date, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id, category_id, description,
            planned_amount, actual_amount,
            is_paid, paid_date, notes
        ))
        conn.commit()
        return cursor.lastrowid


def update_event_expense(
    expense_id: int,
    category_id: int = None,
    description: str = None,
    planned_amount: float = None,
    actual_amount: float = None,
    is_paid: bool = None,
    paid_date: str = None,
    notes: str = None
):
    """
    Met à jour une dépense d'événement
    """
    updates = []
    params = []

    if category_id is not None:
        updates.append("category_id = ?")
        params.append(category_id)

    if description is not None:
        updates.append("description = ?")
        params.append(description)

    if planned_amount is not None:
        updates.append("planned_amount = ?")
        params.append(planned_amount)

    if actual_amount is not None:
        updates.append("actual_amount = ?")
        params.append(actual_amount)

    if is_paid is not None:
        updates.append("is_paid = ?")
        params.append(1 if is_paid else 0)

    if paid_date is not None:
        updates.append("paid_date = ?")
        params.append(paid_date)

    if notes is not None:
        updates.append("notes = ?")
        params.append(notes)

    if not updates:
        return False

    params.append(expense_id)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE event_expense
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)
        conn.commit()
        return cursor.rowcount > 0


def delete_event_expense(expense_id: int):
    """
    Supprime une dépense d'événement
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM event_expense WHERE id = ?", (expense_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_event_budget_summary(event_id: int):
    """
    Calcule un résumé budgétaire complet pour un événement
    Retourne le budget prévisionnel, les dépenses prévues/réelles, et les totaux des ingrédients
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Budget prévisionnel de l'événement
        cursor.execute("SELECT budget_planned FROM event WHERE id = ?", (event_id,))
        result = cursor.fetchone()
        budget_planned = result['budget_planned'] if result and result['budget_planned'] else 0

        # Somme des dépenses (hors ingrédients)
        cursor.execute("""
            SELECT
                COALESCE(SUM(planned_amount), 0) as total_planned,
                COALESCE(SUM(actual_amount), 0) as total_actual
            FROM event_expense
            WHERE event_id = ?
        """, (event_id,))
        expenses = cursor.fetchone()

        # Somme des ingrédients de la liste de courses
        cursor.execute("""
            SELECT
                COALESCE(SUM(
                    CASE
                        WHEN planned_unit_price IS NOT NULL AND purchase_quantity IS NOT NULL
                        THEN planned_unit_price * purchase_quantity
                        ELSE 0
                    END
                ), 0) as ingredients_planned,
                COALESCE(SUM(
                    CASE
                        WHEN actual_unit_price IS NOT NULL AND purchase_quantity IS NOT NULL
                        THEN actual_unit_price * purchase_quantity
                        ELSE 0
                    END
                ), 0) as ingredients_actual
            FROM shopping_list_item
            WHERE event_id = ?
        """, (event_id,))
        ingredients = cursor.fetchone()

        return {
            'budget_planned': budget_planned,
            'expenses_planned': expenses['total_planned'],
            'expenses_actual': expenses['total_actual'],
            'ingredients_planned': ingredients['ingredients_planned'],
            'ingredients_actual': ingredients['ingredients_actual'],
            'total_planned': expenses['total_planned'] + ingredients['ingredients_planned'],
            'total_actual': expenses['total_actual'] + ingredients['ingredients_actual'],
            'remaining': budget_planned - (expenses['total_actual'] + ingredients['ingredients_actual']),
            'variance': (expenses['total_actual'] + ingredients['ingredients_actual']) - (expenses['total_planned'] + ingredients['ingredients_planned'])
        }


def save_expense_ingredient_details(expense_id: int, ingredients_data: list):
    """
    Sauvegarde le détail des ingrédients pour une dépense

    Args:
        expense_id: ID de la dépense
        ingredients_data: Liste de dictionnaires avec les données des ingrédients
            [{'shopping_list_item_id': int, 'ingredient_name': str, 'quantity': float,
              'unit': str, 'planned_unit_price': float, 'actual_unit_price': float}]
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Supprimer les détails existants
        cursor.execute("DELETE FROM expense_ingredient_detail WHERE expense_id = ?", (expense_id,))

        # Insérer les nouveaux détails
        for item in ingredients_data:
            planned_total = item['quantity'] * item.get('planned_unit_price', 0) if item.get('planned_unit_price') else None
            actual_total = item['quantity'] * item.get('actual_unit_price', 0) if item.get('actual_unit_price') else None

            cursor.execute("""
                INSERT INTO expense_ingredient_detail (
                    expense_id, shopping_list_item_id, ingredient_name,
                    quantity, unit, planned_unit_price, actual_unit_price,
                    planned_total, actual_total
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                expense_id,
                item['shopping_list_item_id'],
                item['ingredient_name'],
                item['quantity'],
                item['unit'],
                item.get('planned_unit_price'),
                item.get('actual_unit_price'),
                planned_total,
                actual_total
            ))

        conn.commit()


def get_expense_ingredient_details(expense_id: int):
    """
    Récupère le détail des ingrédients pour une dépense

    Returns:
        Liste des ingrédients avec leurs détails
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM expense_ingredient_detail
            WHERE expense_id = ?
            ORDER BY ingredient_name
        """, (expense_id,))

        return [dict(row) for row in cursor.fetchall()]
