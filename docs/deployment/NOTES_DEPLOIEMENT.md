# Notes de déploiement

## Version 1.3 - À déployer

### ✅ Système de conversion d'unités
- Migration appliquée: `migrations/add_unit_conversions.sql`
- Fonctions ajoutées dans `app/models/db.py`:
  - `convert_unit()`
  - `get_convertible_units()`
  - `calculate_ingredient_price()`
- 37 règles de conversion disponibles

### ✅ Catalogue bilingue FR/JP
- Migration appliquée: `migrations/make_catalog_bilingual.sql`
- Colonnes ajoutées: `ingredient_name_jp`, `unit_jp`, `ingredient_name_fr`, `unit_fr`

### ⚠️ IMPORTANT: Fichiers CSS/JS locaux (Cloudflare)

**Problème**: Cloudflare CDN en panne mondiale le 18/11/2025
**Solution**: Hébergement local de Tailwind CSS et Alpine.js

**Fichiers à copier vers la production**:
```bash
# Sur le serveur Synology
mkdir -p /var/services/homes/christianepp/Recette/static/css/
scp static/css/tailwind.min.js synology:/var/services/homes/christianepp/Recette/static/css/
scp static/css/alpine.min.js synology:/var/services/homes/christianepp/Recette/static/css/
```

**Templates modifiés** (utilisant `/static/css/` au lieu des CDN):
- `app/templates/base.html`
- `app/templates/ingredient_catalog.html`
- `app/templates/events_list.html`
- `app/templates/event_budget.html`
- `app/templates/recette_connexion.html`
- `app/templates/shopping_list.html`
- `app/templates/event_detail.html`
- `app/templates/event_form.html`

### 🤖 Protection contre les bots (robots.txt)
- Fichier créé: `static/robots.txt`
- Route ajoutée dans `main.py` (ligne 109-112)
- Bloque tous les crawlers/bots pour cette application privée

**Déploiement sur NAS**:
```bash
# Le fichier robots.txt sera automatiquement copié avec le reste du dossier static/
# Rien de spécial à faire, juste déployer normalement
```

**Test après déploiement**:
```bash
curl https://votre-nas.com/robots.txt
# Devrait retourner:
# User-agent: *
# Disallow: /
```

### 📋 Checklist de déploiement

1. [ ] Copier les fichiers CSS/JS vers le serveur
2. [ ] Copier le fichier `static/robots.txt` vers le serveur
3. [ ] Déployer les templates mis à jour
4. [ ] Déployer `main.py` mis à jour (route robots.txt)
5. [ ] Appliquer la migration `add_unit_conversions.sql`
6. [ ] Appliquer la migration `make_catalog_bilingual.sql`
7. [ ] Vérifier que la mise en page fonctionne
8. [ ] Tester la conversion d'unités
9. [ ] Tester le catalogue bilingue
10. [ ] Tester `/robots.txt` (curl ou navigateur)

### 🔧 Commandes rapides

```bash
# Appliquer les migrations
sqlite3 data/recette.sqlite3 < migrations/add_unit_conversions.sql
sqlite3 data/recette.sqlite3 < migrations/make_catalog_bilingual.sql

# Vérifier les conversions
sqlite3 data/recette.sqlite3 "SELECT COUNT(*) FROM unit_conversion;"
# Attendu: 37

# Vérifier le catalogue bilingue
sqlite3 data/recette.sqlite3 "SELECT ingredient_name_fr, ingredient_name_jp FROM ingredient_price_catalog LIMIT 3;"
```

## Historique des versions

### Version 1.2
- Gestion des budgets d'événements
- Listes de courses

### Version 1.1
- Authentification
- Gestion d'événements
- Images de recettes

### Version 1.0
- Application de gestion de recettes bilingue FR/JP
