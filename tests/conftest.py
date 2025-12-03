# tests/conftest.py
"""
Configuration partagée pour tous les tests
Les fixtures définies ici sont disponibles dans tous les tests
"""

import os
import sys
import sqlite3
import tempfile
import pytest
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# FIXTURES DE BASE
# ============================================================================

@pytest.fixture(scope="session")
def test_db_path():
    """
    Crée un fichier de base de données temporaire pour les tests
    Scope 'session' = créé une seule fois pour tous les tests
    """
    # Créer un fichier temporaire
    fd, path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(fd)

    yield path  # Fournit le chemin aux tests

    # Nettoyage après tous les tests
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture(scope="function")
def temp_db(test_db_path, monkeypatch):
    """
    Base de données temporaire pour chaque test
    Scope 'function' = recréée pour chaque test (isolation)

    Usage dans un test:
        def test_something(temp_db):
            # temp_db est une connexion SQLite prête à l'emploi
            temp_db.execute("SELECT * FROM recipe")
    """
    # Patcher le chemin de la DB pour utiliser la DB de test
    from app.models import db_core
    monkeypatch.setattr(db_core, 'DB_PATH', test_db_path)

    # Créer les tables
    con = sqlite3.connect(test_db_path)
    con.row_factory = sqlite3.Row

    # Schéma minimal pour les tests (simplifié)
    con.executescript("""
        -- Table recipe
        CREATE TABLE IF NOT EXISTS recipe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            servings_default INTEGER DEFAULT 4,
            country TEXT,
            image_url TEXT,
            thumbnail_url TEXT
        );

        -- Table recipe_translation
        CREATE TABLE IF NOT EXISTS recipe_translation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            lang TEXT NOT NULL,
            name TEXT NOT NULL,
            recipe_type TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipe(id),
            UNIQUE(recipe_id, lang)
        );

        -- Table recipe_ingredient
        CREATE TABLE IF NOT EXISTS recipe_ingredient (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            quantity REAL,
            FOREIGN KEY (recipe_id) REFERENCES recipe(id)
        );

        -- Table recipe_ingredient_translation
        CREATE TABLE IF NOT EXISTS recipe_ingredient_translation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_ingredient_id INTEGER NOT NULL,
            lang TEXT NOT NULL,
            name TEXT,
            unit TEXT,
            notes TEXT,
            FOREIGN KEY (recipe_ingredient_id) REFERENCES recipe_ingredient(id),
            UNIQUE(recipe_ingredient_id, lang)
        );

        -- Table step
        CREATE TABLE IF NOT EXISTS step (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            FOREIGN KEY (recipe_id) REFERENCES recipe(id)
        );

        -- Table step_translation
        CREATE TABLE IF NOT EXISTS step_translation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_id INTEGER NOT NULL,
            lang TEXT NOT NULL,
            text TEXT,
            FOREIGN KEY (step_id) REFERENCES step(id),
            UNIQUE(step_id, lang)
        );

        -- Table unit_conversion
        CREATE TABLE IF NOT EXISTS unit_conversion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_unit TEXT NOT NULL,
            to_unit TEXT NOT NULL,
            factor REAL NOT NULL,
            category TEXT,
            notes TEXT
        );

        -- Données de test pour les conversions
        INSERT INTO unit_conversion (from_unit, to_unit, factor, category) VALUES
            ('g', 'kg', 0.001, 'masse'),
            ('kg', 'g', 1000, 'masse'),
            ('mL', 'L', 0.001, 'volume'),
            ('L', 'mL', 1000, 'volume'),
            ('tasse', 'mL', 250, 'volume'),
            ('c. à soupe', 'mL', 15, 'volume'),
            ('c. à café', 'mL', 5, 'volume');
    """)

    con.commit()

    yield con  # Fournit la connexion aux tests

    # Nettoyage après chaque test
    con.close()


@pytest.fixture
def sample_recipe_data():
    """
    Données d'exemple pour créer une recette dans les tests

    Usage:
        def test_create_recipe(sample_recipe_data):
            recipe = create_recipe(**sample_recipe_data)
    """
    return {
        "slug": "test-recipe",
        "name_fr": "Recette de test",
        "name_jp": "テストレシピ",
        "servings": 4,
        "country": "FR",
        "recipe_type": "PERSO"
    }


# ============================================================================
# FIXTURES POUR LES MARKERS (organisation des tests)
# ============================================================================

def pytest_configure(config):
    """Configuration des markers personnalisés"""
    config.addinivalue_line("markers", "unit: Tests unitaires rapides")
    config.addinivalue_line("markers", "integration: Tests d'intégration")
    config.addinivalue_line("markers", "slow: Tests lents à exécuter")


# ============================================================================
# HOOKS PYTEST (personnalisation du comportement)
# ============================================================================

def pytest_collection_modifyitems(config, items):
    """
    Modifier les tests collectés
    Exemple: Ajouter automatiquement le marker 'database' aux tests qui utilisent temp_db
    """
    for item in items:
        # Si le test utilise la fixture temp_db, ajouter le marker 'database'
        if "temp_db" in item.fixturenames:
            item.add_marker(pytest.mark.database)


# ============================================================================
# FIXTURES UTILITAIRES
# ============================================================================

@pytest.fixture
def mock_groq_api(monkeypatch):
    """
    Simule l'API Groq pour les tests de traduction
    Évite de faire de vraies requêtes API pendant les tests

    Usage:
        def test_translate(mock_groq_api):
            result = translate_text("Bonjour", "fr", "jp")
            assert result == "こんにちは"  # Réponse mockée
    """
    def mock_translate(*args, **kwargs):
        return "Traduction simulée"

    # Patcher la fonction de traduction
    # monkeypatch.setattr("app.services.translation.translate", mock_translate)

    return mock_translate


@pytest.fixture
def capture_logs(caplog):
    """
    Capture les logs pour vérifier qu'ils sont bien émis

    Usage:
        def test_logging(capture_logs):
            log_access("127.0.0.1", "/recipes", "GET")
            assert "127.0.0.1" in capture_logs.text
    """
    return caplog
