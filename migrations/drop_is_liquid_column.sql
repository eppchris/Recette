-- Migration: Supprimer la colonne is_liquid (remplacée par conversion_category)
-- Date: 2025-11-30
-- Description: Nettoyage - supprime le champ redondant is_liquid

-- Vérifier que les données sont bien migrées
SELECT 'Vérification avant suppression:' as info;
SELECT
    COUNT(*) as total,
    COUNT(CASE WHEN conversion_category IS NOT NULL THEN 1 END) as avec_category,
    COUNT(CASE WHEN is_liquid IS NOT NULL THEN 1 END) as avec_is_liquid
FROM ingredient_price_catalog;

-- Supprimer l'index associé à is_liquid
DROP INDEX IF EXISTS idx_ingredient_is_liquid;

-- Supprimer la colonne is_liquid
ALTER TABLE ingredient_price_catalog
DROP COLUMN is_liquid;

-- Vérification après suppression
SELECT 'Vérification après suppression:' as info;
PRAGMA table_info(ingredient_price_catalog);
