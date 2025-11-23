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
        # Entourer les PRAGMA d'un try/except pour éviter les erreurs I/O fatales
        try:
            con.execute("PRAGMA synchronous=NORMAL")
            con.execute("PRAGMA temp_store=MEMORY")
            con.execute("PRAGMA cache_size=-64000")  # 64MB cache
        except sqlite3.OperationalError as pragma_error:
            # Si les PRAGMA échouent, on continue quand même
            print(f"Warning: PRAGMA configuration failed: {pragma_error}")

        yield con
        con.commit()
    except sqlite3.OperationalError as e:
        if con:
            try:
                con.rollback()
            except:
                pass
        # Log l'erreur mais avec plus de contexte
        print(f"Database error: {e}")
        raise
    except Exception as e:
        if con:
            con.rollback()
        raise
    finally:
        if con:
            try:
                con.close()
            except:
                pass


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
                e.currency,
                e.budget_planned,
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
                e.currency,
                e.budget_planned,
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
                r.slug,
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
                'recipe_slug': recipe['slug'],
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


# ============================================================================
# GESTION DU BUDGET
# ============================================================================

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


# ============================================================================
# GESTION DES CATÉGORIES DE DÉPENSES (MULTILINGUE)
# ============================================================================

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


# ============================================================================
# GESTION DES DÉPENSES D'ÉVÉNEMENT
# ============================================================================

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


# ============================================================================
# GESTION DE L'HISTORIQUE DES PRIX D'INGRÉDIENTS
# ============================================================================

def get_ingredient_price_suggestions(ingredient_name: str, unit: str):
    """
    Récupère les suggestions de prix pour un ingrédient basées sur l'historique

    Args:
        ingredient_name: Nom de l'ingrédient (sera normalisé)
        unit: Unité de mesure

    Returns:
        Dict avec le prix suggéré et les statistiques d'usage
    """
    from app.services.ingredient_aggregator import get_ingredient_aggregator

    # Normaliser le nom pour la recherche
    aggregator = get_ingredient_aggregator()
    normalized_name = aggregator.normalize_ingredient_name(ingredient_name)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                ingredient_name_display,
                unit_price,
                unit,
                last_used_date,
                usage_count,
                updated_at
            FROM ingredient_price_history
            WHERE ingredient_name_normalized = ? AND unit = ?
            ORDER BY last_used_date DESC, usage_count DESC
            LIMIT 1
        """, (normalized_name, unit))

        result = cursor.fetchone()
        if result:
            return dict(result)
        return None


def update_ingredient_price_from_shopping_list(ingredient_name: str, unit: str, actual_price: float):
    """
    Met à jour l'historique des prix depuis la liste de courses
    Cette fonction est appelée automatiquement par le trigger, mais peut aussi être appelée manuellement

    Args:
        ingredient_name: Nom de l'ingrédient
        unit: Unité
        actual_price: Prix réel payé
    """
    from app.services.ingredient_aggregator import get_ingredient_aggregator

    aggregator = get_ingredient_aggregator()
    normalized_name = aggregator.normalize_ingredient_name(ingredient_name)

    with get_db() as conn:
        cursor = conn.cursor()

        # Vérifier si un prix existe déjà
        cursor.execute("""
            SELECT id, usage_count FROM ingredient_price_history
            WHERE ingredient_name_normalized = ? AND unit = ?
        """, (normalized_name, unit))

        existing = cursor.fetchone()

        if existing:
            # Mettre à jour le prix existant
            cursor.execute("""
                UPDATE ingredient_price_history
                SET unit_price = ?,
                    last_used_date = CURRENT_DATE,
                    usage_count = ?
                WHERE id = ?
            """, (actual_price, existing['usage_count'] + 1, existing['id']))
        else:
            # Créer une nouvelle entrée
            cursor.execute("""
                INSERT INTO ingredient_price_history (
                    ingredient_name_normalized,
                    ingredient_name_display,
                    unit_price,
                    unit,
                    source,
                    last_used_date,
                    usage_count
                ) VALUES (?, ?, ?, ?, 'shopping_list', CURRENT_DATE, 1)
            """, (normalized_name, ingredient_name, actual_price, unit))

        conn.commit()


# ============================================================================
# CATALOGUE DES PRIX DES INGRÉDIENTS
# ============================================================================

def list_ingredient_catalog(search: str = None, lang: str = 'fr'):
    """
    Liste tous les ingrédients du catalogue avec possibilité de recherche

    Args:
        search: Terme de recherche optionnel
        lang: Langue pour afficher les noms traduits

    Returns:
        Liste des ingrédients avec leurs prix et noms traduits
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Sélectionner les colonnes selon la langue
        if lang == 'jp':
            name_col = 'ingredient_name_jp'
            unit_col = 'unit_jp'
        else:
            name_col = 'ingredient_name_fr'
            unit_col = 'unit_fr'

        # Récupérer tous les ingrédients du catalogue
        base_query = f"""
            SELECT DISTINCT
                c.id,
                c.{name_col} as ingredient_name,
                c.{unit_col} as unit,
                c.price_eur,
                c.price_jpy,
                c.qty,
                c.last_updated,
                c.created_at
            FROM ingredient_price_catalog c
        """

        if search:
            cursor.execute(base_query + f"""
                WHERE c.{name_col} LIKE ?
                ORDER BY c.{name_col}
            """, (f'%{search}%',))
        else:
            cursor.execute(base_query + f"""
                ORDER BY c.{name_col}
            """)

        catalog_items = [dict(row) for row in cursor.fetchall()]
        return catalog_items


