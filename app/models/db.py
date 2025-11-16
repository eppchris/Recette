# app/models/db.py
import os
import sqlite3
import contextlib
import time
from functools import wraps

# Déterminer le chemin de la base de données selon l'environnement
# Même nom en dev et prod, juste un dossier différent
env = os.getenv("ENV", "dev")
db_name = "recette.sqlite3"  # Nom unifié pour dev et prod
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", db_name))

# Initialiser le mode WAL une seule fois au démarrage
def _init_db():
    """Initialise la base de données avec le mode WAL"""
    try:
        con = sqlite3.connect(DB_PATH, timeout=30.0)
        con.execute("PRAGMA journal_mode=WAL").fetchone()
        con.close()
    except sqlite3.OperationalError:
        # Si la base est verrouillée, on continue quand même
        # (peut-être ouverte dans DB Browser ou autre)
        pass

# Appeler l'initialisation au chargement du module
_init_db()

@contextlib.contextmanager
def get_db():
    """Context manager pour obtenir une connexion à la base de données"""
    con = None
    try:
        con = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
        con.row_factory = sqlite3.Row

        # Configurer le busy_timeout pour cette connexion
        con.execute("PRAGMA busy_timeout=30000")  # 30 secondes en millisecondes

        # Optimisations pour réduire les disk I/O errors
        con.execute("PRAGMA synchronous=NORMAL")
        con.execute("PRAGMA temp_store=MEMORY")
        con.execute("PRAGMA cache_size=-64000")  # 64MB cache

        yield con
        con.commit()
    except Exception as e:
        if con:
            con.rollback()
        raise
    finally:
        if con:
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
                r.image_url,
                r.thumbnail_url,
                COALESCE(rt.name, r.slug) AS name,
                rt.recipe_type AS type
            FROM recipe r
            LEFT JOIN recipe_translation rt ON rt.recipe_id = r.id AND rt.lang = ?
            ORDER BY name COLLATE NOCASE
        """
        rows = con.execute(sql, (lang,)).fetchall()
        # Convertir les Row en dictionnaires pour le JSON
        return [dict(row) for row in rows]


def list_recipes_by_type(recipe_type: str, lang: str):
    """
    Liste toutes les recettes d'un type donné dans la langue demandée

    Args:
        recipe_type: Type de recette (PRO, MASTER, PERSO, etc.)
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
                r.image_url,
                r.thumbnail_url,
                COALESCE(rt.name, r.slug) AS name,
                rt.recipe_type AS type
            FROM recipe r
            LEFT JOIN recipe_translation rt ON rt.recipe_id = r.id AND rt.lang = ?
            WHERE rt.recipe_type = ?
            ORDER BY name COLLATE NOCASE
        """
        rows = con.execute(sql, (lang, recipe_type)).fetchall()
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
                r.image_url,
                r.thumbnail_url,
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


def update_servings_default(recipe_id: int, servings: int):
    """
    Met à jour le nombre de personnes par défaut

    Args:
        recipe_id: ID de la recette
        servings: Nombre de personnes
    """
    with get_db() as con:
        sql = """
            UPDATE recipe
            SET servings_default = ?
            WHERE id = ?
        """
        con.execute(sql, (servings, recipe_id))


def update_recipe_complete(recipe_id: int, lang: str, data: dict):
    """
    Met à jour une recette complète en une seule transaction

    Args:
        recipe_id: ID de la recette
        lang: Code de langue
        data: Dictionnaire contenant recipe_type, servings_default, ingredients, steps
    """
    with get_db() as con:
        # Mettre à jour le type de recette (traduction)
        if 'recipe_type' in data and data['recipe_type'] is not None:
            con.execute(
                "UPDATE recipe_translation SET recipe_type = ? WHERE recipe_id = ? AND lang = ?",
                (data['recipe_type'], recipe_id, lang)
            )

        # Mettre à jour le nombre de personnes par défaut
        if 'servings_default' in data and data['servings_default'] is not None:
            con.execute(
                "UPDATE recipe SET servings_default = ? WHERE id = ?",
                (data['servings_default'], recipe_id)
            )

        # Mettre à jour les ingrédients
        for ing in data.get('ingredients', []):
            # Mettre à jour la quantité (indépendante de la langue)
            if 'quantity' in ing:
                con.execute(
                    "UPDATE recipe_ingredient SET quantity = ? WHERE id = ?",
                    (ing['quantity'], ing['id'])
                )

            # Mettre à jour la traduction (nom, unité, notes)
            if 'name' in ing or 'unit' in ing:
                con.execute(
                    """UPDATE recipe_ingredient_translation
                       SET name = ?, unit = ?, notes = ?
                       WHERE recipe_ingredient_id = ? AND lang = ?""",
                    (ing.get('name', ''), ing.get('unit', ''), ing.get('notes', ''), ing['id'], lang)
                )

        # Mettre à jour les étapes
        for step in data.get('steps', []):
            if 'text' in step:
                con.execute(
                    "UPDATE step_translation SET text = ? WHERE step_id = ? AND lang = ?",
                    (step['text'], step['id'], lang)
                )


def delete_recipe(slug: str):
    """
    Supprime une recette et toutes ses données associées

    Args:
        slug: Identifiant unique de la recette

    Returns:
        bool: True si la suppression a réussi, False sinon
    """
    with get_db() as con:
        # Récupérer l'ID de la recette
        recipe = con.execute("SELECT id FROM recipe WHERE slug = ?", (slug,)).fetchone()

        if not recipe:
            return False

        recipe_id = recipe['id']

        # Supprimer les traductions des étapes
        con.execute("""
            DELETE FROM step_translation
            WHERE step_id IN (SELECT id FROM step WHERE recipe_id = ?)
        """, (recipe_id,))

        # Supprimer les étapes
        con.execute("DELETE FROM step WHERE recipe_id = ?", (recipe_id,))

        # Supprimer les traductions des ingrédients
        con.execute("""
            DELETE FROM recipe_ingredient_translation
            WHERE recipe_ingredient_id IN (SELECT id FROM recipe_ingredient WHERE recipe_id = ?)
        """, (recipe_id,))

        # Supprimer les ingrédients
        con.execute("DELETE FROM recipe_ingredient WHERE recipe_id = ?", (recipe_id,))

        # Supprimer les traductions de la recette
        con.execute("DELETE FROM recipe_translation WHERE recipe_id = ?", (recipe_id,))

        # Supprimer la recette
        con.execute("DELETE FROM recipe WHERE id = ?", (recipe_id,))

        return True


def update_recipe_image(recipe_id: int, image_url: str, thumbnail_url: str):
    """
    Met à jour les URLs d'image d'une recette

    Args:
        recipe_id: ID de la recette
        image_url: URL de l'image principale
        thumbnail_url: URL du thumbnail
    """
    with get_db() as con:
        sql = """
            UPDATE recipe
            SET image_url = ?, thumbnail_url = ?
            WHERE id = ?
        """
        con.execute(sql, (image_url, thumbnail_url, recipe_id))


def get_recipe_image_urls(recipe_id: int) -> tuple:
    """
    Récupère les URLs d'image d'une recette

    Args:
        recipe_id: ID de la recette

    Returns:
        Tuple (image_url, thumbnail_url)
    """
    with get_db() as con:
        sql = "SELECT image_url, thumbnail_url FROM recipe WHERE id = ?"
        result = con.execute(sql, (recipe_id,)).fetchone()
        if result:
            return result['image_url'], result['thumbnail_url']
        return None, None


# ============================================================================
# Fonctions pour la gestion des événements
# ============================================================================

def list_event_types():
    """
    Liste tous les types d'événements

    Returns:
        Liste des types d'événements
    """
    with get_db() as con:
        sql = "SELECT id, name, created_at FROM event_type ORDER BY name"
        rows = con.execute(sql).fetchall()
        return [dict(row) for row in rows]


def create_event_type(name: str):
    """
    Crée un nouveau type d'événement

    Args:
        name: Nom du type d'événement

    Returns:
        ID du nouveau type créé
    """
    with get_db() as con:
        sql = "INSERT INTO event_type (name) VALUES (?)"
        cursor = con.execute(sql, (name,))
        return cursor.lastrowid


def delete_event_type(event_type_id: int):
    """
    Supprime un type d'événement (si aucun événement ne l'utilise)

    Args:
        event_type_id: ID du type à supprimer

    Returns:
        True si suppression réussie, False sinon
    """
    with get_db() as con:
        try:
            sql = "DELETE FROM event_type WHERE id = ?"
            con.execute(sql, (event_type_id,))
            return True
        except:
            return False


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
                et.id AS event_type_id,
                et.name AS event_type_name
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
                et.id AS event_type_id,
                et.name AS event_type_name
            FROM event e
            JOIN event_type et ON et.id = e.event_type_id
            WHERE e.id = ?
        """
        result = con.execute(sql, (event_id,)).fetchone()
        return dict(result) if result else None


