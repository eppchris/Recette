"""
Module de gestion du catalogue des prix des ingrédients
"""
import sqlite3
from .db_core import get_db, normalize_ingredient_name


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
                c.conversion_category,
                c.price_eur_source,
                c.price_eur_last_receipt_date,
                c.price_jpy_source,
                c.price_jpy_last_receipt_date,
                c.updated_at,
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


def get_ingredient_from_catalog(ingredient_id: int = None, ingredient_name: str = None):
    """
    Récupère un ingrédient du catalogue par son ID ou son nom

    Args:
        ingredient_id: ID de l'ingrédient (optionnel)
        ingredient_name: Nom de l'ingrédient FR ou JP (optionnel)

    Returns:
        Dict avec les infos de l'ingrédient ou None
    """
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if ingredient_id is not None:
            cursor.execute("SELECT * FROM ingredient_price_catalog WHERE id = ?", (ingredient_id,))
        elif ingredient_name is not None:
            cursor.execute("""
                SELECT *
                FROM ingredient_price_catalog
                WHERE LOWER(ingredient_name_fr) = LOWER(?)
                   OR LOWER(ingredient_name_jp) = LOWER(?)
            """, (ingredient_name, ingredient_name))
        else:
            return None

        result = cursor.fetchone()
        return dict(result) if result else None


def update_ingredient_catalog_price(ingredient_id: int, price_eur: float = None, price_jpy: float = None, unit_fr: str = None, unit_jp: str = None, qty: float = None, conversion_category: str = None):
    """
    Met à jour les prix d'un ingrédient dans le catalogue

    Args:
        ingredient_id: ID de l'ingrédient
        price_eur: Prix en euros (optionnel)
        price_jpy: Prix en yens (optionnel)
        unit_fr: Unité en français (optionnel)
        unit_jp: Unité en japonais (optionnel)
        qty: Quantité de référence pour le prix (optionnel)
        conversion_category: Catégorie de conversion (poids, volume, unite) (optionnel)

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

        if conversion_category is not None:
            updates.append("conversion_category = ?")
            params.append(conversion_category if conversion_category else None)

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
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

    NOUVEAU : Utilise la normalisation des noms (minuscules, sans accents, singulier)
    pour éviter les doublons du type "Oeuf" vs "œuf" vs "Œufs"

    Returns:
        Nombre d'ingrédients ajoutés
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Récupérer tous les noms d'ingrédients existants NORMALISÉS
        cursor.execute("SELECT ingredient_name_fr FROM ingredient_price_catalog")
        existing_normalized = {normalize_ingredient_name(row['ingredient_name_fr']) for row in cursor.fetchall()}

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
            name_fr_original = ing['ingredient_name_fr'].strip()
            name_fr_normalized = normalize_ingredient_name(name_fr_original)
            name_jp = ing['ingredient_name_jp']
            unit_fr = ing['unit_fr']
            unit_jp = ing['unit_jp']

            # Vérifier si existe déjà (avec nom normalisé)
            if name_fr_normalized not in existing_normalized:
                try:
                    # INSERTION SEULE avec le nom NORMALISÉ
                    cursor.execute("""
                        INSERT INTO ingredient_price_catalog
                        (ingredient_name_fr, ingredient_name_jp, unit_fr, unit_jp)
                        VALUES (?, ?, ?, ?)
                    """, (name_fr_normalized, name_jp, unit_fr, unit_jp))
                    added_count += 1
                    existing_normalized.add(name_fr_normalized)
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


def get_all_ingredients_from_catalog():
    """
    Récupère tous les ingrédients du catalogue pour les formulaires

    Returns:
        Liste de tous les ingrédients ordonnés par nom FR
    """
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, ingredient_name_fr, ingredient_name_jp, unit_fr, unit_jp
            FROM ingredient_price_catalog
            ORDER BY ingredient_name_fr
        """)

        rows = cursor.fetchall()
        return [dict(row) for row in rows]


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

        # Chercher dans les deux langues (FR et JP) - insensible à la casse
        if currency == 'EUR':
            cursor.execute("""
                SELECT price_eur, unit_fr, qty
                FROM ingredient_price_catalog
                WHERE LOWER(ingredient_name_fr) = LOWER(?) OR LOWER(ingredient_name_jp) = LOWER(?)
            """, (ingredient_name, ingredient_name))
        else:  # JPY
            cursor.execute("""
                SELECT price_jpy, unit_jp, qty
                FROM ingredient_price_catalog
                WHERE LOWER(ingredient_name_fr) = LOWER(?) OR LOWER(ingredient_name_jp) = LOWER(?)
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
    from .db_conversions import convert_unit, get_specific_conversion

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

    # PRIORITÉ 1: Chercher une conversion spécifique pour cet ingrédient
    # Exemple: dashi 30g (catalogue) → 1000ml (conversion spécifique)
    # On cherche la conversion: catalog_unit → recipe_unit
    specific_conv = get_specific_conversion(ingredient_name, catalog_unit)

    if specific_conv and specific_conv['to_unit'].lower() == recipe_unit.lower():
        # Conversion spécifique trouvée !
        # Le facteur indique combien de "to_unit" on obtient avec 1 "from_unit"
        # Ex: 30g de dashi → 1000ml, donc factor = 1000/30 = 33.33
        factor = specific_conv['factor']

        # On doit convertir quantity (en recipe_unit) vers catalog_unit
        # Ex: 250ml → combien de g ? 250 / 33.33 = 7.5g
        converted_quantity = quantity / factor

        # Prix dans l'unité de la recette
        # Si unit_price = 5.01€/30g = 0.167€/g
        # Et factor = 33.33 ml/g
        # Alors recipe_unit_price = 0.167 / 33.33 = 0.005€/ml
        recipe_unit_price = unit_price / factor

        return {
            'total_price': quantity * recipe_unit_price,
            'unit_price': recipe_unit_price,
            'catalog_unit': catalog_unit,
            'catalog_qty': catalog_qty,
            'catalog_price': catalog_price,
            'converted_quantity': converted_quantity,  # Quantité nécessaire dans l'unité du catalogue
            'recipe_quantity': quantity,
            'recipe_unit': recipe_unit,
            'specific_conversion_used': True,
            'conversion_factor': factor
        }

    # PRIORITÉ 2: Essayer conversion standard (unit_conversion)
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
