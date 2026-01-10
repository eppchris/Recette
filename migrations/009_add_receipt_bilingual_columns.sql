-- Migration: Rendre les items de tickets bilingues
-- Date: 2025-01-07
-- Description: Ajoute les colonnes pour stocker le texte original ET la traduction française

-- ============================================================================
-- Étape 1: Renommer et ajouter les colonnes bilingues
-- ============================================================================

-- Renommer la colonne existante pour indiquer qu'elle contient le texte original
ALTER TABLE receipt_item_match RENAME COLUMN receipt_item_text TO receipt_item_text_original;

-- Ajouter une colonne pour la traduction française
ALTER TABLE receipt_item_match ADD COLUMN receipt_item_text_fr TEXT;

-- ============================================================================
-- Étape 2: Peupler la colonne française avec les données existantes
-- ============================================================================

-- Pour l'instant, copier le texte original dans la colonne française
-- (car les données existantes sont déjà en français suite au bug de traduction)
UPDATE receipt_item_match
SET receipt_item_text_fr = receipt_item_text_original
WHERE receipt_item_text_fr IS NULL;

-- ============================================================================
-- Étape 3: Créer un index pour améliorer les performances
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_receipt_item_text_original ON receipt_item_match(receipt_item_text_original);
CREATE INDEX IF NOT EXISTS idx_receipt_item_text_fr ON receipt_item_match(receipt_item_text_fr);

-- ============================================================================
-- Note: Schéma résultant
-- ============================================================================
-- receipt_item_text_original: Texte tel qu'il apparaît sur le ticket (JP ou FR)
-- receipt_item_text_fr: Traduction française (ou identique si déjà en français)
