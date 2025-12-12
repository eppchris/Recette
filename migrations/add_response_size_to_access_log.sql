-- Migration: Ajout de la taille des réponses dans les logs d'accès
-- Date: 2025-12-08
-- Description: Permet de mesurer la taille des réponses pour identifier les pages lourdes et la lenteur réseau

-- ============================================================================
-- Ajout de la colonne response_size_bytes
-- ============================================================================

ALTER TABLE access_log ADD COLUMN response_size_bytes INTEGER;

-- ============================================================================
-- Mise à jour des vues existantes pour inclure la taille
-- ============================================================================

-- Supprimer l'ancienne vue
DROP VIEW IF EXISTS v_popular_pages_24h;

-- Recréer la vue avec la taille moyenne
CREATE VIEW IF NOT EXISTS v_popular_pages_24h AS
SELECT
    path,
    COUNT(*) as visit_count,
    AVG(response_time_ms) as avg_response_time,
    AVG(response_size_bytes) as avg_response_size,
    COUNT(DISTINCT ip_address) as unique_visitors
FROM access_log
WHERE accessed_at >= datetime('now', '-1 day')
  AND path IS NOT NULL
GROUP BY path
ORDER BY visit_count DESC;

-- ============================================================================
-- Statistiques
-- ============================================================================

SELECT 'Colonne response_size_bytes ajoutée avec succès' as status;
SELECT 'Vue v_popular_pages_24h mise à jour avec avg_response_size' as info;
