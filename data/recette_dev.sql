-- ============================================================================
-- Database Schema - Recipe Application
-- Version 2.0 - 2025-11-05 (schéma simplifié sans référentiel ingredient)
-- ============================================================================

BEGIN TRANSACTION;

-- ============================================================================
-- TABLE RECIPE
-- Main recipe information (language-independent)
-- ============================================================================
CREATE TABLE recipe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    servings_default INTEGER NOT NULL DEFAULT 4,
    country TEXT,  -- jp, fr, it...
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_recipe_slug ON recipe(slug);
CREATE INDEX idx_recipe_country ON recipe(country);

-- ============================================================================
-- TABLE RECIPE_TRANSLATION
-- Recipe name translations in different languages
-- ============================================================================
CREATE TABLE recipe_translation (
    recipe_id INTEGER NOT NULL,
    lang TEXT NOT NULL CHECK(lang IN ('fr', 'jp')),
    name TEXT NOT NULL,
    recipe_type TEXT,  -- "PRO" (FR) vs "プロ" (JP), "MASTER" vs "マスター"
    PRIMARY KEY (recipe_id, lang),
    FOREIGN KEY (recipe_id) REFERENCES recipe(id) ON DELETE CASCADE
);

CREATE INDEX idx_recipe_translation_lang ON recipe_translation(lang);

-- ============================================================================
-- TABLE RECIPE_INGREDIENT
-- Ingredients of a recipe (language-independent: only quantity)
-- ============================================================================
CREATE TABLE recipe_ingredient (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    position INTEGER NOT NULL,  -- display order
    quantity REAL,  -- can be NULL
    FOREIGN KEY (recipe_id) REFERENCES recipe(id) ON DELETE CASCADE
);

CREATE INDEX idx_recipe_ingredient_recipe ON recipe_ingredient(recipe_id);
CREATE INDEX idx_recipe_ingredient_position ON recipe_ingredient(recipe_id, position);

-- ============================================================================
-- TABLE RECIPE_INGREDIENT_TRANSLATION
-- Translations for ingredient name, unit and notes
-- ============================================================================
CREATE TABLE recipe_ingredient_translation (
    recipe_ingredient_id INTEGER NOT NULL,
    lang TEXT NOT NULL CHECK(lang IN ('fr', 'jp')),
    name TEXT NOT NULL,  -- ingredient name (e.g., "Saumon", "鮭")
    unit TEXT,  -- "cs" (FR) vs "大" (JP), "tasse" vs "カップ"
    notes TEXT,  -- "par personne" (FR) vs "人数分" (JP)
    PRIMARY KEY (recipe_ingredient_id, lang),
    FOREIGN KEY (recipe_ingredient_id) REFERENCES recipe_ingredient(id) ON DELETE CASCADE
);

CREATE INDEX idx_recipe_ingredient_translation_lang ON recipe_ingredient_translation(lang);
CREATE INDEX idx_recipe_ingredient_translation_name ON recipe_ingredient_translation(name);

-- ============================================================================
-- TABLE STEP
-- Recipe preparation steps (language-independent structure)
-- ============================================================================
CREATE TABLE step (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    position INTEGER NOT NULL,  -- execution order
    FOREIGN KEY (recipe_id) REFERENCES recipe(id) ON DELETE CASCADE
);

CREATE INDEX idx_step_recipe ON step(recipe_id);
CREATE INDEX idx_step_position ON step(recipe_id, position);

-- ============================================================================
-- TABLE STEP_TRANSLATION
-- Step text translations
-- ============================================================================
CREATE TABLE step_translation (
    step_id INTEGER NOT NULL,
    lang TEXT NOT NULL CHECK(lang IN ('fr', 'jp')),
    text TEXT NOT NULL,
    PRIMARY KEY (step_id, lang),
    FOREIGN KEY (step_id) REFERENCES step(id) ON DELETE CASCADE
);

CREATE INDEX idx_step_translation_lang ON step_translation(lang);

-- ============================================================================
-- TRIGGERS for automatic updated_at timestamp
-- ============================================================================
CREATE TRIGGER update_recipe_timestamp 
AFTER UPDATE ON recipe
BEGIN
    UPDATE recipe SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

COMMIT;

-- ============================================================================
-- Notes pour le futur :
-- Quand on voudra créer le référentiel d'ingrédients global, on ajoutera :
-- - TABLE ingredient (id, standard_unit)
-- - TABLE ingredient_translation (ingredient_id, lang, name)
-- Et on fera un batch pour détecter les doublons et les corriger
-- ============================================================================