-- Migration: Ajout des images dans les étapes
-- Date: 2026-02-08
-- Description: Permet d'ajouter des photos comme étapes dans les recettes
-- Les étapes peuvent maintenant être de type 'text' ou 'image'

-- Ajouter la colonne type à step
ALTER TABLE step ADD COLUMN type TEXT DEFAULT 'text' CHECK(type IN ('text', 'image'));

-- Ajouter la colonne image_url à step
ALTER TABLE step ADD COLUMN image_url TEXT DEFAULT NULL;

-- Créer un index sur le type pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_step_type ON step(type);

-- Message de confirmation
SELECT 'Migration terminée: Colonnes type et image_url ajoutées à step' AS status;
