-- Migration: Système many-to-many entre recettes et types d'événements
-- Permet à une recette d'être liée à plusieurs types d'événements (PRO + MASTER + WORKSHOP)

BEGIN TRANSACTION;

-- 1. Créer la table de liaison many-to-many
CREATE TABLE recipe_event_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    event_type_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recipe_id) REFERENCES recipe(id) ON DELETE CASCADE,
    FOREIGN KEY (event_type_id) REFERENCES event_type(id) ON DELETE CASCADE,
    UNIQUE(recipe_id, event_type_id)
);

-- 2. Index pour performance
CREATE INDEX idx_recipe_event_type_recipe ON recipe_event_type(recipe_id);
CREATE INDEX idx_recipe_event_type_event_type ON recipe_event_type(event_type_id);

-- 3. Migrer les données existantes depuis recipe.type
-- Mapping : PRO → event_type_id=1, MASTER → 2, PERSO → 3
INSERT INTO recipe_event_type (recipe_id, event_type_id)
SELECT
    r.id,
    CASE
        WHEN r.type = 'PRO' OR r.type = 'プロ' THEN 1
        WHEN r.type = 'MASTER' OR r.type = 'マイスター' THEN 2
        WHEN r.type = 'PERSO' OR r.type = 'じぶん' THEN 3
        ELSE NULL
    END as event_type_id
FROM recipe r
WHERE r.type IS NOT NULL
  AND CASE
        WHEN r.type = 'PRO' OR r.type = 'プロ' THEN 1
        WHEN r.type = 'MASTER' OR r.type = 'マイスター' THEN 2
        WHEN r.type = 'PERSO' OR r.type = 'じぶん' THEN 3
        ELSE NULL
      END IS NOT NULL;

-- 4. NOTE: On garde la colonne recipe.type pour compatibilité temporaire
-- Elle sera supprimée dans une future migration après validation

COMMIT;
