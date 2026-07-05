-- Ajoute la préférence de langue par utilisateur
ALTER TABLE user ADD COLUMN preferred_lang TEXT NOT NULL DEFAULT 'fr';
