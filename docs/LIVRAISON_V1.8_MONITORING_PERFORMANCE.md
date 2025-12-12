# Livraison V1.8 - Monitoring de Performance Réseau et Client

**Date:** 2025-12-08
**Version:** 1.8
**Type:** Feature - Amélioration du monitoring

---

## 📋 Résumé des modifications

Amélioration du système de monitoring pour distinguer la lenteur réseau de la lenteur serveur, en ajoutant :
- Mesure de la taille des réponses HTTP
- Capture des métriques de performance côté client (Navigation Timing API)
- Visualisation comparative entre temps serveur et temps total perçu par l'utilisateur

---

## 🎯 Problème résolu

Avant cette livraison, les logs mesuraient uniquement le temps de traitement côté serveur. Il était impossible de savoir si une page lente était due à :
- Un serveur lent
- Un réseau lent
- Une réponse volumineuse
- Un rendu client lent

Maintenant, toutes ces métriques sont mesurées et visualisées.

---

## 📦 Fichiers modifiés

### Nouveaux fichiers
```
app/static/js/performance_monitor.js          # Script de capture des métriques client
app/routes/monitoring_routes.py               # API endpoint pour recevoir les métriques
migrations/add_response_size_to_access_log.sql # Migration colonne response_size_bytes
migrations/add_client_performance_log.sql     # Migration table client_performance_log
LIVRAISON_V1.8_MONITORING_PERFORMANCE.md      # Ce fichier
```

### Fichiers modifiés
```
app/middleware/access_logger.py               # Ajout capture taille réponse
app/models/db_logging.py                      # Nouvelles fonctions de logging client
app/models/__init__.py                        # Export des nouvelles fonctions
app/routes/catalog_routes.py                  # Route /access-logs mise à jour
app/templates/access_logs.html                # Nouvelles sections de visualisation
app/templates/base.html                       # Inclusion du script performance
main.py                                       # Enregistrement du router monitoring
```

---

## 🚀 Instructions de déploiement

### Option A : Déploiement automatisé (Recommandé)

Un script de déploiement automatisé est fourni pour faciliter le déploiement sur le NAS Synology :

```bash
# Depuis votre machine de développement
./deploy/deploy_synology_V1_9_monitoring.sh
```

Le script effectue automatiquement toutes les étapes :
- ✅ Création des backups (DB et fichiers)
- ✅ Copie des fichiers modifiés
- ✅ Application des migrations
- ✅ Vérification des migrations
- ✅ Redémarrage du service
- ✅ Tests de fonctionnement

**Note:** Vérifiez et ajustez les variables dans le script avant l'exécution :
- `SYNOLOGY_USER` : Votre nom d'utilisateur SSH
- `SYNOLOGY_HOST` : L'adresse IP de votre NAS
- `SYNOLOGY_PATH` : Le chemin de l'application sur le NAS

---

### Option B : Déploiement manuel

Si vous préférez déployer manuellement ou si le script automatisé ne fonctionne pas :

#### 1. Backup de la base de données
```bash
# Sur le serveur de production
cp data/recette.sqlite3 data/recette.sqlite3.backup_v1.8_$(date +%Y%m%d_%H%M%S)
```

#### 2. Arrêter l'application
```bash
# Synology via systemd
sudo systemctl stop recette

# Ou via Docker (si applicable)
docker stop recette
```

#### 3. Déployer le code
```bash
# Transférer les fichiers modifiés vers le serveur
# Utiliser rsync ou git pull selon votre méthode habituelle

# Exemple avec rsync (adapter les chemins)
rsync -avz --exclude 'venv' --exclude 'data' --exclude '__pycache__' \
  /Users/christianepp/Documents/DEV/Recette/ \
  user@synology:/volume1/docker/recette/
```