def get_ingredient_from_catalog(ingredient_id: int):
    """Récupère un ingrédient du catalogue par son ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ingredient_price_catalog WHERE id = ?", (ingredient_id,))
        result = cursor.fetchone()
        return dict(result) if result else None


def update_ingredient_catalog_price(ingredient_id: int, price_eur: float = None, price_jpy: float = None, unit_fr: str = None, unit_jp: str = None, qty: float = None):
    """
    Met à jour les prix d'un ingrédient dans le catalogue

    Args:
        ingredient_id: ID de l'ingrédient
        price_eur: Prix en euros (optionnel)
        price_jpy: Prix en yens (optionnel)
        unit_fr: Unité en français (optionnel)
        unit_jp: Unité en japonais (optionnel)
        qty: Quantité de référence pour le prix (optionnel)

    Returns:
        True si succès, False sinon
    """
    with get_db() as conn:
        cursor = conn.cursor()

        updates = []
        params = []

        if price_eur is not None:
            updates.append("price_eur = ?")
            params.append(price_eur)

        if price_jpy is not None:
            updates.append("price_jpy = ?")
            params.append(price_jpy)

        if unit_fr is not None:
            updates.append("unit_fr = ?")
            params.append(unit_fr)

        if unit_jp is not None:
            updates.append("unit_jp = ?")
            params.append(unit_jp)

        if qty is not None:
            updates.append("qty = ?")
            params.append(qty)

        if updates:
            updates.append("last_updated = CURRENT_TIMESTAMP")
            params.append(ingredient_id)

            sql = f"UPDATE ingredient_price_catalog SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(sql, params)
            conn.commit()
            return cursor.rowcount > 0

        return False


def delete_ingredient_from_catalog(ingredient_id: int):
    """
    Supprime un ingrédient du catalogue de prix

    Args:
        ingredient_id: ID de l'ingrédient à supprimer

    Returns:
        True si succès, False sinon
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ingredient_price_catalog WHERE id = ?", (ingredient_id,))
        conn.commit()
        return cursor.rowcount > 0


