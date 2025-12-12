-- Migration: Ajout du champ description dans recipe_translation
-- Date: 2025-12-09
-- Description: Permet d'ajouter une description courte pour chaque recette

-- Ajouter la colonne description à recipe_translation
ALTER TABLE recipe_translation ADD COLUMN description TEXT DEFAULT '';

-- Message de confirmation
SELECT 'Migration terminée: Colonne description ajoutée à recipe_translation' AS status;
