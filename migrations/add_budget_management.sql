-- Migration: Ajout de la gestion budgétaire pour les événements
-- Date: 2025-11-17
-- Description: Ajoute la gestion de budget prévisionnel/réel avec catégories personnalisables et multilingues

-- ============================================================================
-- 1. Ajouter le budget prévisionnel à la table event
-- ============================================================================

ALTER TABLE event ADD COLUMN budget_planned REAL DEFAULT NULL;

-- ============================================================================
-- 2. Créer la table des catégories de dépenses personnalisables (multilingue)
-- ============================================================================

CREATE TABLE IF NOT EXISTS expense_category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    is_system BOOLEAN DEFAULT 0,  -- Les catégories système ne peuvent pas être supprimées
    icon TEXT DEFAULT '📋',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table de traduction des catégories
CREATE TABLE IF NOT EXISTS expense_category_translation (
    category_id INTEGER NOT NULL,
    lang TEXT NOT NULL,
    name TEXT NOT NULL,
    PRIMARY KEY (category_id, lang),
    FOREIGN KEY (category_id) REFERENCES expense_category(id) ON DELETE CASCADE
);

-- Insérer les catégories par défaut
INSERT INTO expense_category (id, icon, is_system) VALUES
    (1, '🏠', 1),
    (2, '🎨', 1),
    (3, '🍽️', 1),
    (4, '🚗', 1),
    (5, '👥', 1),
    (6, '🎵', 1),
    (7, '📋', 1);

-- Traductions FR
INSERT INTO expense_category_translation (category_id, lang, name) VALUES
    (1, 'fr', 'Location'),
    (2, 'fr', 'Décoration'),
    (3, 'fr', 'Matériel'),
    (4, 'fr', 'Transport'),
    (5, 'fr', 'Personnel'),
    (6, 'fr', 'Animation'),
    (7, 'fr', 'Autre');

-- Traductions JP
INSERT INTO expense_category_translation (category_id, lang, name) VALUES
    (1, 'jp', '会場'),
    (2, 'jp', '装飾'),
    (3, 'jp', '材料'),
    (4, 'jp', '交通'),
    (5, 'jp', '人員'),
    (6, 'jp', '演出'),
    (7, 'jp', 'その他');

-- ============================================================================
-- 3. Créer la table des dépenses (hors ingrédients)
-- ============================================================================

CREATE TABLE IF NOT EXISTS event_expense (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    planned_amount REAL NOT NULL,      -- Montant prévu
    actual_amount REAL DEFAULT NULL,   -- Montant réel (NULL = pas encore payé)
    is_paid BOOLEAN DEFAULT 0,
    paid_date DATE DEFAULT NULL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES event(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES expense_category(id)
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_event_expense_event_id ON event_expense(event_id);
CREATE INDEX IF NOT EXISTS idx_event_expense_category_id ON event_expense(category_id);

-- ============================================================================
-- 4. Table des prix d'ingrédients (réutilisable entre événements)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ingredient_price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_name_normalized TEXT NOT NULL,  -- Nom normalisé (sans accents, minuscules)
    ingredient_name_display TEXT NOT NULL,     -- Nom affiché (avec accents, casse correcte)
    unit_price REAL NOT NULL,
    unit TEXT NOT NULL,
    source TEXT DEFAULT 'manual',  -- 'manual', 'shopping_list', 'import'
    last_used_date DATE DEFAULT CURRENT_DATE,
    usage_count INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherche rapide par nom
CREATE INDEX IF NOT EXISTS idx_ingredient_price_normalized ON ingredient_price_history(ingredient_name_normalized);

-- ============================================================================
-- 5. Ajouter les colonnes de prix à la table shopping_list_item
-- ============================================================================

-- Prix unitaire prévisionnel
ALTER TABLE shopping_list_item ADD COLUMN planned_unit_price REAL DEFAULT NULL;

-- Prix unitaire réel
ALTER TABLE shopping_list_item ADD COLUMN actual_unit_price REAL DEFAULT NULL;

-- Indicateur d'achat effectué
ALTER TABLE shopping_list_item ADD COLUMN is_purchased BOOLEAN DEFAULT 0;

-- ============================================================================
-- 6. Triggers
-- ============================================================================

-- Trigger pour mettre à jour updated_at sur event_expense
CREATE TRIGGER IF NOT EXISTS update_event_expense_timestamp
AFTER UPDATE ON event_expense
FOR EACH ROW
BEGIN
    UPDATE event_expense SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger pour mettre à jour updated_at sur ingredient_price_history
CREATE TRIGGER IF NOT EXISTS update_ingredient_price_timestamp
AFTER UPDATE ON ingredient_price_history
FOR EACH ROW
BEGIN
    UPDATE ingredient_price_history SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger pour sauvegarder les prix réels dans l'historique quand un item est acheté
CREATE TRIGGER IF NOT EXISTS save_actual_price_to_history
AFTER UPDATE OF actual_unit_price, is_purchased ON shopping_list_item
FOR EACH ROW
WHEN NEW.actual_unit_price IS NOT NULL AND NEW.is_purchased = 1
BEGIN
    -- Normaliser le nom pour la recherche
    INSERT OR REPLACE INTO ingredient_price_history (
        ingredient_name_normalized,
        ingredient_name_display,
        unit_price,
        unit,
        source,
        last_used_date,
        usage_count
    )
    VALUES (
        lower(replace(replace(NEW.ingredient_name, 'Œ', 'oe'), 'œ', 'oe')),
        NEW.ingredient_name,
        NEW.actual_unit_price,
        NEW.purchase_unit,
        'shopping_list',
        CURRENT_DATE,
        COALESCE(
            (SELECT usage_count + 1
             FROM ingredient_price_history
             WHERE ingredient_name_normalized = lower(replace(replace(NEW.ingredient_name, 'Œ', 'oe'), 'œ', 'oe'))
             AND unit = NEW.purchase_unit
             LIMIT 1),
            1
        )
    );
END;
