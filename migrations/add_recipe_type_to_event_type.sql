-- Migration: Ajoute le lien entre type d'événement et type de recette
-- Permet de définir quel type de recette (PRO/PERSO/MASTER) est associé à chaque événement

BEGIN TRANSACTION;

-- 1. Ajouter la colonne recipe_type avec des valeurs par défaut
ALTER TABLE event_type ADD COLUMN recipe_type_fr TEXT;
ALTER TABLE event_type ADD COLUMN recipe_type_jp TEXT;

-- 2. Remplir avec les valeurs pour les types existants
UPDATE event_type SET recipe_type_fr = 'PRO', recipe_type_jp = 'プロ'
WHERE name_fr = 'Événement professionnel';

UPDATE event_type SET recipe_type_fr = 'MASTER', recipe_type_jp = 'マイスター'
WHERE name_fr = 'Cours de cuisine';

UPDATE event_type SET recipe_type_fr = 'PERSO', recipe_type_jp = 'じぶん'
WHERE name_fr = 'Réception privée';

-- 3. Rendre les colonnes NOT NULL après les avoir remplies
-- (SQLite ne permet pas de créer directement avec NOT NULL et valeurs par défaut)
CREATE TABLE event_type_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_fr TEXT NOT NULL UNIQUE,
    name_jp TEXT NOT NULL,
    description_fr TEXT,
    description_jp TEXT,
    recipe_type_fr TEXT NOT NULL,
    recipe_type_jp TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO event_type_new (id, name_fr, name_jp, description_fr, description_jp, recipe_type_fr, recipe_type_jp, created_at)
SELECT id, name_fr, name_jp, description_fr, description_jp, recipe_type_fr, recipe_type_jp, created_at
FROM event_type;

DROP TABLE event_type;
ALTER TABLE event_type_new RENAME TO event_type;

-- 4. Recréer les index
CREATE INDEX idx_event_type_name_fr ON event_type(name_fr);
CREATE INDEX idx_event_type_name_jp ON event_type(name_jp);

COMMIT;