def sync_ingredients_from_recipes():
    """
    Synchronise le catalogue avec tous les ingrédients des recettes
    Ajoute UNIQUEMENT les ingrédients manquants (sans toucher aux prix existants)

    IMPORTANT: Cette fonction N'INSÈRE QUE de nouvelles lignes.
    Elle ne fait AUCUN UPDATE, ne touche JAMAIS aux prix existants.

    Returns:
        Nombre d'ingrédients ajoutés
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Récupérer tous les noms d'ingrédients existants (en minuscules pour comparaison)
        cursor.execute("SELECT LOWER(TRIM(ingredient_name_fr)) as lower_name FROM ingredient_price_catalog")
        existing_lower = {row['lower_name'] for row in cursor.fetchall()}

        # Récupérer tous les ingrédients uniques des recettes
        cursor.execute("""
            SELECT DISTINCT
                rit_fr.name as ingredient_name_fr,
                COALESCE(rit_jp.name, rit_fr.name) as ingredient_name_jp,
                COALESCE(rit_fr.unit, 'g') as unit_fr,
                COALESCE(rit_jp.unit, rit_fr.unit, 'g') as unit_jp
            FROM recipe_ingredient ri
            JOIN recipe_ingredient_translation rit_fr
                ON rit_fr.recipe_ingredient_id = ri.id AND rit_fr.lang = 'fr'
            LEFT JOIN recipe_ingredient_translation rit_jp
                ON rit_jp.recipe_ingredient_id = ri.id AND rit_jp.lang = 'jp'
            ORDER BY rit_fr.name
        """)

        recipe_ingredients = cursor.fetchall()

        # Insérer UNIQUEMENT les nouveaux (en Python, pas en SQL)
        added_count = 0
        for ing in recipe_ingredients:
            name_fr = ing['ingredient_name_fr'].strip()
            name_jp = ing['ingredient_name_jp']
            unit_fr = ing['unit_fr']
            unit_jp = ing['unit_jp']

            # Vérifier si existe déjà (insensible à la casse)
            if name_fr.lower() not in existing_lower:
                try:
                    # INSERTION SEULE - Pas d'UPDATE possible ici
                    cursor.execute("""
                        INSERT INTO ingredient_price_catalog
                        (ingredient_name_fr, ingredient_name_jp, unit_fr, unit_jp)
                        VALUES (?, ?, ?, ?)
                    """, (name_fr, name_jp, unit_fr, unit_jp))
                    added_count += 1
                    existing_lower.add(name_fr.lower())
                except Exception:
                    # Ignorer les doublons (contrainte UNIQUE)
                    pass

        conn.commit()
        return added_count


def cleanup_unused_ingredients_from_catalog():
    """
    Supprime du catalogue:
    1. Les doublons (en ignorant la casse, garde celui avec prix ou le plus ancien)
    2. Les ingrédients qui ne sont plus utilisés dans aucune recette

    Returns:
        Nombre d'ingrédients supprimés
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Compter avant
        cursor.execute("SELECT COUNT(*) as count FROM ingredient_price_catalog")
        count_before = cursor.fetchone()['count']

        # Étape 1: Supprimer les doublons (ignorer la casse sur nom français)
        # Garder celui avec prix, sinon le plus ancien (id le plus petit)
        cursor.execute("""
            DELETE FROM ingredient_price_catalog
            WHERE id NOT IN (
                SELECT id FROM (
                    SELECT
                        id,
                        LOWER(ingredient_name_fr) as lower_name,
                        ROW_NUMBER() OVER (
                            PARTITION BY LOWER(ingredient_name_fr)
                            ORDER BY
                                CASE WHEN price_eur IS NOT NULL OR price_jpy IS NOT NULL THEN 0 ELSE 1 END,
                                id ASC
                        ) as rn
                    FROM ingredient_price_catalog
                ) WHERE rn = 1
            )
        """)

        # Étape 2: Supprimer les ingrédients non utilisés dans les recettes (ignorer la casse)
        cursor.execute("""
            DELETE FROM ingredient_price_catalog
            WHERE LOWER(ingredient_name_fr) NOT IN (
                SELECT DISTINCT LOWER(rit.name)
                FROM recipe_ingredient ri
                JOIN recipe_ingredient_translation rit ON rit.recipe_ingredient_id = ri.id
                WHERE rit.lang = 'fr'
            )
        """)

        conn.commit()

        # Compter après
        cursor.execute("SELECT COUNT(*) as count FROM ingredient_price_catalog")
        count_after = cursor.fetchone()['count']

        return count_before - count_after


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


