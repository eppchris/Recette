-- Migration: Ajout du support des photos de recettes
-- Date: 2025-11-13
-- Description: Ajoute les colonnes image_url et thumbnail_url à la table recipe

-- Ajouter la colonne pour l'image principale (800px)
ALTER TABLE recipe ADD COLUMN image_url TEXT DEFAULT NULL;

-- Ajouter la colonne pour le thumbnail (300px)
ALTER TABLE recipe ADD COLUMN thumbnail_url TEXT DEFAULT NULL;

-- Créer un index pour optimiser les requêtes sur les recettes avec images
CREATE INDEX IF NOT EXISTS idx_recipe_image ON recipe(image_url);
