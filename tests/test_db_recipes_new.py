# tests/test_db_recipes_new.py
"""
Tests pour le module db_recipes
Teste les opérations CRUD (Create, Read, Update, Delete) sur les recettes
"""

import pytest
from app.models.db_recipes import (
    list_recipes,
    get_recipe_by_slug,
    get_recipe_id_by_slug,
    check_translation_exists,
    get_source_language,
    delete_recipe,
)


# ============================================================================
# TESTS DE LECTURE (Read)
# ============================================================================

class TestListRecipes:
    """Tests pour la fonction list_recipes()"""

    @pytest.mark.database
    def test_list_recipes_empty_database(self, temp_db):
        """Teste list_recipes avec une base vide"""
        recipes = list_recipes("fr")
        assert isinstance(recipes, list), "Devrait retourner une liste"
        assert len(recipes) == 0, "La base vide devrait retourner 0 recettes"

    @pytest.mark.database
    def test_list_recipes_with_data(self, temp_db):
        """Teste list_recipes avec des données"""
        # Insérer une recette de test
        temp_db.execute("""
            INSERT INTO recipe (slug, servings_default, country)
            VALUES ('ramen', 4, 'JP')
        """)
        recipe_id = temp_db.lastrowid

        temp_db.execute("""
            INSERT INTO recipe_translation (recipe_id, lang, name, recipe_type)
            VALUES (?, 'fr', 'Ramen', 'PRO')
        """, (recipe_id,))
        temp_db.commit()

        # Lister les recettes
        recipes = list_recipes("fr")

        assert len(recipes) == 1, "Devrait retourner 1 recette"
        assert recipes[0]['slug'] == 'ramen'
        assert recipes[0]['name'] == 'Ramen'
        assert recipes[0]['servings'] == 4

    @pytest.mark.database
    def test_list_recipes_returns_only_requested_language(self, temp_db):
        """Teste que seule la langue demandée est retournée"""
        # Insérer une recette avec traductions FR et JP
        temp_db.execute("INSERT INTO recipe (slug) VALUES ('test')")
        recipe_id = temp_db.lastrowid

        temp_db.execute("""
            INSERT INTO recipe_translation (recipe_id, lang, name, recipe_type)
            VALUES (?, 'fr', 'Nom français', 'PERSO')
        """, (recipe_id,))

        temp_db.execute("""
            INSERT INTO recipe_translation (recipe_id, lang, name, recipe_type)
            VALUES (?, 'jp', '日本語名', 'PERSO')
        """, (recipe_id,))
        temp_db.commit()

        # Lister en français
        recipes_fr = list_recipes("fr")
        assert recipes_fr[0]['name'] == 'Nom français'

        # Lister en japonais
        recipes_jp = list_recipes("jp")
        assert recipes_jp[0]['name'] == '日本語名'


class TestGetRecipeBySlug:
    """Tests pour get_recipe_by_slug()"""

    @pytest.mark.database
    def test_get_recipe_by_slug_not_found(self, temp_db):
        """Teste avec un slug inexistant"""
        result = get_recipe_by_slug("inexistant", "fr")
        assert result is None, "Une recette inexistante devrait retourner None"

    @pytest.mark.database
    def test_get_recipe_by_slug_found(self, temp_db):
        """Teste la récupération d'une recette complète"""
        # Créer une recette
        temp_db.execute("""
            INSERT INTO recipe (slug, servings_default, country)
            VALUES ('test-recipe', 4, 'FR')
        """)
        recipe_id = temp_db.lastrowid

        # Ajouter traduction
        temp_db.execute("""
            INSERT INTO recipe_translation (recipe_id, lang, name, recipe_type)
            VALUES (?, 'fr', 'Recette de test', 'PERSO')
        """, (recipe_id,))

        # Ajouter un ingrédient
        temp_db.execute("""
            INSERT INTO recipe_ingredient (recipe_id, position, quantity)
            VALUES (?, 1, 200)
        """, (recipe_id,))
        ingredient_id = temp_db.lastrowid

        temp_db.execute("""
            INSERT INTO recipe_ingredient_translation (recipe_ingredient_id, lang, name, unit)
            VALUES (?, 'fr', 'Farine', 'g')
        """, (ingredient_id,))

        # Ajouter une étape
        temp_db.execute("""
            INSERT INTO step (recipe_id, position)
            VALUES (?, 1)
        """, (recipe_id,))
        step_id = temp_db.lastrowid

        temp_db.execute("""
            INSERT INTO step_translation (step_id, lang, text)
            VALUES (?, 'fr', 'Mélanger la farine')
        """, (step_id,))

        temp_db.commit()

        # Récupérer la recette
        result = get_recipe_by_slug("test-recipe", "fr")

        assert result is not None, "La recette devrait être trouvée"
        recipe, ingredients, steps = result

        # Vérifier la recette
        assert recipe['slug'] == 'test-recipe'
        assert recipe['name'] == 'Recette de test'
        assert recipe['servings'] == 4

        # Vérifier les ingrédients
        assert len(ingredients) == 1
        assert ingredients[0]['name'] == 'Farine'
        assert ingredients[0]['quantity'] == 200
        assert ingredients[0]['unit'] == 'g'

        # Vérifier les étapes
        assert len(steps) == 1
        assert steps[0]['text'] == 'Mélanger la farine'


