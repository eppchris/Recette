-- Ajout d'un champ "conseils" libre sur les traductions de recette
ALTER TABLE recipe_translation ADD COLUMN tips TEXT;
