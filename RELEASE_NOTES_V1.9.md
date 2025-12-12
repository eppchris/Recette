# Release Notes - Version 1.9

**Date de sortie :** 2025-12-08
**Type :** Feature - Monitoring de Performance

---

## 🎯 Qu'est-ce qui change ?

Avant la V1.9, impossible de savoir si une page lente était due au serveur ou au réseau.

Maintenant, vous pouvez voir :
- ⏱️ Le temps serveur (traitement)
- 🌐 Le temps réseau (DNS + TCP + download)
- 🖥️ Le temps client (rendu DOM + JavaScript)
- 📦 La taille des réponses (en KB)

## ✨ Nouvelles fonctionnalités

### 1. Taille des réponses HTTP
Chaque log d'accès inclut maintenant la taille de la réponse en KB.

**Utilité :** Identifier les pages qui envoient trop de données.

### 2. Métriques de performance client
Les navigateurs envoient automatiquement leurs métriques de performance au serveur.

**Utilité :** Distinguer un serveur lent d'un rendu client lent.

### 3. Visualisation comparative
Nouvelle section "Performance Client vs Serveur" dans `/access-logs`.

**Utilité :** Voir d'un coup d'œil où se situe le problème de performance.

### 4. Pages les plus lourdes
Nouvelle section montrant les pages avec les plus grosses réponses.

**Utilité :** Prioriser les optimisations.

---

## 📊 Exemple de visualisation

```
┌─────────────────────────────────────────────────────────────────────┐
│ Performance Client vs Serveur (dernières 24h)                       │
├───────────────┬──────────┬────────────┬──────────┬─────────────────┤
│ Page          │ Serveur  │ Total      │ Réseau   │ Overhead Client │
│               │ (ms)     │ Client (ms)│ (ms)     │ (ms)            │
├───────────────┼──────────┼────────────┼──────────┼─────────────────┤
│ /recipes      │ 120      │ 450        │ 80       │ 🟡 330          │
│ /events       │ 80       │ 200        │ 50       │ 🟢 120          │
│ /shopping     │ 200      │ 950        │ 100      │ 🔴 750          │
└───────────────┴──────────┴────────────┴──────────┴─────────────────┘

Légende :
🟢 < 200ms : Bon
🟡 200-500ms : À surveiller
🔴 > 500ms : Problème à corriger
```

---

## 🔧 Changements techniques

### Fichiers modifiés
- `app/middleware/access_logger.py` - Capture taille réponse
- `app/models/db_logging.py` - Nouvelles fonctions de logging
- `app/models/__init__.py` - Export des nouvelles fonctions
- `app/routes/catalog_routes.py` - Mise à jour route access-logs
- `app/templates/access_logs.html` - Nouvelles visualisations
- `app/templates/base.html` - Inclusion script performance
- `main.py` - Enregistrement router monitoring

### Nouveaux fichiers
- `app/static/js/performance_monitor.js` - Script de capture client
- `app/routes/monitoring_routes.py` - API endpoint métriques
- `migrations/add_response_size_to_access_log.sql` - Migration colonne
- `migrations/add_client_performance_log.sql` - Migration table
- `deploy/deploy_synology_V1_9_monitoring.sh` - Script de déploiement

### Base de données
- **Nouvelle colonne** : `access_log.response_size_bytes`
- **Nouvelle table** : `client_performance_log`
- **Nouvelle vue** : `v_client_performance_24h`
- **Vue mise à jour** : `v_popular_pages_24h`

---

## 🚀 Déploiement

### Option 1 : Script automatisé (Recommandé)
```bash
./deploy/deploy_synology_V1_9_monitoring.sh
```

### Option 2 : Manuel
Suivre les instructions dans `LIVRAISON_V1.8_MONITORING_PERFORMANCE.md`

---

## 🧪 Comment tester

1. **Démarrer l'application**
   ```bash
   python -m uvicorn main:app --reload
   ```

2. **Naviguer sur plusieurs pages**
   - Aller sur `/recipes`
   - Aller sur `/events`
   - Aller sur quelques recettes

3. **Vérifier les métriques**
   - Aller sur `/access-logs`
   - Vérifier la colonne "Taille (KB)" dans les logs récents
   - Vérifier la section "Pages les plus lourdes"
   - Vérifier la section "Performance Client vs Serveur"

4. **Vérifier l'API**
   ```bash
   curl -X POST http://localhost:8000/api/client-performance \
     -H "Content-Type: application/json" \
     -d '{"page_url": "/test", "total_load_time": 100}'
   ```

---

## 📚 Documentation

- **Guide détaillé** : `docs/MONITORING_PERFORMANCE.md`
- **Guide de déploiement** : `LIVRAISON_V1.8_MONITORING_PERFORMANCE.md`

---

## ⚠️ Points d'attention

### Performance
- Overhead négligeable : < 1ms par requête côté serveur
- Script JS léger : 2.5 KB non minifié
- Pas d'impact sur la navigation (utilise sendBeacon)

### Base de données
- La table `client_performance_log` peut grossir rapidement
- Prévoir un nettoyage périodique (actuellement 30 jours)
- Environ 20 MB par mois pour 50 pages vues/jour

### Compatibilité
- Navigation Timing API supportée par tous les navigateurs modernes
- Graceful degradation : pas d'erreur si API non disponible

---

## 🔄 Rollback

Si problème en production :

1. **Arrêter le service**
   ```bash
   sudo systemctl stop recette
   ```

2. **Restaurer le backup**
   ```bash
   cp data/recette.sqlite3.backup_v1.8_XXXXXXXX data/recette.sqlite3
   ```

3. **Restaurer le code**
   ```bash
   git checkout v1.8  # ou restaurer depuis backup
   ```

4. **Redémarrer**
   ```bash
   sudo systemctl start recette
   ```

---

## 🐛 Problèmes connus

Aucun problème connu pour le moment.

---

## 💡 Utilisation recommandée

### Identifier les problèmes de performance

1. **Page lente avec taille élevée (> 1 MB)**
   → Réduire la quantité de données (pagination, lazy loading)

2. **Temps serveur élevé (> 500ms)**
   → Optimiser les requêtes SQL, ajouter des index

3. **Overhead client élevé (> 500ms)**
   → Réduire le JavaScript, optimiser le DOM

4. **Temps réseau élevé (> 200ms)**
   → Activer la compression, réduire la taille des réponses

---

## 👥 Support

En cas de problème :
1. Vérifier les logs : `sudo journalctl -u recette -f`
2. Vérifier que les migrations ont été appliquées
3. Consulter la documentation : `docs/MONITORING_PERFORMANCE.md`

---

## 📝 Changelog complet

### Ajouté
- Capture de la taille des réponses HTTP (middleware)
- Métriques de performance client via Navigation Timing API
- API endpoint `/api/client-performance`
- Visualisation "Performance Client vs Serveur"
- Visualisation "Pages les plus lourdes"
- Table `client_performance_log` en DB
- Vue `v_client_performance_24h`
- Script de déploiement automatisé V1.9

### Modifié
- Middleware `access_logger.py` pour capturer `response_size_bytes`
- Template `access_logs.html` avec nouvelles sections
- Template `base.html` pour inclure `performance_monitor.js`
- Vue `v_popular_pages_24h` pour inclure `avg_response_size`

### Corrigé
- N/A (nouvelle fonctionnalité)

---

**Développé avec ❤️ pour une meilleure observabilité**
