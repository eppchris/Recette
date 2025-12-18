"""
Module de gestion des recettes
"""
from .db_core import get_db


def list_recipes(lang: str, user_id: int = None):
    """
    Liste toutes les recettes dans la langue demandée

    Args:
        lang: Code de langue ('fr' ou 'jp')
        user_id: ID utilisateur optionnel pour filtrer par créateur

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
                rt.recipe_type AS type,
                r.user_id,
                COALESCE(u.display_name, u.username) AS creator_name
            FROM recipe r
            LEFT JOIN recipe_translation rt ON rt.recipe_id = r.id AND rt.lang = ?
            LEFT JOIN user u ON u.id = r.user_id
        """

        params = [lang]

        # Ajouter le filtre par créateur si spécifié
        if user_id is not None:
            sql += " WHERE r.user_id = ?"
            params.append(user_id)

        sql += " ORDER BY name COLLATE NOCASE"

        rows = con.execute(sql, params).fetchall()
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


def list_recipes_by_event_types(event_type_ids: list, lang: str):
    """
    Liste toutes les recettes associées à un ou plusieurs types d'événements

    Args:
        event_type_ids: Liste des IDs de types d'événements
        lang: Code de langue ('fr' ou 'jp')

    Returns:
        Liste des recettes avec leurs informations de base
    """
    if not event_type_ids:
        return []

    with get_db() as con:
        # Créer les placeholders pour la clause IN
        placeholders = ','.join('?' * len(event_type_ids))

        sql = f"""
            SELECT DISTINCT
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
            INNER JOIN recipe_event_type ret ON ret.recipe_id = r.id
            WHERE ret.event_type_id IN ({placeholders})
            ORDER BY name COLLATE NOCASE
        """
        params = [lang] + event_type_ids
        rows = con.execute(sql, params).fetchall()
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
                rt.recipe_type AS type,
                rt.description,
                r.user_id,
                u.username AS creator_username,
                u.display_name AS creator_display_name
            FROM recipe r
            LEFT JOIN recipe_translation rt ON rt.recipe_id = r.id AND rt.lang = ?
            LEFT JOIN user u ON u.id = r.user_id
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


def update_recipe_complete(recipe_id: int, lang: str, data: dict):
    """
    Met à jour une recette complète en une seule transaction

    Args:
        recipe_id: ID de la recette
        lang: Code de langue
        data: Dictionnaire contenant recipe_type, servings_default, ingredients, steps
    """
    with get_db() as con:
        # Mettre à jour le type de recette et la description (traduction)
        if 'recipe_type' in data and data['recipe_type'] is not None:
            con.execute(
                "UPDATE recipe_translation SET recipe_type = ? WHERE recipe_id = ? AND lang = ?",
                (data['recipe_type'], recipe_id, lang)
            )

        # Mettre à jour la description
        if 'description' in data:
            con.execute(
                "UPDATE recipe_translation SET description = ? WHERE recipe_id = ? AND lang = ?",
                (data.get('description', ''), recipe_id, lang)
            )

        # Mettre à jour le nombre de personnes par défaut
        if 'servings_default' in data and data['servings_default'] is not None:
            con.execute(
                "UPDATE recipe SET servings_default = ? WHERE id = ?",
                (data['servings_default'], recipe_id)
            )

        # Mettre à jour l'utilisateur créateur
        if 'user_id' in data:
            con.execute(
                "UPDATE recipe SET user_id = ? WHERE id = ?",
                (data['user_id'], recipe_id)
            )

        # Mettre à jour les ingrédients
        for order, ing in enumerate(data.get('ingredients', []), start=1):
            if ing.get('id'):
                # Mettre à jour un ingrédient existant
                # Mettre à jour la quantité et la position (indépendants de la langue)
                con.execute(
                    "UPDATE recipe_ingredient SET quantity = ?, position = ? WHERE id = ?",
                    (ing.get('quantity'), order, ing['id'])
                )

                # Mettre à jour la traduction (nom, unité, notes)
                con.execute(
                    """UPDATE recipe_ingredient_translation
                       SET name = ?, unit = ?, notes = ?
                       WHERE recipe_ingredient_id = ? AND lang = ?""",
                    (ing.get('name', ''), ing.get('unit', ''), ing.get('notes', ''), ing['id'], lang)
                )
            else:
                # Insérer un nouvel ingrédient
                cur = con.execute(
                    "INSERT INTO recipe_ingredient (recipe_id, quantity, position) VALUES (?, ?, ?)",
                    (recipe_id, ing.get('quantity'), order)
                )
                new_ing_id = cur.lastrowid

                # Insérer la traduction
                con.execute(
                    """INSERT INTO recipe_ingredient_translation
                       (recipe_ingredient_id, lang, name, unit, notes)
                       VALUES (?, ?, ?, ?, ?)""",
                    (new_ing_id, lang, ing.get('name', ''), ing.get('unit', ''), ing.get('notes', ''))
                )

        # Mettre à jour les étapes
        for order, step in enumerate(data.get('steps', []), start=1):
            if step.get('id'):
                # Mettre à jour une étape existante
                con.execute(
                    "UPDATE step SET position = ? WHERE id = ?",
                    (order, step['id'])
                )

                con.execute(
                    "UPDATE step_translation SET text = ? WHERE step_id = ? AND lang = ?",
                    (step.get('text', ''), step['id'], lang)
                )
            else:
                # Insérer une nouvelle étape
                cur = con.execute(
                    "INSERT INTO step (recipe_id, position) VALUES (?, ?)",
                    (recipe_id, order)
                )
                new_step_id = cur.lastrowid

                # Insérer la traduction
                con.execute(
                    "INSERT INTO step_translation (step_id, lang, text) VALUES (?, ?, ?)",
                    (new_step_id, lang, step.get('text', ''))
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


def search_recipes_by_ingredients(ingredients: list, lang: str = 'fr'):
    """
    Recherche des recettes contenant tous les ingrédients spécifiés (ET logique)

    Args:
        ingredients: Liste de noms d'ingrédients à rechercher
        lang: Langue pour l'affichage ('fr' ou 'jp')

    Returns:
        Liste de recettes contenant tous les ingrédients
    """
    if not ingredients:
        return []

    with get_db() as conn:
        # Pour chaque recette, compter combien d'ingrédients matchent
        # On ne garde que les recettes qui ont TOUS les ingrédients
        sql = """
            SELECT DISTINCT
                r.id,
                r.slug,
                COALESCE(rt.name, r.slug) AS name,
                r.image_url,
                r.thumbnail_url,
                r.servings_default AS servings
            FROM recipe r
            LEFT JOIN recipe_translation rt ON r.id = rt.recipe_id AND rt.lang = ?
            LEFT JOIN recipe_ingredient ri ON ri.recipe_id = r.id
            LEFT JOIN recipe_ingredient_translation rit ON rit.recipe_ingredient_id = ri.id AND rit.lang = ?
            WHERE (
                {}
            )
            GROUP BY r.id
            HAVING COUNT(DISTINCT LOWER(rit.name)) >= ?
            ORDER BY r.slug
        """

        # Construire les conditions pour chaque ingrédient
        ingredient_conditions = []
        params = [lang, lang]

        for ingredient in ingredients:
            ingredient_lower = ingredient.strip().lower()
            ingredient_conditions.append(
                "LOWER(rit.name) LIKE ?"
            )
            params.append(f"%{ingredient_lower}%")

        # Combiner avec OR pour matcher n'importe quel ingrédient
        sql = sql.format(" OR ".join(ingredient_conditions))

        # Ajouter le nombre d'ingrédients requis (tous doivent être présents)
        params.append(len(ingredients))

        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]


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

