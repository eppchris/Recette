-- Migration: Ajouter 'unite' aux valeurs possibles de conversion_category
-- Date: 2025-11-30
-- Description: Permet de gérer les ingrédients achetés à l'unité (ex: oeufs, sachets)

-- SQLite ne permet pas de modifier directement une contrainte CHECK
-- Il faut recréer la table avec la nouvelle contrainte

BEGIN TRANSACTION;

-- 1. Créer une table temporaire avec la nouvelle contrainte
CREATE TABLE ingredient_price_catalog_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_name_fr TEXT NOT NULL,
    ingredient_name_jp TEXT,
    unit_fr TEXT NOT NULL,
    unit_jp TEXT,
    price_eur REAL,
    price_jpy REAL,
    qty REAL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    conversion_category TEXT CHECK(conversion_category IN ('volume', 'poids', 'unite')),
    UNIQUE(ingredient_name_fr, unit_fr)
);

-- 2. Copier toutes les données (avec toutes les colonnes explicitement)
INSERT INTO ingredient_price_catalog_new
    (id, ingredient_name_fr, ingredient_name_jp, unit_fr, unit_jp, price_eur, price_jpy, qty, created_at, updated_at, conversion_category)
SELECT
    id, ingredient_name_fr, ingredient_name_jp, unit_fr, unit_jp, price_eur, price_jpy, qty, created_at, updated_at, conversion_category
FROM ingredient_price_catalog;

-- 3. Supprimer l'ancienne table
DROP TABLE ingredient_price_catalog;

-- 4. Renommer la nouvelle table
ALTER TABLE ingredient_price_catalog_new RENAME TO ingredient_price_catalog;

-- 5. Recréer les index
CREATE INDEX IF NOT EXISTS idx_ingredient_name_fr ON ingredient_price_catalog(ingredient_name_fr);
CREATE INDEX IF NOT EXISTS idx_ingredient_name_jp ON ingredient_price_catalog(ingredient_name_jp);
CREATE INDEX IF NOT EXISTS idx_conversion_category ON ingredient_price_catalog(conversion_category);

COMMIT;

-- 6. Vérification
SELECT 'Vérification après migration:' as info;
SELECT
    COUNT(*) as total,
    COUNT(CASE WHEN conversion_category = 'volume' THEN 1 END) as volume_count,
    COUNT(CASE WHEN conversion_category = 'poids' THEN 1 END) as poids_count,
    COUNT(CASE WHEN conversion_category = 'unite' THEN 1 END) as unite_count,
    COUNT(CASE WHEN conversion_category IS NULL THEN 1 END) as null_count
FROM ingredient_price_catalog;

-- 7. Afficher la structure de la table
SELECT 'Structure de la table:' as info;
PRAGMA table_info(ingredient_price_catalog);
