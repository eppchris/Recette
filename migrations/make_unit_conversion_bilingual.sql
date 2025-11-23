-- Migration: Rendre la table unit_conversion bilingue (FR/JP)
-- Date: 2025-11-19
-- Description: Ajoute des colonnes pour les noms français et japonais des unités

-- ============================================================================
-- Ajouter les colonnes bilingues
-- ============================================================================

-- Ajouter colonnes pour noms français
ALTER TABLE unit_conversion ADD COLUMN from_unit_fr TEXT;
ALTER TABLE unit_conversion ADD COLUMN to_unit_fr TEXT;

-- Ajouter colonnes pour noms japonais
ALTER TABLE unit_conversion ADD COLUMN from_unit_jp TEXT;
ALTER TABLE unit_conversion ADD COLUMN to_unit_jp TEXT;

-- ============================================================================
-- Migrer les données existantes
-- ============================================================================

-- Copier les valeurs existantes dans les colonnes FR
UPDATE unit_conversion SET from_unit_fr = from_unit;
UPDATE unit_conversion SET to_unit_fr = to_unit;

-- ============================================================================
-- Remplir les traductions japonaises pour les unités de volume
-- ============================================================================

UPDATE unit_conversion SET from_unit_jp = 'ml' WHERE from_unit = 'ml';
UPDATE unit_conversion SET to_unit_jp = 'ml' WHERE to_unit = 'ml';

UPDATE unit_conversion SET from_unit_jp = 'L' WHERE from_unit = 'L';
UPDATE unit_conversion SET to_unit_jp = 'L' WHERE to_unit = 'L';

UPDATE unit_conversion SET from_unit_jp = '大さじ' WHERE from_unit IN ('c.s.', 'cs', '大');
UPDATE unit_conversion SET to_unit_jp = '大さじ' WHERE to_unit IN ('c.s.', 'cs', '大');

UPDATE unit_conversion SET from_unit_jp = '小さじ' WHERE from_unit IN ('c.c.', 'cc', '小');
UPDATE unit_conversion SET to_unit_jp = '小さじ' WHERE to_unit IN ('c.c.', 'cc', '小');

UPDATE unit_conversion SET from_unit_jp = 'カップ' WHERE from_unit IN ('tasse', 'cup', 'カップ');
UPDATE unit_conversion SET to_unit_jp = 'カップ' WHERE to_unit IN ('tasse', 'cup', 'カップ');

-- ============================================================================
-- Remplir les traductions japonaises pour les unités de poids
-- ============================================================================

UPDATE unit_conversion SET from_unit_jp = 'g' WHERE from_unit = 'g';
UPDATE unit_conversion SET to_unit_jp = 'g' WHERE to_unit = 'g';

UPDATE unit_conversion SET from_unit_jp = 'kg' WHERE from_unit = 'kg';
UPDATE unit_conversion SET to_unit_jp = 'kg' WHERE to_unit = 'kg';

-- ============================================================================
-- Remplir les traductions japonaises pour les unités de quantité
-- ============================================================================

UPDATE unit_conversion SET from_unit_jp = '個' WHERE from_unit = 'pièce';
UPDATE unit_conversion SET to_unit_jp = '個' WHERE to_unit = 'pièce';

UPDATE unit_conversion SET from_unit_jp = 'かけ' WHERE from_unit = 'gousse';
UPDATE unit_conversion SET to_unit_jp = 'かけ' WHERE to_unit = 'gousse';

UPDATE unit_conversion SET from_unit_jp = '株' WHERE from_unit = 'pied';
UPDATE unit_conversion SET to_unit_jp = '株' WHERE to_unit = 'pied';

UPDATE unit_conversion SET from_unit_jp = '切れ' WHERE from_unit = 'tranche';
UPDATE unit_conversion SET to_unit_jp = '切れ' WHERE to_unit = 'tranche';

UPDATE unit_conversion SET from_unit_jp = '丁' WHERE from_unit = 'bloc';
UPDATE unit_conversion SET to_unit_jp = '丁' WHERE to_unit = 'bloc';

