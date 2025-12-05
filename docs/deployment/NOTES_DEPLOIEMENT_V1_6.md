# Notes de Déploiement - Version 1.6

**Date**: 2025-12-04
**Version**: 1.6
**Commit**: 8fe57aa

## Nouvelles Fonctionnalités

### 🥕 Recherche par Ingrédients
- Interface de recherche dans la liste des recettes
- Support multi-ingrédients (ex: "tomate, basilic, mozzarella")
- Logique ET: trouve uniquement les recettes contenant TOUS les ingrédients
- Nouvelle fonction: `search_recipes_by_ingredients()` dans `db_recipes.py`
- Nouveau endpoint API: `/api/recipes/search-by-ingredients`

### 📅 Événements Multi-jours
- Gestion complète des événements sur plusieurs jours
- Champs: `date_debut`, `date_fin`, `nombre_jours`
- Sélection des dates travaillées (possibilité de désélectionner certains jours)
- Interface de sélection des dates dans le formulaire d'événement

### 📋 Organisation & Planification
- **Vue Organisation** (`/events/{id}/organization`): Affichage lecture seule des recettes par jour
- **Vue Planification** (`/events/{id}/planning`): Interface drag & drop pour assigner les recettes aux dates
- Défilement indépendant des colonnes
- Nouvelles tables: `event_date`, `event_recipe_planning`

### 🛒 Amélioration Liste de Courses
- Auto-génération de la liste si vide lors de l'accès au budget
- Ajustement automatique lors du changement du nombre de participants

## Fichiers Modifiés

### Modèles
- `app/models/__init__.py` - Ajout des nouvelles fonctions
- `app/models/db_recipes.py` - Fonction `search_recipes_by_ingredients()`
- `app/models/db_events.py` - Fonctions multi-jours: `save_event_dates()`, `get_event_dates()`, `save_recipe_planning()`, `get_recipe_planning()`

### Routes
- `app/routes/recipe_routes.py` - Endpoint `/api/recipes/search-by-ingredients`
- `app/routes/event_routes.py` - Routes organization, planning, gestion multi-jours

### Templates
- `app/templates/recipes_list.html` - Interface de recherche par ingrédients
- `app/templates/event_form.html` - Sélection des dates multi-jours
- `app/templates/event_detail.html` - Lien vers organisation/planification
- `app/templates/event_organization.html` - **NOUVEAU** - Vue organisation
- `app/templates/event_planning.html` - **NOUVEAU** - Vue planification drag & drop

### Migration
- `migrations/add_event_multi_days.sql` - **NOUVEAU** - Migration base de données

## Procédure de Déploiement Manuel

### 1. Préparation Locale

L'archive a déjà été créée:
```bash
# Archive disponible: /tmp/recette_v1_6_deploy.tar.gz (7,8M)
```

### 2. Transfert vers le Synology

```bash
# Option A: Avec scp
scp /tmp/recette_v1_6_deploy.tar.gz admin@192.168.1.14:recette/

# Option B: Avec rsync
rsync -avz /tmp/recette_v1_6_deploy.tar.gz admin@192.168.1.14:recette/
```

### 3. Connexion SSH au Synology

```bash
ssh admin@192.168.1.14
cd recette
```

### 4. Backup de la Base de Données

```bash
mkdir -p backups
cp data/recette.sqlite3 backups/recette_pre_v1_6_$(date +%Y%m%d_%H%M%S).sqlite3
```

### 5. Arrêt de l'Application

```bash
bash stop_recette.sh
sleep 2
```

### 6. Backup du Code

```bash
BACKUP_DIR="backups/code_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r app "$BACKUP_DIR/"
```

### 7. Extraction des Fichiers

```bash
tar xzf recette_v1_6_deploy.tar.gz
rm recette_v1_6_deploy.tar.gz
```

### 8. Installation des Dépendances

```bash
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 9. Migration de la Base de Données

```bash
sqlite3 data/recette.sqlite3 < migrations/add_event_multi_days.sql
```

### 10. Vérification de la Migration

```bash
# Vérifier les nouvelles colonnes
sqlite3 data/recette.sqlite3 "PRAGMA table_info(event);" | grep -E "date_debut|date_fin|nombre_jours"

