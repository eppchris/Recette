"""
Routes pour le monitoring et les métriques de performance
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
from app.models import log_client_performance

router = APIRouter()


class ClientPerformanceMetrics(BaseModel):
    """Modèle pour les métriques de performance côté client"""
    page_url: str
    network_time: Optional[float] = None
    dns_time: Optional[float] = None
    tcp_time: Optional[float] = None
    server_time: Optional[float] = None
    download_time: Optional[float] = None
    dom_processing_time: Optional[float] = None
    total_load_time: Optional[float] = None
    dom_interactive_time: Optional[float] = None
    navigation_type: Optional[int] = None
    redirect_count: Optional[int] = None


@router.post("/api/client-performance")
async def log_client_performance_metrics(metrics: ClientPerformanceMetrics, request: Request):
    """
    Endpoint pour recevoir les métriques de performance côté client
    """
    try:
        # Récupérer le user agent depuis les headers
        user_agent = request.headers.get('user-agent', '')

        # Enregistrer les métriques
        log_client_performance(
            page_url=metrics.page_url,
            network_time=metrics.network_time,
            dns_time=metrics.dns_time,
            tcp_time=metrics.tcp_time,
            server_time=metrics.server_time,
            download_time=metrics.download_time,
            dom_processing_time=metrics.dom_processing_time,
            total_load_time=metrics.total_load_time,
            dom_interactive_time=metrics.dom_interactive_time,
            navigation_type=metrics.navigation_type,
            redirect_count=metrics.redirect_count,
            user_agent=user_agent
        )

        return {"status": "success"}
    except Exception as e:
        # Ne pas faire échouer la requête si le logging échoue
        print(f"Erreur lors de l'enregistrement des métriques client: {e}")
        return {"status": "error", "message": str(e)}
