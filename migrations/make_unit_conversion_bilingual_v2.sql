-- Migration: Rendre la table unit_conversion bilingue (FR/JP) - Version 2
-- Date: 2025-11-19
-- Description: Ajoute des colonnes pour les noms français et japonais des unités
--              Sans simplifier les noms (garde les parenthèses)

-- ============================================================================
-- Ajouter les colonnes bilingues
-- ============================================================================

ALTER TABLE unit_conversion ADD COLUMN from_unit_fr TEXT;
ALTER TABLE unit_conversion ADD COLUMN to_unit_fr TEXT;
ALTER TABLE unit_conversion ADD COLUMN from_unit_jp TEXT;
ALTER TABLE unit_conversion ADD COLUMN to_unit_jp TEXT;

-- ============================================================================
-- Migrer les données existantes - Colonnes FR
-- ============================================================================

UPDATE unit_conversion SET from_unit_fr = from_unit;
UPDATE unit_conversion SET to_unit_fr = to_unit;

-- ============================================================================
-- Traductions japonaises - Volume (liquides)
-- ============================================================================

-- ml, L
UPDATE unit_conversion SET from_unit_jp = 'ml' WHERE from_unit = 'ml';
UPDATE unit_conversion SET to_unit_jp = 'ml' WHERE to_unit = 'ml';
UPDATE unit_conversion SET from_unit_jp = 'L' WHERE from_unit = 'L';
UPDATE unit_conversion SET to_unit_jp = 'L' WHERE to_unit = 'L';

-- c.s. / 大さじ
UPDATE unit_conversion SET from_unit_jp = '大さじ' WHERE from_unit IN ('c.s.', 'cs', '大');
UPDATE unit_conversion SET to_unit_jp = '大さじ' WHERE to_unit IN ('c.s.', 'cs', '大');

-- c.c. / 小さじ
UPDATE unit_conversion SET from_unit_jp = '小さじ' WHERE from_unit IN ('c.c.', 'cc', '小');
UPDATE unit_conversion SET to_unit_jp = '小さじ' WHERE to_unit IN ('c.c.', 'cc', '小');

-- tasse / カップ
UPDATE unit_conversion SET from_unit_jp = 'カップ' WHERE from_unit IN ('tasse', 'cup');
UPDATE unit_conversion SET to_unit_jp = 'カップ' WHERE to_unit IN ('tasse', 'cup');
UPDATE unit_conversion SET from_unit_jp = 'カップ' WHERE from_unit = 'カップ';
UPDATE unit_conversion SET to_unit_jp = 'カップ' WHERE to_unit = 'カップ';

-- ============================================================================
-- Traductions japonaises - Poids
-- ============================================================================

UPDATE unit_conversion SET from_unit_jp = 'g' WHERE from_unit = 'g';
UPDATE unit_conversion SET to_unit_jp = 'g' WHERE to_unit = 'g';
UPDATE unit_conversion SET from_unit_jp = 'kg' WHERE from_unit = 'kg';
UPDATE unit_conversion SET to_unit_jp = 'kg' WHERE to_unit = 'kg';

-- ============================================================================
-- Traductions japonaises - Unités spécifiques par ingrédient
-- ============================================================================

-- Farine
UPDATE unit_conversion SET from_unit_jp = '大さじ (小麦粉)' WHERE from_unit = 'c.s. (farine)';
UPDATE unit_conversion SET from_unit_jp = '小さじ (小麦粉)' WHERE from_unit = 'c.c. (farine)';
UPDATE unit_conversion SET from_unit_jp = 'カップ (小麦粉)' WHERE from_unit = 'tasse (farine)';
UPDATE unit_conversion SET from_unit_jp = 'カップ (小麦粉)' WHERE from_unit = 'カップ (farine)';

-- Huile
UPDATE unit_conversion SET from_unit_jp = '大さじ (油)' WHERE from_unit = 'c.s. (huile)';
UPDATE unit_conversion SET from_unit_jp = '小さじ (油)' WHERE from_unit = 'c.c. (huile)';

-- Sucre
UPDATE unit_conversion SET from_unit_jp = '大さじ (砂糖)' WHERE from_unit = 'c.s. (sucre)';
UPDATE unit_conversion SET from_unit_jp = '小さじ (砂糖)' WHERE from_unit = 'c.c. (sucre)';
UPDATE unit_conversion SET from_unit_jp = 'カップ (砂糖)' WHERE from_unit = 'tasse (sucre)';
UPDATE unit_conversion SET from_unit_jp = 'カップ (砂糖)' WHERE from_unit = 'カップ (sucre)';

-- ============================================================================
-- Traductions japonaises - Unités de quantité
-- ============================================================================

UPDATE unit_conversion SET from_unit_jp = '本' WHERE from_unit = '本';
UPDATE unit_conversion SET to_unit_jp = '個' WHERE to_unit = 'pièce';

UPDATE unit_conversion SET from_unit_jp = '個' WHERE from_unit = '個';
UPDATE unit_conversion SET to_unit_jp = '個' WHERE to_unit = 'pièce';

UPDATE unit_conversion SET from_unit_jp = 'かけ' WHERE from_unit = 'かけ';
UPDATE unit_conversion SET to_unit_jp = 'かけ' WHERE to_unit = 'gousse';

UPDATE unit_conversion SET from_unit_jp = '株' WHERE from_unit = '株';
UPDATE unit_conversion SET to_unit_jp = '株' WHERE to_unit = 'pied';

UPDATE unit_conversion SET from_unit_jp = '切れ' WHERE from_unit = '切';
UPDATE unit_conversion SET to_unit_jp = '切れ' WHERE to_unit = 'tranche';

UPDATE unit_conversion SET from_unit_jp = '丁' WHERE from_unit = '丁';
UPDATE unit_conversion SET to_unit_jp = '丁' WHERE to_unit = 'bloc';

-- ============================================================================
-- Remplir les traductions manquantes (copier FR si JP manquant)
-- ============================================================================

UPDATE unit_conversion SET from_unit_jp = from_unit_fr WHERE from_unit_jp IS NULL;
UPDATE unit_conversion SET to_unit_jp = to_unit_fr WHERE to_unit_jp IS NULL;