#### 4. Appliquer les migrations
```bash
# Se connecter au serveur et exécuter
cd /volume1/docker/recette  # Adapter le chemin

# IMPORTANT: L'application utilise data/recette.sqlite3

# Migration 1 : Ajouter colonne response_size_bytes
sqlite3 data/recette.sqlite3 "ALTER TABLE access_log ADD COLUMN response_size_bytes INTEGER;"

# Migration 2 : Créer table client_performance_log
sqlite3 data/recette.sqlite3 < migrations/add_client_performance_log.sql

# Migration 3 : Mettre à jour la vue v_popular_pages_24h
sqlite3 data/recette.sqlite3 "DROP VIEW IF EXISTS v_popular_pages_24h; CREATE VIEW IF NOT EXISTS v_popular_pages_24h AS SELECT path, COUNT(*) as visit_count, AVG(response_time_ms) as avg_response_time, AVG(response_size_bytes) as avg_response_size, COUNT(DISTINCT ip_address) as unique_visitors FROM access_log WHERE accessed_at >= datetime('now', '-1 day') AND path IS NOT NULL GROUP BY path ORDER BY visit_count DESC;"
```

#### 5. Vérifier les migrations
```bash
# Vérifier que les colonnes/tables existent
sqlite3 data/recette.sqlite3 "PRAGMA table_info(access_log);" | grep response_size_bytes
sqlite3 data/recette.sqlite3 ".tables" | grep client_performance_log

# Vérifier les vues
sqlite3 data/recette.sqlite3 "SELECT name FROM sqlite_master WHERE type='view';"
```

#### 6. Redémarrer l'application
```bash
# Synology via systemd
sudo systemctl start recette

# Ou via Docker (si applicable)
docker start recette
```

#### 7. Vérifier le déploiement
```bash
# Vérifier que l'application démarre sans erreur
sudo journalctl -u recette -n 50

# Tester l'endpoint de monitoring
curl -X POST http://localhost:8000/api/client-performance \
  -H "Content-Type: application/json" \
  -d '{"page_url": "/test", "total_load_time": 100}'

# Vérifier que la page de logs fonctionne
curl http://localhost:8000/access-logs?lang=fr
```

---

## 🧪 Tests à effectuer après déploiement

### Test 1 : Vérifier la capture de taille
1. Naviguer sur quelques pages de l'application
2. Aller sur `/access-logs`
3. Vérifier que la colonne "Taille (KB)" affiche des valeurs dans la section "Logs récents"
4. Vérifier que la section "Pages les plus lourdes" s'affiche

### Test 2 : Vérifier les métriques client
1. Naviguer sur quelques pages (attendre le chargement complet)
2. Aller sur `/access-logs`
3. Vérifier que la section "Performance Client vs Serveur" s'affiche
4. Vérifier que les colonnes affichent des valeurs cohérentes :
   - Serveur (ms) < Total Client (ms)
   - Overhead Client = Total - Serveur

### Test 3 : Vérifier l'API de monitoring
```bash
# Tester l'endpoint depuis le navigateur (console)
fetch('/api/client-performance', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    page_url: '/recipes',
    network_time: 50,
    server_time: 100,
    total_load_time: 200
  })
}).then(r => r.json()).then(console.log);
```

### Test 4 : Vérifier le script JavaScript
1. Ouvrir la console du navigateur (F12)
2. Naviguer sur une page
3. Attendre le chargement complet
4. Vérifier qu'aucune erreur JavaScript n'apparaît
5. Vérifier dans l'onglet "Network" qu'une requête POST est envoyée vers `/api/client-performance`

---

## 📊 Nouvelles fonctionnalités disponibles

### 1. Visualisation de la taille des réponses
- Colonne "Taille (KB)" dans les logs récents
- Section "Pages les plus lourdes" montrant les pages avec les plus grosses réponses

### 2. Métriques de performance client
La section "Performance Client vs Serveur" affiche :
- **Serveur (ms)** : Temps de traitement côté serveur
- **Total Client (ms)** : Temps total perçu par l'utilisateur
- **Réseau (ms)** : Temps réseau (DNS + TCP + download)
- **Overhead Client (ms)** : Temps de rendu navigateur (DOM + JavaScript)
  - 🟢 Vert : < 200ms (bon)
  - 🟡 Jaune : 200-500ms (attention)
  - 🔴 Rouge : > 500ms (problème)

