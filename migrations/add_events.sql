-- Migration: Système de gestion d'événements
-- Date: 2025-11-13
-- Description: Ajoute les tables pour gérer les événements culinaires et la génération de listes de courses

-- Table des types d'événements (PRO, MASTER, INVITATION, etc.)
CREATE TABLE IF NOT EXISTS event_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des événements
CREATE TABLE IF NOT EXISTS event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    event_date DATE NOT NULL,
    location TEXT,
    attendees INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_type_id) REFERENCES event_type(id) ON DELETE RESTRICT
);

-- Table d'association événement ↔ recettes
CREATE TABLE IF NOT EXISTS event_recipe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    recipe_id INTEGER NOT NULL,
    servings_multiplier REAL NOT NULL DEFAULT 1.0,
    position INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (event_id) REFERENCES event(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipe(id) ON DELETE CASCADE,
    UNIQUE(event_id, recipe_id)
);

-- Modification de la table shopping_list existante pour la lier aux événements
-- On va ajouter event_id si la table existe déjà
ALTER TABLE shopping_list ADD COLUMN event_id INTEGER REFERENCES event(id) ON DELETE SET NULL;

-- Index pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_event_date ON event(event_date DESC);
CREATE INDEX IF NOT EXISTS idx_event_type ON event(event_type_id);
CREATE INDEX IF NOT EXISTS idx_event_recipe_event ON event_recipe(event_id);
CREATE INDEX IF NOT EXISTS idx_event_recipe_recipe ON event_recipe(recipe_id);
CREATE INDEX IF NOT EXISTS idx_shopping_list_event ON shopping_list(event_id);

-- Insertion des types d'événements par défaut
INSERT OR IGNORE INTO event_type (name) VALUES ('PRO');
INSERT OR IGNORE INTO event_type (name) VALUES ('MASTER');
INSERT OR IGNORE INTO event_type (name) VALUES ('INVITATION');
