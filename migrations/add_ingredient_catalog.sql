-- Migration: Catalogue des prix des ingrédients
-- Date: 2025-11-17
-- Description: Ajoute les tables pour gérer le catalogue de prix des ingrédients

-- ============================================================================
-- Table: ingredient_price_catalog
-- Catalogue centralisé des prix des ingrédients
-- ============================================================================

CREATE TABLE IF NOT EXISTS ingredient_price_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_name TEXT NOT NULL UNIQUE,
    price_eur REAL,          -- Prix en euros (nullable)
    price_jpy REAL,          -- Prix en yens (nullable)
    unit TEXT DEFAULT 'kg',  -- Unité (kg, g, L, ml, pièce, etc.)
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ingredient_name ON ingredient_price_catalog(ingredient_name);

-- ============================================================================
-- Table: expense_ingredient_detail
-- Détail des ingrédients pour une dépense de type "Ingrédients"
-- ============================================================================

CREATE TABLE IF NOT EXISTS expense_ingredient_detail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_id INTEGER NOT NULL,
    shopping_list_item_id INTEGER NOT NULL,  -- Lien vers l'item de la liste de courses
    ingredient_name TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    planned_unit_price REAL,     -- Prix unitaire prévu
    actual_unit_price REAL,      -- Prix unitaire réel (après achat)
    planned_total REAL,          -- Quantité × Prix prévu
    actual_total REAL,           -- Quantité × Prix réel
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (expense_id) REFERENCES event_expense(id) ON DELETE CASCADE,
    FOREIGN KEY (shopping_list_item_id) REFERENCES shopping_list_item(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_expense_ingredient_expense ON expense_ingredient_detail(expense_id);
CREATE INDEX IF NOT EXISTS idx_expense_ingredient_shopping ON expense_ingredient_detail(shopping_list_item_id);

-- ============================================================================
-- Trigger: Mettre à jour le catalogue après achat réel
-- ============================================================================

CREATE TRIGGER IF NOT EXISTS update_catalog_after_actual_price
AFTER UPDATE OF actual_unit_price ON expense_ingredient_detail
WHEN NEW.actual_unit_price IS NOT NULL
BEGIN
    -- Récupérer la devise de l'événement
    UPDATE ingredient_price_catalog
    SET
        price_eur = CASE
            WHEN (SELECT currency FROM event WHERE id = (SELECT event_id FROM event_expense WHERE id = NEW.expense_id)) = 'EUR'
            THEN NEW.actual_unit_price
            ELSE price_eur
        END,
        price_jpy = CASE
            WHEN (SELECT currency FROM event WHERE id = (SELECT event_id FROM event_expense WHERE id = NEW.expense_id)) = 'JPY'
            THEN NEW.actual_unit_price
            ELSE price_jpy
        END,
        last_updated = CURRENT_TIMESTAMP
    WHERE ingredient_name = NEW.ingredient_name;

    -- Si l'ingrédient n'existe pas, l'insérer
    INSERT OR IGNORE INTO ingredient_price_catalog (ingredient_name, unit)
    VALUES (NEW.ingredient_name, NEW.unit);
END;

-- ============================================================================
-- Données initiales: Synchroniser les ingrédients existants
-- ============================================================================

-- Insérer tous les ingrédients uniques depuis les recettes (sans prix)
INSERT OR IGNORE INTO ingredient_price_catalog (ingredient_name, unit)
SELECT DISTINCT
    rit.name as ingredient_name,
    COALESCE(rit.unit, 'kg') as unit
FROM recipe_ingredient ri
JOIN recipe_ingredient_translation rit ON rit.recipe_ingredient_id = ri.id
WHERE rit.lang = 'fr'  -- On prend les noms français comme référence
ORDER BY rit.name;
