-- Migration: Rendre les items de tickets bilingues
-- Date: 2025-01-07
-- Description: Ajoute les colonnes pour stocker le texte original ET la traduction française
-- Méthode: Recréation de table (compatible avec SQLite < 3.25.0)

-- ============================================================================
-- Étape 1: Créer une nouvelle table avec les nouvelles colonnes
-- ============================================================================

CREATE TABLE receipt_item_match_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id INTEGER NOT NULL,
    receipt_item_text_original TEXT NOT NULL,  -- Nouvelle colonne (ancien nom: receipt_item_text)
    receipt_item_text_fr TEXT,                  -- Nouvelle colonne pour traduction FR
    receipt_price REAL,
    receipt_quantity REAL DEFAULT 1.0,
    receipt_unit TEXT,
    matched_ingredient_id INTEGER,
    confidence_score REAL DEFAULT 0.0,
    status TEXT DEFAULT 'pending',
    validated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (receipt_id) REFERENCES receipt_upload_history(id) ON DELETE CASCADE,
    FOREIGN KEY (matched_ingredient_id) REFERENCES ingredient_price_catalog(id) ON DELETE SET NULL
);

-- ============================================================================
-- Étape 2: Copier les données de l'ancienne table vers la nouvelle
-- ============================================================================

INSERT INTO receipt_item_match_new (
    id,
    receipt_id,
    receipt_item_text_original,
    receipt_item_text_fr,
    receipt_price,
    receipt_quantity,
    receipt_unit,
    matched_ingredient_id,
    confidence_score,
    status,
    validated_at,
    created_at
)
SELECT
    id,
    receipt_id,
    receipt_item_text,           -- Ancienne colonne → receipt_item_text_original
    receipt_item_text,           -- Copier aussi dans receipt_item_text_fr
    receipt_price,
    receipt_quantity,
    receipt_unit,
    matched_ingredient_id,
    confidence_score,
    status,
    validated_at,
    created_at
FROM receipt_item_match;

-- ============================================================================
-- Étape 3: Supprimer l'ancienne table
-- ============================================================================

DROP TABLE receipt_item_match;

-- ============================================================================
-- Étape 4: Renommer la nouvelle table
-- ============================================================================

ALTER TABLE receipt_item_match_new RENAME TO receipt_item_match;

-- ============================================================================
-- Étape 5: Recréer les index
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_receipt_item_receipt_id ON receipt_item_match(receipt_id);
CREATE INDEX IF NOT EXISTS idx_receipt_item_status ON receipt_item_match(status);
CREATE INDEX IF NOT EXISTS idx_receipt_item_text_original ON receipt_item_match(receipt_item_text_original);
CREATE INDEX IF NOT EXISTS idx_receipt_item_text_fr ON receipt_item_match(receipt_item_text_fr);

-- ============================================================================
-- Note: Schéma résultant
-- ============================================================================
-- receipt_item_text_original: Texte tel qu'il apparaît sur le ticket (JP ou FR)
-- receipt_item_text_fr: Traduction française (ou identique si déjà en français)
--
-- Cette migration est compatible avec SQLite < 3.25.0 car elle utilise
-- la technique de recréation de table au lieu de ALTER TABLE RENAME COLUMN
