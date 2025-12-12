# Monitoring de Performance Réseau et Client

## Vue d'ensemble

Cette fonctionnalité permet de distinguer la lenteur serveur de la lenteur réseau/client en mesurant :
- **Côté serveur** : Taille des réponses HTTP
- **Côté client** : Métriques de performance via Navigation Timing API

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  Navigateur │────────▶│   FastAPI    │────────▶│  SQLite DB  │
│   Client    │         │  Middleware  │         │             │
└─────────────┘         └──────────────┘         └─────────────┘
      │                                                  ▲
      │                 ┌──────────────┐                │
      └────────────────▶│   API POST   │────────────────┘
      (sendBeacon)      │ /api/client- │
                        │ performance  │
                        └──────────────┘
```

### Flux de données

1. **Requête HTTP** → Middleware capture la taille de la réponse
2. **Réponse HTML** → Inclut `performance_monitor.js`
3. **Chargement complet** → Script mesure les métriques via Navigation Timing API
4. **sendBeacon** → Envoie les métriques à `/api/client-performance`
5. **Stockage DB** → Les métriques sont sauvegardées dans `client_performance_log`
6. **Visualisation** → Page `/access-logs` affiche les statistiques

## Métriques capturées

### Serveur (Middleware)
```python
# app/middleware/access_logger.py
response_size_bytes = int(response.headers['content-length'])
```

### Client (JavaScript)
```javascript
// app/static/js/performance_monitor.js
const timing = window.performance.timing;

métriques = {
  network_time: DNS + TCP + Request + Response
  dns_time: Résolution DNS
  tcp_time: Connexion TCP
  server_time: Temps de traitement serveur
  download_time: Téléchargement de la réponse
  dom_processing_time: Traitement DOM
  total_load_time: Temps total perçu
}
```

## Tables de base de données

### `access_log` (modifiée)
```sql
ALTER TABLE access_log
ADD COLUMN response_size_bytes INTEGER;
```

### `client_performance_log` (nouvelle)
```sql
CREATE TABLE client_performance_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    page_url TEXT NOT NULL,
    network_time REAL,
    dns_time REAL,
    tcp_time REAL,
    server_time REAL,
    download_time REAL,
    dom_processing_time REAL,
    total_load_time REAL,
    dom_interactive_time REAL,
    navigation_type INTEGER,
    redirect_count INTEGER,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Vues SQL

### `v_popular_pages_24h` (mise à jour)
Inclut maintenant `avg_response_size` :
```sql
SELECT path,
       COUNT(*) as visit_count,
       AVG(response_time_ms) as avg_response_time,
       AVG(response_size_bytes) as avg_response_size,
       COUNT(DISTINCT ip_address) as unique_visitors
FROM access_log
WHERE accessed_at >= datetime('now', '-1 day')
GROUP BY path
ORDER BY visit_count DESC;
```

### `v_client_performance_24h` (nouvelle)
Statistiques de performance client :
```sql
SELECT page_url,
       AVG(total_load_time) as avg_load_time,
       AVG(network_time) as avg_network_time,
       AVG(server_time) as avg_server_time,
       AVG(dom_processing_time) as avg_dom_time,
       COUNT(*) as sample_count
FROM client_performance_log
WHERE created_at >= datetime('now', '-1 day')
GROUP BY page_url;
```

## API Endpoints

### POST `/api/client-performance`
Reçoit les métriques de performance côté client.

**Payload :**
```json
{
  "page_url": "/recipes",
  "network_time": 50.2,
  "dns_time": 10.5,
  "tcp_time": 15.3,
  "server_time": 120.8,
  "download_time": 24.4,
  "dom_processing_time": 85.6,
  "total_load_time": 256.3,
  "dom_interactive_time": 200.1,
  "navigation_type": 0,
  "redirect_count": 0
}
```

**Réponse :**
```json
{
  "status": "success"
}
```

## Visualisation

### Page `/access-logs`

#### Section 1 : Logs récents
| Heure | IP | Path | Méthode | Status | Temps (ms) | **Taille (KB)** |
|-------|----|----|---------|--------|------------|-----------------|
| 14:30:25 | 192.168.1.10 | /recipes | GET | 200 | 125 | **45.2** |

#### Section 2 : Pages les plus lourdes
| Page | Taille moyenne (KB) | Nombre d'accès |
|------|---------------------|----------------|
| /events/123/shopping-list | 256.4 | 15 |
| /recipes/tonkatsu | 189.7 | 42 |