def get_ingredient_price_for_currency(ingredient_name: str, currency: str):
    """
    Récupère le prix d'un ingrédient pour une devise donnée

    Args:
        ingredient_name: Nom de l'ingrédient (peut être en FR ou JP)
        currency: 'EUR' ou 'JPY'

    Returns:
        Prix ou None si pas trouvé
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Chercher dans les deux langues (FR et JP)
        if currency == 'EUR':
            cursor.execute("""
                SELECT price_eur, unit_fr, qty
                FROM ingredient_price_catalog
                WHERE ingredient_name_fr = ? OR ingredient_name_jp = ?
            """, (ingredient_name, ingredient_name))
        else:  # JPY
            cursor.execute("""
                SELECT price_jpy, unit_jp, qty
                FROM ingredient_price_catalog
                WHERE ingredient_name_fr = ? OR ingredient_name_jp = ?
            """, (ingredient_name, ingredient_name))

        result = cursor.fetchone()
        if result:
            price = result[0]  # price_eur ou price_jpy
            unit = result[1]
            qty = result[2] if result[2] else 1.0  # Quantité de référence (défaut 1.0)
            return {'price': price, 'unit': unit, 'qty': qty} if price else None
        return None


def calculate_ingredient_price(ingredient_name: str, quantity: float, recipe_unit: str, currency: str):
    """
    Calcule le prix d'un ingrédient en convertissant automatiquement les unités si nécessaire

    Args:
        ingredient_name: Nom de l'ingrédient (peut être en FR ou JP)
        quantity: Quantité dans l'unité de la recette
        recipe_unit: Unité utilisée dans la recette (ex: c.s., g, ml)
        currency: 'EUR' ou 'JPY'

    Returns:
        Dict avec:
        - 'total_price': Prix total calculé
        - 'unit_price': Prix unitaire dans le catalogue
        - 'catalog_unit': Unité du catalogue
        - 'converted_quantity': Quantité convertie dans l'unité du catalogue
        - 'recipe_quantity': Quantité originale de la recette
        - 'recipe_unit': Unité originale de la recette
        Ou None si l'ingrédient n'est pas trouvé
    """
    # Récupérer le prix du catalogue
    price_info = get_ingredient_price_for_currency(ingredient_name, currency)
    if not price_info or not price_info['price']:
        return None

    catalog_unit = price_info['unit']
    catalog_price = price_info['price']
    catalog_qty = price_info.get('qty', 1.0)  # Quantité de référence

    # Calculer le prix unitaire réel : price / qty
    # Exemple: 1.5 EUR pour 250g → unit_price = 1.5 / 250 = 0.006 EUR/g
    unit_price = catalog_price / catalog_qty

    # Si les unités sont identiques, calcul direct
    if recipe_unit.lower() == catalog_unit.lower():
        return {
            'total_price': quantity * unit_price,
            'unit_price': unit_price,
            'catalog_unit': catalog_unit,
            'catalog_qty': catalog_qty,
            'catalog_price': catalog_price,
            'converted_quantity': quantity,
            'recipe_quantity': quantity,
            'recipe_unit': recipe_unit
        }

    # Essayer de convertir l'unité de la recette vers l'unité du catalogue
    converted_quantity = convert_unit(quantity, recipe_unit, catalog_unit)

    if converted_quantity is not None:
        # Calculer le prix unitaire dans l'unité de la recette
        # Ex: si catalog = 255 JPY/kg et recipe = g, alors unit_price_recipe = 255/1000 = 0.255 JPY/g
        recipe_unit_price = (converted_quantity / quantity) * unit_price if quantity > 0 else unit_price

        return {
            'total_price': converted_quantity * unit_price,
            'unit_price': recipe_unit_price,  # Prix dans l'unité de la recette
            'catalog_unit': catalog_unit,
            'catalog_qty': catalog_qty,
            'catalog_price': catalog_price,
            'converted_quantity': converted_quantity,
            'recipe_quantity': quantity,
            'recipe_unit': recipe_unit
        }

    # Pas de conversion disponible, calcul direct (supposer que les unités sont compatibles)
    return {
        'total_price': quantity * unit_price,
        'unit_price': unit_price,
        'catalog_unit': catalog_unit,
        'catalog_qty': catalog_qty,
        'catalog_price': catalog_price,
        'converted_quantity': quantity,
        'recipe_quantity': quantity,
        'recipe_unit': recipe_unit,
        'warning': f'Conversion {recipe_unit} → {catalog_unit} non disponible'
    }


# ============================================================================
# DÉTAIL DES DÉPENSES INGRÉDIENTS
# ============================================================================

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


# ============================================================================
# GESTION DES CONVERSIONS D'UNITÉS
# ============================================================================

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


# ============================================================================
# Fonctions de logging des accès
# ============================================================================

def log_access(ip_address: str, user_agent: str = None, path: str = None,
               method: str = 'GET', status_code: int = None,
               response_time_ms: float = None, referer: str = None,
               lang: str = None):
    """
    Enregistre un accès à l'application

    Args:
        ip_address: Adresse IP du client
        user_agent: User agent du navigateur
        path: Chemin de l'URL accédée
        method: Méthode HTTP (GET, POST, etc.)
        status_code: Code de statut HTTP de la réponse
        response_time_ms: Temps de réponse en millisecondes
        referer: URL de référence
        lang: Langue de l'interface
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO access_log (ip_address, user_agent, path, method, status_code,
                                   response_time_ms, referer, lang)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ip_address, user_agent, path, method, status_code,
              response_time_ms, referer, lang))


