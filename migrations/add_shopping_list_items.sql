-- Migration: Ajout de la table des items de liste de courses
-- Date: 2025-11-13
-- Description: Transforme la liste de courses en objet persistant modifiable

-- Table des items de liste de courses
CREATE TABLE IF NOT EXISTS shopping_list_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    ingredient_name TEXT NOT NULL,
    needed_quantity REAL,          -- Quantité calculée nécessaire
    needed_unit TEXT,               -- Unité de la quantité nécessaire
    purchase_quantity REAL,         -- Quantité à acheter (modifiable par l'utilisateur)
    purchase_unit TEXT,             -- Unité d'achat (modifiable)
    is_checked BOOLEAN DEFAULT 0,  -- Coché ou non dans la liste
    notes TEXT,                     -- Notes de l'agrégation + notes utilisateur
    source_recipes TEXT,            -- JSON avec les recettes sources
    position INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES event(id) ON DELETE CASCADE
);
