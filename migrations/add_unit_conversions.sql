-- Migration: Système de conversion d'unités
-- Date: 2025-11-17
-- Description: Ajoute une table pour convertir entre unités de recette et unités d'achat

-- ============================================================================
-- Table: unit_conversion
-- Stocke les facteurs de conversion entre différentes unités
-- ============================================================================

CREATE TABLE IF NOT EXISTS unit_conversion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_unit TEXT NOT NULL,      -- Unité source (ex: c.s., ml, g)
    to_unit TEXT NOT NULL,         -- Unité cible (ex: L, kg)
    factor REAL NOT NULL,          -- Facteur de multiplication (from * factor = to)
    category TEXT,                 -- Catégorie (volume, poids, quantité)
    notes TEXT,                    -- Notes explicatives
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(from_unit, to_unit)
);

-- ============================================================================
-- Conversions de volume (liquides)
-- ============================================================================

-- Millilitres
INSERT OR IGNORE INTO unit_conversion (from_unit, to_unit, factor, category, notes) VALUES
('ml', 'L', 0.001, 'volume', '1 ml = 0.001 L'),
('L', 'ml', 1000, 'volume', '1 L = 1000 ml');

-- Cuillères à soupe (c.s.) et cuillères à café (c.c.)
INSERT OR IGNORE INTO unit_conversion (from_unit, to_unit, factor, category, notes) VALUES
('c.s.', 'ml', 15, 'volume', '1 cuillère à soupe = 15 ml'),
('大', 'ml', 15, 'volume', '1 cuillère à soupe (jp) = 15 ml'),
('c.c.', 'ml', 5, 'volume', '1 cuillère à café = 5 ml'),
('小', 'ml', 5, 'volume', '1 cuillère à café (jp) = 5 ml');

-- Tasses
INSERT OR IGNORE INTO unit_conversion (from_unit, to_unit, factor, category, notes) VALUES
('tasse', 'ml', 250, 'volume', '1 tasse = 250 ml'),
('カップ', 'ml', 200, 'volume', '1 tasse japonaise = 200 ml'),
('cup', 'ml', 240, 'volume', '1 cup US = 240 ml');

-- ============================================================================
-- Conversions de poids
-- ============================================================================

INSERT OR IGNORE INTO unit_conversion (from_unit, to_unit, factor, category, notes) VALUES
('g', 'kg', 0.001, 'poids', '1 g = 0.001 kg'),
('kg', 'g', 1000, 'poids', '1 kg = 1000 g');

-- ============================================================================
-- Conversions spécifiques aux ingrédients courants
-- ============================================================================

-- Huile d'olive (densité ~0.92)
INSERT OR IGNORE INTO unit_conversion (from_unit, to_unit, factor, category, notes) VALUES
('c.s. (huile)', 'ml', 15, 'volume-huile', '1 c.s. huile = 15 ml'),
('c.s. (huile)', 'g', 13.8, 'poids-huile', '1 c.s. huile ≈ 13.8g (densité 0.92)');

-- Farine (densité ~0.6)
INSERT OR IGNORE INTO unit_conversion (from_unit, to_unit, factor, category, notes) VALUES
('c.s. (farine)', 'g', 8, 'poids-farine', '1 c.s. farine ≈ 8g'),
('tasse (farine)', 'g', 120, 'poids-farine', '1 tasse farine ≈ 120g');

-- Sucre (densité ~0.85)
INSERT OR IGNORE INTO unit_conversion (from_unit, to_unit, factor, category, notes) VALUES
('c.s. (sucre)', 'g', 12.5, 'poids-sucre', '1 c.s. sucre ≈ 12.5g'),
('tasse (sucre)', 'g', 200, 'poids-sucre', '1 tasse sucre ≈ 200g');

-- ============================================================================
-- Unités japonaises
-- ============================================================================

-- Unités de quantité
INSERT OR IGNORE INTO unit_conversion (from_unit, to_unit, factor, category, notes) VALUES
('本', 'pièce', 1, 'quantité', '本 = pièce/unité'),
('個', 'pièce', 1, 'quantité', '個 = pièce'),
('かけ', 'gousse', 1, 'quantité', 'かけ = gousse'),
('株', 'pied', 1, 'quantité', '株 = pied (légume)'),
('切', 'tranche', 1, 'quantité', '切 = tranche'),
('丁', 'bloc', 1, 'quantité', '丁 = bloc');

-- ============================================================================
-- Index pour performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_unit_from ON unit_conversion(from_unit);
CREATE INDEX IF NOT EXISTS idx_unit_to ON unit_conversion(to_unit);
CREATE INDEX IF NOT EXISTS idx_unit_category ON unit_conversion(category);

-- ============================================================================
-- Vue: Conversions bidirectionnelles complètes
-- Pour faciliter les requêtes dans les deux sens
-- ============================================================================

CREATE VIEW IF NOT EXISTS v_unit_conversions_bidirectional AS
SELECT
    from_unit,
    to_unit,
    factor,
    category,
    notes
FROM unit_conversion
UNION ALL
-- Ajouter les conversions inverses automatiquement (si pas déjà définies)
SELECT
    to_unit as from_unit,
    from_unit as to_unit,
    1.0 / factor as factor,
    category,
    'Conversion inverse de: ' || notes as notes
FROM unit_conversion
WHERE NOT EXISTS (
    SELECT 1 FROM unit_conversion uc2
    WHERE uc2.from_unit = unit_conversion.to_unit
      AND uc2.to_unit = unit_conversion.from_unit
);
