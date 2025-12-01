-- Migration: Remplacer is_liquid par conversion_category
-- Date: 2025-11-30
-- Description: Rend le code plus explicite et maintenable

-- Étape 1 : Ajouter la nouvelle colonne
ALTER TABLE ingredient_price_catalog
ADD COLUMN conversion_category TEXT CHECK(conversion_category IN ('volume', 'poids'));

-- Étape 2 : Migrer les données existantes
UPDATE ingredient_price_catalog
SET conversion_category = CASE
    WHEN is_liquid = 1 THEN 'volume'
    WHEN is_liquid = 0 THEN 'poids'
    ELSE NULL  -- Garder NULL si is_liquid était NULL
END;

-- Étape 3 : Vérification
-- SELECT ingredient_name_fr, is_liquid, conversion_category FROM ingredient_price_catalog LIMIT 10;

-- Étape 4 : Supprimer l'ancienne colonne (optionnel - à faire après vérification)
-- Note: SQLite ne supporte pas DROP COLUMN avant version 3.35.0
-- Si votre SQLite est ancien, garder is_liquid mais ne plus l'utiliser
-- ALTER TABLE ingredient_price_catalog DROP COLUMN is_liquid;

-- Étape 5 : Index pour performance
CREATE INDEX IF NOT EXISTS idx_ingredient_conversion_category
ON ingredient_price_catalog(conversion_category);

-- Commentaire explicatif
-- conversion_category peut avoir 3 valeurs:
--   'volume' = liquide (agrégation vers L)
--   'poids'  = solide (agrégation vers kg)
--   NULL     = non défini (utiliser valeur par défaut)
