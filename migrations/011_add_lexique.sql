-- Migration 011 : Ajout de la colonne de lecture phonétique japonaise (furigana)
-- Utilisée dans le lexique bilingue pour afficher les hiragana au-dessus des kanji

ALTER TABLE ingredient_price_catalog
ADD COLUMN ingredient_name_jp_reading TEXT;

-- Index pour la recherche par lecture phonétique
CREATE INDEX IF NOT EXISTS idx_ingredient_name_jp_reading
    ON ingredient_price_catalog(ingredient_name_jp_reading);