# Vérifier les nouvelles tables
sqlite3 data/recette.sqlite3 "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('event_date', 'event_recipe_planning');"
```

Sortie attendue:
```
date_debut
date_fin
nombre_jours
event_date
event_recipe_planning
```

### 11. Redémarrage de l'Application

```bash
bash start_recette.sh
sleep 3
ps aux | grep uvicorn
```

### 12. Nettoyage Local (sur Mac)

```bash
rm /tmp/recette_v1_6_deploy.tar.gz
```

## Tests Post-Déploiement

### 1. Recherche par Ingrédients
- [ ] Aller sur http://recipe.e2pc.fr/recipes?lang=fr
- [ ] Voir le bloc vert "Recherche par ingrédients"
- [ ] Tester avec un ingrédient: "tomate"
- [ ] Tester avec plusieurs: "tomate, oignon"
- [ ] Vérifier que seules les recettes avec TOUS les ingrédients sont affichées

### 2. Événements Multi-jours
- [ ] Créer un nouvel événement
- [ ] Sélectionner une date de début et une date de fin (ex: 5 jours)
- [ ] Vérifier que le nombre de jours se calcule automatiquement
- [ ] Désélectionner certains jours (ex: week-end)
- [ ] Sauvegarder et vérifier que les dates sont bien enregistrées

### 3. Organisation des Recettes
- [ ] Ouvrir un événement existant
- [ ] Ajouter quelques recettes à l'événement
- [ ] Cliquer sur "Organisation" dans le menu de l'événement
- [ ] Vérifier l'affichage des dates
- [ ] Cliquer sur "Créer la planification"

### 4. Planification Drag & Drop
- [ ] Dans la vue planification, voir les recettes disponibles à gauche
- [ ] Glisser-déposer une recette vers une date à droite
- [ ] Vérifier que la recette apparaît bien dans la date
- [ ] Glisser-déposer la recette vers une autre date
- [ ] Supprimer une recette d'une date (bouton X)
- [ ] Sauvegarder et retourner à l'organisation
- [ ] Vérifier que les recettes sont bien assignées aux dates

### 5. Liste de Courses Auto-générée
- [ ] Aller dans le budget d'un événement avec des recettes mais sans liste de courses
- [ ] Vérifier que la liste de courses a été auto-générée
- [ ] Modifier le nombre de participants
- [ ] Vérifier que les quantités sont ajustées

### 6. Compatibilité Ancien Système
- [ ] Vérifier les événements existants (créés avant V1.6)
- [ ] Vérifier qu'ils fonctionnent toujours normalement
- [ ] Les anciens événements devraient avoir date_debut = date_fin = event_date

## Migration Base de Données - Détails

### Nouvelles Colonnes dans `event`
```sql
ALTER TABLE event ADD COLUMN date_debut DATE;
ALTER TABLE event ADD COLUMN date_fin DATE;
ALTER TABLE event ADD COLUMN nombre_jours INTEGER DEFAULT 1;
```

### Nouvelle Table `event_date`
```sql
CREATE TABLE event_date (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    date DATE NOT NULL,
    is_selected BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES event(id) ON DELETE CASCADE
);
```

### Nouvelle Table `event_recipe_planning`
```sql
CREATE TABLE event_recipe_planning (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    recipe_id INTEGER NOT NULL,
    event_date_id INTEGER NOT NULL,
    position INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES event(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipe(id) ON DELETE CASCADE,
    FOREIGN KEY (event_date_id) REFERENCES event_date(id) ON DELETE CASCADE
);
```

## Rollback en Cas de Problème

Si un problème survient après le déploiement:

### 1. Restaurer la Base de Données
```bash
cd ~/recette
bash stop_recette.sh
cp backups/recette_pre_v1_6_*.sqlite3 data/recette.sqlite3
```

### 2. Restaurer le Code
```bash
rm -rf app
cp -r backups/code_backup_*/app ./
```

### 3. Redémarrer
```bash
bash start_recette.sh
```

## URLs de l'Application

- **Local**: http://192.168.1.14:8000
- **Public**: http://recipe.e2pc.fr
- **Login**: http://recipe.e2pc.fr/login

## Informations Techniques

### Architecture
- Backend: FastAPI + Python 3
- Frontend: Alpine.js + Tailwind CSS
- Base de données: SQLite3
- Serveur: Uvicorn

### Backups Automatiques
- Base de données: `~/recette/backups/recette_pre_v1_6_*.sqlite3`
- Code: `~/recette/backups/code_backup_*/`

## Notes Importantes

1. **Migration Automatique**: La migration des anciennes données se fait automatiquement
   - `event_date` → `date_debut` et `date_fin`
   - `nombre_jours` initialisé à 1 pour les événements existants

2. **Compatibilité**: Les anciennes fonctionnalités restent intactes
   - Événements sur un seul jour continuent de fonctionner
   - Aucun changement dans l'interface des recettes (sauf ajout de la recherche)

3. **Performance**:
   - Recherche par ingrédients optimisée avec index SQL
   - Drag & drop utilise Alpine.js (pas de rechargement de page)
   - Défilement indépendant pour une meilleure UX

## Support

En cas de problème:
1. Vérifier les logs: `~/recette/logs/`
2. Vérifier le processus: `ps aux | grep uvicorn`
3. Tester l'accès: `curl http://localhost:8000`
4. Consulter les backups: `ls -la ~/recette/backups/`

## Prochaines Améliorations Possibles

- [ ] Export de la planification en PDF
- [ ] Notifications pour les événements à venir
- [ ] Copie d'événements avec leur planification
- [ ] Filtres avancés dans la recherche par ingrédients (OU logique)
- [ ] Suggestions d'ingrédients pendant la saisie
