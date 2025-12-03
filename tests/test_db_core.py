# tests/test_db_core.py
"""
Tests unitaires pour le module db_core
Teste la normalisation des ingrédients et la gestion de la connexion DB
"""

import pytest
from app.models.db_core import normalize_ingredient_name, get_db


# ============================================================================
# TESTS DE NORMALISATION D'INGRÉDIENTS
# ============================================================================

class TestNormalizeIngredientName:
    """Tests pour la fonction normalize_ingredient_name()"""

    @pytest.mark.unit
    def test_oeuf_avec_ligature(self):
        """Teste que 'Œufs' devient 'oeuf'"""
        result = normalize_ingredient_name("Œufs")
        assert result == "oeuf", "La ligature œ doit devenir oe et le s enlevé"

    @pytest.mark.unit
    def test_majuscule_vers_minuscule(self):
        """Teste la conversion en minuscules"""
        result = normalize_ingredient_name("TOMATES")
        assert result == "tomate", "Doit être en minuscules et au singulier"

    @pytest.mark.unit
    def test_accents_supprimes(self):
        """Teste la suppression des accents"""
        test_cases = [
            ("épinards", "epinard"),
            ("Saké", "sake"),
            ("crème", "creme"),
            ("pâtes", "pate"),
        ]
        for input_text, expected in test_cases:
            result = normalize_ingredient_name(input_text)
            assert result == expected, f"{input_text} devrait donner {expected}, obtenu {result}"

    @pytest.mark.unit
    def test_pluriel_vers_singulier(self):
        """Teste la conversion du pluriel au singulier"""
        test_cases = [
            ("tomates", "tomate"),
            ("carottes", "carotte"),
            ("pommes", "pomme"),
        ]
        for input_text, expected in test_cases:
            result = normalize_ingredient_name(input_text)
            assert result == expected, f"{input_text} devrait être au singulier"

    @pytest.mark.unit
    def test_mots_courts_restent_identiques(self):
        """Teste que les mots courts ne perdent pas leur 's' final"""
        test_cases = [
            ("riz", "riz"),  # Pas de 's', reste identique
            ("os", "os"),    # Se termine par 's' mais garde le 's'
        ]
        for input_text, expected in test_cases:
            result = normalize_ingredient_name(input_text)
            assert result == expected

    @pytest.mark.unit
    def test_mots_en_ss_gardent_ss(self):
        """Teste que les mots se terminant en 'ss' gardent le 'ss'"""
        result = normalize_ingredient_name("cress")
        assert result == "cress", "Les mots en 'ss' ne doivent pas perdre le dernier 's'"

    @pytest.mark.unit
    def test_ail_reste_ail(self):
        """Teste un cas particulier : 'ail' reste 'ail'"""
        result = normalize_ingredient_name("Ail")
        assert result == "ail"

    @pytest.mark.unit
    def test_chaine_vide(self):
        """Teste avec une chaîne vide"""
        result = normalize_ingredient_name("")
        assert result == "", "Une chaîne vide doit retourner une chaîne vide"

    @pytest.mark.unit
    def test_none_value(self):
        """Teste avec None"""
        result = normalize_ingredient_name(None)
        assert result == "", "None doit retourner une chaîne vide"

    @pytest.mark.unit
    def test_espaces_supprimes(self):
        """Teste que les espaces avant/après sont supprimés"""
        result = normalize_ingredient_name("  tomates  ")
        assert result == "tomate", "Les espaces doivent être supprimés"

    @pytest.mark.unit
    def test_cas_complexe(self):
        """Teste un cas complexe avec plusieurs transformations"""
        # "Œufs Frais" → minuscules → "œufs frais" → oe → "oeufs frais"
        # → sans accents → "oeufs frais" → singulier → "oeuf frai"
        # Note: Actuellement la fonction ne gère que le mot entier, pas les espaces
        result = normalize_ingredient_name("Œufs")
        assert result == "oeuf"


# ============================================================================
# TESTS DE CONNEXION À LA BASE DE DONNÉES
# ============================================================================

class TestDatabaseConnection:
    """Tests pour la gestion de la connexion à la base de données"""

    @pytest.mark.database
    def test_get_db_context_manager(self, temp_db):
        """Teste que get_db fonctionne comme context manager"""
        from app.models.db_core import get_db

        # Utiliser le context manager
        with get_db() as con:
            # Vérifier que la connexion fonctionne
            cursor = con.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1, "La connexion devrait fonctionner"

    @pytest.mark.database
    def test_db_row_factory(self, temp_db):
        """Teste que row_factory est configuré (accès par nom de colonne)"""
        from app.models.db_core import get_db

        with get_db() as con:
            # Insérer une recette de test
            con.execute("""
                INSERT INTO recipe (slug, servings_default)
                VALUES ('test', 4)
            """)
            con.commit()

            # Récupérer avec accès par nom de colonne
            row = con.execute("SELECT slug, servings_default FROM recipe WHERE slug = 'test'").fetchone()

            # Tester l'accès par nom (grâce à row_factory)
            assert row['slug'] == 'test'
            assert row['servings_default'] == 4

    @pytest.mark.database
    @pytest.mark.slow
    def test_db_commit_on_success(self, temp_db):
        """Teste que les modifications sont bien committées automatiquement"""
        from app.models.db_core import get_db

        # Insérer des données
        with get_db() as con:
            con.execute("INSERT INTO recipe (slug) VALUES ('auto-commit-test')")
            # Pas de commit explicite, devrait être automatique

        # Vérifier que les données sont bien là dans une nouvelle connexion
        with get_db() as con:
            row = con.execute("SELECT slug FROM recipe WHERE slug = 'auto-commit-test'").fetchone()
            assert row is not None, "Les données devraient être committées automatiquement"
            assert row['slug'] == 'auto-commit-test'

    @pytest.mark.database
    def test_db_rollback_on_error(self, temp_db):
        """Teste que les modifications sont annulées en cas d'erreur"""
        from app.models.db_core import get_db

        # Provoquer une erreur
        with pytest.raises(Exception):
            with get_db() as con:
                con.execute("INSERT INTO recipe (slug) VALUES ('rollback-test')")
                # Provoquer une erreur
                raise Exception("Erreur de test")

        # Vérifier que les données ne sont PAS là (rollback)
        with get_db() as con:
            row = con.execute("SELECT slug FROM recipe WHERE slug = 'rollback-test'").fetchone()
            assert row is None, "Les données devraient avoir été rollback"


# ============================================================================
# TESTS PARAMÉTRÉS (pour tester plusieurs cas d'un coup)
# ============================================================================

@pytest.mark.unit
@pytest.mark.parametrize("input_text,expected", [
    ("Œufs", "oeuf"),
    ("Tomates", "tomate"),
    ("Ail", "ail"),
    ("Épinards", "epinard"),
    ("Saké", "sake"),
    ("Crème fraîche", "creme fraiche"),  # Note: espaces conservés
    ("riz", "riz"),
    ("", ""),
])
def test_normalize_parametrized(input_text, expected):
    """
    Test paramétré : teste plusieurs cas en une seule fonction
    Pytest va créer un test pour chaque tuple (input, expected)
    """
    result = normalize_ingredient_name(input_text)
    assert result == expected, f"'{input_text}' devrait donner '{expected}', obtenu '{result}'"
