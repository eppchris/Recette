-- Migration: Créer la table ingredient_specific_conversions
-- Date: 2025-11-30
-- Description: Stocke les conversions spécifiques par ingrédient (ex: 50ml sucre = 80g)

CREATE TABLE IF NOT EXISTS ingredient_specific_conversions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_name_fr TEXT NOT NULL,

    -- Conversion
    from_unit TEXT NOT NULL,
    to_unit TEXT NOT NULL,
    factor REAL NOT NULL,

    -- Métadonnées
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Contraintes
    UNIQUE(ingredient_name_fr, from_unit, to_unit),
    FOREIGN KEY (ingredient_name_fr) REFERENCES ingredient_price_catalog(ingredient_name_fr) ON DELETE CASCADE
);

-- Index pour performance
CREATE INDEX IF NOT EXISTS idx_specific_conv_ingredient
ON ingredient_specific_conversions(ingredient_name_fr);

CREATE INDEX IF NOT EXISTS idx_specific_conv_units
ON ingredient_specific_conversions(ingredient_name_fr, from_unit);

-- Trigger pour updated_at
CREATE TRIGGER IF NOT EXISTS update_specific_conv_timestamp
AFTER UPDATE ON ingredient_specific_conversions
FOR EACH ROW
BEGIN
    UPDATE ingredient_specific_conversions
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- Exemples de conversions spécifiques (à décommenter si besoin)
-- INSERT INTO ingredient_specific_conversions (ingredient_name_fr, from_unit, to_unit, factor, notes) VALUES
-- ('Sucre', 'ml', 'g', 1.6, '50 ml de sucre en poudre tassé ≈ 80g'),
-- ('Dashi', 'ml', 'g', 0.02, '50 ml de bouillon = 1g de poudre (dilution 1:50)'),
-- ('Bouillon cube', 'cube', 'ml', 500.0, '1 cube = 500ml de bouillon');

-- Commentaire explicatif
-- Cette table permet de gérer les cas où :
-- 1. Une unité de recette n'existe pas dans unit_conversion (ex: "cube")
-- 2. Une conversion dépend de l'ingrédient (ex: ml de sucre ≠ ml d'eau)
-- 3. Un ingrédient change de forme (poudre → liquide comme le dashi)
