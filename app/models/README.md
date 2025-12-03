# Module de Gestion de la Base de Données

## Architecture

Le fichier monolithique `db.py` (3113 lignes) a été découpé en 10 modules distincts pour améliorer la maintenabilité et l'organisation du code.

## Modules

### 1. `db_core.py` - Fonctions de Base
- `get_db()` - Context manager pour les connexions à la base de données
- `normalize_ingredient_name()` - Normalisation des noms d'ingrédients
- Initialisation de la base de données (mode WAL)
- Configuration de la connexion SQLite

### 2. `db_recipes.py` - Gestion des Recettes
Fonctions pour la manipulation des recettes :
- `list_recipes()` - Liste toutes les recettes
- `list_recipes_by_type()` - Filtre par type
- `get_recipe_by_slug()` - Récupère une recette complète
- `get_recipe_steps_with_ids()` - Récupère les étapes avec IDs
- `check_translation_exists()` - Vérifie l'existence d'une traduction
- `get_recipe_id_by_slug()` - Récupère l'ID d'une recette
- `get_source_language()` - Détermine la langue source
- `update_recipe_complete()` - Mise à jour complète
- `delete_recipe()` - Suppression
- `update_recipe_image()` - Mise à jour des images
- `get_recipe_image_urls()` - Récupère les URLs d'images
- `update_servings_default()` - Mise à jour du nombre de personnes
- `search_recipes_by_filters()` - Recherche avancée

### 3. `db_translations.py` - Gestion des Traductions
Fonctions pour la gestion multilingue :
- `insert_recipe_translation()` - Insère une traduction de recette
- `insert_ingredient_translation()` - Insère une traduction d'ingrédient
- `insert_step_translation()` - Insère une traduction d'étape
- `update_ingredient_translation()` - Met à jour une traduction d'ingrédient
- `update_ingredient_quantity()` - Met à jour une quantité
- `update_step_translation()` - Met à jour une traduction d'étape
- `update_recipe_type()` - Met à jour le type de recette

### 4. `db_events.py` - Gestion des Événements
Fonctions pour les événements et leurs recettes :
- `list_event_types()` - Liste les types d'événements
- `get_all_event_types()` - Récupère tous les types avec statistiques
- `create_event_type()` - Crée un type d'événement
- `update_event_type()` - Met à jour un type d'événement
- `list_events()` - Liste tous les événements
- `get_event_by_id()` - Récupère un événement
- `create_event()` - Crée un événement
- `update_event()` - Met à jour un événement
- `delete_event()` - Supprime un événement
- `add_recipe_to_event()` - Ajoute une recette
- `update_event_recipe_servings()` - Met à jour les portions
- `update_event_recipes_multipliers()` - Ajuste tous les multiplicateurs
- `remove_recipe_from_event()` - Retire une recette
- `get_event_recipes()` - Récupère les recettes d'un événement
- `get_event_recipes_with_ingredients()` - Récupère avec ingrédients

### 5. `db_shopping.py` - Listes de Courses
Fonctions pour la gestion des listes de courses :
- `get_shopping_list_items()` - Récupère les items
- `save_shopping_list_items()` - Sauvegarde la liste
- `update_shopping_list_item()` - Met à jour un item
- `update_shopping_list_item_prices()` - Met à jour les prix
- `update_event_ingredients_actual_total()` - Met à jour le total réel
- `delete_shopping_list_item()` - Supprime un item
- `delete_all_shopping_list_items()` - Vide la liste
- `regenerate_shopping_list()` - Régénère la liste

### 6. `db_budget.py` - Gestion du Budget
Fonctions pour le budget des événements :
- `get_event_budget_planned()` - Récupère le budget prévisionnel
- `update_event_budget_planned()` - Met à jour le budget
- `update_event_currency()` - Change la devise
- `list_expense_categories()` - Liste les catégories de dépenses
- `create_expense_category()` - Crée une catégorie
- `update_expense_category()` - Met à jour une catégorie
- `delete_expense_category()` - Supprime une catégorie
- `get_event_expenses()` - Récupère les dépenses
- `create_event_expense()` - Crée une dépense
- `update_event_expense()` - Met à jour une dépense
- `delete_event_expense()` - Supprime une dépense
- `get_event_budget_summary()` - Résumé budgétaire
- `save_expense_ingredient_details()` - Détails des ingrédients
- `get_expense_ingredient_details()` - Récupère les détails

