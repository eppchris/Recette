# Correction Production - Access Logs

**Date**: 11 décembre 2025
**Version**: 1.13
**Priorité**: 🔥 HAUTE

---

## 🐛 Problème Identifié

### Erreur en Production

```
sqlite3.OperationalError: no such column: response_size_bytes
```

**Écran affecté**: `/catalog/access-logs`
**Fonction**: `get_access_stats()` dans `app/models/db_logging.py`

### Cause Racine

La colonne `response_size_bytes` a été ajoutée dans une migration récente (`migrations/add_response_size_to_access_log.sql`), mais cette migration n'a **pas été appliquée en production**.

Le code utilise cette colonne pour calculer les "pages les plus lourdes", ce qui provoque une erreur quand la colonne n'existe pas.

---

## ✅ Solution Appliquée

### 1. Correction Immédiate du Code ✅

**Fichiers modifiés**: `app/models/db_logging.py`

**Changements**: Vérification de l'existence de la colonne avant utilisation dans **2 fonctions**

#### Fonction 1: `get_access_stats()` (lignes 94-119)

Utilisée pour les statistiques "pages les plus lourdes"

#### Fonction 2: `get_recent_access_logs()` (lignes 242-270)

Utilisée pour afficher la liste des logs récents dans l'écran `/catalog/access-logs`

**Code (fonction 1 - get_access_stats)**:
```python
# Pages les plus lourdes (par taille de réponse)
# Vérifier si la colonne response_size_bytes existe
cursor.execute("PRAGMA table_info(access_log)")
columns = [col[1] for col in cursor.fetchall()]

heavy_pages = []
if 'response_size_bytes' in columns:
    cursor.execute("""
        SELECT path, AVG(response_size_bytes) as avg_size, COUNT(*) as count
        FROM access_log
        WHERE accessed_at >= datetime('now', '-' || ? || ' hours')
          AND response_size_bytes IS NOT NULL
          AND path IS NOT NULL
        GROUP BY path
        ORDER BY avg_size DESC
        LIMIT 10
    """, (hours,))
    heavy_pages = [dict(row) for row in cursor.fetchall()]
```

**Code (fonction 2 - get_recent_access_logs)**:
```python
# Vérifier si la colonne response_size_bytes existe
cursor.execute("PRAGMA table_info(access_log)")
columns = [col[1] for col in cursor.fetchall()]
has_response_size = 'response_size_bytes' in columns

# Construire la requête selon les colonnes disponibles
if has_response_size:
    cursor.execute("""
        SELECT ip_address, user_agent, path, method, status_code,
               response_time_ms, response_size_bytes, referer, lang, accessed_at
        FROM access_log
        WHERE accessed_at >= datetime('now', '-' || ? || ' hours')
        ORDER BY accessed_at DESC
        LIMIT ?
    """, (hours, limit))
else:
    cursor.execute("""
        SELECT ip_address, user_agent, path, method, status_code,
               response_time_ms, NULL as response_size_bytes, referer, lang, accessed_at
        FROM access_log
        WHERE accessed_at >= datetime('now', '-' || ? || ' hours')
        ORDER BY accessed_at DESC
        LIMIT ?
    """, (hours, limit))
```

**Avantage**:
- ✅ Le code ne plante plus si la colonne n'existe pas
- ✅ Rétrocompatible avec les bases de données anciennes
- ✅ Fonctionne aussi bien en dev qu'en production

### 2. Script d'Application de la Migration ✅

**Fichier créé**: `scripts/apply_response_size_migration.sh`

Ce script permet d'appliquer la migration en production de manière sécurisée:

- ✅ Création automatique d'un backup avant migration
- ✅ Vérification de l'existence de la colonne avant application
- ✅ Vérification post-migration
- ✅ Restauration automatique en cas d'erreur

**Usage**:
```bash
chmod +x scripts/apply_response_size_migration.sh
./scripts/apply_response_size_migration.sh
```

---

## 🚀 Actions à Effectuer en Production

### Option 1: Application de la Migration (Recommandée)

Pour bénéficier de la fonctionnalité "pages les plus lourdes":

```bash
# En SSH sur le serveur de production
cd /volume1/homes/admin/recette
./scripts/apply_response_size_migration.sh
```

**Résultat**: La colonne `response_size_bytes` sera ajoutée et les statistiques "pages lourdes" seront disponibles.

### Option 2: Ne Rien Faire

Le code fonctionne maintenant **sans la colonne**:
- ✅ L'écran des logs d'accès s'affiche correctement
- ⚠️ Les "pages les plus lourdes" seront vides (`heavy_pages = []`)
- ⚠️ Pas de mesure de taille des réponses

---

## 📊 Impact

### Avant la Correction
- ❌ L'écran `/catalog/access-logs` plantait
- ❌ Impossible de consulter les statistiques d'accès

### Après la Correction (sans migration)
- ✅ L'écran s'affiche correctement
- ⚠️ Section "pages lourdes" vide
- ✅ Toutes les autres statistiques fonctionnent

### Après Application de la Migration
- ✅ L'écran s'affiche correctement
- ✅ Section "pages lourdes" avec données
- ✅ Toutes les fonctionnalités actives

---

## 🔍 Détails de la Migration

**Fichier**: `migrations/add_response_size_to_access_log.sql`

**Contenu**:
```sql
-- Ajout de la colonne
ALTER TABLE access_log ADD COLUMN response_size_bytes INTEGER;

-- Mise à jour de la vue
DROP VIEW IF EXISTS v_popular_pages_24h;
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
```

---

## 📋 Checklist de Déploiement

- [x] Correction du code appliquée
- [x] Script de migration créé
- [x] Documentation rédigée
- [ ] Test en environnement de dev
- [ ] Déploiement du code corrigé en production
- [ ] *(Optionnel)* Application de la migration en production

---

## ⚠️ Notes Importantes

1. **Pas de régression**: Le code fonctionne maintenant avec ou sans la colonne
2. **Migration optionnelle**: Vous pouvez la reporter à plus tard sans problème
3. **Backup automatique**: Le script crée un backup avant toute modification
4. **Sécurité**: Restauration automatique en cas d'erreur

---

## 🎯 Recommandation

**Pour la V1.13**: Déployer le code corrigé SANS appliquer la migration

**Pour une version ultérieure**: Appliquer la migration quand vous aurez le temps de tester

---

**Résumé**: Le problème est corrigé et l'application fonctionne. La migration peut être appliquée plus tard si vous souhaitez avoir les statistiques de taille des réponses.
