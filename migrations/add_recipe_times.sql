-- Ajout des temps de préparation et cuisson sur la recette
ALTER TABLE recipe ADD COLUMN prep_time INTEGER DEFAULT 0;
ALTER TABLE recipe ADD COLUMN cook_time INTEGER DEFAULT 0;