def calculate_recipe_cost(slug: str, lang: str, servings: int = None):
    """
    Calcule le coût d'une recette avec prix du catalogue
    Utilise le nouveau système de calcul de coût (cost_calculator.py)

    Args:
        slug: Identifiant de la recette
        lang: Langue
        servings: Nombre de personnes (si None, utilise servings_default)

    Returns:
        Dict contenant les ingrédients avec prix et le total
    """
    from app.services.ingredient_aggregator import get_ingredient_aggregator
    from app.services.cost_calculator import compute_estimated_cost_for_ingredient
    from .db_core import get_db

    result = get_recipe_by_slug(slug, lang)
    if not result:
        return None

    recipe, ingredients, _ = result
    target_servings = servings or recipe['servings']
    original_servings = recipe['servings']

    # Calculer le ratio de conversion
    ratio = target_servings / original_servings if original_servings > 0 else 1

    # Déterminer la devise selon la langue
    currency = 'EUR' if lang == 'fr' else 'JPY'

    aggregator = get_ingredient_aggregator()
    ingredients_with_cost = []
    total_cost = 0

    with get_db() as conn:
        for ing in ingredients:
            # Quantité ajustée selon le nombre de personnes
            adjusted_quantity = (ing['quantity'] or 0) * ratio

            # Normaliser le nom pour recherche dans le catalogue
            normalized_name = aggregator.normalize_ingredient_name(ing['name'])

            # Calculer le coût avec le nouveau système
            cost_result = compute_estimated_cost_for_ingredient(
                conn=conn,
                ingredient_name_fr=ing['name'],
                recipe_qty=adjusted_quantity,
                recipe_unit=ing['unit'],
                currency=currency,
                lang=lang
            )

            # Extraire les données du debug pour l'affichage
            debug_info = cost_result.debug
            catalog_quantity = debug_info.get('pack_qty')
            catalog_unit = debug_info.get('ipc_unit', ing['unit'])
            catalog_price = debug_info.get('pack_price')

            # Calculer le prix unitaire dans l'unité de la recette si possible
            if cost_result.status == "ok" and adjusted_quantity > 0:
                planned_unit_price = cost_result.cost / adjusted_quantity
            else:
                planned_unit_price = 0

            total_cost += cost_result.cost

            ingredients_with_cost.append({
                'name': ing['name'],
                'normalized_name': normalized_name,
                # Catalogue (Prix de référence)
                'catalog_quantity': catalog_quantity,
                'catalog_unit': catalog_unit,
                'catalog_price': catalog_price,
                # Recette (Besoin)
                'recipe_quantity': adjusted_quantity,
                'recipe_unit': ing['unit'],
                # Coût Estimé
                'planned_unit_price': planned_unit_price,
                'planned_total': cost_result.cost,
                'notes': ing.get('notes', ''),
                # Nouveaux champs pour le debug
                'cost_status': cost_result.status,
                'cost_debug': cost_result.debug
            })

    return {
        'recipe': recipe,
        'servings': target_servings,
        'original_servings': original_servings,
        'ingredients': ingredients_with_cost,
        'total_planned': total_cost,
        'currency': currency
    }
