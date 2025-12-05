# Notes de déploiement V1.7

## 📅 Informations

- **Version**: 1.7
- **Date de déploiement**: Décembre 2024
- **Commits inclus**:
  - `999e324` - Aide modifiable par admin en Markdown
  - `bac34f6` - Ajout bouton retour dans l'aide

## 🎯 Objectif de la version

Rendre la page d'aide **modifiable par les administrateurs** via une interface web, sans nécessiter de redéploiement.

## ✨ Nouvelles fonctionnalités

### 1. Aide modifiable par admin

**Route**: `/admin/help/edit`

**Fonctionnalités**:
- Éditeur Markdown avec textarea
- Toggle Édition/Aperçu en temps réel avec Alpine.js
- Preview du rendu avant sauvegarde
- Édition séparée pour FR et JP
- Bouton "Éditer l'aide" visible uniquement pour les admins
- Modifications instantanées sans redéploiement

**Fichiers de contenu**:
- `docs/help/content/help_fr.md` - Contenu français
- `docs/help/content/help_jp.md` - Contenu japonais

### 2. Bouton retour dans l'aide

**Changement**: Ajout d'un bouton "← Retour" en haut de la page d'aide pour retourner à la page précédente avec `history.back()`.

## 📦 Fichiers modifiés

### Nouveaux fichiers
- `app/templates/admin_help_edit.html` - Template d'édition de l'aide
- `docs/help/content/help_fr.md` - Contenu français en Markdown
- `docs/help/content/help_jp.md` - Contenu japonais en Markdown

### Fichiers modifiés
- `requirements.txt` - Ajout de `markdown>=3.5.0`
- `app/routes/auth_routes.py` - Nouvelles routes `/admin/help/edit` (GET/POST)
- `app/templates/help.html` - Charge maintenant le contenu depuis Markdown
- `docs/help/README.md` - Documentation mise à jour
- `.gitignore` - Exception pour `deploy_synology_V1_7.sh`

### Script de déploiement
- `deploy/deploy_synology_V1_7.sh` - Script de déploiement pour V1.7

## 🔧 Dépendances ajoutées

```txt
markdown>=3.5.0
```

Cette bibliothèque permet de:
- Convertir le Markdown en HTML
- Supporter les tables Markdown
- Supporter les blocs de code avec triple backticks

## 🗄️ Migrations de base de données

**Aucune migration nécessaire** pour cette version. Pas de changement dans le schéma de la base de données.

## 📝 Procédure de déploiement

### 1. Préparation (en local)

```bash
# Vérifier les commits
git log --oneline -5

# Vérifier que tous les fichiers sont présents
ls -la app/templates/admin_help_edit.html
ls -la docs/help/content/
ls -la deploy/deploy_synology_V1_7.sh
```

### 2. Exécution du déploiement

```bash
cd /Users/christianepp/Documents/DEV/Recette
./deploy/deploy_synology_V1_7.sh
```

Le script effectue automatiquement:
1. ✅ Vérification des fichiers requis
2. ✅ Création de l'archive (excluant .git, venv, etc.)
3. ✅ Transfert SSH vers le Synology
4. ✅ Backup automatique de la BDD (`backups/recette_pre_v1_7_*.sqlite3`)
5. ✅ Arrêt de l'application
6. ✅ Extraction des fichiers
7. ✅ Installation des dépendances (dont `markdown`)
8. ✅ Redémarrage de l'application

### 3. Durée estimée

- **Transfert**: ~30 secondes
- **Installation**: ~1 minute
- **Total**: ~2 minutes

## ✅ Tests post-déploiement

### 1. Tests fonctionnels

**En tant qu'admin**:
```
1. ✅ Se connecter en tant qu'admin
2. ✅ Cliquer sur l'icône ❓ dans la sidebar
3. ✅ Vérifier que le bouton "← Retour" fonctionne
4. ✅ Vérifier que le bouton "✏️ Éditer l'aide" est visible
5. ✅ Cliquer sur "Éditer l'aide"
6. ✅ Modifier du contenu Markdown
7. ✅ Basculer sur "Aperçu" et vérifier le rendu
8. ✅ Enregistrer les modifications
9. ✅ Retourner à /help et vérifier les changements
10. ✅ Tester en FR et JP séparément
```

**En tant qu'utilisateur normal**:
```
1. ✅ Se connecter en tant qu'utilisateur normal
2. ✅ Accéder à la page d'aide
3. ✅ Vérifier que le bouton "Éditer l'aide" n'est PAS visible
4. ✅ Vérifier que /admin/help/edit redirige vers /recipes
```

### 2. Tests de sécurité

