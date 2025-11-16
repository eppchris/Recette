-- Script d'initialisation complète de la base de données
-- À exécuter sur une base vide pour créer toutes les tables

-- Table principale des recettes
CREATE TABLE IF NOT EXISTS recipe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    servings_default INTEGER NOT NULL DEFAULT 4,
    country TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    image_url TEXT DEFAULT NULL,
    thumbnail_url TEXT DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_recipe_slug ON recipe(slug);
CREATE INDEX IF NOT EXISTS idx_recipe_country ON recipe(country);
CREATE INDEX IF NOT EXISTS idx_recipe_image ON recipe(image_url);

-- Traductions des recettes
CREATE TABLE IF NOT EXISTS recipe_translation (
    recipe_id INTEGER NOT NULL,
    lang TEXT NOT NULL CHECK(lang IN ('fr', 'jp')),
    name TEXT NOT NULL,
    recipe_type TEXT,
    PRIMARY KEY (recipe_id, lang),
    FOREIGN KEY (recipe_id) REFERENCES recipe(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_recipe_translation_lang ON recipe_translation(lang);

-- Ingrédients des recettes
CREATE TABLE IF NOT EXISTS recipe_ingredient (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    quantity REAL,
    FOREIGN KEY (recipe_id) REFERENCES recipe(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_recipe_ingredient_recipe ON recipe_ingredient(recipe_id);
CREATE INDEX IF NOT EXISTS idx_recipe_ingredient_position ON recipe_ingredient(recipe_id, position);

-- Traductions des ingrédients
CREATE TABLE IF NOT EXISTS recipe_ingredient_translation (
    recipe_ingredient_id INTEGER NOT NULL,
    lang TEXT NOT NULL CHECK(lang IN ('fr', 'jp')),
    name TEXT NOT NULL,
    unit TEXT,
    notes TEXT,
    PRIMARY KEY (recipe_ingredient_id, lang),
    FOREIGN KEY (recipe_ingredient_id) REFERENCES recipe_ingredient(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_recipe_ingredient_translation_lang ON recipe_ingredient_translation(lang);
CREATE INDEX IF NOT EXISTS idx_recipe_ingredient_translation_name ON recipe_ingredient_translation(name);

-- Étapes des recettes
CREATE TABLE IF NOT EXISTS step (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    FOREIGN KEY (recipe_id) REFERENCES recipe(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_step_recipe ON step(recipe_id);
CREATE INDEX IF NOT EXISTS idx_step_position ON step(recipe_id, position);

-- Traductions des étapes
CREATE TABLE IF NOT EXISTS step_translation (
    step_id INTEGER NOT NULL,
    lang TEXT NOT NULL CHECK(lang IN ('fr', 'jp')),
    text TEXT NOT NULL,
    PRIMARY KEY (step_id, lang),
    FOREIGN KEY (step_id) REFERENCES step(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_step_translation_lang ON step_translation(lang);

-- Trigger pour mettre à jour le timestamp
DROP TRIGGER IF EXISTS update_recipe_timestamp;
CREATE TRIGGER update_recipe_timestamp
AFTER UPDATE ON recipe
BEGIN
    UPDATE recipe SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Types d'événements
CREATE TABLE IF NOT EXISTS event_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Événements
CREATE TABLE IF NOT EXISTS event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    event_date DATE NOT NULL,
    location TEXT,
    attendees INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_type_id) REFERENCES event_type(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_event_date ON event(event_date DESC);
CREATE INDEX IF NOT EXISTS idx_event_type ON event(event_type_id);

-- Recettes associées aux événements
CREATE TABLE IF NOT EXISTS event_recipe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    recipe_id INTEGER NOT NULL,
    servings_multiplier REAL NOT NULL DEFAULT 1.0,
    position INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (event_id) REFERENCES event(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipe(id) ON DELETE CASCADE,
    UNIQUE(event_id, recipe_id)
);

CREATE INDEX IF NOT EXISTS idx_event_recipe_event ON event_recipe(event_id);
CREATE INDEX IF NOT EXISTS idx_event_recipe_recipe ON event_recipe(recipe_id);

-- Liste de courses
CREATE TABLE IF NOT EXISTS shopping_list_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    ingredient_name TEXT NOT NULL,
    needed_quantity REAL,
    needed_unit TEXT,
    purchase_quantity REAL,
    purchase_unit TEXT,
    is_checked BOOLEAN DEFAULT 0,
    notes TEXT,
    source_recipes TEXT,
    position INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES event(id) ON DELETE CASCADE
);

-- Insérer les types d'événements par défaut
INSERT OR IGNORE INTO event_type (name) VALUES
    ('Dîner'),
    ('Déjeuner'),
    ('Pique-nique'),
    ('Fête'),
    ('Autre');
