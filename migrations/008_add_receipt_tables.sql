-- ============================================================================
-- Migration 008: Tables pour la gestion des tickets de caisse
-- ============================================================================
-- Date: 2026-01-06
-- Description: Ajout des tables pour l'upload et l'analyse des tickets de caisse PDF
--              Permet d'extraire les prix et de mettre à jour le catalogue des ingrédients
-- ============================================================================

-- Table principale des tickets de caisse uploadés
CREATE TABLE IF NOT EXISTS receipt_upload_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,                              -- Nom du fichier PDF uploadé
    receipt_name TEXT,                                   -- Nom personnalisé donné par l'utilisateur
    store_name TEXT,                                     -- Nom du commerce (extrait du PDF)
    receipt_date DATE,                                   -- Date du ticket (extrait du PDF)
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,     -- Date d'upload
    processed_at TIMESTAMP,                              -- Date de traitement complet
    total_items INTEGER DEFAULT 0,                       -- Nombre total d'articles extraits
    matched_items INTEGER DEFAULT 0,                     -- Nombre d'articles matchés avec catalogue
    validated_items INTEGER DEFAULT 0,                   -- Nombre d'articles validés par l'utilisateur
    status TEXT DEFAULT 'pending',                       -- pending, processed, error
    error_message TEXT,                                  -- Message d'erreur si extraction échoue
    currency TEXT DEFAULT 'EUR',                         -- Devise détectée (EUR, JPY)
    user_id INTEGER,                                     -- Utilisateur qui a uploadé
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL
);

-- Index pour améliorer les recherches
CREATE INDEX IF NOT EXISTS idx_receipt_upload_date ON receipt_upload_history(upload_date DESC);
CREATE INDEX IF NOT EXISTS idx_receipt_status ON receipt_upload_history(status);
CREATE INDEX IF NOT EXISTS idx_receipt_user ON receipt_upload_history(user_id);

-- Table des articles extraits du ticket avec leur matching
CREATE TABLE IF NOT EXISTS receipt_item_match (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id INTEGER NOT NULL,                         -- Référence au ticket
    receipt_item_text TEXT NOT NULL,                     -- Texte brut de l'article sur le ticket
    receipt_price REAL NOT NULL,                         -- Prix sur le ticket
    receipt_quantity REAL,                               -- Quantité (si détectée)
    receipt_unit TEXT,                                   -- Unité (kg, g, L, ml, pièce, etc.)

    -- Matching avec le catalogue
    matched_ingredient_id INTEGER,                       -- ID de l'ingrédient correspondant
    confidence_score REAL,                               -- Score de confiance du matching (0.0 à 1.0)

    -- Workflow de validation
    status TEXT DEFAULT 'pending',                       -- pending, validated, rejected, applied
    validated_at TIMESTAMP,                              -- Date de validation par l'utilisateur
    notes TEXT,                                          -- Notes de l'utilisateur

    FOREIGN KEY (receipt_id) REFERENCES receipt_upload_history(id) ON DELETE CASCADE,
    FOREIGN KEY (matched_ingredient_id) REFERENCES ingredient_price_catalog(id) ON DELETE SET NULL
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_receipt_item_receipt ON receipt_item_match(receipt_id);
CREATE INDEX IF NOT EXISTS idx_receipt_item_status ON receipt_item_match(status);
CREATE INDEX IF NOT EXISTS idx_receipt_item_ingredient ON receipt_item_match(matched_ingredient_id);

-- ============================================================================
-- Trigger pour mettre à jour automatiquement les compteurs
-- ============================================================================

-- Trigger pour compter les items validés
CREATE TRIGGER IF NOT EXISTS update_receipt_validated_count
AFTER UPDATE OF status ON receipt_item_match
WHEN NEW.status = 'validated' OR OLD.status = 'validated'
BEGIN
    UPDATE receipt_upload_history
    SET validated_items = (
        SELECT COUNT(*)
        FROM receipt_item_match
        WHERE receipt_id = NEW.receipt_id
        AND status = 'validated'
    )
    WHERE id = NEW.receipt_id;
END;

-- Trigger pour compter les items matchés
CREATE TRIGGER IF NOT EXISTS update_receipt_matched_count
AFTER UPDATE OF matched_ingredient_id ON receipt_item_match
WHEN NEW.matched_ingredient_id IS NOT NULL OR OLD.matched_ingredient_id IS NOT NULL
BEGIN
    UPDATE receipt_upload_history
    SET matched_items = (
        SELECT COUNT(*)
        FROM receipt_item_match
        WHERE receipt_id = NEW.receipt_id
        AND matched_ingredient_id IS NOT NULL
    )
    WHERE id = NEW.receipt_id;
END;

-- ============================================================================
-- Vue pour faciliter les requêtes
-- ============================================================================

-- Vue qui joint les receipts avec leurs statistiques détaillées
CREATE VIEW IF NOT EXISTS receipt_summary AS
SELECT
    r.id,
    r.filename,
    r.receipt_name,
    r.store_name,
    r.receipt_date,
    r.upload_date,
    r.processed_at,
    r.status,
    r.currency,
    r.total_items,
    r.matched_items,
    r.validated_items,
    r.user_id,
    u.username,
    -- Statistiques calculées
    ROUND(CAST(r.matched_items AS REAL) / NULLIF(r.total_items, 0) * 100, 1) as match_percentage,
    ROUND(CAST(r.validated_items AS REAL) / NULLIF(r.total_items, 0) * 100, 1) as validation_percentage
FROM receipt_upload_history r
LEFT JOIN user u ON r.user_id = u.id;
