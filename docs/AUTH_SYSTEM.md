# Système d'authentification multi-utilisateur

## Vue d'ensemble

Le système d'authentification a été implémenté pour remplacer l'ancien système à mot de passe partagé. Il permet désormais à chaque utilisateur d'avoir son propre compte avec username, email et mot de passe.

## Architecture

### Base de données

**Nouvelle table `user`** ([migrations/add_user_system.sql](../migrations/add_user_system.sql))
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    is_active INTEGER DEFAULT 1,
    is_admin INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

**Colonnes ajoutées aux tables existantes:**
- `recipe.user_id` : Propriétaire de la recette
- `event.user_id` : Propriétaire de l'événement
- `ingredient_price_catalog.created_by` : Créateur du prix

### Module de gestion des utilisateurs

**Fichier:** [app/models/db_users.py](../app/models/db_users.py)

**Fonctions principales:**
- `hash_password(password)` : Hash un mot de passe avec bcrypt
- `verify_password(password, hash)` : Vérifie un mot de passe
- `create_user(username, email, password, ...)` : Crée un utilisateur
- `authenticate_user(username_or_email, password)` : Authentifie un utilisateur
- `get_user_by_id(user_id)` : Récupère un utilisateur par ID
- `get_user_by_username(username)` : Récupère un utilisateur par username
- `get_user_by_email(email)` : Récupère un utilisateur par email
- `list_users()` : Liste tous les utilisateurs
- `update_user_password(user_id, new_password)` : Change le mot de passe
- `deactivate_user(user_id)` : Désactive un utilisateur
- `activate_user(user_id)` : Réactive un utilisateur

### Routes d'authentification

**Fichier:** [app/routes/auth_routes.py](../app/routes/auth_routes.py)

#### GET `/login`
Affiche le formulaire de connexion avec:
- Champ username ou email
- Champ mot de passe
- Lien vers la page d'inscription
- Sélecteur de langue (FR/JP)
- Toggle mode sombre

#### POST `/login`
Authentifie l'utilisateur et crée une session avec:
- `user_id` : ID de l'utilisateur
- `username` : Nom d'utilisateur
- `is_admin` : Statut administrateur
- `authenticated` : Flag d'authentification

#### GET `/register`
Affiche le formulaire d'inscription avec:
- Champ username (3+ caractères, alphanumériques)
- Champ email (validé)
- Champ nom d'affichage (optionnel)
- Champ mot de passe (6+ caractères)
- Champ confirmation de mot de passe
- Validation JavaScript pour vérifier la correspondance des mots de passe

#### POST `/register`
Crée un nouveau compte utilisateur et connecte automatiquement l'utilisateur.

#### GET `/logout`
Détruit la session et redirige vers la page de login.

#### GET `/profile`
Affiche le profil de l'utilisateur connecté avec:
- Username
- Email
- Nom d'affichage
- Badge Admin (si applicable)
- Date de création du compte
- Dernière connexion
- Boutons pour retourner aux recettes ou se déconnecter

### Middleware d'authentification

**Fichier:** [app/middleware/auth.py](../app/middleware/auth.py)

Protège toutes les routes sauf:
- `/login`
- `/register`
- `/static/*`
- `/health`
- `/robots.txt`

Si l'utilisateur n'est pas authentifié (`request.session.get("authenticated") == False`), il est redirigé vers `/login`.

### Templates

#### [app/templates/login.html](../app/templates/login.html)
- Design moderne avec Tailwind CSS
- Mode sombre/clair
- Support FR/JP
- Champs username et password
- Lien vers inscription
- Messages d'erreur

#### [app/templates/register.html](../app/templates/register.html)
- Formulaire complet d'inscription
- Validation côté client des mots de passe
- Pattern HTML5 pour le username
- Messages d'erreur
- Lien vers connexion

#### [app/templates/profile.html](../app/templates/profile.html)
- Affichage des informations utilisateur
- Badge admin
- Boutons d'action (retour, déconnexion)

#### [app/templates/base.html](../app/templates/base.html) (modifié)
Ajout dans le footer de la sidebar:
- Bloc utilisateur avec username et badge admin
- Lien vers le profil
- Bouton de déconnexion

## Sécurité

### Hashing des mots de passe
- **Algorithme:** bcrypt avec salt automatique
- **Fonction:** `bcrypt.hashpw(password, salt)`
- **Vérification:** `bcrypt.checkpw(password, hash)`

### Protection SQL Injection
- Toutes les requêtes utilisent des paramètres préparés (`?` placeholders)
- Aucune interpolation de chaînes dans les requêtes SQL

### Session management
- Sessions FastAPI avec secret key
- Cookie sécurisé `recette_session`
- Durée: 24 heures
- Données stockées: `user_id`, `username`, `is_admin`, `authenticated`

### Validation des données
- Email: Pattern HTML5 + contrainte CHECK en base
- Username: 3-50 caractères, alphanumériques + `-` et `_`
- Mot de passe: 6+ caractères minimum
- Mots de passe confirmés côté client

## Utilisateur par défaut

**Username:** `admin`
**Email:** `admin@recette.local`
**Password:** `admin123`
**Admin:** Oui

⚠️ **IMPORTANT:** Changer le mot de passe après le premier déploiement!

## Tests

**Fichier:** [test_auth.py](../test_auth.py)

Lance 4 tests:
1. Connexion avec username
2. Connexion avec email
3. Rejet avec mauvais mot de passe
4. Création de nouveau compte

Exécution:
```bash
python test_auth.py
```

## Migration

La migration a été appliquée avec:
```bash
sqlite3 data/recette.db < migrations/add_user_system.sql
```

Toutes les données existantes ont été automatiquement assignées à l'utilisateur admin (ID: 1).

## Prochaines étapes

### Filtrage par utilisateur
Actuellement, tous les utilisateurs voient toutes les recettes et événements. Il faudra:

1. **Filtrer les listes par user_id:**
   - `GET /recipes` : Afficher uniquement `recipe.user_id = current_user_id`
   - `GET /events` : Afficher uniquement `event.user_id = current_user_id`

2. **Vérifier les permissions:**
   - Empêcher la modification de recettes/événements d'autres utilisateurs
   - Ajouter des checks dans les routes PUT/DELETE

3. **Partage optionnel:**
   - Ajouter un flag `recipe.is_public` pour partager des recettes
   - Permettre aux admins de tout voir/modifier

### Interface d'administration
- Page `/admin/users` pour gérer les utilisateurs (admins uniquement)
- Activer/désactiver des comptes
- Réinitialiser des mots de passe
- Promouvoir/rétrograder des admins

### Amélioration UX
- Liens "Mot de passe oublié?" avec reset par email
- Avatar utilisateur personnalisable
- Préférences utilisateur (langue par défaut, thème par défaut)

## Déploiement en production

### Configuration
Dans [config.py](../config.py), s'assurer que:
```python
REQUIRE_PASSWORD = True  # Activer la protection
SECRET_KEY = "clé_secrète_forte_et_unique"  # Générer avec secrets.token_hex(32)
```

### Checklist
- ✅ Changer le mot de passe admin
- ✅ Générer une nouvelle SECRET_KEY
- ✅ Sauvegarder la base de données
- ⏳ Ajouter le filtrage par user_id
- ⏳ Mettre en place les permissions
- ⏳ Tester tous les scénarios d'authentification

## Support

Pour toute question ou problème, consulter:
- [Documentation principale](README.md)
- [Notes de déploiement v1.4](DEPLOY_v1.4.md)
- Issues GitHub du projet
