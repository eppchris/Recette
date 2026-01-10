# -*- coding: utf-8 -*-
"""
Package models - Gestion de la base de donnees

Ce package contient tous les modules de gestion de la base de donnees,
organises par domaine fonctionnel.
"""

# Créer un module 'db' pour compatibilité avec l'ancien code
from types import SimpleNamespace

# Import des fonctions de base
from .db_core import get_db, normalize_ingredient_name

# Import des fonctions de gestion des recettes
from .db_recipes import (
    list_recipes,
    list_recipes_by_type,
    list_recipes_by_event_types,
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
    search_recipes_by_ingredients,
    calculate_recipe_cost,
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
    get_recipe_event_types,
    set_recipe_event_types,
    save_event_dates,
    get_event_dates,
    toggle_event_date_selection,
    save_recipe_planning,
    get_recipe_planning,
    copy_event,
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

# Import des fonctions de gestion des utilisateurs
from .db_users import (
    hash_password,
    verify_password,
    create_user,
    get_user_by_username,
    get_user_by_email,
    get_user_by_id,
    authenticate_user,
    list_users,
    update_user_password,
    deactivate_user,
    activate_user,
)

# Import des fonctions de gestion des participants
from .db_participants import (
    list_participants,
    get_participant_by_id,
    create_participant,
    update_participant,
    delete_participant,
    list_groups,
    get_group_by_id,
    create_group,
    update_group,
    delete_group,
    get_group_members,
    get_participant_groups,
    add_participant_to_group,
    remove_participant_from_group,
    set_participant_groups,
    set_group_members,
    get_event_participants,
    add_participant_to_event,
    add_group_to_event,
    remove_participant_from_event,
    get_participant_events,
)

# Import des fonctions de gestion des tickets de caisse
from .db_receipt import (
    create_receipt_upload,
    save_receipt_items,
    get_receipt_with_matches,
    list_all_receipts,
    get_receipt_by_id,
    delete_receipt,
    update_receipt_status,
    validate_match,
    update_match_ingredient,
    apply_validated_prices,
    get_all_catalog_ingredients_for_dropdown,
)

__all__ = [
    # Core
    'get_db',
    'normalize_ingredient_name',

    # Recipes
    'list_recipes',
    'list_recipes_by_type',
    'list_recipes_by_event_types',
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
    'search_recipes_by_ingredients',
    'calculate_recipe_cost',

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
    'get_recipe_event_types',
    'set_recipe_event_types',
    'save_event_dates',
    'get_event_dates',
    'toggle_event_date_selection',
    'save_recipe_planning',
    'get_recipe_planning',
    'copy_event',

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

    # Users
    'hash_password',
    'verify_password',
    'create_user',
    'get_user_by_username',
    'get_user_by_email',
    'get_user_by_id',
    'authenticate_user',
    'list_users',
    'update_user_password',
    'deactivate_user',
    'activate_user',

    # Participants
    'list_participants',
    'get_participant_by_id',
    'create_participant',
    'update_participant',
    'delete_participant',
    'list_groups',
    'get_group_by_id',
    'create_group',
    'update_group',
    'delete_group',
    'get_group_members',
    'get_participant_groups',
    'add_participant_to_group',
    'remove_participant_from_group',
    'set_participant_groups',
    'set_group_members',
    'get_event_participants',
    'add_participant_to_event',
    'add_group_to_event',
    'remove_participant_from_event',
    'get_participant_events',

    # Receipts
    'create_receipt_upload',
    'save_receipt_items',
    'get_receipt_with_matches',
    'list_all_receipts',
    'get_receipt_by_id',
    'delete_receipt',
    'update_receipt_status',
    'validate_match',
    'update_match_ingredient',
    'apply_validated_prices',
    'get_all_catalog_ingredients_for_dropdown',
]

# Créer un objet 'db' pour compatibilité avec l'ancien code (permet d'utiliser db.fonction())
db = SimpleNamespace(
    # Core
    get_db=get_db,
    normalize_ingredient_name=normalize_ingredient_name,

    # Recipes
    list_recipes=list_recipes,
    list_recipes_by_type=list_recipes_by_type,
    list_recipes_by_event_types=list_recipes_by_event_types,
    get_recipe_by_slug=get_recipe_by_slug,
    get_recipe_steps_with_ids=get_recipe_steps_with_ids,
    check_translation_exists=check_translation_exists,
    get_recipe_id_by_slug=get_recipe_id_by_slug,
    get_source_language=get_source_language,
    update_recipe_complete=update_recipe_complete,
    delete_recipe=delete_recipe,
    update_recipe_image=update_recipe_image,
    get_recipe_image_urls=get_recipe_image_urls,
    update_servings_default=update_servings_default,
    search_recipes_by_filters=search_recipes_by_filters,
    search_recipes_by_ingredients=search_recipes_by_ingredients,
    calculate_recipe_cost=calculate_recipe_cost,

    # Translations
    insert_recipe_translation=insert_recipe_translation,
    insert_ingredient_translation=insert_ingredient_translation,
    insert_step_translation=insert_step_translation,
    update_ingredient_translation=update_ingredient_translation,
    update_ingredient_quantity=update_ingredient_quantity,
    update_step_translation=update_step_translation,
    update_recipe_type=update_recipe_type,

    # Events
    list_event_types=list_event_types,
    get_all_event_types=get_all_event_types,
    create_event_type=create_event_type,
    update_event_type=update_event_type,
    list_events=list_events,
    get_event_by_id=get_event_by_id,
    create_event=create_event,
    update_event=update_event,
    delete_event=delete_event,
    add_recipe_to_event=add_recipe_to_event,
    update_event_recipe_servings=update_event_recipe_servings,
    update_event_recipes_multipliers=update_event_recipes_multipliers,
    remove_recipe_from_event=remove_recipe_from_event,
    get_event_recipes=get_event_recipes,
    get_event_recipes_with_ingredients=get_event_recipes_with_ingredients,
    get_recipe_event_types=get_recipe_event_types,
    set_recipe_event_types=set_recipe_event_types,
    save_event_dates=save_event_dates,
    get_event_dates=get_event_dates,
    toggle_event_date_selection=toggle_event_date_selection,
    save_recipe_planning=save_recipe_planning,
    get_recipe_planning=get_recipe_planning,
    copy_event=copy_event,

    # Shopping
    get_shopping_list_items=get_shopping_list_items,
    save_shopping_list_items=save_shopping_list_items,
    update_shopping_list_item=update_shopping_list_item,
    update_shopping_list_item_prices=update_shopping_list_item_prices,
    update_event_ingredients_actual_total=update_event_ingredients_actual_total,
    delete_shopping_list_item=delete_shopping_list_item,
    delete_all_shopping_list_items=delete_all_shopping_list_items,
    regenerate_shopping_list=regenerate_shopping_list,

    # Budget
    get_event_budget_planned=get_event_budget_planned,
    update_event_budget_planned=update_event_budget_planned,
    update_event_currency=update_event_currency,
    list_expense_categories=list_expense_categories,
    create_expense_category=create_expense_category,
    update_expense_category=update_expense_category,
    delete_expense_category=delete_expense_category,
    get_event_expenses=get_event_expenses,
    create_event_expense=create_event_expense,
    update_event_expense=update_event_expense,
    delete_event_expense=delete_event_expense,
    get_event_budget_summary=get_event_budget_summary,
    save_expense_ingredient_details=save_expense_ingredient_details,
    get_expense_ingredient_details=get_expense_ingredient_details,

    # Catalog
    get_ingredient_price_suggestions=get_ingredient_price_suggestions,
    update_ingredient_price_from_shopping_list=update_ingredient_price_from_shopping_list,
    list_ingredient_catalog=list_ingredient_catalog,
    get_ingredient_from_catalog=get_ingredient_from_catalog,
    update_ingredient_catalog_price=update_ingredient_catalog_price,
    delete_ingredient_from_catalog=delete_ingredient_from_catalog,
    sync_ingredients_from_recipes=sync_ingredients_from_recipes,
    cleanup_unused_ingredients_from_catalog=cleanup_unused_ingredients_from_catalog,
    get_all_ingredients_from_catalog=get_all_ingredients_from_catalog,
    get_ingredient_price_for_currency=get_ingredient_price_for_currency,
    calculate_ingredient_price=calculate_ingredient_price,

    # Conversions
    convert_unit=convert_unit,
    get_convertible_units=get_convertible_units,
    get_all_unit_conversions=get_all_unit_conversions,
    get_unit_conversion_by_id=get_unit_conversion_by_id,
    add_unit_conversion=add_unit_conversion,
    update_unit_conversion=update_unit_conversion,
    delete_unit_conversion=delete_unit_conversion,
    get_specific_conversion=get_specific_conversion,
    get_all_specific_conversions=get_all_specific_conversions,
    add_specific_conversion=add_specific_conversion,
    update_specific_conversion=update_specific_conversion,
    delete_specific_conversion=delete_specific_conversion,

    # Metadata
    get_all_categories=get_all_categories,
    get_all_tags=get_all_tags,
    get_recipe_categories=get_recipe_categories,
    get_recipe_tags=get_recipe_tags,
    set_recipe_categories=set_recipe_categories,
    set_recipe_tags=set_recipe_tags,
    create_tag=create_tag,
    update_tag=update_tag,
    delete_tag=delete_tag,
    create_category=create_category,
    update_category=update_category,
    delete_category=delete_category,

    # Logging
    log_access=log_access,
    get_access_stats=get_access_stats,
    cleanup_old_access_logs=cleanup_old_access_logs,
    get_recent_access_logs=get_recent_access_logs,

    # Users
    hash_password=hash_password,
    verify_password=verify_password,
    create_user=create_user,
    get_user_by_username=get_user_by_username,
    get_user_by_email=get_user_by_email,
    get_user_by_id=get_user_by_id,
    authenticate_user=authenticate_user,
    list_users=list_users,
    update_user_password=update_user_password,
    deactivate_user=deactivate_user,
    activate_user=activate_user,

    # Participants
    list_participants=list_participants,
    get_participant_by_id=get_participant_by_id,
    create_participant=create_participant,
    update_participant=update_participant,
    delete_participant=delete_participant,
    list_groups=list_groups,
    get_group_by_id=get_group_by_id,
    create_group=create_group,
    update_group=update_group,
    delete_group=delete_group,
    get_group_members=get_group_members,
    get_participant_groups=get_participant_groups,
    add_participant_to_group=add_participant_to_group,
    remove_participant_from_group=remove_participant_from_group,
    set_participant_groups=set_participant_groups,
    set_group_members=set_group_members,
    get_event_participants=get_event_participants,
    add_participant_to_event=add_participant_to_event,
    add_group_to_event=add_group_to_event,
    remove_participant_from_event=remove_participant_from_event,
    get_participant_events=get_participant_events,

    # Receipts
    create_receipt_upload=create_receipt_upload,
    save_receipt_items=save_receipt_items,
    get_receipt_with_matches=get_receipt_with_matches,
    list_all_receipts=list_all_receipts,
    get_receipt_by_id=get_receipt_by_id,
    delete_receipt=delete_receipt,
    update_receipt_status=update_receipt_status,
    validate_match=validate_match,
    update_match_ingredient=update_match_ingredient,
    apply_validated_prices=apply_validated_prices,
    get_all_catalog_ingredients_for_dropdown=get_all_catalog_ingredients_for_dropdown,
)
