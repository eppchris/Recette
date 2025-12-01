-- Migration: Ajoute le support bilingue aux types d'événements
-- Les types d'événements seront gérables dans l'interface admin Tags & Catégories

BEGIN TRANSACTION;

-- 1. Créer nouvelle table avec colonnes bilingues
CREATE TABLE event_type_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_fr TEXT NOT NULL UNIQUE,
    name_jp TEXT NOT NULL,
    description_fr TEXT,
    description_jp TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Migrer les données existantes avec traductions
INSERT INTO event_type_new (id, name_fr, name_jp, description_fr, description_jp, created_at)
VALUES
    (1, 'Événement professionnel', 'プロイベント', 'Pour clients ou partenaires professionnels', 'プロのお客様またはパートナー向け', '2025-11-13 16:38:06'),
    (2, 'Cours de cuisine', 'マスタークラス', 'Atelier ou cours de cuisine', '料理教室またはワークショップ', '2025-11-13 16:38:06'),
    (3, 'Réception privée', 'プライベートパーティー', 'Invitation chez soi ou restaurant', '自宅またはレストランでの招待', '2025-11-13 16:38:06');

-- 3. Supprimer ancienne table
DROP TABLE event_type;

-- 4. Renommer nouvelle table
ALTER TABLE event_type_new RENAME TO event_type;

-- 5. Créer index pour performance
CREATE INDEX idx_event_type_name_fr ON event_type(name_fr);
CREATE INDEX idx_event_type_name_jp ON event_type(name_jp);

COMMIT;
