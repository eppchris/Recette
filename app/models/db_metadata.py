"""
Module de gestion des catégories et tags de recettes
"""
from .db_core import get_db


def get_all_categories():
    """Récupère toutes les catégories triées par display_order avec le nombre de recettes"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                c.id,
                c.name_fr,
                c.name_jp,
                c.description_fr,
                c.description_jp,
                c.display_order,
                COUNT(rc.recipe_id) as recipe_count
            FROM category c
            LEFT JOIN recipe_category rc ON c.id = rc.category_id
            GROUP BY c.id, c.name_fr, c.name_jp, c.description_fr, c.description_jp, c.display_order
            ORDER BY c.display_order, c.name_fr
        """)
        return [dict(row) for row in cursor.fetchall()]


def get_all_tags():
    """Récupère tous les tags triés par nom avec le nombre de recettes"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                t.id,
                t.name_fr,
                t.name_jp,
                t.description_fr,
                t.description_jp,
                t.color,
                t.is_system,
                COUNT(rt.recipe_id) as recipe_count
            FROM tag t
            LEFT JOIN recipe_tag rt ON t.id = rt.tag_id
            GROUP BY t.id, t.name_fr, t.name_jp, t.description_fr, t.description_jp, t.color, t.is_system
            ORDER BY t.name_fr
        """)
        return [dict(row) for row in cursor.fetchall()]


def get_recipe_categories(recipe_id: int):
    """Récupère les catégories d'une recette"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.name_fr, c.name_jp, c.description_fr, c.description_jp
            FROM category c
            JOIN recipe_category rc ON c.id = rc.category_id
            WHERE rc.recipe_id = ?
            ORDER BY c.display_order
        """, (recipe_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_recipe_tags(recipe_id: int):
    """Récupère les tags d'une recette"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.name_fr, t.name_jp, t.description_fr, t.description_jp, t.color
            FROM tag t
            JOIN recipe_tag rt ON t.id = rt.tag_id
            WHERE rt.recipe_id = ?
            ORDER BY t.name_fr
        """, (recipe_id,))
        return [dict(row) for row in cursor.fetchall()]


def set_recipe_categories(recipe_id: int, category_ids: list):
    """Définit les catégories d'une recette (remplace les anciennes)"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Supprimer les anciennes associations
        cursor.execute("DELETE FROM recipe_category WHERE recipe_id = ?", (recipe_id,))
        # Ajouter les nouvelles
        for category_id in category_ids:
            cursor.execute(
                "INSERT INTO recipe_category (recipe_id, category_id) VALUES (?, ?)",
                (recipe_id, category_id)
            )
        conn.commit()


def set_recipe_tags(recipe_id: int, tag_ids: list):
    """Définit les tags d'une recette (remplace les anciens)"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Supprimer les anciennes associations
        cursor.execute("DELETE FROM recipe_tag WHERE recipe_id = ?", (recipe_id,))
        # Ajouter les nouvelles
        for tag_id in tag_ids:
            cursor.execute(
                "INSERT INTO recipe_tag (recipe_id, tag_id) VALUES (?, ?)",
                (recipe_id, tag_id)
            )
        conn.commit()


def create_tag(name_fr: str, name_jp: str, description_fr: str = None,
               description_jp: str = None, color: str = "#3B82F6"):
    """Crée un nouveau tag personnalisé"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tag (name_fr, name_jp, description_fr, description_jp, color, is_system)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (name_fr, name_jp, description_fr, description_jp, color))
        conn.commit()
        return cursor.lastrowid


def update_tag(tag_id: int, name_fr: str = None, name_jp: str = None,
               description_fr: str = None, description_jp: str = None,
               color: str = None) -> bool:
    """
    Modifier un tag existant
    Ne peut modifier que les tags non-système
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Vérifier que ce n'est pas un tag système
        cursor.execute("SELECT is_system FROM tag WHERE id = ?", (tag_id,))
        row = cursor.fetchone()
        if not row:
            return False
        if row['is_system']:
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
        if color is not None:
            updates.append("color = ?")
            params.append(color)

        if not updates:
            return False

        params.append(tag_id)
        query = f"UPDATE tag SET {', '.join(updates)} WHERE id = ?"

        cursor.execute(query, params)
        conn.commit()
        return True


def delete_tag(tag_id: int):
    """
    Supprime un tag (seulement si is_system = 0 et non utilisé)
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Vérifier que ce n'est pas un tag système
        cursor.execute("SELECT is_system FROM tag WHERE id = ?", (tag_id,))
        row = cursor.fetchone()
        if row and row['is_system'] == 1:
            raise ValueError("Cannot delete system tag")

        # Vérifier si le tag est utilisé par des recettes
        cursor.execute("""
            SELECT COUNT(*) as count FROM recipe_tag WHERE tag_id = ?
        """, (tag_id,))
        row = cursor.fetchone()

        if row['count'] > 0:
            raise ValueError(f"Cannot delete tag: used by {row['count']} recipe(s)")

        cursor.execute("DELETE FROM tag WHERE id = ?", (tag_id,))
        conn.commit()


def create_category(name_fr: str, name_jp: str, description_fr: str = None,
                   description_jp: str = None):
    """Crée une nouvelle catégorie"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Trouver le prochain display_order
        cursor.execute("SELECT MAX(display_order) as max_order FROM category")
        row = cursor.fetchone()
        next_order = (row['max_order'] or 0) + 1

        cursor.execute("""
            INSERT INTO category (name_fr, name_jp, description_fr, description_jp, display_order)
            VALUES (?, ?, ?, ?, ?)
        """, (name_fr, name_jp, description_fr, description_jp, next_order))
        conn.commit()
        return cursor.lastrowid


def update_category(category_id: int, name_fr: str = None, name_jp: str = None,
                   description_fr: str = None, description_jp: str = None) -> bool:
    """Modifier une catégorie existante"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Vérifier que la catégorie existe
        cursor.execute("SELECT id FROM category WHERE id = ?", (category_id,))
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

        params.append(category_id)
        query = f"UPDATE category SET {', '.join(updates)} WHERE id = ?"

        cursor.execute(query, params)
        conn.commit()
        return True


def delete_category(category_id: int):
    """
    Supprime une catégorie
    Impossible si elle est utilisée par au moins une recette
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Vérifier si la catégorie est utilisée
        cursor.execute("""
            SELECT COUNT(*) as count FROM recipe_category WHERE category_id = ?
        """, (category_id,))
        row = cursor.fetchone()

        if row['count'] > 0:
            raise ValueError(f"Cannot delete category: used by {row['count']} recipe(s)")

        # Supprimer la catégorie
        cursor.execute("DELETE FROM category WHERE id = ?", (category_id,))
        conn.commit()
