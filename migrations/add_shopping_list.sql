-- Migration: Ajout du système de listes de courses avec conversion
-- Date: 2025-11-13
-- Description: Tables pour gérer les conversions de quantités et listes de courses

-- Table des listes de courses
CREATE TABLE IF NOT EXISTS shopping_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lang TEXT NOT NULL DEFAULT 'fr'
);

-- Table des items de liste de courses (ingrédients convertis)
CREATE TABLE IF NOT EXISTS shopping_list_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shopping_list_id INTEGER NOT NULL,
    recipe_id INTEGER,
    ingredient_name TEXT NOT NULL,
    original_quantity REAL,
    original_unit TEXT,
    converted_quantity REAL,
    purchase_unit TEXT,
    is_negligible BOOLEAN DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (shopping_list_id) REFERENCES shopping_list(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipe(id) ON DELETE SET NULL
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_shopping_list_created ON shopping_list(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_shopping_list_item_list ON shopping_list_item(shopping_list_id);
