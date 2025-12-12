-- Migration: Ajout d'une table pour les métriques de performance côté client
-- Date: 2025-12-08
-- Description: Capture les métriques Navigation Timing API pour mesurer la performance réelle perçue par l'utilisateur

-- ============================================================================
-- Table: client_performance_log
-- Stocke les métriques de performance capturées côté client (navigateur)
-- ============================================================================

CREATE TABLE IF NOT EXISTS client_performance_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    page_url TEXT NOT NULL,                  -- URL de la page

    -- Métriques réseau
    network_time REAL,                       -- Temps réseau total (ms)
    dns_time REAL,                           -- Temps de résolution DNS (ms)
    tcp_time REAL,                           -- Temps de connexion TCP (ms)
    server_time REAL,                        -- Temps de traitement serveur (ms)
    download_time REAL,                      -- Temps de téléchargement de la réponse (ms)

    -- Métriques de traitement
    dom_processing_time REAL,                -- Temps de traitement DOM (ms)
    total_load_time REAL,                    -- Temps de chargement total (ms)
    dom_interactive_time REAL,               -- Temps jusqu'au DOM interactif (ms)

    -- Informations de navigation
    navigation_type INTEGER,                 -- 0: navigation, 1: reload, 2: back/forward
    redirect_count INTEGER,                  -- Nombre de redirections

    -- Métadonnées
    user_agent TEXT,                         -- User agent du navigateur
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour améliorer les performances des requêtes
CREATE INDEX IF NOT EXISTS idx_client_perf_page_url ON client_performance_log(page_url);
CREATE INDEX IF NOT EXISTS idx_client_perf_created_at ON client_performance_log(created_at);
CREATE INDEX IF NOT EXISTS idx_client_perf_total_load ON client_performance_log(total_load_time);

-- ============================================================================
-- Vue: Performance moyenne par page (dernières 24h)
-- ============================================================================

CREATE VIEW IF NOT EXISTS v_client_performance_24h AS
SELECT
    page_url,
    COUNT(*) as measurement_count,
    AVG(network_time) as avg_network_time,
    AVG(server_time) as avg_server_time,
    AVG(download_time) as avg_download_time,
    AVG(dom_processing_time) as avg_dom_time,
    AVG(total_load_time) as avg_total_time,
    MAX(total_load_time) as max_total_time,
    MIN(total_load_time) as min_total_time
FROM client_performance_log
WHERE created_at >= datetime('now', '-1 day')
GROUP BY page_url
ORDER BY measurement_count DESC;

-- ============================================================================
-- Statistiques
-- ============================================================================

SELECT 'Table client_performance_log créée avec succès' as status;
SELECT 'Index créés pour optimiser les requêtes de performance' as info;
SELECT 'Vue v_client_performance_24h créée pour analyses rapides' as info;
