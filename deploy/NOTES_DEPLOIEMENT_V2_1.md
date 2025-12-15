# Notes de Déploiement - Version 2.1

**Date**: Décembre 2024
**Version**: 2.1 (Major Update)
**Script**: `deploy_synology_V2_1.sh`

## 🎯 Résumé

Version majeure introduisant un système complet de gestion des participants et groupes avec isolation multi-utilisateurs, refonte de l'interface de connexion, et améliorations UX diverses.

## ✨ Nouvelles Fonctionnalités

### 1. Système de Participants
- Gestion de participants (personnes non-utilisateurs de l'app)
- Champs : nom, prénom, rôle, téléphone, email, adresse
- Page d'index avec liste et recherche
- Page de détail pour chaque participant
- CRUD complet (création, modification, suppression)

### 2. Système de Groupes
- Création de groupes de participants (ex: "Famille Dupont", "Amis du club")
- Liaison many-to-many : un participant peut être dans plusieurs groupes
- Gestion bidirectionnelle : ajouter/retirer participants depuis le groupe ou depuis le participant
- Page d'index avec liste des groupes
- Page de détail avec gestion des membres

### 3. Participants pour les Événements
- Bouton "Participants" sur la page de détail d'événement
- Modal dual-list intuitive :
  - **Colonne gauche** : Ajouter participants individuellement ou par groupe entier
  - **Colonne droite** : Liste des participants inscrits avec possibilité de retrait
- Indication si participant ajouté individuellement ou via un groupe
- Ajout/retrait en temps réel (AJAX)

### 4. Isolation Multi-utilisateurs
- Chaque utilisateur voit uniquement ses propres participants/groupes
- Exception : l'admin voit tout
- Colonnes `user_id` ajoutées à `participant` et `participant_group`
- Index pour performances optimales

### 5. Nouveau Template de Connexion
- Remplacement de `login.html` par `recette_connexion.html`
- Design moderne et épuré
- Toggle pour afficher/masquer le mot de passe
- Mode sombre intégré
- Sélecteur de langue FR/JP

### 6. Persistance des Filtres (Recipes List)
- Les filtres (catégories, tags, créateur, tri) sont maintenant dans l'URL
- Navigation entre recettes et retour conserve les filtres actifs
- Fonction `updateURL()` en Alpine.js
- Amélioration de l'UX pour la navigation

### 7. Import de Recettes par URL
- Nouvelle option d'import dans `import_recipes.html`
- Grid passé de 2 à 3 colonnes (CSV, JSON, URL)
- Icône 🔗 pour l'import URL

## 📁 Fichiers Modifiés

### Backend (Python)
- `app/routes/auth_routes.py` - Utilisation du nouveau template connexion
- `app/routes/event_routes.py` - Ajout données participants/groupes
- `app/routes/participant_routes.py` - **NOUVEAU** Routes CRUD participants/groupes
- `app/models/db_participants.py` - **NOUVEAU** Logique DB participants/groupes
- `app/models/__init__.py` - Import du nouveau module

### Frontend (Templates)
- `app/templates/recette_connexion.html` - **NOUVEAU** Template connexion moderne
- `app/templates/event_detail.html` - Modal gestion participants (164 lignes ajoutées)
- `app/templates/participants_index.html` - **NOUVEAU** Liste participants/groupes
- `app/templates/participant_detail.html` - **NOUVEAU** Détail participant
- `app/templates/group_detail.html` - **NOUVEAU** Détail groupe
- `app/templates/base.html` - Fix session `user_id` au lieu de `authenticated`
- `app/templates/recipes_list.html` - Persistance filtres URL
- `app/templates/import_recipes.html` - Ajout option import URL

### Migrations
- `migrations/add_participants_and_groups.sql` - **NOUVEAU** Tables participants/groupes
- `migrations/add_user_id_to_participants.sql` - **NOUVEAU** Colonnes user_id

### Assets
- `app/static/css/alpine.min.js` - **NOUVEAU** Framework JS réactif
- `app/static/css/tailwind.min.js` - **NOUVEAU** Framework CSS (CDN → local)

### Documentation
- `docs/PARTICIPANTS_GROUPS_SYSTEM.md` - **NOUVEAU** Doc complète système
- `docs/README.md` - Mise à jour structure et liens
- `docs/AUTH_SYSTEM.md` - Référence au nouveau template

### Configuration
- `.gitignore` - Ajout exclusions `data/*.db`, `data/*.csv`, script V2_1
- `deploy/deploy_synology_V2_1.sh` - **NOUVEAU** Script de déploiement

### Fichiers Déplacés
- `liste_modifications.py` → `scripts/compare_dev_prod.py`
- `OPTIMISATION_SQL_V1.10.md` → `docs/`
- `RELEASE_NOTES_V1.9.md` → `docs/`
- `README.md` → `docs/` (restructuré)

### Fichiers Retirés du Tracking
- `data/recipes.db` - Désormais en .gitignore
- `data/Participants.csv` - Données personnelles

## 🗄️ Modifications de Base de Données

### Nouvelles Tables

#### `participant`
```sql
- id (PK)
- nom (NOT NULL)
- prenom
- role
- telephone
- email
- adresse
- user_id (FK → user.id)
- created_at
- updated_at
```

#### `participant_group`
```sql
- id (PK)
- nom (UNIQUE, NOT NULL)
- description
- user_id (FK → user.id)
- created_at
- updated_at
```

#### `participant_group_member`
```sql
- id (PK)
- participant_id (FK → participant.id)
- group_id (FK → participant_group.id)
- created_at
- UNIQUE(participant_id, group_id)
```

#### `event_participant`
```sql
- id (PK)
- event_id (FK → event.id)
- participant_id (FK → participant.id)
- added_via_group_id (FK → participant_group.id, nullable)
- created_at
- UNIQUE(event_id, participant_id)
```

### Index Créés
- `idx_participant_nom`
- `idx_participant_email`
- `idx_participant_user_id`
- `idx_participant_group_nom`
- `idx_participant_group_user_id`
- `idx_pgm_participant`
- `idx_pgm_group`
- `idx_ep_event`
- `idx_ep_participant`
- `idx_ep_group`

## 📋 Procédure de Déploiement

### Pré-requis
- Version actuelle : V1.5+ (avec système d'authentification)
- Accès SSH au Synology
- Base de données SQLite fonctionnelle

### Étapes Automatisées (par le script)

1. **Préparation Archive**
   - Exclusion de `data/`, `.git`, `venv`, etc.
   - Archive : `/tmp/recette_v2_1_deploy.tar.gz`

2. **Transfert SSH**
   - Upload vers `~/recette/` sur Synology

3. **Backup BDD**
   - Création : `backups/recette_pre_v2_1_YYYYMMDD_HHMMSS.sqlite3`
   - Vérification intégrité (`PRAGMA integrity_check`)

4. **Arrêt Application**
   - Exécution `stop_recette.sh`
   - Pause 2 secondes

5. **Déploiement Fichiers**
   - Backup ancien code : `backups/code_backup_YYYYMMDD_HHMMSS/`
   - Extraction archive
   - Copie `.env.example` → `.env` si nécessaire

6. **Installation Dépendances**
   - `pip install --upgrade pip`
   - `pip install -r requirements.txt`

7. **Migrations BDD** (2 étapes)
   - Migration 1 : `add_participants_and_groups.sql`
   - Migration 2 : `add_user_id_to_participants.sql`
   - Vérifications post-migration automatiques

8. **Redémarrage Application**
   - Exécution `start_recette.sh`
   - Vérification processus `uvicorn`

### Commande de Déploiement
```bash
cd /Users/christianepp/Documents/DEV/Recette
./deploy/deploy_synology_V2_1.sh
```

## ✅ Tests Post-Déploiement

### Test 1 : Connexion
- [ ] Accéder à http://recipe.e2pc.fr/login
- [ ] Vérifier le nouveau design
- [ ] Tester toggle mot de passe
- [ ] Tester switch FR/JP
- [ ] Se connecter avec succès

### Test 2 : Participants
- [ ] Accéder à `/participants`
- [ ] Créer un nouveau participant (ex: "Dupont Jean")
- [ ] Vérifier que le participant apparaît dans la liste
- [ ] Cliquer sur le participant → page de détail
- [ ] Modifier les informations
- [ ] Vérifier la sauvegarde

### Test 3 : Groupes
- [ ] Dans `/participants`, créer un groupe (ex: "Famille")
- [ ] Ajouter 2-3 participants au groupe
- [ ] Vérifier que les participants apparaissent dans le groupe
- [ ] Depuis un participant, vérifier qu'il voit ses groupes
- [ ] Retirer un participant du groupe
- [ ] Vérifier la cohérence

### Test 4 : Événements
- [ ] Ouvrir un événement existant
- [ ] Cliquer sur "Participants (0)"
- [ ] Modal s'ouvre correctement
- [ ] Ajouter un participant individuellement
- [ ] Compteur passe à "Participants (1)"
- [ ] Ajouter un groupe de 3 personnes
- [ ] Vérifier que tous apparaissent avec "via groupe: [nom]"
- [ ] Retirer un participant individuel (instantané)
- [ ] Retirer un participant de groupe (rechargement)

### Test 5 : Isolation Multi-utilisateurs
- [ ] Créer un 2e compte utilisateur
- [ ] Se connecter avec ce compte
- [ ] Aller sur `/participants`
- [ ] Vérifier liste vide (ne voit pas les participants de l'autre user)
- [ ] Créer un participant
- [ ] Se reconnecter avec le 1er compte
- [ ] Vérifier que ce participant n'apparaît pas
- [ ] Se connecter avec admin
- [ ] Vérifier qu'admin voit TOUS les participants

### Test 6 : Persistance Filtres
- [ ] Aller sur `/recipes`
- [ ] Appliquer des filtres (catégorie, tag, recherche)
- [ ] Noter l'URL (contient les paramètres)
- [ ] Cliquer sur une recette
- [ ] Revenir en arrière
- [ ] Vérifier que les filtres sont toujours actifs

### Test 7 : Import URL
- [ ] Aller sur `/import`
- [ ] Vérifier présence de la 3e option "Import URL"
- [ ] Cliquer dessus
- [ ] Vérifier redirection vers `/import-url`

## 🔄 Procédure de Rollback

En cas de problème majeur :

```bash
# Se connecter au Synology
ssh admin@192.168.1.14

# Aller dans le dossier
cd recette

# Arrêter l'application
bash stop_recette.sh

# Restaurer la base de données
cp backups/recette_pre_v2_1_*.sqlite3 data/recette.sqlite3

# Restaurer le code (si nécessaire)
# rm -rf app/
# cp -r backups/code_backup_YYYYMMDD_HHMMSS/app/ ./

# Redémarrer
bash start_recette.sh
```

## 🐛 Problèmes Connus & Solutions

### Problème 1 : Alpine.js ou Tailwind ne se charge pas
**Symptômes** : Modal ne fonctionne pas, styles cassés
**Solution** : Vérifier que `app/static/css/alpine.min.js` et `tailwind.min.js` sont présents

### Problème 2 : Erreur "table participant already exists"
**Cause** : Migration déjà exécutée
**Solution** : Normal si re-déploiement, les `CREATE TABLE IF NOT EXISTS` gèrent cela

### Problème 3 : Participants vides pour tous les utilisateurs
**Cause** : Colonne `user_id` NULL
**Solution** : Vérifier migration `add_user_id_to_participants.sql` exécutée

### Problème 4 : Admin ne voit pas tous les participants
**Cause** : Vérification username incorrect
**Solution** : Vérifier que `db.list_participants(is_admin=True)` fonctionne

## 📊 Statistiques

- **Commits inclus** : 10+ commits depuis V1.5
- **Lignes de code ajoutées** : ~1500+
- **Nouveaux fichiers** : 10+
- **Migrations SQL** : 2
- **Nouvelles tables** : 4
- **Index créés** : 10

## 🔗 Commits Inclus

```
8d7d3ad - Fix: Utilisation correcte de la session (user_id au lieu de user)
148c581 - Feature: Gestion multi-utilisateurs participants et groupes
985adb4 - Fix: Ajout Alpine.js et Tailwind + Améliorations UX participants
bea628a - Amélioration UI: Interface dual-list pour sélection groupes/participants
7cdfb73 - Frontend: Gestion bidirectionnelle participants ↔ groupes dans les modales
e7d7676 - Backend: Ajout gestion bidirectionnelle participants ↔ groupes
718bd9a - Fix: Correction des boutons modifier participants/groupes
e252941 - Fix: Ajout commit explicite pour add_participant_to_group
e488770 - Fix: Correction des fonctions de mise à jour participants/groupes
fa2abb5 - Ajout templates de détail participants et groupes
d9ddfbb - Ajout de la gestion des participants et groupes (V1.12 - Base)
```

## 📚 Documentation Associée

- [PARTICIPANTS_GROUPS_SYSTEM.md](../docs/PARTICIPANTS_GROUPS_SYSTEM.md) - Documentation complète
- [AUTH_SYSTEM.md](../docs/AUTH_SYSTEM.md) - Système d'authentification
- [README.md](../docs/README.md) - Index de la documentation

## 🎓 Notes pour les Développeurs

### Ajout d'un Participant en Code
```python
from app.models.db_participants import add_participant

participant_id = add_participant(
    nom="Dupont",
    prenom="Jean",
    role="Invité",
    user_id=current_user_id
)
```

### Ajout d'un Groupe en Code
```python
from app.models.db_participants import create_group, add_participant_to_group

group_id = create_group(nom="Famille Dupont", user_id=current_user_id)
add_participant_to_group(group_id, participant_id)
```

### Ajouter un Groupe à un Événement
```python
from app.models.db_participants import add_group_to_event

add_group_to_event(event_id=123, group_id=456)
# Ajoute automatiquement tous les membres du groupe
```

---

**Déployé par** : Claude Code
**Dernière mise à jour** : Décembre 2024
