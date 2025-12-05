# Règles du Projet Recette

## 🚫 RÈGLES CRITIQUES - NE JAMAIS FAIRE

### 1. **NE JAMAIS démarrer l'application automatiquement**
- ❌ Ne JAMAIS exécuter `uvicorn`, `python main.py`, ou tout autre commande pour lancer l'app
- ❌ Ne JAMAIS tester l'application en la démarrant
- ✅ C'est l'utilisateur qui démarre l'application quand il le souhaite
- ✅ Tu peux faire des `curl` sur `localhost:8000` si l'app tourne déjà

### 2. **NE JAMAIS oublier .gitignore pour les scripts de déploiement**
- Quand tu crées un nouveau script `deploy_synology_V{X}_{Y}.sh`
- Tu DOIS TOUJOURS ajouter l'exception dans `.gitignore`:
  ```
  !deploy/deploy_synology_V{X}_{Y}.sh
  ```

## 📋 Git & Commits

### Format des commits
Tous les commits doivent suivre ce format:
```
Titre court et descriptif (max 72 caractères)

Description détaillée si nécessaire:
- Point 1
- Point 2
- Point 3

Détails techniques ou notes importantes.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Bonnes pratiques
- Messages de commit en français
- Commits atomiques (une fonctionnalité = un commit)
- Toujours vérifier `git status` avant de commit
- Toujours pousser vers `origin/main` après commit

## 🚀 Déploiement

### Nomenclature des scripts
- Pattern: `deploy_synology_V{major}_{minor}.sh`
- Exemples:
  - `deploy_synology_V1_5.sh`
  - `deploy_synology_V1_6.sh`
  - `deploy_synology_V2_0.sh`

### Checklist pour un nouveau script de déploiement

1. **Créer le script** `deploy/deploy_synology_V{X}_{Y}.sh`
2. **Ajouter dans .gitignore**:
   ```bash
   # Dans .gitignore, section "Scripts de déploiement spécifiques"
   !deploy/deploy_synology_V{X}_{Y}.sh
   ```
3. **Rendre exécutable**: `chmod +x deploy/deploy_synology_V{X}_{Y}.sh`
4. **Vérifier REQUIRED_FILES** dans le script
5. **Mettre à jour la description** des fonctionnalités
6. **Lister les commits inclus** dans le message final
7. **Créer NOTES_DEPLOIEMENT_V{X}_{Y}.md** dans `deploy/`

### Structure d'un script de déploiement

```bash
#!/bin/bash
# Script de déploiement pour Synology DS213+
# Version {X}.{Y} - Description des features
# Usage: ./deploy_synology_V{X}_{Y}.sh

SYNOLOGY_USER="admin"
SYNOLOGY_HOST="192.168.1.14"
DEPLOY_PATH="recette"

# 8 étapes:
# 1. Préparation archive
# 2. Transfert SSH
# 3. Backup BDD
# 4. Arrêt application
# 5. Déploiement fichiers
# 6. Installation dépendances
# 7. Migration BDD (si nécessaire)
# 8. Redémarrage
```

## 💻 Code & Architecture

### Application bilingue
- **TOUJOURS** supporter FR et JP
- Format: `{{ 'Texte français' if lang == 'fr' else 'テキスト日本語' }}`
- Tester les deux langues: `?lang=fr` et `?lang=jp`

### Mode sombre
- **TOUJOURS** supporter le mode clair et sombre
- Classes Tailwind: `dark:bg-gray-800`, `dark:text-white`, etc.
- Tester avec le toggle dans la sidebar

### Style & UI
- **Framework CSS**: Tailwind CSS
- **Interactivité**: Alpine.js
- **Templates**: Jinja2
- **Format**: Responsive mobile-first

### Backend
- **Framework**: FastAPI
- **Base de données**: SQLite3
- **Structure**:
  - Routes: `app/routes/`
  - Modèles: `app/models/`
  - Templates: `app/templates/`
  - Migrations: `migrations/`

## 📦 Base de données

### Migrations
- Scripts SQL dans `migrations/`
- Nomenclature: `add_{feature}_{description}.sql`
- Exemple: `add_event_multi_days.sql`

### Bonnes pratiques
- **TOUJOURS** créer un backup avant migration
- Utiliser des transactions
- Vérifier l'intégrité post-migration
- Documenter les changements dans NOTES_DEPLOIEMENT

### Backup automatique
```bash
BACKUP_FILE="backups/recette_pre_v{X}_{Y}_$(date +%Y%m%d_%H%M%S).sqlite3"
cp data/recette.sqlite3 "$BACKUP_FILE"
```

## 📚 Documentation

### Structure des docs
```
docs/
├── help/
│   └── README.md          # Guide modification page d'aide
├── deployment/
│   └── README.md          # Guide général déploiement
└── features/
    └── {feature}.md       # Doc par feature
