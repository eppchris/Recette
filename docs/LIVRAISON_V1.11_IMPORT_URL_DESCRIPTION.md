# 📦 Livraison V1.11 - Import URL + Description

**Date**: 2025-12-09
**Version**: V1.11
**Environnement cible**: Production (Synology)

---

## 🎯 Résumé des fonctionnalités

### 1. 🌐 Import de recettes depuis URL avec IA
- Import automatique depuis n'importe quelle URL de recette (Marmiton, Cookpad, AllRecipes, etc.)
- Extraction intelligente avec Groq AI (Llama 3.3 70B)
- Traduction automatique FR ↔ JP
- Interface utilisateur avec prévisualisation avant sauvegarde
- Menu d'import amélioré (CSV, URL, PDF)

### 2. 📝 Champ Description pour les recettes
- Ajout du champ description dans les recettes (multi-langue)
- Affichage dans un bandeau visible sous le titre
- Édition dans le modal de modification
- Migration de base de données

---

## 📋 Fichiers modifiés

### Nouveaux fichiers
- `app/services/web_recipe_importer.py` - Service d'import web avec IA
- `app/templates/import_url.html` - Interface d'import URL
- `migrations/add_recipe_description.sql` - Migration description
- `deploy/deploy_synology_V1_11_url_import.sh` - Script de déploiement

### Fichiers modifiés
- `main.py` - Initialisation du service d'import web
- `app/routes/recipe_routes.py` - Routes d'import URL + sauvegarde description
- `app/templates/recipe_detail.html` - Affichage et édition description
- `app/templates/recipes_list.html` - Menu d'import amélioré
- `app/models/db_recipes.py` - Récupération et sauvegarde description

---

## 🔧 Installation et déploiement

### Option 1 : Script automatique (RECOMMANDÉ)

```bash
cd /Users/christianepp/Documents/DEV/Recette
./deploy/deploy_synology_V1_11_url_import.sh
```

Le script effectue automatiquement :
1. ✅ Backup de la prod
2. ✅ Copie des fichiers
3. ✅ Installation des dépendances (`requests`, `beautifulsoup4`)
4. ✅ Application de la migration SQL
5. ✅ Redémarrage du service
6. ✅ Vérification de l'application

### Option 2 : Déploiement manuel

#### 1. Backup
```bash
ssh christianepp@192.168.1.154
cd /volume1/docker/recette
tar -czf backups/backup_pre_V1.11_$(date +%Y%m%d_%H%M%S).tar.gz \
  --exclude='backups' --exclude='venv' --exclude='__pycache__' .
```

#### 2. Copie des fichiers
```bash
# Depuis votre Mac
cd /Users/christianepp/Documents/DEV/Recette

# Service
scp app/services/web_recipe_importer.py christianepp@192.168.1.154:/volume1/docker/recette/app/services/

# Templates
scp app/templates/import_url.html christianepp@192.168.1.154:/volume1/docker/recette/app/templates/
scp app/templates/recipe_detail.html christianepp@192.168.1.154:/volume1/docker/recette/app/templates/
scp app/templates/recipes_list.html christianepp@192.168.1.154:/volume1/docker/recette/app/templates/

# Routes et Models
scp app/routes/recipe_routes.py christianepp@192.168.1.154:/volume1/docker/recette/app/routes/
scp app/models/db_recipes.py christianepp@192.168.1.154:/volume1/docker/recette/app/models/

# Main
scp main.py christianepp@192.168.1.154:/volume1/docker/recette/

# Migration
scp migrations/add_recipe_description.sql christianepp@192.168.1.154:/volume1/docker/recette/migrations/
```

#### 3. Installation des dépendances
```bash
ssh christianepp@192.168.1.154
cd /volume1/docker/recette
source venv/bin/activate
pip install requests beautifulsoup4
```

#### 4. Application de la migration
```bash
sqlite3 data/recette.sqlite3 < migrations/add_recipe_description.sql
```

#### 5. Redémarrage
```bash
docker-compose restart
```

#### 6. Vérification
```bash
curl http://localhost:8000/health
# Devrait retourner: {"status":"ok",...}
```

---

## ✅ Tests de validation

### 1. Test import depuis URL

1. Aller sur http://192.168.1.154:8000/recipes?lang=fr
2. Cliquer sur le bouton "Import" → "Import depuis URL"
3. Coller une URL de recette (ex: une recette Marmiton ou Cookpad)
4. Choisir la langue cible (FR ou JP)
5. Cliquer sur "Analyser l'URL"
6. Vérifier que les informations sont correctement extraites :
   - ✅ Nom de la recette
   - ✅ Description
   - ✅ Ingrédients avec quantités
   - ✅ Étapes de préparation