-- ============================================================================
-- Simplifier les unités spécifiques (enlever les parenthèses d'ingrédient)
-- ============================================================================

-- Remplacer "c.s. (farine)" par "c.s." et ajouter l'info dans category/notes
UPDATE unit_conversion
SET from_unit = 'c.s.',
    from_unit_fr = 'c.s.',
    from_unit_jp = '大さじ',
    category = 'farine',
    notes = REPLACE(notes, 'c.s. (farine)', 'c.s. farine')
WHERE from_unit LIKE 'c.s. (farine)%';

UPDATE unit_conversion
SET to_unit = 'c.s.',
    to_unit_fr = 'c.s.',
    to_unit_jp = '大さじ'
WHERE to_unit LIKE 'c.s. (farine)%';

UPDATE unit_conversion
SET from_unit = 'c.c.',
    from_unit_fr = 'c.c.',
    from_unit_jp = '小さじ',
    category = 'farine',
    notes = REPLACE(notes, 'c.c. (farine)', 'c.c. farine')
WHERE from_unit LIKE 'c.c. (farine)%';

UPDATE unit_conversion
SET from_unit = 'tasse',
    from_unit_fr = 'tasse',
    from_unit_jp = 'カップ',
    category = 'farine',
    notes = REPLACE(notes, 'tasse (farine)', 'tasse farine')
WHERE from_unit LIKE 'tasse (farine)%';

UPDATE unit_conversion
SET from_unit = 'カップ',
    from_unit_fr = 'tasse',
    from_unit_jp = 'カップ',
    category = 'farine',
    notes = REPLACE(notes, 'カップ (farine)', 'カップ farine')
WHERE from_unit LIKE 'カップ (farine)%';

-- Huile
UPDATE unit_conversion
SET from_unit = 'c.s.',
    from_unit_fr = 'c.s.',
    from_unit_jp = '大さじ',
    category = 'huile',
    notes = REPLACE(notes, 'c.s. (huile)', 'c.s. huile')
WHERE from_unit LIKE 'c.s. (huile)%';

UPDATE unit_conversion
SET from_unit = 'c.c.',
    from_unit_fr = 'c.c.',
    from_unit_jp = '小さじ',
    category = 'huile',
    notes = REPLACE(notes, 'c.c. (huile)', 'c.c. huile')
WHERE from_unit LIKE 'c.c. (huile)%';

-- Sucre
UPDATE unit_conversion
SET from_unit = 'c.s.',
    from_unit_fr = 'c.s.',
    from_unit_jp = '大さじ',
    category = 'sucre',
    notes = REPLACE(notes, 'c.s. (sucre)', 'c.s. sucre')
WHERE from_unit LIKE 'c.s. (sucre)%';

UPDATE unit_conversion
SET from_unit = 'c.c.',
    from_unit_fr = 'c.c.',
    from_unit_jp = '小さじ',
    category = 'sucre',
    notes = REPLACE(notes, 'c.c. (sucre)', 'c.c. sucre')
WHERE from_unit LIKE 'c.c. (sucre)%';

UPDATE unit_conversion
SET from_unit = 'tasse',
    from_unit_fr = 'tasse',
    from_unit_jp = 'カップ',
    category = 'sucre',
    notes = REPLACE(notes, 'tasse (sucre)', 'tasse sucre')
WHERE from_unit LIKE 'tasse (sucre)%';

UPDATE unit_conversion
SET from_unit = 'カップ',
    from_unit_fr = 'tasse',
    from_unit_jp = 'カップ',
    category = 'sucre',
    notes = REPLACE(notes, 'カップ (sucre)', 'カップ sucre')
WHERE from_unit LIKE 'カップ (sucre)%';

-- ============================================================================
-- Remplir les traductions manquantes
-- ============================================================================

-- Pour toutes les lignes sans traduction JP, copier FR
UPDATE unit_conversion SET from_unit_jp = from_unit_fr WHERE from_unit_jp IS NULL;
UPDATE unit_conversion SET to_unit_jp = to_unit_fr WHERE to_unit_jp IS NULL;

-- ============================================================================
-- Renommer les catégories pour être plus simples
-- ============================================================================

UPDATE unit_conversion SET category = 'volume' WHERE category LIKE 'volume%';
UPDATE unit_conversion SET category = 'poids' WHERE category LIKE 'poids%';
UPDATE unit_conversion SET category = 'quantité' WHERE category LIKE 'quantit%';
