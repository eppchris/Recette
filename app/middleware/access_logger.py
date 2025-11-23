"""
Middleware pour logger tous les accès à l'application
"""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.models import db


class AccessLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware qui enregistre tous les accès HTTP dans la base de données
    """

    async def dispatch(self, request: Request, call_next):
        # Capturer l'heure de début
        start_time = time.time()

        # Extraire les informations de la requête
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get('user-agent', '')
        referer = request.headers.get('referer', '')
        path = request.url.path
        method = request.method

        # Extraire la langue depuis les query params
        lang = request.query_params.get('lang', '')

        # Exécuter la requête
        response = await call_next(request)

        # Calculer le temps de réponse
        response_time_ms = (time.time() - start_time) * 1000

        # Logger l'accès (de manière asynchrone pour ne pas ralentir la réponse)
        try:
            db.log_access(
                ip_address=client_ip,
                user_agent=user_agent,
                path=path,
                method=method,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                referer=referer,
                lang=lang
            )
        except Exception as e:
            # Ne pas faire échouer la requête si le logging échoue
            print(f"Erreur lors du logging d'accès: {e}")

        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        Récupère l'adresse IP du client en tenant compte des proxies
        """
        # Vérifier les headers de proxy courants
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            # Prendre la première IP (client original)
            return forwarded_for.split(',')[0].strip()

        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip

        # Fallback sur l'IP directe
        if request.client:
            return request.client.host

        return 'unknown'