7. Modifier si nécessaire
8. Cliquer sur "Sauvegarder"
9. Vérifier que la recette est créée et affichée

### 2. Test du champ description

1. Aller sur une recette existante
2. Vérifier qu'il n'y a pas de description (normal pour les anciennes recettes)
3. Cliquer sur "Modifier"
4. Ajouter une description dans le champ "Description"
5. Cliquer sur "Sauvegarder"
6. Vérifier que la description s'affiche dans le bandeau bleu sous le titre
7. Changer de langue (FR ↔ JP)
8. Modifier à nouveau et ajouter une description dans l'autre langue
9. Vérifier que chaque langue a sa propre description

### 3. Test des recettes importées depuis URL

1. Importer une recette depuis URL
2. Vérifier que la description extraite par l'IA est visible
3. Tester l'édition de la description
4. Tester la conversion de quantités

---

## 🔄 Rollback (en cas de problème)

### Restauration rapide
```bash
ssh christianepp@192.168.1.154
cd /volume1/docker/recette/backups

# Lister les backups
ls -lht backup_pre_V1.11_*

# Restaurer le dernier backup
tar -xzf backup_pre_V1.11_YYYYMMDD_HHMMSS.tar.gz -C ..

# Redémarrer
cd ..
docker-compose restart
```

### Annulation de la migration
```bash
ssh christianepp@192.168.1.154
cd /volume1/docker/recette

# La migration ne peut pas être facilement annulée car elle ne fait qu'ajouter une colonne
# Mais elle est sans danger (valeur par défaut = '')
# Si vraiment nécessaire, restaurer la base depuis le backup
```

---

## 📊 Métriques et monitoring

### Logs à surveiller
```bash
# Logs du service d'import
ssh christianepp@192.168.1.154
docker logs recette-app | grep "Service d'import de recettes web"

# Logs d'erreurs
docker logs recette-app | grep -i error | tail -20
```

### Points de vérification
- ✅ Service web répond : `curl http://192.168.1.154:8000/health`
- ✅ Import URL accessible : `curl http://192.168.1.154:8000/import-url?lang=fr`
- ✅ Base de données : `sqlite3 data/recette.sqlite3 "SELECT COUNT(*) FROM recipe_translation WHERE description != '';"`

---

## 🎓 Guide utilisateur

### Comment importer une recette depuis URL

1. **Trouver une recette en ligne**
   - Sites compatibles : Marmiton, 750g, Cuisine AZ, AllRecipes, Cookpad, etc.
   - N'importe quelle page web contenant une recette

2. **Lancer l'import**
   - Cliquer sur "Import" → "Import depuis URL"
   - Coller l'URL de la page
   - Choisir la langue cible (FR ou JP)
   - L'IA va automatiquement traduire si nécessaire

3. **Vérifier et ajuster**
   - Vérifier les informations extraites
   - Corriger si besoin (quantités, unités, étapes)
   - Ajouter ou modifier la description

4. **Sauvegarder**
   - La recette est créée dans la langue choisie
   - Vous pouvez ensuite la traduire dans l'autre langue

### Comment ajouter/modifier une description

1. **Sur une recette existante**
   - Ouvrir la recette
   - Cliquer sur "Modifier"
   - Remplir le champ "Description"
   - Sauvegarder

2. **Lors d'un import URL**
   - La description est extraite automatiquement
   - Vous pouvez la modifier avant de sauvegarder

---

## 🔐 Sécurité et configuration

### Prérequis
- ✅ Clé API Groq configurée dans `.env` : `GROQ_API_KEY=...`
- ✅ Python 3.9+
- ✅ Dépendances : `requests`, `beautifulsoup4`

### Limites de l'API Groq
- 1000 requêtes/minute (Free tier)
- 12000 tokens/minute
- Le service affiche un message si la clé API n'est pas configurée

---

## 📞 Support

### En cas de problème

1. **Vérifier les logs**
   ```bash
   docker logs recette-app --tail 100
   ```

2. **Vérifier la configuration**
   ```bash
   ssh christianepp@192.168.1.154
   cd /volume1/docker/recette
   cat .env | grep GROQ_API_KEY
   ```

3. **Tester l'API**
   ```bash
   curl http://192.168.1.154:8000/api/translation/status
   ```

4. **Rollback si nécessaire** (voir section Rollback ci-dessus)

---

## ✨ Améliorations futures (optionnel)

- [ ] Support d'images dans l'import URL
- [ ] Historique des imports
- [ ] Détection automatique de la langue source
- [ ] Import batch (plusieurs URLs)
- [ ] Suggestions de recettes similaires basées sur l'IA

---

**Déploiement préparé par**: Claude
**Date de livraison**: 2025-12-09
**Version**: V1.11