def get_access_stats(hours: int = 24):
    """
    Récupère les statistiques d'accès

    Args:
        hours: Nombre d'heures à analyser (par défaut 24h)

    Returns:
        Dictionnaire avec les statistiques d'accès
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Nombre total d'accès
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM access_log
            WHERE accessed_at >= datetime('now', '-' || ? || ' hours')
        """, (hours,))
        total_accesses = cursor.fetchone()['total']

        # Accès par IP
        cursor.execute("""
            SELECT ip_address, COUNT(*) as count,
                   MIN(accessed_at) as first_access,
                   MAX(accessed_at) as last_access
            FROM access_log
            WHERE accessed_at >= datetime('now', '-' || ? || ' hours')
            GROUP BY ip_address
            ORDER BY count DESC
            LIMIT 10
        """, (hours,))
        by_ip = [dict(row) for row in cursor.fetchall()]

        # Pages les plus visitées
        cursor.execute("""
            SELECT path, COUNT(*) as count
            FROM access_log
            WHERE accessed_at >= datetime('now', '-' || ? || ' hours')
              AND path IS NOT NULL
            GROUP BY path
            ORDER BY count DESC
            LIMIT 10
        """, (hours,))
        popular_pages = [dict(row) for row in cursor.fetchall()]

        # Temps de réponse moyen par page
        cursor.execute("""
            SELECT path, AVG(response_time_ms) as avg_time, COUNT(*) as count
            FROM access_log
            WHERE accessed_at >= datetime('now', '-' || ? || ' hours')
              AND response_time_ms IS NOT NULL
              AND path IS NOT NULL
            GROUP BY path
            ORDER BY avg_time DESC
            LIMIT 10
        """, (hours,))
        slow_pages = [dict(row) for row in cursor.fetchall()]

        return {
            'total_accesses': total_accesses,
            'by_ip': by_ip,
            'popular_pages': popular_pages,
            'slow_pages': slow_pages
        }


