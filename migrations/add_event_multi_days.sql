-- Migration: Gestion événements multi-jours avec organisation par jour
-- Date: 2025-12-04
-- Description: Ajoute les champs pour gérer les événements sur plusieurs jours
--             et l'organisation des recettes par jour

-- 1. Ajouter les champs date_debut, date_fin et nombre_jours à la table event
-- Ces champs permettent de gérer des événements sur plusieurs jours
BEGIN TRANSACTION;

-- Ajouter date_debut
ALTER TABLE event ADD COLUMN date_debut DATE;

-- Ajouter date_fin
ALTER TABLE event ADD COLUMN date_fin DATE;

-- Ajouter nombre_jours (nombre de jours travaillés, peut être différent de date_fin - date_debut)
ALTER TABLE event ADD COLUMN nombre_jours INTEGER DEFAULT 1;

-- 2. Migrer les données existantes (event_date devient date_debut et date_fin)
UPDATE event
SET date_debut = event_date,
    date_fin = event_date,
    nombre_jours = 1;

COMMIT;

-- 3. Table pour stocker les dates sélectionnées d'un événement
-- Permet de désélectionner certains jours (ex: week-end)
CREATE TABLE IF NOT EXISTS event_date (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    date DATE NOT NULL,
    is_selected BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES event(id) ON DELETE CASCADE,
    UNIQUE(event_id, date)
);

-- 4. Table pour l'organisation des recettes par jour
-- Stocke quelle recette est prévue pour quel jour et dans quel ordre
CREATE TABLE IF NOT EXISTS event_recipe_planning (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    recipe_id INTEGER NOT NULL,
    event_date_id INTEGER NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES event(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipe(id) ON DELETE CASCADE,
    FOREIGN KEY (event_date_id) REFERENCES event_date(id) ON DELETE CASCADE,
    UNIQUE(event_id, recipe_id, event_date_id)
);

-- Index pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_event_date_event ON event_date(event_id);
CREATE INDEX IF NOT EXISTS idx_event_date_date ON event_date(date);
CREATE INDEX IF NOT EXISTS idx_event_recipe_planning_event ON event_recipe_planning(event_id);
CREATE INDEX IF NOT EXISTS idx_event_recipe_planning_date ON event_recipe_planning(event_date_id);
CREATE INDEX IF NOT EXISTS idx_event_recipe_planning_recipe ON event_recipe_planning(recipe_id);
