"""
Module de gestion des conversions d'unités
"""
import sqlite3
from .db_core import get_db


def convert_unit(quantity: float, from_unit: str, to_unit: str) -> float:
    """
    Convertit une quantité d'une unité à une autre en utilisant la table de conversion
    Gère les conversions directes et en chaîne (ex: cs → ml → L)
    Cherche aussi dans les colonnes bilingues (FR/JP)

    Args:
        quantity: Quantité à convertir
        from_unit: Unité source (peut être FR ou JP)
        to_unit: Unité cible (peut être FR ou JP)

    Returns:
        Quantité convertie, ou None si aucune conversion n'est disponible
    """
    # Si les unités sont identiques, pas de conversion
    if from_unit.lower() == to_unit.lower():
        return quantity

    with get_db() as conn:
        cursor = conn.cursor()

        # Chercher la conversion directe (dans toutes les colonnes: from_unit, from_unit_fr, from_unit_jp)
        cursor.execute("""
            SELECT factor
            FROM unit_conversion
            WHERE (LOWER(from_unit) = LOWER(?) OR LOWER(from_unit_fr) = LOWER(?) OR LOWER(from_unit_jp) = LOWER(?))
              AND (LOWER(to_unit) = LOWER(?) OR LOWER(to_unit_fr) = LOWER(?) OR LOWER(to_unit_jp) = LOWER(?))
        """, (from_unit, from_unit, from_unit, to_unit, to_unit, to_unit))

        result = cursor.fetchone()
        if result:
            return quantity * result['factor']

        # Essayer conversion en chaîne (1 étape intermédiaire)
        # Exemple: cs → ml → L
        cursor.execute("""
            SELECT c1.to_unit as intermediate, c1.factor as factor1, c2.factor as factor2
            FROM unit_conversion c1
            JOIN unit_conversion c2 ON (
                LOWER(c1.to_unit) = LOWER(c2.from_unit) OR
                LOWER(c1.to_unit) = LOWER(c2.from_unit_fr) OR
                LOWER(c1.to_unit) = LOWER(c2.from_unit_jp)
            )
            WHERE (LOWER(c1.from_unit) = LOWER(?) OR LOWER(c1.from_unit_fr) = LOWER(?) OR LOWER(c1.from_unit_jp) = LOWER(?))
              AND (LOWER(c2.to_unit) = LOWER(?) OR LOWER(c2.to_unit_fr) = LOWER(?) OR LOWER(c2.to_unit_jp) = LOWER(?))
            LIMIT 1
        """, (from_unit, from_unit, from_unit, to_unit, to_unit, to_unit))

        result = cursor.fetchone()
        if result:
            # Conversion en chaîne: quantity * factor1 * factor2
            return quantity * result['factor1'] * result['factor2']

        # Pas de conversion trouvée
        return None


