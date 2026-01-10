-- Migration: Traçabilité de la source des prix (ticket vs manuel)
-- Date: 2025-01-07
-- Description: Ajoute des colonnes pour tracer l'origine des prix

-- ============================================================================
-- Étape 1: Ajouter les colonnes de traçabilité
-- ============================================================================

-- Pour les prix en EUR
ALTER TABLE ingredient_price_catalog ADD COLUMN price_eur_source TEXT DEFAULT 'manual';
ALTER TABLE ingredient_price_catalog ADD COLUMN price_eur_last_receipt_date TEXT;

-- Pour les prix en JPY
ALTER TABLE ingredient_price_catalog ADD COLUMN price_jpy_source TEXT DEFAULT 'manual';
ALTER TABLE ingredient_price_catalog ADD COLUMN price_jpy_last_receipt_date TEXT;

-- ============================================================================
-- Étape 2: Mettre à jour les prix existants comme "manual"
-- ============================================================================

UPDATE ingredient_price_catalog
SET price_eur_source = 'manual'
WHERE price_eur IS NOT NULL;

UPDATE ingredient_price_catalog
SET price_jpy_source = 'manual'
WHERE price_jpy IS NOT NULL;

-- ============================================================================
-- Étape 3: Créer des index pour améliorer les performances
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_price_eur_source ON ingredient_price_catalog(price_eur_source);
CREATE INDEX IF NOT EXISTS idx_price_jpy_source ON ingredient_price_catalog(price_jpy_source);

-- ============================================================================
-- Note: Le trigger existant update_catalog_after_actual_price sera modifié
-- pour mettre à jour ces nouvelles colonnes lors de l'application d'un ticket
-- ============================================================================
