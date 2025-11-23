-- Migration: Simplification du système de conversion d'unités
-- Date: 2025-11-19
-- Description:
--   1. Supprimer toutes les conversions spécifiques (farine, huile, sucre)
--   2. Garder seulement les conversions de base
--   3. Renommer c.s. → cs, c.c. → cc

-- ============================================================================
-- Nettoyer la table: supprimer tout et repartir de zéro
-- ============================================================================

DELETE FROM unit_conversion;

-- ============================================================================
-- CONVERSIONS DE BASE - LIQUIDES (vers L)
-- ============================================================================

-- ml ↔ L
INSERT INTO unit_conversion (from_unit, to_unit, factor, category, notes, from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp)
VALUES
('ml', 'L', 0.001, 'volume', '1 ml = 0.001 L', 'ml', 'L', 'ml', 'L'),
('L', 'ml', 1000, 'volume', '1 L = 1000 ml', 'L', 'ml', 'L', 'ml');

-- cs (cuillère à soupe) → ml → L
INSERT INTO unit_conversion (from_unit, to_unit, factor, category, notes, from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp)
VALUES
('cs', 'ml', 15, 'volume', '1 cs = 15 ml', 'cs', 'ml', '大さじ', 'ml'),
('cs', 'L', 0.015, 'volume', '1 cs = 15 ml = 0.015 L', 'cs', 'L', '大さじ', 'L');

-- cc (cuillère à café) → ml → L
INSERT INTO unit_conversion (from_unit, to_unit, factor, category, notes, from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp)
VALUES
('cc', 'ml', 5, 'volume', '1 cc = 5 ml', 'cc', 'ml', '小さじ', 'ml'),
('cc', 'L', 0.005, 'volume', '1 cc = 5 ml = 0.005 L', 'cc', 'L', '小さじ', 'L');

-- tasse → ml → L (version française: 250ml)
INSERT INTO unit_conversion (from_unit, to_unit, factor, category, notes, from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp)
VALUES
('tasse', 'ml', 250, 'volume', '1 tasse = 250 ml', 'tasse', 'ml', 'カップ', 'ml'),
('tasse', 'L', 0.250, 'volume', '1 tasse = 250 ml = 0.250 L', 'tasse', 'L', 'カップ', 'L');

-- cup (version japonaise: 200ml)
INSERT INTO unit_conversion (from_unit, to_unit, factor, category, notes, from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp)
VALUES
('cup', 'ml', 200, 'volume', '1 cup (JP) = 200 ml', 'cup', 'ml', 'カップ', 'ml'),
('cup', 'L', 0.200, 'volume', '1 cup (JP) = 200 ml = 0.200 L', 'cup', 'L', 'カップ', 'L');

-- ============================================================================
-- CONVERSIONS DE BASE - SOLIDES (vers kg ou g selon quantité)
-- ============================================================================

-- g ↔ kg
INSERT INTO unit_conversion (from_unit, to_unit, factor, category, notes, from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp)
VALUES
('g', 'kg', 0.001, 'poids', '1 g = 0.001 kg', 'g', 'kg', 'g', 'kg'),
('kg', 'g', 1000, 'poids', '1 kg = 1000 g', 'kg', 'g', 'kg', 'g');

-- cs → g → kg (approximation générale: 15g)
INSERT INTO unit_conversion (from_unit, to_unit, factor, category, notes, from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp)
VALUES
('cs', 'g', 15, 'poids', '1 cs ≈ 15 g', 'cs', 'g', '大さじ', 'g'),
('cs', 'kg', 0.015, 'poids', '1 cs ≈ 15 g = 0.015 kg', 'cs', 'kg', '大さじ', 'kg');

-- cc → g → kg (approximation générale: 5g)
INSERT INTO unit_conversion (from_unit, to_unit, factor, category, notes, from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp)
VALUES
('cc', 'g', 5, 'poids', '1 cc ≈ 5 g', 'cc', 'g', '小さじ', 'g'),
('cc', 'kg', 0.005, 'poids', '1 cc ≈ 5 g = 0.005 kg', 'cc', 'kg', '小さじ', 'kg');

-- tasse → g → kg (approximation générale: 180g)
INSERT INTO unit_conversion (from_unit, to_unit, factor, category, notes, from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp)
VALUES
('tasse', 'g', 180, 'poids', '1 tasse ≈ 180 g', 'tasse', 'g', 'カップ', 'g'),
('tasse', 'kg', 0.180, 'poids', '1 tasse ≈ 180 g = 0.180 kg', 'tasse', 'kg', 'カップ', 'kg');

-- ============================================================================
-- CONVERSIONS DE QUANTITÉ (unités japonaises)
-- ============================================================================

INSERT INTO unit_conversion (from_unit, to_unit, factor, category, notes, from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp)
VALUES
('本', 'pièce', 1, 'quantité', '本 = pièce', 'pièce', 'pièce', '本', '本'),
('個', 'pièce', 1, 'quantité', '個 = pièce', 'pièce', 'pièce', '個', '個'),
('かけ', 'gousse', 1, 'quantité', 'かけ = gousse', 'gousse', 'gousse', 'かけ', 'かけ'),
('株', 'pied', 1, 'quantité', '株 = pied', 'pied', 'pied', '株', '株'),
('切', 'tranche', 1, 'quantité', '切 = tranche', 'tranche', 'tranche', '切れ', '切れ'),
('丁', 'bloc', 1, 'quantité', '丁 = bloc', 'bloc', 'bloc', '丁', '丁');

-- ============================================================================
-- Résumé
-- ============================================================================

SELECT 'Migration terminée. Total des conversions:', COUNT(*) FROM unit_conversion;
SELECT 'Conversions par catégorie:';
SELECT category, COUNT(*) as nombre FROM unit_conversion GROUP BY category ORDER BY category;
