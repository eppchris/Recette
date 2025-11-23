-- Migration: Ajout d'une table de logs d'accès à l'application
-- Date: 2025-11-19
-- Description: Trace les connexions avec IP et timestamp pour monitoring et sécurité

-- ============================================================================
-- Table: access_log
-- Stocke les logs de connexion à l'application
-- ============================================================================

CREATE TABLE IF NOT EXISTS access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL,           -- Adresse IP du client
    user_agent TEXT,                     -- User-Agent du navigateur
    path TEXT,                           -- Page/route accédée (ex: /recipes, /events)
    method TEXT DEFAULT 'GET',           -- Méthode HTTP (GET, POST, etc.)
    status_code INTEGER,                 -- Code de réponse HTTP (200, 404, etc.)
    response_time_ms REAL,               -- Temps de réponse en millisecondes
    referer TEXT,                        -- Page d'origine (referer)
    lang TEXT,                           -- Langue utilisée (fr/jp)
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Horodatage de l'accès
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour améliorer les performances des requêtes
CREATE INDEX IF NOT EXISTS idx_access_log_ip ON access_log(ip_address);
CREATE INDEX IF NOT EXISTS idx_access_log_accessed_at ON access_log(accessed_at);
CREATE INDEX IF NOT EXISTS idx_access_log_path ON access_log(path);

-- ============================================================================
-- Vues utiles pour le monitoring
-- ============================================================================

-- Vue: Nombre d'accès par IP (dernières 24h)
CREATE VIEW IF NOT EXISTS v_access_by_ip_24h AS
SELECT
    ip_address,
    COUNT(*) as access_count,
    MIN(accessed_at) as first_access,
    MAX(accessed_at) as last_access,
    GROUP_CONCAT(DISTINCT path) as pages_accessed
FROM access_log
WHERE accessed_at >= datetime('now', '-1 day')
GROUP BY ip_address
ORDER BY access_count DESC;

-- Vue: Pages les plus visitées (dernières 24h)
CREATE VIEW IF NOT EXISTS v_popular_pages_24h AS
SELECT
    path,
    COUNT(*) as visit_count,
    AVG(response_time_ms) as avg_response_time,
    COUNT(DISTINCT ip_address) as unique_visitors
FROM access_log
WHERE accessed_at >= datetime('now', '-1 day')
  AND path IS NOT NULL
GROUP BY path
ORDER BY visit_count DESC;

-- ============================================================================
-- Fonction de nettoyage automatique (optionnel)
-- ============================================================================

-- Trigger pour limiter la taille de la table (garder seulement 30 jours)
-- Note: À activer manuellement si souhaité
-- CREATE TRIGGER IF NOT EXISTS cleanup_old_access_logs
-- AFTER INSERT ON access_log
-- BEGIN
--     DELETE FROM access_log
--     WHERE accessed_at < datetime('now', '-30 days');
-- END;

-- ============================================================================
-- Statistiques initiales
-- ============================================================================

SELECT 'Table access_log créée avec succès' as status;
SELECT 'Index créés: idx_access_log_ip, idx_access_log_accessed_at, idx_access_log_path' as info;
SELECT 'Vues créées: v_access_by_ip_24h, v_popular_pages_24h' as info;