### 7. `db_catalog.py` - Catalogue des Prix
Fonctions pour le catalogue des ingrédients :
- `get_ingredient_price_suggestions()` - Suggestions de prix
- `update_ingredient_price_from_shopping_list()` - Met à jour depuis la liste
- `list_ingredient_catalog()` - Liste le catalogue
- `get_ingredient_from_catalog()` - Récupère un ingrédient
- `update_ingredient_catalog_price()` - Met à jour un prix
- `delete_ingredient_from_catalog()` - Supprime un ingrédient
- `sync_ingredients_from_recipes()` - Synchronise avec les recettes
- `cleanup_unused_ingredients_from_catalog()` - Nettoie le catalogue
- `get_all_ingredients_from_catalog()` - Récupère tous les ingrédients
- `get_ingredient_price_for_currency()` - Prix par devise
- `calculate_ingredient_price()` - Calcule le prix avec conversion

### 8. `db_conversions.py` - Conversions d'Unités
Fonctions pour la conversion d'unités :
- `convert_unit()` - Convertit une quantité
- `get_convertible_units()` - Liste les unités convertibles
- `get_all_unit_conversions()` - Récupère toutes les conversions
- `get_unit_conversion_by_id()` - Récupère par ID
- `add_unit_conversion()` - Ajoute une conversion
- `update_unit_conversion()` - Met à jour une conversion
- `delete_unit_conversion()` - Supprime une conversion
- `get_specific_conversion()` - Conversion spécifique par ingrédient
- `get_all_specific_conversions()` - Toutes les conversions spécifiques
- `add_specific_conversion()` - Ajoute une conversion spécifique
- `update_specific_conversion()` - Met à jour une conversion spécifique
- `delete_specific_conversion()` - Supprime une conversion spécifique

### 9. `db_metadata.py` - Catégories et Tags
Fonctions pour les métadonnées des recettes :
- `get_all_categories()` - Récupère toutes les catégories
- `get_all_tags()` - Récupère tous les tags
- `get_recipe_categories()` - Catégories d'une recette
- `get_recipe_tags()` - Tags d'une recette
- `set_recipe_categories()` - Définit les catégories
- `set_recipe_tags()` - Définit les tags
- `create_tag()` - Crée un tag
- `update_tag()` - Met à jour un tag
- `delete_tag()` - Supprime un tag
- `create_category()` - Crée une catégorie
- `update_category()` - Met à jour une catégorie
- `delete_category()` - Supprime une catégorie

### 10. `db_logging.py` - Logs d'Accès
Fonctions pour le logging :
- `log_access()` - Enregistre un accès
- `get_access_stats()` - Statistiques d'accès
- `cleanup_old_access_logs()` - Nettoie les anciens logs
- `get_recent_access_logs()` - Récupère les logs récents

## Utilisation

### Import Direct depuis le Package
```python
from app.models import get_db, list_recipes, create_event
```

### Import depuis un Module Spécifique
```python
from app.models.db_recipes import get_recipe_by_slug
from app.models.db_events import create_event
from app.models.db_conversions import convert_unit
```

## Compatibilité

Le fichier `__init__.py` réexporte toutes les fonctions des modules, garantissant la **compatibilité totale** avec le code existant qui importait depuis `app.models.db`.

### Avant
```python
from app.models.db import list_recipes, get_event_by_id
```

### Après (fonctionne toujours !)
```python
from app.models import list_recipes, get_event_by_id
```

## Avantages

1. **Meilleure Organisation** - Code organisé par domaine fonctionnel
2. **Maintenabilité** - Modules plus petits et focalisés
3. **Navigation** - Plus facile de trouver le code recherché
4. **Tests** - Possibilité de tester chaque module indépendamment
5. **Performance** - Imports plus rapides (seulement ce qui est nécessaire)
6. **Collaboration** - Réduit les conflits Git sur un seul gros fichier

## Structure des Fichiers

```
app/models/
├── __init__.py              # Réexporte toutes les fonctions
├── db_core.py              # Fonctions de base (get_db, normalize_ingredient_name)
├── db_recipes.py           # Gestion des recettes
├── db_translations.py      # Gestion des traductions
├── db_events.py            # Gestion des événements
├── db_shopping.py          # Listes de courses
├── db_budget.py            # Gestion du budget
├── db_catalog.py           # Catalogue des prix
├── db_conversions.py       # Conversions d'unités
├── db_metadata.py          # Catégories et tags
├── db_logging.py           # Logs d'accès
├── db.py                   # Fichier original (à conserver pour référence)
└── README.md               # Cette documentation
```

## Notes de Migration

- L'ancien fichier `db.py` est conservé pour référence
- Tous les imports existants continuent de fonctionner
- Aucune modification du code appelant n'est nécessaire
- Les modules peuvent être utilisés indépendamment si besoin
