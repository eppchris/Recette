"""
Module de gestion des traductions de recettes
"""
from .db_core import get_db


def insert_recipe_translation(recipe_id: int, lang: str, name: str, recipe_type: str):
    """
    Insère une nouvelle traduction de recette

    Args:
        recipe_id: ID de la recette
        lang: Code de langue
        name: Nom traduit
        recipe_type: Type de recette (copié de la version source)
    """
    with get_db() as con:
        sql = """
            INSERT INTO recipe_translation (recipe_id, lang, name, recipe_type)
            VALUES (?, ?, ?, ?)
        """
        con.execute(sql, (recipe_id, lang, name, recipe_type))


def insert_ingredient_translation(ingredient_id: int, lang: str, name: str, unit: str, notes: str = ''):
    """
    Insère une nouvelle traduction d'ingrédient

    Args:
        ingredient_id: ID de l'ingrédient
        lang: Code de langue
        name: Nom traduit
        unit: Unité (copiée)
        notes: Notes traduites (optionnel)
    """
    with get_db() as con:
        sql = """
            INSERT INTO recipe_ingredient_translation (recipe_ingredient_id, lang, name, unit, notes)
            VALUES (?, ?, ?, ?, ?)
        """
        con.execute(sql, (ingredient_id, lang, name, unit, notes))


def insert_step_translation(step_id: int, lang: str, text: str):
    """
    Insère une nouvelle traduction d'étape

    Args:
        step_id: ID de l'étape
        lang: Code de langue
        text: Texte traduit de l'étape
    """
    with get_db() as con:
        sql = """
            INSERT INTO step_translation (step_id, lang, text)
            VALUES (?, ?, ?)
        """
        con.execute(sql, (step_id, lang, text))


def update_ingredient_translation(ingredient_id: int, lang: str, name: str, unit: str, notes: str = None):
    """
    Met à jour la traduction d'un ingrédient

    Args:
        ingredient_id: ID de l'ingrédient
        lang: Code de langue
        name: Nom de l'ingrédient
        unit: Unité
        notes: Notes optionnelles
    """
    with get_db() as con:
        sql = """
            UPDATE recipe_ingredient_translation
            SET name = ?, unit = ?, notes = ?
            WHERE recipe_ingredient_id = ? AND lang = ?
        """
        con.execute(sql, (name, unit, notes, ingredient_id, lang))


def update_ingredient_quantity(ingredient_id: int, quantity: float):
    """
    Met à jour la quantité d'un ingrédient

    Args:
        ingredient_id: ID de l'ingrédient
        quantity: Nouvelle quantité
    """
    with get_db() as con:
        sql = """
            UPDATE recipe_ingredient
            SET quantity = ?
            WHERE id = ?
        """
        con.execute(sql, (quantity, ingredient_id))


def update_step_translation(step_id: int, lang: str, text: str):
    """
    Met à jour la traduction d'une étape

    Args:
        step_id: ID de l'étape
        lang: Code de langue
        text: Texte de l'étape
    """
    with get_db() as con:
        sql = """
            UPDATE step_translation
            SET text = ?
            WHERE step_id = ? AND lang = ?
        """
        con.execute(sql, (text, step_id, lang))


def update_recipe_type(recipe_id: int, lang: str, recipe_type: str):
    """
    Met à jour le type de recette (traduction)

    Args:
        recipe_id: ID de la recette
        lang: Code de langue
        recipe_type: Type de recette
    """
    with get_db() as con:
        sql = """
            UPDATE recipe_translation
            SET recipe_type = ?
            WHERE recipe_id = ? AND lang = ?
        """
        con.execute(sql, (recipe_type, recipe_id, lang))
