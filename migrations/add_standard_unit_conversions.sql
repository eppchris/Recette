-- Migration: Ajout des conversions d'unités standard dans unit_conversion
-- Date: 2024-12-17
-- Description: Remplace les données fixes de conversion_service.py par des données en base
--              Ces conversions sont utilisées par le nouveau système de calcul de coût

-- ============================================================================
-- CONVERSIONS DE POIDS (category = 'poids')
-- ============================================================================

-- Conversions vers grammes (base)
INSERT OR IGNORE INTO unit_conversion (from_unit, to_unit, factor, category, notes, from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp)
VALUES
    ('kg', 'g', 1000, 'poids', '1 kg = 1000 g', 'kg', 'g', 'kg', 'g'),
    ('g', 'kg', 0.001, 'poids', '1 g = 0.001 kg', 'g', 'kg', 'g', 'kg'),
    ('mg', 'g', 0.001, 'poids', '1 mg = 0.001 g', 'mg', 'g', 'mg', 'g'),
    ('g', 'mg', 1000, 'poids', '1 g = 1000 mg', 'g', 'mg', 'g', 'mg');

-- ============================================================================
-- CONVERSIONS DE VOLUME (category = 'volume')
-- ============================================================================

-- Conversions vers millilitres (base)
INSERT OR IGNORE INTO unit_conversion (from_unit, to_unit, factor, category, notes, from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp)
VALUES
    ('l', 'ml', 1000, 'volume', '1 L = 1000 ml', 'L', 'ml', 'L', 'ml'),
    ('ml', 'l', 0.001, 'volume', '1 ml = 0.001 L', 'ml', 'L', 'ml', 'L'),
    ('cl', 'ml', 10, 'volume', '1 cL = 10 ml', 'cL', 'ml', 'cL', 'ml'),
    ('ml', 'cl', 0.1, 'volume', '1 ml = 0.1 cL', 'ml', 'cL', 'ml', 'cL'),
    ('dl', 'ml', 100, 'volume', '1 dL = 100 ml', 'dL', 'ml', 'dL', 'ml'),
    ('ml', 'dl', 0.01, 'volume', '1 ml = 0.01 dL', 'ml', 'dL', 'ml', 'dL');

-- Conversions cuillères (basées sur volume standard)
-- Note: Ces valeurs sont des approximations culinaires standard
INSERT OR IGNORE INTO unit_conversion (from_unit, to_unit, factor, category, notes, from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp)
VALUES
    ('c.s.', 'ml', 15, 'volume', '1 cuillère à soupe ≈ 15 ml', 'c.s.', 'ml', '大さじ', 'ml'),
    ('ml', 'c.s.', 0.0667, 'volume', '1 ml ≈ 0.0667 c.s.', 'ml', 'c.s.', 'ml', '大さじ'),
    ('c.c.', 'ml', 5, 'volume', '1 cuillère à café ≈ 5 ml', 'c.c.', 'ml', '小さじ', 'ml'),
    ('ml', 'c.c.', 0.2, 'volume', '1 ml = 0.2 c.c.', 'ml', 'c.c.', 'ml', '小さじ'),
    ('tbsp', 'ml', 15, 'volume', '1 tablespoon ≈ 15 ml', 'c.s.', 'ml', '大さじ', 'ml'),
    ('tsp', 'ml', 5, 'volume', '1 teaspoon ≈ 5 ml', 'c.c.', 'ml', '小さじ', 'ml');

-- Conversions tasses (basées sur standard US/métrique)
INSERT OR IGNORE INTO unit_conversion (from_unit, to_unit, factor, category, notes, from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp)
VALUES
    ('tasse', 'ml', 250, 'volume', '1 tasse métrique = 250 ml', 'tasse', 'ml', 'カップ', 'ml'),
    ('ml', 'tasse', 0.004, 'volume', '1 ml = 0.004 tasse', 'ml', 'tasse', 'ml', 'カップ'),
    ('cup', 'ml', 240, 'volume', '1 cup US ≈ 240 ml', 'tasse', 'ml', 'カップ', 'ml');

-- ============================================================================
-- CONVERSIONS D'UNITÉS (category = 'unite')
-- ============================================================================

-- Conversions pour unités discrètes (pièces, sachets, etc.)
-- Note: Ces conversions sont génériques, les conversions spécifiques par ingrédient
--       doivent être dans ingredient_specific_conversions
INSERT OR IGNORE INTO unit_conversion (from_unit, to_unit, factor, category, notes, from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp)
VALUES
    ('pièce', 'pièce', 1, 'unite', 'Identité: 1 pièce = 1 pièce', 'pièce', 'pièce', '個', '個'),
    ('sachet', 'sachet', 1, 'unite', 'Identité: 1 sachet = 1 sachet', 'sachet', 'sachet', '袋', '袋'),
    ('boîte', 'boîte', 1, 'unite', 'Identité: 1 boîte = 1 boîte', 'boîte', 'boîte', '缶', '缶');

-- ============================================================================
-- VÉRIFICATION POST-INSERTION
-- ============================================================================

-- Afficher le nombre de conversions par catégorie
-- Cette requête est pour information (commentée en production)
-- SELECT category, COUNT(*) as count FROM unit_conversion GROUP BY category;
