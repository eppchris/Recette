-- Migration: Ajout de la gestion des participants et groupes
-- Date: 2025-12-12
-- Description: Permet de gérer des participants (non utilisateurs) et de les organiser en groupes
--              Les participants peuvent être liés à des événements individuellement ou via des groupes

-- ============================================================================
-- Table: participant
-- Stocke les informations des participants (indépendants des utilisateurs)
-- ============================================================================
CREATE TABLE IF NOT EXISTS participant (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,                    -- Obligatoire
    prenom TEXT,                          -- Optionnel
    role TEXT,                            -- Texte libre (ex: "invité", "organisateur", "famille")
    telephone TEXT,                       -- Optionnel
    email TEXT,                           -- Optionnel
    adresse TEXT,                         -- Optionnel
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherche rapide par nom
CREATE INDEX IF NOT EXISTS idx_participant_nom ON participant(nom);
CREATE INDEX IF NOT EXISTS idx_participant_email ON participant(email);

-- ============================================================================
-- Table: participant_group
-- Stocke les groupes de participants (ex: "Famille Dupont", "Amis du club")
-- ============================================================================
CREATE TABLE IF NOT EXISTS participant_group (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE,            -- Nom du groupe (unique)
    description TEXT,                     -- Description optionnelle
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherche rapide par nom de groupe
CREATE INDEX IF NOT EXISTS idx_participant_group_nom ON participant_group(nom);

-- ============================================================================
-- Table: participant_group_member
-- Liaison many-to-many entre participants et groupes
-- Un participant peut appartenir à plusieurs groupes
-- ============================================================================
CREATE TABLE IF NOT EXISTS participant_group_member (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (participant_id) REFERENCES participant(id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES participant_group(id) ON DELETE CASCADE,
    UNIQUE(participant_id, group_id)     -- Un participant ne peut être qu'une fois dans un groupe
);

-- Index pour jointures rapides
CREATE INDEX IF NOT EXISTS idx_pgm_participant ON participant_group_member(participant_id);
CREATE INDEX IF NOT EXISTS idx_pgm_group ON participant_group_member(group_id);

-- ============================================================================
-- Table: event_participant
-- Liaison entre événements et participants
-- Les participants sont ajoutés individuellement même s'ils viennent d'un groupe
-- ============================================================================
CREATE TABLE IF NOT EXISTS event_participant (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    participant_id INTEGER NOT NULL,
    added_via_group_id INTEGER,          -- NULL si ajouté manuellement, sinon ID du groupe source
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES event(id) ON DELETE CASCADE,
    FOREIGN KEY (participant_id) REFERENCES participant(id) ON DELETE CASCADE,
    FOREIGN KEY (added_via_group_id) REFERENCES participant_group(id) ON DELETE SET NULL,
    UNIQUE(event_id, participant_id)     -- Un participant ne peut être lié qu'une fois par événement
);

-- Index pour jointures rapides
CREATE INDEX IF NOT EXISTS idx_ep_event ON event_participant(event_id);
CREATE INDEX IF NOT EXISTS idx_ep_participant ON event_participant(participant_id);
CREATE INDEX IF NOT EXISTS idx_ep_group ON event_participant(added_via_group_id);
