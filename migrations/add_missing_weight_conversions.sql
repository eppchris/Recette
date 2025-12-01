-- Migration: Ajouter les conversions poids manquantes pour les unités japonaises
-- Date: 2025-11-30
-- Description: Permet de convertir 大 (cuillère à soupe) et カップ (tasse) vers g/kg pour les ingrédients solides

-- Conversions pour 大さじ (grande cuillère japonaise) vers poids
INSERT INTO unit_conversion
    (from_unit, to_unit, factor, category, notes, from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp)
VALUES
    ('大', 'g', 15.0, 'poids', '1 大さじ ≈ 15 g (approximation pour solides)', 'cs', 'g', '大', 'g'),
    ('大', 'kg', 0.015, 'poids', '1 大さじ ≈ 15 g = 0.015 kg', 'cs', 'kg', '大', 'kg');

-- Conversions pour カップ (tasse japonaise) vers poids
-- Note: 1 カップ (JP) = 200ml, pour les solides ≈ 180g (basé sur le riz)
INSERT INTO unit_conversion
    (from_unit, to_unit, factor, category, notes, from_unit_fr, to_unit_fr, from_unit_jp, to_unit_jp)
VALUES
    ('カップ', 'g', 180.0, 'poids', '1 カップ ≈ 180 g (approximation pour solides type riz)', 'tasse', 'g', 'カップ', 'g'),
    ('カップ', 'kg', 0.18, 'poids', '1 カップ ≈ 180 g = 0.18 kg', 'tasse', 'kg', 'カップ', 'kg');

-- Vérification
SELECT '=== Conversions ajoutées ===' as info;
SELECT from_unit, to_unit, factor, category, notes
FROM unit_conversion
WHERE from_unit IN ('大', 'カップ')
ORDER BY from_unit, category, to_unit;
