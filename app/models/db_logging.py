"""
Module de gestion des logs d'accès
"""
from .db_core import get_db


def log_access(ip_address: str, user_agent: str = None, path: str = None,
               method: str = 'GET', status_code: int = None,
               response_time_ms: float = None, referer: str = None,
               lang: str = None):
    """
    Enregistre un accès à l'application

    Args:
        ip_address: Adresse IP du client
        user_agent: User agent du navigateur
        path: Chemin de l'URL accédée
        method: Méthode HTTP (GET, POST, etc.)
        status_code: Code de statut HTTP de la réponse
        response_time_ms: Temps de réponse en millisecondes
        referer: URL de référence
        lang: Langue de l'interface
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO access_log (ip_address, user_agent, path, method, status_code,
                                   response_time_ms, referer, lang)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ip_address, user_agent, path, method, status_code,
              response_time_ms, referer, lang))


def get_access_stats(hours: int = 24):
    """
    Récupère les statistiques d'accès

    Args:
        hours: Nombre d'heures à analyser (par défaut 24h)

    Returns:
        Dictionnaire avec les statistiques d'accès
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Nombre total d'accès
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM access_log
            WHERE accessed_at >= datetime('now', '-' || ? || ' hours')
        """, (hours,))
        total_accesses = cursor.fetchone()['total']

        # Accès par IP
        cursor.execute("""
            SELECT ip_address, COUNT(*) as count,
                   MIN(accessed_at) as first_access,
                   MAX(accessed_at) as last_access
            FROM access_log
            WHERE accessed_at >= datetime('now', '-' || ? || ' hours')
            GROUP BY ip_address
            ORDER BY count DESC
            LIMIT 10
        """, (hours,))
        by_ip = [dict(row) for row in cursor.fetchall()]

        # Pages les plus visitées
        cursor.execute("""
            SELECT path, COUNT(*) as count
            FROM access_log
            WHERE accessed_at >= datetime('now', '-' || ? || ' hours')
              AND path IS NOT NULL
            GROUP BY path
            ORDER BY count DESC
            LIMIT 10
        """, (hours,))
        popular_pages = [dict(row) for row in cursor.fetchall()]

        # Temps de réponse moyen par page
        cursor.execute("""
            SELECT path, AVG(response_time_ms) as avg_time, COUNT(*) as count
            FROM access_log
            WHERE accessed_at >= datetime('now', '-' || ? || ' hours')
              AND response_time_ms IS NOT NULL
              AND path IS NOT NULL
            GROUP BY path
            ORDER BY avg_time DESC
            LIMIT 10
        """, (hours,))
        slow_pages = [dict(row) for row in cursor.fetchall()]

        return {
            'total_accesses': total_accesses,
            'by_ip': by_ip,
            'popular_pages': popular_pages,
            'slow_pages': slow_pages
        }


def cleanup_old_access_logs(days: int = 30):
    """
    Nettoie les logs d'accès anciens

    Args:
        days: Nombre de jours à conserver (par défaut 30)

    Returns:
        Nombre de lignes supprimées
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM access_log
            WHERE accessed_at < datetime('now', '-' || ? || ' days')
        """, (days,))
        deleted_count = cursor.rowcount
        return deleted_count


def get_recent_access_logs(limit: int = 50, hours: int = 24):
    """
    Récupère les logs d'accès récents

    Args:
        limit: Nombre maximum de logs à retourner (par défaut 50)
        hours: Nombre d'heures à analyser (par défaut 24)

    Returns:
        Liste des logs d'accès récents
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ip_address, user_agent, path, method, status_code,
                   response_time_ms, referer, lang, accessed_at
            FROM access_log
            WHERE accessed_at >= datetime('now', '-' || ? || ' hours')
            ORDER BY accessed_at DESC
            LIMIT ?
        """, (hours, limit))
        return [dict(row) for row in cursor.fetchall()]
