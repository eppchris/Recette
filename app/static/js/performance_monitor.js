/**
 * Performance Monitor - Capture des métriques de performance côté client
 * Utilise l'API Navigation Timing pour mesurer le temps total perçu par l'utilisateur
 */

(function() {
    'use strict';

    // Attendre que la page soit complètement chargée
    window.addEventListener('load', function() {
        // Utiliser un délai pour s'assurer que toutes les métriques sont disponibles
        setTimeout(function() {
            capturePerformanceMetrics();
        }, 0);
    });

    function capturePerformanceMetrics() {
        // Vérifier si l'API Performance est disponible
        if (!window.performance || !window.performance.timing) {
            console.warn('Performance API non disponible');
            return;
        }

        const timing = window.performance.timing;
        const navigation = window.performance.navigation;

        // Calculer les métriques clés
        const metrics = {
            // Temps réseau (DNS + TCP + Requête + Réponse)
            network_time: timing.responseEnd - timing.fetchStart,

            // Temps DNS
            dns_time: timing.domainLookupEnd - timing.domainLookupStart,

            // Temps de connexion TCP
            tcp_time: timing.connectEnd - timing.connectStart,

            // Temps de requête/réponse serveur (ce qui est mesuré côté serveur)
            server_time: timing.responseEnd - timing.requestStart,

            // Temps de téléchargement de la réponse
            download_time: timing.responseEnd - timing.responseStart,

            // Temps de traitement DOM
            dom_processing_time: timing.domComplete - timing.domLoading,

            // Temps total de chargement de la page
            total_load_time: timing.loadEventEnd - timing.fetchStart,

            // Temps jusqu'au premier rendu
            dom_interactive_time: timing.domInteractive - timing.fetchStart,

            // Informations supplémentaires
            page_url: window.location.pathname,
            navigation_type: navigation.type, // 0: navigation, 1: reload, 2: back/forward
            redirect_count: navigation.redirectCount
        };

        // Vérifier que les métriques sont valides (pas de valeurs négatives)
        const validMetrics = {};
        for (const [key, value] of Object.entries(metrics)) {
            if (typeof value === 'number' && value >= 0) {
                validMetrics[key] = value;
            } else if (typeof value !== 'number') {
                validMetrics[key] = value;
            }
        }

        // Envoyer les métriques au serveur
        sendMetricsToServer(validMetrics);
    }

    function sendMetricsToServer(metrics) {
        // Utiliser sendBeacon pour envoyer les données de manière asynchrone
        // même si l'utilisateur quitte la page
        const url = '/api/client-performance';
        const data = JSON.stringify(metrics);

        if (navigator.sendBeacon) {
            // Préférer sendBeacon pour la fiabilité
            const blob = new Blob([data], { type: 'application/json' });
            navigator.sendBeacon(url, blob);
        } else {
            // Fallback sur fetch avec keepalive
            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: data,
                keepalive: true
            }).catch(function(error) {
                console.error('Erreur lors de l\'envoi des métriques:', error);
            });
        }
    }

    // Capturer également les Resource Timing pour les ressources individuelles (optionnel)
    function captureResourceMetrics() {
        if (!window.performance || !window.performance.getEntriesByType) {
            return;
        }

        const resources = window.performance.getEntriesByType('resource');
        const heavyResources = resources
            .filter(function(r) {
                // Ne garder que les ressources volumineuses (> 100KB)
                return r.transferSize && r.transferSize > 102400;
            })
            .map(function(r) {
                return {
                    name: r.name,
                    size: r.transferSize,
                    duration: r.duration,
                    type: r.initiatorType
                };
            });

        if (heavyResources.length > 0) {
            console.log('Ressources volumineuses détectées:', heavyResources);
            // On pourrait aussi les envoyer au serveur si nécessaire
        }
    }
})();