#### Section 3 : Performance Client vs Serveur
| Page | Serveur (ms) | Total Client (ms) | Réseau (ms) | Overhead Client (ms) |
|------|--------------|-------------------|-------------|----------------------|
| /recipes | 120 | 450 | 80 | 🟡 330 |
| /events | 80 | 200 | 50 | 🟢 120 |
| /shopping | 200 | 950 | 100 | 🔴 750 |

**Légende des couleurs :**
- 🟢 Vert : < 200ms (bon)
- 🟡 Jaune : 200-500ms (attention)
- 🔴 Rouge : > 500ms (problème)

## Interprétation des métriques

### Temps serveur élevé (> 500ms)
**Problème :** Le serveur met trop de temps à générer la réponse
**Solutions :**
- Optimiser les requêtes SQL
- Ajouter des index
- Mettre en cache les données

### Taille de réponse élevée (> 1 MB)
**Problème :** La page contient trop de données
**Solutions :**
- Paginer les résultats
- Compresser les images
- Lazy loading des données

### Overhead client élevé (> 500ms)
**Problème :** Le navigateur met trop de temps à rendre la page
**Solutions :**
- Réduire le JavaScript
- Optimiser le CSS
- Simplifier le DOM

### Temps réseau élevé (> 200ms)
**Problème :** La connexion réseau est lente
**Solutions :**
- Réduire la taille des réponses
- Activer la compression gzip
- CDN pour les assets statiques

## Maintenance

### Nettoyage automatique des logs
Les logs de plus de 30 jours sont automatiquement supprimés (configurable).

### Taille de la base de données
La table `client_performance_log` peut grossir rapidement :
- ~200 bytes par enregistrement
- ~100 000 enregistrements par mois pour 50 pages vues/jour
- ~20 MB par mois

**Recommandation :** Nettoyer régulièrement les logs anciens.

## Compatibilité

### Navigation Timing API
- ✅ Chrome/Edge : Toutes versions récentes
- ✅ Firefox : Version 7+
- ✅ Safari : Version 8+
- ✅ Mobile : iOS Safari 9+, Chrome Mobile

### Graceful degradation
Si l'API n'est pas disponible, aucune erreur n'est levée et l'application fonctionne normalement.

## Performance Impact

### Côté serveur
- **Overhead par requête :** < 1ms (lecture du Content-Length header)
- **Stockage DB :** ~50 bytes par requête

### Côté client
- **Taille du script :** 2.5 KB (non minifié)
- **Temps d'exécution :** < 5ms après chargement complet
- **Impact navigation :** Aucun (utilise sendBeacon)

## Développement

### Tester en local
```bash
# Démarrer le serveur
python -m uvicorn main:app --reload

# Visiter des pages
open http://localhost:8000/recipes

# Vérifier les logs
open http://localhost:8000/access-logs
```

### Tester l'API manuellement
```bash
curl -X POST http://localhost:8000/api/client-performance \
  -H "Content-Type: application/json" \
  -d '{
    "page_url": "/test",
    "network_time": 50,
    "server_time": 100,
    "total_load_time": 200
  }'
```

### Vérifier les données en DB
```bash
sqlite3 data/recette.sqlite3

-- Voir les métriques récentes
SELECT * FROM client_performance_log
ORDER BY created_at DESC
LIMIT 10;

-- Statistiques par page
SELECT * FROM v_client_performance_24h;
```

## Dépannage

### Les métriques client ne s'affichent pas
1. Vérifier que `performance_monitor.js` est chargé (DevTools > Network)
2. Vérifier qu'aucune erreur JS n'est présente (DevTools > Console)
3. Vérifier que la requête POST est envoyée (DevTools > Network)
4. Vérifier les logs serveur pour les erreurs

### La colonne "Taille (KB)" est vide
1. Vérifier que la migration a été appliquée
2. Vérifier que le header `Content-Length` est présent dans les réponses
3. Les anciennes requêtes n'auront pas cette information (seulement les nouvelles)

### Erreur "no such column: response_size_bytes"
La migration n'a pas été appliquée correctement :
```bash
sqlite3 data/recette.sqlite3 "ALTER TABLE access_log ADD COLUMN response_size_bytes INTEGER;"
```

## Références

- [Navigation Timing API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/Navigation_timing_API)
- [sendBeacon - MDN](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/sendBeacon)
- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)

---

**Version :** 1.9
**Date :** 2025-12-08
**Auteur :** Christian Epp