```

### Documentation à créer pour chaque version
1. **NOTES_DEPLOIEMENT_V{X}_{Y}.md** dans `deploy/`
   - Nouvelles fonctionnalités
   - Fichiers modifiés
   - Procédure de déploiement
   - Migration BDD
   - Tests post-déploiement
   - Rollback si nécessaire

2. **README.md** pour les features majeures
   - Comment utiliser
   - Exemples de code
   - Screenshots si utile

## 🎯 Workflow Standard

### Ajout d'une nouvelle fonctionnalité

1. **Développement**
   - Lire les fichiers existants avant de modifier
   - Respecter l'architecture existante
   - Tester bilingue (FR/JP)
   - Tester mode clair/sombre

2. **Commit**
   - `git add {fichiers}`
   - `git commit` avec le format standard
   - `git push origin main`

3. **Déploiement** (pour nouvelle version)
   - Créer `deploy_synology_V{X}_{Y}.sh`
   - Ajouter exception dans `.gitignore`
   - Créer `NOTES_DEPLOIEMENT_V{X}_{Y}.md`
   - Commit + Push
   - L'utilisateur exécute le script manuellement

4. **Documentation**
   - Mettre à jour la page d'aide si nécessaire
   - Créer/mettre à jour README si feature majeure

## ⚙️ Configuration

### Environnement
- **Dev**: `data/recette.sqlite3` (local, gitignore)
- **Prod**: Synology DS213+ (192.168.1.14:8000)
- **URL publique**: http://recipe.e2pc.fr

### Fichiers sensibles (.gitignore)
- `.env` (secrets)
- `data/*.sqlite3` (bases de données locales)
- `deploy/*.sh` (sauf exceptions explicites)
- `__pycache__/`
- `*.pyc`
- `logs/`

## 🔧 Outils & Commandes

### Commandes utiles (mais ne pas exécuter automatiquement)
```bash
# Lancer l'app (UTILISATEUR SEULEMENT)
uvicorn app.main:app --reload --port 8000

# Tests SQL
sqlite3 data/recette.sqlite3 "SELECT COUNT(*) FROM recipe;"

# Vérifier fichiers modifiés
git status

# Voir l'historique
git log --oneline -n 10
```

### Ce que Claude PEUT faire
✅ Lire des fichiers
✅ Modifier des fichiers
✅ Créer des fichiers
✅ Exécuter des commandes git
✅ Faire des `curl` sur localhost si l'app tourne
✅ Exécuter des scripts bash (sauf démarrage app)

### Ce que Claude NE DOIT PAS faire
❌ Démarrer l'application
❌ Redémarrer l'application
❌ Arrêter l'application
❌ Oublier .gitignore pour les scripts de déploiement

## 📝 Templates & Snippets

### Template commit message
```
Titre du commit

Description:
- Modification 1
- Modification 2

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Template route FastAPI bilingue
```python
@router.get("/ma-route", response_class=HTMLResponse)
async def ma_route(request: Request, lang: str = Query("fr")):
    """Description de la route"""
    return templates.TemplateResponse(
        "mon_template.html",
        {"request": request, "lang": lang}
    )
```

### Template Jinja bilingue
```html
<h1>{{ 'Titre français' if lang == 'fr' else '日本語タイトル' }}</h1>

{% if lang == 'fr' %}
<p>Contenu en français</p>
{% else %}
<p>日本語のコンテンツ</p>
{% endif %}
```

## 🎨 Conventions de style

### Emojis standards
- 📖 Recettes
- 🔍 Recherche
- 📅 Événements (1 jour)
- 📆 Événements multi-jours
- 🗓️ Planification
- 🛒 Liste de courses
- 💰 Budget
- 📚 Catalogue
- ❓ Aide
- ⚙️ Paramètres
- 👤 Utilisateur
- 🚀 Déploiement
- ✅ Succès
- ❌ Erreur
- 💡 Astuce
- 📌 Exemple

### Classes Tailwind fréquentes
```html
<!-- Bouton primaire -->
<button class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg">

<!-- Carte -->
<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">

<!-- Badge -->
<span class="bg-green-500 text-white text-xs px-2 py-1 rounded">NOUVEAU</span>

<!-- Encadré astuce -->
<div class="bg-blue-50 dark:bg-blue-900/30 p-4 rounded-lg border border-blue-200">
```

## 🔄 Versioning

### Numérotation
- **Major.Minor**: V1.6, V1.7, V2.0
- Incrémenter Minor pour nouvelles features
- Incrémenter Major pour changements majeurs

### Commits par version
- Lister tous les commits inclus dans le script de déploiement
- Format: `{hash} - {description courte}`

---

**Dernière mise à jour**: Version 1.6 (Décembre 2025)