def get_convertible_units(unit: str):
    """
    Retourne la liste des unités vers lesquelles on peut convertir depuis une unité donnée

    Args:
        unit: Unité source

    Returns:
        Liste de tuples (to_unit, factor, category, notes)
    """
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT to_unit, factor, category, notes
            FROM unit_conversion
            WHERE LOWER(from_unit) = LOWER(?)
            ORDER BY category, to_unit
        """, (unit,))

        return cursor.fetchall()


def get_all_unit_conversions(search: str = None):
    """
    Récupère toutes les conversions d'unités avec filtrage optionnel

    Args:
        search: Terme de recherche (optionnel)

    Returns:
        Liste de dictionnaires avec les conversions (incluant colonnes bilingues FR/JP)
    """
    with get_db() as conn:
        cursor = conn.cursor()

        if search:
            cursor.execute("""
                SELECT id, from_unit, to_unit, factor, category, notes,
                       from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp
                FROM unit_conversion
                WHERE from_unit LIKE ? OR to_unit LIKE ? OR category LIKE ? OR notes LIKE ?
                   OR from_unit_fr LIKE ? OR to_unit_fr LIKE ?
                   OR from_unit_jp LIKE ? OR to_unit_jp LIKE ?
                ORDER BY category, from_unit, to_unit
            """, (f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%',
                  f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%'))
        else:
            cursor.execute("""
                SELECT id, from_unit, to_unit, factor, category, notes,
                       from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp
                FROM unit_conversion
                ORDER BY category, from_unit, to_unit
            """)

        return [dict(row) for row in cursor.fetchall()]


def get_unit_conversion_by_id(conversion_id: int):
    """
    Récupère une conversion par son ID

    Args:
        conversion_id: ID de la conversion

    Returns:
        Dictionnaire avec les données de la conversion (incluant colonnes bilingues) ou None
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, from_unit, to_unit, factor, category, notes,
                   from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp
            FROM unit_conversion
            WHERE id = ?
        """, (conversion_id,))

        result = cursor.fetchone()
        return dict(result) if result else None


def add_unit_conversion(from_unit: str, to_unit: str, factor: float, category: str = None, notes: str = None,
                       from_unit_fr: str = None, to_unit_fr: str = None,
                       from_unit_jp: str = None, to_unit_jp: str = None):
    """
    Ajoute une nouvelle conversion d'unité

    Args:
        from_unit: Unité source (code technique)
        to_unit: Unité cible (code technique)
        factor: Facteur de conversion
        category: Catégorie (optionnel)
        notes: Notes explicatives (optionnel)
        from_unit_fr, to_unit_fr: Noms français (optionnel, par défaut = from_unit/to_unit)
        from_unit_jp, to_unit_jp: Noms japonais (optionnel, par défaut = from_unit/to_unit)

    Returns:
        ID de la conversion créée
    """
    # Utiliser les valeurs par défaut si non fournies
    from_unit_fr = from_unit_fr or from_unit
    to_unit_fr = to_unit_fr or to_unit
    from_unit_jp = from_unit_jp or from_unit
    to_unit_jp = to_unit_jp or to_unit

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO unit_conversion (from_unit, to_unit, factor, category, notes,
                                        from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (from_unit, to_unit, factor, category, notes,
              from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp))

        return cursor.lastrowid


def update_unit_conversion(conversion_id: int, from_unit: str, to_unit: str, factor: float,
                           category: str = None, notes: str = None,
                           from_unit_fr: str = None, to_unit_fr: str = None,
                           from_unit_jp: str = None, to_unit_jp: str = None):
    """
    Met à jour une conversion existante

    Args:
        conversion_id: ID de la conversion
        from_unit: Unité source (code technique)
        to_unit: Unité cible (code technique)
        factor: Facteur de conversion
        category: Catégorie (optionnel)
        notes: Notes explicatives (optionnel)
        from_unit_fr, to_unit_fr: Noms français (optionnel, par défaut = from_unit/to_unit)
        from_unit_jp, to_unit_jp: Noms japonais (optionnel, par défaut = from_unit/to_unit)
    """
    # Utiliser les valeurs par défaut si non fournies
    from_unit_fr = from_unit_fr or from_unit
    to_unit_fr = to_unit_fr or to_unit
    from_unit_jp = from_unit_jp or from_unit
    to_unit_jp = to_unit_jp or to_unit

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE unit_conversion
            SET from_unit = ?, to_unit = ?, factor = ?, category = ?, notes = ?,
                from_unit_fr = ?, to_unit_fr = ?, from_unit_jp = ?, to_unit_jp = ?
            WHERE id = ?
        """, (from_unit, to_unit, factor, category, notes,
              from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp, conversion_id))


def delete_unit_conversion(conversion_id: int):
    """
    Supprime une conversion d'unité

    Args:
        conversion_id: ID de la conversion à supprimer
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM unit_conversion WHERE id = ?", (conversion_id,))


def get_specific_conversion(ingredient_name: str, from_unit: str):
    """
    Récupère une conversion spécifique pour un ingrédient

    Args:
        ingredient_name: Nom de l'ingrédient
        from_unit: Unité source

    Returns:
        Dict avec la conversion ou None
    """
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM ingredient_specific_conversions
            WHERE LOWER(ingredient_name_fr) = LOWER(?)
              AND LOWER(from_unit) = LOWER(?)
        """, (ingredient_name, from_unit))

        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_specific_conversions():
    """
    Récupère toutes les conversions spécifiques

    Returns:
        Liste de dicts avec les conversions
    """
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM ingredient_specific_conversions
            ORDER BY ingredient_name_fr, from_unit
        """)

        return [dict(row) for row in cursor.fetchall()]


def add_specific_conversion(ingredient_name_fr: str, from_unit: str, to_unit: str, factor: float, notes: str = None):
    """
    Ajoute une conversion spécifique

    Args:
        ingredient_name_fr: Nom de l'ingrédient
        from_unit: Unité source
        to_unit: Unité cible
        factor: Facteur de conversion
        notes: Notes optionnelles
    """
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ingredient_specific_conversions
                (ingredient_name_fr, from_unit, to_unit, factor, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (ingredient_name_fr, from_unit, to_unit, factor, notes))

        conn.commit()


def update_specific_conversion(conversion_id: int, from_unit: str, to_unit: str, factor: float, notes: str = None):
    """
    Met à jour une conversion spécifique

    Args:
        conversion_id: ID de la conversion
        from_unit: Unité source
        to_unit: Unité cible
        factor: Facteur de conversion
        notes: Notes optionnelles
    """
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE ingredient_specific_conversions
            SET from_unit = ?, to_unit = ?, factor = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (from_unit, to_unit, factor, notes, conversion_id))

        conn.commit()


def delete_specific_conversion(conversion_id: int):
    """
    Supprime une conversion spécifique

    Args:
        conversion_id: ID de la conversion
    """
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM ingredient_specific_conversions
            WHERE id = ?
        """, (conversion_id,))

        conn.commit()