```bash
# Vérifier que les utilisateurs non-admin ne peuvent pas accéder à l'édition
curl -i http://recipe.e2pc.fr/admin/help/edit
# Doit rediriger vers /recipes

# Vérifier que le contenu Markdown est bien converti
curl -s http://recipe.e2pc.fr/help?lang=fr | grep "<h1>"
```

### 3. Vérification logs

```bash
ssh admin@192.168.1.14 'tail -f recette/logs/app.log'
```

Rechercher:
- ✅ Aucune erreur au démarrage
- ✅ Bibliothèque markdown chargée
- ✅ Routes `/admin/help/edit` disponibles

## 🔄 Rollback

En cas de problème:

### 1. Rollback base de données (si nécessaire)

```bash
ssh admin@192.168.1.14
cd recette
cp backups/recette_pre_v1_7_YYYYMMDD_HHMMSS.sqlite3 data/recette.sqlite3
```

### 2. Rollback code

Redéployer la V1.6:
```bash
./deploy/deploy_synology_V1_6.sh
```

### 3. Vérification post-rollback

```bash
curl -s http://recipe.e2pc.fr/help | grep "Version 1.6"
```

## 📊 Architecture technique

### Routes ajoutées

```python
# GET /admin/help/edit
# - Charge le fichier docs/help/content/help_{lang}.md
# - Génère preview HTML avec markdown.markdown()
# - Affiche template admin_help_edit.html

# POST /admin/help/edit
# - Sauvegarde le contenu dans docs/help/content/help_{lang}.md
# - Régénère preview
# - Affiche message de succès
```

### Flux de données

```
User (admin) → /admin/help/edit
              ↓
         Load help_{lang}.md
              ↓
    Generate Markdown preview
              ↓
   Display admin_help_edit.html
              ↓
    User edits & clicks Save
              ↓
      POST /admin/help/edit
              ↓
   Save to help_{lang}.md
              ↓
         Success message
              ↓
    User views /help
              ↓
   Load & convert Markdown
              ↓
    Display updated content
```

### Extensions Markdown supportées

```python
markdown.markdown(content, extensions=['tables', 'fenced_code'])
```

- `tables`: Support des tableaux Markdown
- `fenced_code`: Blocs de code avec triple backticks

## 🎨 Styles prose

Le rendu Markdown utilise les classes Tailwind `prose`:

```html
<div class="prose dark:prose-invert max-w-none">
    {{ help_content | safe }}
</div>
```

Avec styles custom pour:
- Titres H1, H2, H3
- Paragraphes
- Listes
- Code inline et blocs
- Citations
- Mode sombre

## 🔐 Sécurité

### Contrôles d'accès

```python
# Vérification admin uniquement
if not user_id or not is_admin:
    return RedirectResponse(url=f"/recipes?lang={lang}", status_code=303)
```

### Fichiers modifiables

Les admins peuvent **uniquement** modifier:
- `docs/help/content/help_fr.md`
- `docs/help/content/help_jp.md`

Pas d'accès aux autres fichiers système.

### Échappement HTML

Le contenu Markdown est converti en HTML sécurisé par la bibliothèque `markdown`, puis rendu avec `| safe` car le contenu est contrôlé (accessible uniquement aux admins).

## 📈 Avantages de cette approche

✅ **Modifications sans redéploiement**: L'admin peut modifier l'aide directement en production
✅ **Prévisualisation**: Voir le rendu avant de sauvegarder
✅ **Bilingue**: Édition séparée FR/JP
✅ **Sécurisé**: Réservé aux admins uniquement
✅ **Maintenable**: Format Markdown simple et lisible
✅ **Versionnable**: Fichiers .md dans git pour historique

## 📚 Documentation

- [docs/help/README.md](../docs/help/README.md) - Guide complet du système d'aide
- [.claude/project-rules.md](../.claude/project-rules.md) - Règles du projet

## 🐛 Problèmes connus

Aucun problème connu à ce jour.

## 📝 Notes pour les prochaines versions

### V1.8+ (Améliorations possibles)

- [ ] Éditeur Markdown avancé (Monaco, CodeMirror)
- [ ] Upload d'images dans l'aide
- [ ] Historique des modifications (versioning)
- [ ] Recherche dans l'aide
- [ ] Export PDF de l'aide
- [ ] Mise à jour automatique du numéro de version

## 🔗 Ressources

- **GitHub**: https://github.com/eppchris/Recette
- **Production**: http://recipe.e2pc.fr
- **Markdown syntax**: https://www.markdownguide.org/basic-syntax/

---

**Dernière mise à jour**: Décembre 2024
**Responsable**: Christian EPP
**Statut**: ✅ Déployé en production