def create_event(event_type_id: int, name: str, event_date: str, location: str, attendees: int, notes: str = ''):
    """
    Crée un nouvel événement

    Args:
        event_type_id: ID du type d'événement
        name: Nom de l'événement
        event_date: Date de l'événement (format YYYY-MM-DD)
        location: Lieu de l'événement
        attendees: Nombre de convives
        notes: Notes optionnelles

    Returns:
        ID du nouvel événement créé
    """
    with get_db() as con:
        sql = """
            INSERT INTO event (event_type_id, name, event_date, location, attendees, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor = con.execute(sql, (event_type_id, name, event_date, location, attendees, notes))
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
                'recipe_name': recipe['name'],
                'servings_multiplier': recipe['servings_multiplier'],
                'ingredients': [dict(ing) for ing in ingredients]
            })

        return result


# ============================================================================
# GESTION DES LISTES DE COURSES
# ============================================================================

def get_shopping_list_items(event_id: int):
    """
    Récupère tous les items d'une liste de courses pour un événement
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # DEBUG: Vérifier que la table existe et lister ses colonnes
        cursor.execute("PRAGMA table_info(shopping_list_item)")
        columns = cursor.fetchall()
        print(f"DEBUG: shopping_list_item columns: {[col[1] for col in columns]}")

        cursor.execute("""
            SELECT id, event_id, ingredient_name,
                   needed_quantity, needed_unit,
                   purchase_quantity, purchase_unit,
                   is_checked, notes, source_recipes, position,
                   created_at, updated_at
            FROM shopping_list_item
            WHERE event_id = ?
            ORDER BY position, ingredient_name
        """, (event_id,))

        items = []
        for row in cursor.fetchall():
            item = dict(row)
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

    # Récupérer les recettes avec leurs ingrédients
    recipes_data = get_event_recipes_with_ingredients(event_id, lang)

    # Agréger les ingrédients
    aggregator = get_ingredient_aggregator()
    aggregated_ingredients = aggregator.aggregate_ingredients(recipes_data, lang)

    # Sauvegarder dans la base de données
    save_shopping_list_items(event_id, aggregated_ingredients)

    return aggregated_ingredients