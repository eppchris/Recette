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
        
        # DEBUG : afficher les ingrédients récupérés
        print(f"DEBUG - Ingrédients récupérés pour recipe_id={recipe['id']}, lang={lang}:")
        for ing in ingredients:
            print(f"  - {dict(ing)}")
        
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
        
        return recipe, ingredients, steps