### 3. API de monitoring
Nouvel endpoint `/api/client-performance` pour recevoir les métriques client

---

## 🔍 Métriques capturées

### Côté serveur (existant + nouveau)
- ✅ Temps de traitement serveur
- ✅ Nombre de requêtes
- ✅ Codes de statut HTTP
- 🆕 **Taille des réponses en octets**

### Côté client (nouveau)
- 🆕 **Temps réseau total** (DNS + TCP + requête/réponse)
- 🆕 **Temps DNS**
- 🆕 **Temps de connexion TCP**
- 🆕 **Temps de téléchargement**
- 🆕 **Temps de traitement DOM**
- 🆕 **Temps de rendu**
- 🆕 **Temps total perçu par l'utilisateur**

---

## ⚠️ Points d'attention

### Performance
- Le script JavaScript s'exécute après le chargement complet de la page (événement `load`)
- L'envoi des métriques utilise `navigator.sendBeacon()` pour ne pas bloquer la navigation
- Les métriques sont envoyées de manière asynchrone

### Base de données
- La table `client_performance_log` peut grossir rapidement
- Prévoir un nettoyage automatique similaire à `access_log` (actuellement 30 jours)
- Les index ont été créés pour optimiser les requêtes

### Compatibilité
- L'API Navigation Timing est supportée par tous les navigateurs modernes
- Graceful degradation : si l'API n'est pas disponible, aucune erreur n'est levée

---

## 🔄 Rollback (en cas de problème)

### 1. Arrêter l'application
```bash
docker stop recette
```

### 2. Restaurer la base de données
```bash
# Restaurer le backup
cp data/recipes.db.backup_v1.7_XXXXXXXX_XXXXXX data/recipes.db
```

### 3. Restaurer le code précédent
```bash
# Via git
git checkout v1.7

# Ou restaurer les fichiers depuis le backup
```

### 4. Redémarrer
```bash
docker start recette
```

---

## 📝 Notes de développement

### Structure des données

**Table `access_log`** (modifiée)
```sql
-- Nouvelle colonne
response_size_bytes INTEGER  -- Taille de la réponse en octets
```

**Table `client_performance_log`** (nouvelle)
```sql
CREATE TABLE client_performance_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    page_url TEXT NOT NULL,
    network_time REAL,           -- Temps réseau total
    dns_time REAL,               -- Temps DNS
    tcp_time REAL,               -- Temps TCP
    server_time REAL,            -- Temps serveur
    download_time REAL,          -- Temps de téléchargement
    dom_processing_time REAL,    -- Temps de traitement DOM
    total_load_time REAL,        -- Temps total
    dom_interactive_time REAL,   -- Temps jusqu'au DOM interactif
    navigation_type INTEGER,     -- Type de navigation
    redirect_count INTEGER,      -- Nombre de redirections
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Nouvelles vues SQL
- `v_client_performance_24h` : Statistiques de performance client sur 24h
- `v_popular_pages_24h` : Mise à jour pour inclure `avg_response_size`

---

## 📞 Support

En cas de problème :
1. Vérifier les logs : `docker logs recette`
2. Vérifier que les migrations ont été appliquées
3. Vérifier les permissions sur les fichiers
4. Contacter le développeur avec les logs d'erreur

---

## ✅ Checklist de déploiement

- [ ] Backup de la base de données effectué
- [ ] Application arrêtée
- [ ] Code déployé sur le serveur
- [ ] Migration 1 appliquée (response_size_bytes)
- [ ] Migration 2 appliquée (client_performance_log)
- [ ] Migrations vérifiées
- [ ] Application redémarrée
- [ ] Logs vérifiés (pas d'erreur)
- [ ] Test 1 effectué (taille des réponses)
- [ ] Test 2 effectué (métriques client)
- [ ] Test 3 effectué (API monitoring)
- [ ] Test 4 effectué (script JavaScript)
- [ ] Backup de validation créé

---

**Développé avec ❤️ pour une meilleure observabilité**