def cleanup_old_access_logs(days: int = 30):
    """
    Nettoie les logs d'accès anciens

    Args:
        days: Nombre de jours à conserver (par défaut 30)

    Returns:
        Nombre de lignes supprimées
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM access_log
            WHERE accessed_at < datetime('now', '-' || ? || ' days')
        """, (days,))
        deleted_count = cursor.rowcount
        return deleted_count


def get_recent_access_logs(limit: int = 50, hours: int = 24):
    """
    Récupère les logs d'accès récents

    Args:
        limit: Nombre maximum de logs à retourner (par défaut 50)
        hours: Nombre d'heures à analyser (par défaut 24)

    Returns:
        Liste des logs d'accès récents
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ip_address, user_agent, path, method, status_code,
                   response_time_ms, referer, lang, accessed_at
            FROM access_log
            WHERE accessed_at >= datetime('now', '-' || ? || ' hours')
            ORDER BY accessed_at DESC
            LIMIT ?
        """, (hours, limit))
        return [dict(row) for row in cursor.fetchall()]


# ============================================================================
# GESTION DES CATÉGORIES ET TAGS
# ============================================================================

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


def search_recipes_by_filters(search_text: str = None, category_ids: list = None,
                              tag_ids: list = None, lang: str = 'fr'):
    """
    Recherche avancée de recettes avec filtres multiples

    Args:
        search_text: Texte à rechercher dans le titre/ingrédients
        category_ids: Liste d'IDs de catégories (OU logique)
        tag_ids: Liste d'IDs de tags (OU logique)
        lang: Langue pour l'affichage

    Returns:
        Liste de recettes correspondantes
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Construction de la requête dynamique
        query = """
            SELECT DISTINCT r.id, r.title_fr, r.title_jp, r.image_url, r.created_at
            FROM recipe r
        """

        conditions = []
        params = []

        # Filtre par catégories
        if category_ids and len(category_ids) > 0:
            placeholders = ','.join('?' * len(category_ids))
            query += f"""
                JOIN recipe_category rc ON r.id = rc.recipe_id
            """
            conditions.append(f"rc.category_id IN ({placeholders})")
            params.extend(category_ids)

        # Filtre par tags
        if tag_ids and len(tag_ids) > 0:
            placeholders = ','.join('?' * len(tag_ids))
            query += f"""
                JOIN recipe_tag rt ON r.id = rt.recipe_id
            """
            conditions.append(f"rt.tag_id IN ({placeholders})")
            params.extend(tag_ids)

        # Recherche textuelle
        if search_text:
            if lang == 'jp':
                conditions.append("(r.title_jp LIKE ? OR r.ingredients_jp LIKE ?)")
            else:
                conditions.append("(r.title_fr LIKE ? OR r.ingredients_fr LIKE ?)")
            search_pattern = f"%{search_text}%"
            params.extend([search_pattern, search_pattern])

        # Ajouter les conditions WHERE si nécessaire
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY r.created_at DESC"

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def update_tag(tag_id: int, name_fr: str = None, name_jp: str = None,
               description_fr: str = None, description_jp: str = None,
               color: str = None) -> bool:
    """
    Modifier un tag existant
    Ne peut modifier que les tags non-système
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Vérifier que ce n'est pas un tag système
    cursor.execute("SELECT is_system FROM tag WHERE id = ?", (tag_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    if row['is_system']:
        conn.close()
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
        conn.close()
        return False

    params.append(tag_id)
    query = f"UPDATE tag SET {', '.join(updates)} WHERE id = ?"

    cursor.execute(query, params)
    conn.commit()
    conn.close()
    return True


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
    conn = get_db_connection()
    cursor = conn.cursor()

    # Vérifier que la catégorie existe
    cursor.execute("SELECT id FROM category WHERE id = ?", (category_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
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
        conn.close()
        return False

    params.append(category_id)
    query = f"UPDATE category SET {', '.join(updates)} WHERE id = ?"

    cursor.execute(query, params)
    conn.commit()
    conn.close()
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