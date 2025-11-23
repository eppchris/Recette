-- Migration: Rendre le catalogue des prix bilingue
-- Date: 2025-11-17
-- Description: Ajoute les colonnes japonaises pour les noms et unités d'ingrédients

-- ============================================================================
-- Étape 1: Ajouter les colonnes pour le japonais
-- ============================================================================

-- Renommer la colonne existante pour être explicite sur la langue
ALTER TABLE ingredient_price_catalog RENAME COLUMN ingredient_name TO ingredient_name_fr;
ALTER TABLE ingredient_price_catalog RENAME COLUMN unit TO unit_fr;

-- Ajouter les colonnes japonaises
ALTER TABLE ingredient_price_catalog ADD COLUMN ingredient_name_jp TEXT;
ALTER TABLE ingredient_price_catalog ADD COLUMN unit_jp TEXT;

-- ============================================================================
-- Étape 2: Peupler les colonnes japonaises depuis les recettes
-- ============================================================================

-- Pour chaque ingrédient français, trouver son équivalent japonais
UPDATE ingredient_price_catalog
SET ingredient_name_jp = (
    SELECT rit_jp.name
    FROM recipe_ingredient_translation rit_fr
    JOIN recipe_ingredient ri ON ri.id = rit_fr.recipe_ingredient_id
    JOIN recipe_ingredient_translation rit_jp ON rit_jp.recipe_ingredient_id = ri.id
    WHERE rit_fr.lang = 'fr'
      AND rit_jp.lang = 'jp'
      AND LOWER(rit_fr.name) = LOWER(ingredient_price_catalog.ingredient_name_fr)
    LIMIT 1
),
unit_jp = (
    SELECT rit_jp.unit
    FROM recipe_ingredient_translation rit_fr
    JOIN recipe_ingredient ri ON ri.id = rit_fr.recipe_ingredient_id
    JOIN recipe_ingredient_translation rit_jp ON rit_jp.recipe_ingredient_id = ri.id
    WHERE rit_fr.lang = 'fr'
      AND rit_jp.lang = 'jp'
      AND LOWER(rit_fr.name) = LOWER(ingredient_price_catalog.ingredient_name_fr)
      AND rit_jp.unit IS NOT NULL
    LIMIT 1
);

-- ============================================================================
-- Étape 3: Valeurs par défaut pour les entrées sans traduction
-- ============================================================================

-- Si pas de nom japonais trouvé, copier le français
UPDATE ingredient_price_catalog
SET ingredient_name_jp = ingredient_name_fr
WHERE ingredient_name_jp IS NULL;

-- Si pas d'unité japonaise trouvée, copier le français
UPDATE ingredient_price_catalog
SET unit_jp = unit_fr
WHERE unit_jp IS NULL;

-- Rendre les colonnes NOT NULL maintenant qu'elles sont peuplées
-- Note: SQLite ne supporte pas ALTER COLUMN, on laisse nullable pour la flexibilité

-- ============================================================================
-- Étape 4: Mettre à jour l'index
-- ============================================================================

-- Recréer l'index pour couvrir les deux langues
DROP INDEX IF EXISTS idx_ingredient_name;
CREATE INDEX IF NOT EXISTS idx_ingredient_name_fr ON ingredient_price_catalog(ingredient_name_fr);
CREATE INDEX IF NOT EXISTS idx_ingredient_name_jp ON ingredient_price_catalog(ingredient_name_jp);

-- ============================================================================
-- Vérification: Afficher quelques exemples
-- ============================================================================

-- SELECT
--     ingredient_name_fr,
--     ingredient_name_jp,
--     unit_fr,
--     unit_jp,
--     price_eur,
--     price_jpy
-- FROM ingredient_price_catalog
-- LIMIT 10;
