# app/models/db.py
import os
import sqlite3
import contextlib

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "recette_dev.sqlite3"))

@contextlib.contextmanager
def get_db():
    """Context manager pour obtenir une connexion à la base de données"""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def list_recipes(lang: str):
    """
    Liste toutes les recettes dans la langue demandée
    
    Args:
        lang: Code de langue ('fr' ou 'jp')
    
    Returns:
        Liste des recettes avec leurs informations de base
    """
    with get_db() as con:
        sql = """
            SELECT 
                r.id,
                r.slug,
                r.servings_default AS servings,
                r.country,
                COALESCE(rt.name, r.slug) AS name,
                rt.recipe_type AS type
            FROM recipe r
            LEFT JOIN recipe_translation rt ON rt.recipe_id = r.id AND rt.lang = ?
            ORDER BY name COLLATE NOCASE
        """
        rows = con.execute(sql, (lang,)).fetchall()
        # Convertir les Row en dictionnaires pour le JSON
        return [dict(row) for row in rows]


def get_recipe_by_slug(slug: str, lang: str):
    """
    Récupère une recette complète avec ses ingrédients et étapes
    
    Args:
        slug: Identifiant unique de la recette
        lang: Code de langue ('fr' ou 'jp')
    
    Returns:
        Tuple (recipe, ingredients, steps) ou None si non trouvée
    """
    with get_db() as con:
        # Récupérer la recette
        recipe_sql = """
            SELECT 
                r.id,
                r.slug,
                r.servings_default AS servings,
                r.country,
                COALESCE(rt.name, r.slug) AS name,
                rt.recipe_type AS type
            FROM recipe r
            LEFT JOIN recipe_translation rt ON rt.recipe_id = r.id AND rt.lang = ?
            WHERE r.slug = ?
        """
        recipe = con.execute(recipe_sql, (lang, slug)).fetchone()
        
        if not recipe:
            return None
        
        # Récupérer les ingrédients avec leurs traductions
        ingredients_sql = """
            SELECT 
                ri.id,
                ri.position,
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

        # Convertir en dictionnaires pour faciliter la manipulation
        ingredients_list = [dict(ing) for ing in ingredients]

        # Récupérer les étapes avec leurs traductions
        steps_sql = """
            SELECT
                s.position,
                COALESCE(st.text, '') AS text
            FROM step s
            LEFT JOIN step_translation st ON st.step_id = s.id AND st.lang = ?
            WHERE s.recipe_id = ?
            ORDER BY s.position
        """
        steps = con.execute(steps_sql, (lang, recipe['id'])).fetchall()
        steps_list = [dict(step) for step in steps]

        return dict(recipe), ingredients_list, steps_list


def get_recipe_steps_with_ids(recipe_id: int, lang: str):
    """
    Récupère les étapes d'une recette avec leurs IDs

    Args:
        recipe_id: ID de la recette
        lang: Langue des traductions

    Returns:
        Liste de dictionnaires contenant id, position et text
    """
    with get_db() as con:
        sql = """
            SELECT
                s.id,
                s.position,
                COALESCE(st.text, '') AS text
            FROM step s
            LEFT JOIN step_translation st ON st.step_id = s.id AND st.lang = ?
            WHERE s.recipe_id = ?
            ORDER BY s.position
        """
        steps = con.execute(sql, (lang, recipe_id)).fetchall()
        return [dict(step) for step in steps]


def check_translation_exists(recipe_id: int, lang: str) -> bool:
    """
    Vérifie si une traduction existe pour une recette dans une langue donnée

    Args:
        recipe_id: ID de la recette
        lang: Code de langue ('fr' ou 'jp')

    Returns:
        True si la traduction existe, False sinon
    """
    with get_db() as con:
        sql = "SELECT COUNT(*) as count FROM recipe_translation WHERE recipe_id = ? AND lang = ?"
        result = con.execute(sql, (recipe_id, lang)).fetchone()
        return result['count'] > 0


def get_recipe_id_by_slug(slug: str) -> int:
    """
    Récupère l'ID d'une recette à partir de son slug

    Args:
        slug: Slug de la recette

    Returns:
        ID de la recette ou None si non trouvée
    """
    with get_db() as con:
        sql = "SELECT id FROM recipe WHERE slug = ?"
        result = con.execute(sql, (slug,)).fetchone()
        return result['id'] if result else None


def get_source_language(recipe_id: int) -> str:
    """
    Détermine la langue source disponible pour une recette

    Args:
        recipe_id: ID de la recette

    Returns:
        Code de langue ('fr' ou 'jp') ou None si aucune traduction
    """
    with get_db() as con:
        sql = "SELECT lang FROM recipe_translation WHERE recipe_id = ? LIMIT 1"
        result = con.execute(sql, (recipe_id,)).fetchone()
        return result['lang'] if result else None


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


def insert_ingredient_translation(ingredient_id: int, lang: str, name: str, unit: str):
    """
    Insère une nouvelle traduction d'ingrédient

    Args:
        ingredient_id: ID de l'ingrédient
        lang: Code de langue
        name: Nom traduit
        unit: Unité (copiée)
    """
    with get_db() as con:
        sql = """
            INSERT INTO recipe_ingredient_translation (recipe_ingredient_id, lang, name, unit)
            VALUES (?, ?, ?, ?)
        """
        con.execute(sql, (ingredient_id, lang, name, unit))


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