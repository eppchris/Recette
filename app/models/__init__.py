# -*- coding: utf-8 -*-
"""
Package models - Gestion de la base de donnees

Ce package contient tous les modules de gestion de la base de donnees,
organises par domaine fonctionnel.
"""

# Import des fonctions de base
from .db_core import get_db, normalize_ingredient_name

# Import des fonctions de gestion des recettes
from .db_recipes import (
    list_recipes,
    list_recipes_by_type,
    get_recipe_by_slug,
    get_recipe_steps_with_ids,
    check_translation_exists,
    get_recipe_id_by_slug,
    get_source_language,
    update_recipe_complete,
    delete_recipe,
    update_recipe_image,
    get_recipe_image_urls,
    update_servings_default,
    search_recipes_by_filters,
)

# Import des fonctions de traduction
from .db_translations import (
    insert_recipe_translation,
    insert_ingredient_translation,
    insert_step_translation,
    update_ingredient_translation,
    update_ingredient_quantity,
    update_step_translation,
    update_recipe_type,
)

# Import des fonctions de gestion des evenements
from .db_events import (
    list_event_types,
    get_all_event_types,
    create_event_type,
    update_event_type,
    list_events,
    get_event_by_id,
    create_event,
    update_event,
    delete_event,
    add_recipe_to_event,
    update_event_recipe_servings,
    update_event_recipes_multipliers,
    remove_recipe_from_event,
    get_event_recipes,
    get_event_recipes_with_ingredients,
)

# Import des fonctions de gestion des listes de courses
from .db_shopping import (
    get_shopping_list_items,
    save_shopping_list_items,
    update_shopping_list_item,
    update_shopping_list_item_prices,
    update_event_ingredients_actual_total,
    delete_shopping_list_item,
    delete_all_shopping_list_items,
    regenerate_shopping_list,
)

# Import des fonctions de gestion du budget
from .db_budget import (
    get_event_budget_planned,
    update_event_budget_planned,
    update_event_currency,
    list_expense_categories,
    create_expense_category,
    update_expense_category,
    delete_expense_category,
    get_event_expenses,
    create_event_expense,
    update_event_expense,
    delete_event_expense,
    get_event_budget_summary,
    save_expense_ingredient_details,
    get_expense_ingredient_details,
)

# Import des fonctions de gestion du catalogue
from .db_catalog import (
    get_ingredient_price_suggestions,
    update_ingredient_price_from_shopping_list,
    list_ingredient_catalog,
    get_ingredient_from_catalog,
    update_ingredient_catalog_price,
    delete_ingredient_from_catalog,
    sync_ingredients_from_recipes,
    cleanup_unused_ingredients_from_catalog,
    get_all_ingredients_from_catalog,
    get_ingredient_price_for_currency,
    calculate_ingredient_price,
)

# Import des fonctions de conversion d'unites
from .db_conversions import (
    convert_unit,
    get_convertible_units,
    get_all_unit_conversions,
    get_unit_conversion_by_id,
    add_unit_conversion,
    update_unit_conversion,
    delete_unit_conversion,
    get_specific_conversion,
    get_all_specific_conversions,
    add_specific_conversion,
    update_specific_conversion,
    delete_specific_conversion,
)

# Import des fonctions de gestion des metadonnees (categories et tags)
from .db_metadata import (
    get_all_categories,
    get_all_tags,
    get_recipe_categories,
    get_recipe_tags,
    set_recipe_categories,
    set_recipe_tags,
    create_tag,
    update_tag,
    delete_tag,
    create_category,
    update_category,
    delete_category,
)

# Import des fonctions de logging
from .db_logging import (
    log_access,
    get_access_stats,
    cleanup_old_access_logs,
    get_recent_access_logs,
)

__all__ = [
    # Core
    'get_db',
    'normalize_ingredient_name',

    # Recipes
    'list_recipes',
    'list_recipes_by_type',
    'get_recipe_by_slug',
    'get_recipe_steps_with_ids',
    'check_translation_exists',
    'get_recipe_id_by_slug',
    'get_source_language',
    'update_recipe_complete',
    'delete_recipe',
    'update_recipe_image',
    'get_recipe_image_urls',
    'update_servings_default',
    'search_recipes_by_filters',

    # Translations
    'insert_recipe_translation',
    'insert_ingredient_translation',
    'insert_step_translation',
    'update_ingredient_translation',
    'update_ingredient_quantity',
    'update_step_translation',
    'update_recipe_type',

    # Events
    'list_event_types',
    'get_all_event_types',
    'create_event_type',
    'update_event_type',
    'list_events',
    'get_event_by_id',
    'create_event',
    'update_event',
    'delete_event',
    'add_recipe_to_event',
    'update_event_recipe_servings',
    'update_event_recipes_multipliers',
    'remove_recipe_from_event',
    'get_event_recipes',
    'get_event_recipes_with_ingredients',

    # Shopping
    'get_shopping_list_items',
    'save_shopping_list_items',
    'update_shopping_list_item',
    'update_shopping_list_item_prices',
    'update_event_ingredients_actual_total',
    'delete_shopping_list_item',
    'delete_all_shopping_list_items',
    'regenerate_shopping_list',

    # Budget
    'get_event_budget_planned',
    'update_event_budget_planned',
    'update_event_currency',
    'list_expense_categories',
    'create_expense_category',
    'update_expense_category',
    'delete_expense_category',
    'get_event_expenses',
    'create_event_expense',
    'update_event_expense',
    'delete_event_expense',
    'get_event_budget_summary',
    'save_expense_ingredient_details',
    'get_expense_ingredient_details',

    # Catalog
    'get_ingredient_price_suggestions',
    'update_ingredient_price_from_shopping_list',
    'list_ingredient_catalog',
    'get_ingredient_from_catalog',
    'update_ingredient_catalog_price',
    'delete_ingredient_from_catalog',
    'sync_ingredients_from_recipes',
    'cleanup_unused_ingredients_from_catalog',
    'get_all_ingredients_from_catalog',
    'get_ingredient_price_for_currency',
    'calculate_ingredient_price',

    # Conversions
    'convert_unit',
    'get_convertible_units',
    'get_all_unit_conversions',
    'get_unit_conversion_by_id',
    'add_unit_conversion',
    'update_unit_conversion',
    'delete_unit_conversion',
    'get_specific_conversion',
    'get_all_specific_conversions',
    'add_specific_conversion',
    'update_specific_conversion',
    'delete_specific_conversion',

    # Metadata
    'get_all_categories',
    'get_all_tags',
    'get_recipe_categories',
    'get_recipe_tags',
    'set_recipe_categories',
    'set_recipe_tags',
    'create_tag',
    'update_tag',
    'delete_tag',
    'create_category',
    'update_category',
    'delete_category',

    # Logging
    'log_access',
    'get_access_stats',
    'cleanup_old_access_logs',
    'get_recent_access_logs',
]
