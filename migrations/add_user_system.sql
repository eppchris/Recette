-- Migration : Ajout du système d'authentification utilisateur
-- Date : 2 décembre 2025
-- Version : 1.5

-- ============================================================================
-- Table des utilisateurs
-- ============================================================================

CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    is_active INTEGER DEFAULT 1,
    is_admin INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    CONSTRAINT email_format CHECK (email LIKE '%@%')
);

CREATE INDEX IF NOT EXISTS idx_user_username ON user(username);
CREATE INDEX IF NOT EXISTS idx_user_email ON user(email);

-- ============================================================================
-- Ajouter user_id aux tables existantes
-- ============================================================================

-- Recettes
ALTER TABLE recipe ADD COLUMN user_id INTEGER REFERENCES user(id);
CREATE INDEX IF NOT EXISTS idx_recipe_user ON recipe(user_id);

-- Événements
ALTER TABLE event ADD COLUMN user_id INTEGER REFERENCES event(id);
CREATE INDEX IF NOT EXISTS idx_event_user ON event(user_id);

-- Catalogue de prix (partagé mais on garde la trace de qui a créé)
ALTER TABLE ingredient_price_catalog ADD COLUMN created_by INTEGER REFERENCES user(id);

-- ============================================================================
-- Données de test : Créer un utilisateur admin par défaut
-- ============================================================================
-- Mot de passe : "admin123" (à changer après première connexion)
-- Hash PBKDF2-SHA256 : $pbkdf2-sha256$29000$2TtHKAVA6N3735vT.l.r1Q$ZU0fCFkHJLOiNMtMkU2PceL/2oumGnW3H4Xq.DE9OEw

INSERT OR IGNORE INTO user (id, username, email, password_hash, display_name, is_admin)
VALUES (
    1,
    'admin',
    'admin@recette.local',
    '$pbkdf2-sha256$29000$2TtHKAVA6N3735vT.l.r1Q$ZU0fCFkHJLOiNMtMkU2PceL/2oumGnW3H4Xq.DE9OEw',
    'Administrateur',
    1
);

-- ============================================================================
-- Mettre à jour les données existantes avec l'admin comme propriétaire
-- ============================================================================

UPDATE recipe SET user_id = 1 WHERE user_id IS NULL;
UPDATE event SET user_id = 1 WHERE user_id IS NULL;
UPDATE ingredient_price_catalog SET created_by = 1 WHERE created_by IS NULL;
