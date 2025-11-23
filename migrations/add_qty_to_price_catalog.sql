-- Migration: Ajouter la colonne qty (quantité) au catalogue des prix
-- Date: 2025-11-19
-- Description: Ajoute une colonne pour stocker la quantité de référence du prix

-- Ajouter la colonne qty avec valeur par défaut 1
ALTER TABLE ingredient_price_catalog ADD COLUMN qty REAL DEFAULT 1.0;

-- Mettre à jour les descriptions
-- Les prix sont désormais exprimés pour une quantité donnée
-- Exemple: 1.5 EUR pour 250g, donc qty=250 et unit='g'

-- Afficher la structure mise à jour
SELECT 'Migration terminée. Structure de la table:';
PRAGMA table_info(ingredient_price_catalog);