class TestGetRecipeIdBySlug:
    """Tests pour get_recipe_id_by_slug()"""

    @pytest.mark.database
    def test_get_recipe_id_by_slug_found(self, temp_db):
        """Teste la récupération de l'ID d'une recette"""
        temp_db.execute("INSERT INTO recipe (slug) VALUES ('test')")
        expected_id = temp_db.lastrowid
        temp_db.commit()

        result = get_recipe_id_by_slug("test")
        assert result == expected_id, f"L'ID devrait être {expected_id}"

    @pytest.mark.database
    def test_get_recipe_id_by_slug_not_found(self, temp_db):
        """Teste avec un slug inexistant"""
        result = get_recipe_id_by_slug("inexistant")
        assert result is None, "Un slug inexistant devrait retourner None"


# ============================================================================
# TESTS DE SUPPRESSION (Delete)
# ============================================================================

class TestDeleteRecipe:
    """Tests pour delete_recipe()"""

    @pytest.mark.database
    def test_delete_recipe_removes_recipe(self, temp_db):
        """Teste que delete_recipe supprime bien la recette"""
        # Créer une recette
        temp_db.execute("INSERT INTO recipe (slug) VALUES ('to-delete')")
        recipe_id = temp_db.lastrowid
        temp_db.commit()

        # Vérifier qu'elle existe
        assert get_recipe_id_by_slug("to-delete") is not None

        # Supprimer
        delete_recipe("to-delete")

        # Vérifier qu'elle n'existe plus
        assert get_recipe_id_by_slug("to-delete") is None

    @pytest.mark.database
    def test_delete_recipe_cascade_deletes_related_data(self, temp_db):
        """Teste que la suppression supprime aussi les données liées"""
        # Créer une recette avec ingrédients et étapes
        temp_db.execute("INSERT INTO recipe (slug) VALUES ('cascade-test')")
        recipe_id = temp_db.lastrowid

        temp_db.execute("""
            INSERT INTO recipe_ingredient (recipe_id, position, quantity)
            VALUES (?, 1, 100)
        """, (recipe_id,))

        temp_db.execute("""
            INSERT INTO step (recipe_id, position)
            VALUES (?, 1)
        """, (recipe_id,))

        temp_db.commit()

        # Vérifier que les données liées existent
        ingredients_count = temp_db.execute(
            "SELECT COUNT(*) FROM recipe_ingredient WHERE recipe_id = ?", (recipe_id,)
        ).fetchone()[0]
        steps_count = temp_db.execute(
            "SELECT COUNT(*) FROM step WHERE recipe_id = ?", (recipe_id,)
        ).fetchone()[0]

        assert ingredients_count == 1, "L'ingrédient devrait exister"
        assert steps_count == 1, "L'étape devrait exister"

        # Supprimer la recette
        delete_recipe("cascade-test")

        # Vérifier que les données liées sont supprimées
        ingredients_count = temp_db.execute(
            "SELECT COUNT(*) FROM recipe_ingredient WHERE recipe_id = ?", (recipe_id,)
        ).fetchone()[0]
        steps_count = temp_db.execute(
            "SELECT COUNT(*) FROM step WHERE recipe_id = ?", (recipe_id,)
        ).fetchone()[0]

        assert ingredients_count == 0, "Les ingrédients devraient être supprimés"
        assert steps_count == 0, "Les étapes devraient être supprimées"


