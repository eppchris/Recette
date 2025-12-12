-- Migration: Ajout de user_id aux tables participant et participant_group
-- Date: 2025-12-12
-- Description: Permet à chaque utilisateur de gérer ses propres participants et groupes
--              L'utilisateur 'admin' (username='admin') voit tout

-- Ajouter colonne user_id à la table participant
ALTER TABLE participant ADD COLUMN user_id INTEGER;

-- Ajouter colonne user_id à la table participant_group
ALTER TABLE participant_group ADD COLUMN user_id INTEGER;

-- Associer les participants existants à l'utilisateur admin (id=1)
-- On suppose que l'utilisateur admin a l'ID 1
UPDATE participant SET user_id = 1 WHERE user_id IS NULL;
UPDATE participant_group SET user_id = 1 WHERE user_id IS NULL;

-- Rendre user_id obligatoire maintenant que les données existantes sont migrées
-- Note: SQLite ne supporte pas ALTER COLUMN, donc on accepte NULL mais on le gère dans l'application

-- Créer des index pour améliorer les performances des requêtes filtrées par user_id
CREATE INDEX IF NOT EXISTS idx_participant_user_id ON participant(user_id);
CREATE INDEX IF NOT EXISTS idx_participant_group_user_id ON participant_group(user_id);