# ============================================================================
# TESTS DE VÉRIFICATION
# ============================================================================

class TestCheckTranslationExists:
    """Tests pour check_translation_exists()"""

    @pytest.mark.database
    def test_translation_exists(self, temp_db):
        """Teste avec une traduction existante"""
        temp_db.execute("INSERT INTO recipe (slug) VALUES ('test')")
        recipe_id = temp_db.lastrowid

        temp_db.execute("""
            INSERT INTO recipe_translation (recipe_id, lang, name, recipe_type)
            VALUES (?, 'fr', 'Test', 'PERSO')
        """, (recipe_id,))
        temp_db.commit()

        result = check_translation_exists(recipe_id, "fr")
        assert result is True, "La traduction FR devrait exister"

    @pytest.mark.database
    def test_translation_does_not_exist(self, temp_db):
        """Teste avec une traduction inexistante"""
        temp_db.execute("INSERT INTO recipe (slug) VALUES ('test')")
        recipe_id = temp_db.lastrowid
        temp_db.commit()

        result = check_translation_exists(recipe_id, "jp")
        assert result is False, "La traduction JP ne devrait pas exister"


class TestGetSourceLanguage:
    """Tests pour get_source_language()"""

    @pytest.mark.database
    def test_get_source_language_returns_first_available(self, temp_db):
        """Teste que la première langue disponible est retournée"""
        temp_db.execute("INSERT INTO recipe (slug) VALUES ('test')")
        recipe_id = temp_db.lastrowid

        temp_db.execute("""
            INSERT INTO recipe_translation (recipe_id, lang, name, recipe_type)
            VALUES (?, 'jp', 'テスト', 'PERSO')
        """, (recipe_id,))
        temp_db.commit()

        result = get_source_language(recipe_id)
        assert result == 'jp', "La langue source devrait être 'jp'"

    @pytest.mark.database
    def test_get_source_language_no_translation(self, temp_db):
        """Teste avec une recette sans traduction"""
        temp_db.execute("INSERT INTO recipe (slug) VALUES ('test')")
        recipe_id = temp_db.lastrowid
        temp_db.commit()

        result = get_source_language(recipe_id)
        assert result is None, "Devrait retourner None si aucune traduction"


# ============================================================================
# TESTS D'INTÉGRATION
# ============================================================================

@pytest.mark.integration
@pytest.mark.database
def test_full_recipe_lifecycle(temp_db):
    """
    Test d'intégration : Cycle de vie complet d'une recette
    Create → Read → Update → Delete
    """
    # 1. CREATE - Créer une recette complète
    temp_db.execute("""
        INSERT INTO recipe (slug, servings_default, country)
        VALUES ('integration-test', 4, 'FR')
    """)
    recipe_id = temp_db.lastrowid

    temp_db.execute("""
        INSERT INTO recipe_translation (recipe_id, lang, name, recipe_type)
        VALUES (?, 'fr', 'Recette d''intégration', 'PERSO')
    """, (recipe_id,))
    temp_db.commit()

    # 2. READ - Vérifier qu'elle existe
    recipes = list_recipes("fr")
    assert len(recipes) == 1
    assert recipes[0]['slug'] == 'integration-test'

    # 3. READ (détails) - Récupérer les détails
    result = get_recipe_by_slug("integration-test", "fr")
    assert result is not None
    recipe, ingredients, steps = result
    assert recipe['name'] == 'Recette d\'intégration'

    # 4. DELETE - Supprimer
    delete_recipe("integration-test")

    # 5. VERIFY - Vérifier qu'elle n'existe plus
    recipes = list_recipes("fr")
    assert len(recipes) == 0, "La recette devrait être supprimée"
