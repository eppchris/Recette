# Notes de déploiement - Version 1.5

**Date** : 3 décembre 2025
**Version** : 1.5
**Tag Git** : v1.5

---

## 🎯 Résumé des changements

Cette version apporte deux améliorations majeures :

### 🔐 Système d'authentification multi-utilisateur
- Chaque utilisateur a son propre compte (username, email, mot de passe)
- Pages de connexion, inscription et profil
- Gestion des rôles (admin/utilisateur standard)
- Hash sécurisé des mots de passe avec bcrypt
- Sessions sécurisées avec middleware d'authentification

### 🏗️ Refactoring de l'architecture
- Fichier monolithique `db.py` (3114 lignes) → 10 modules spécialisés
- Meilleure organisation du code par domaine fonctionnel
- Infrastructure de tests unitaires avec pytest
- Documentation complète du système

---

## ⚠️ IMPORTANT - Migration manuelle de la base de données

**Cette version nécessite une migration SQL que vous devez appliquer manuellement.**

### Pourquoi manuel ?
- Vous préférez faire un copier-coller direct de la base de données
- Cela évite les complications d'un script automatique
- Vous gardez le contrôle total sur la migration

---

## 📋 Procédure de déploiement

### 1. Sauvegarde de la base de données

**CRUCIAL** : Faites une copie de sauvegarde avant toute manipulation !

```bash
# Sur votre machine locale ou sur le serveur
cp data/recette.sqlite3 data/recette.sqlite3.backup-$(date +%Y%m%d-%H%M%S)
```

### 2. Récupération du code sur GitHub

```bash
# Pousser depuis votre machine locale
git push origin main

# Puis sur le serveur de production
cd ~/recette
git pull origin main
```

### 3. Installation des nouvelles dépendances

```bash
# Sur le serveur de production
cd ~/recette
source venv/bin/activate
pip install -r requirements.txt
```

**Nouvelles dépendances installées :**
- `bcrypt>=4.0.0` : Hash sécurisé des mots de passe
- `pytest>=7.4.0` : Framework de tests unitaires
- `pytest-cov>=4.1.0` : Mesure de couverture de code
- `pytest-asyncio>=0.21.0` : Support des tests async
- `starlette[full]` : Sessions et middleware (peut-être déjà installé)

### 4. Migration de la base de données (MANUEL)

**Option A - Avec sqlite3 en ligne de commande**

```bash
# Sur le serveur de production
cd ~/recette
sqlite3 data/recette.sqlite3 < migrations/add_user_system.sql
```

**Option B - Copier-coller SQL directement**

```bash
# Ouvrir SQLite
sqlite3 data/recette.sqlite3
```

Puis copier-coller le contenu suivant :

```sql
-- ============================================================================
-- Table des utilisateurs
-- ============================================================================

CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    is_active INTEGER DEFAULT 1,
    is_admin INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    CONSTRAINT email_format CHECK (email LIKE '%@%')
);

CREATE INDEX IF NOT EXISTS idx_user_username ON user(username);
CREATE INDEX IF NOT EXISTS idx_user_email ON user(email);

-- ============================================================================
-- Ajouter user_id aux tables existantes
-- ============================================================================

-- Recettes
ALTER TABLE recipe ADD COLUMN user_id INTEGER REFERENCES user(id);
CREATE INDEX IF NOT EXISTS idx_recipe_user ON recipe(user_id);

-- Événements
ALTER TABLE event ADD COLUMN user_id INTEGER REFERENCES event(id);
CREATE INDEX IF NOT EXISTS idx_event_user ON event(user_id);

-- Catalogue de prix
ALTER TABLE ingredient_price_catalog ADD COLUMN created_by INTEGER REFERENCES user(id);

-- ============================================================================
-- Utilisateur admin par défaut
-- ============================================================================
-- Username: admin
-- Email: admin@recette.local
-- Password: admin123 (⚠️ À CHANGER APRÈS LE DÉPLOIEMENT !)
-- Hash bcrypt: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eDzNq3tJZ7Wy

INSERT OR IGNORE INTO user (id, username, email, password_hash, display_name, is_admin)
VALUES (
    1,
    'admin',
    'admin@recette.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eDzNq3tJZ7Wy',
    'Administrateur',
    1
);

-- ============================================================================
-- Assigner les données existantes à l'admin
-- ============================================================================

UPDATE recipe SET user_id = 1 WHERE user_id IS NULL;
UPDATE event SET user_id = 1 WHERE user_id IS NULL;
UPDATE ingredient_price_catalog SET created_by = 1 WHERE created_by IS NULL;
```

Puis taper `.quit` pour quitter SQLite.

### 5. Vérification de la migration

```bash
# Vérifier que la table user existe
sqlite3 data/recette.sqlite3 "SELECT COUNT(*) FROM user;"
# Devrait afficher : 1

# Vérifier l'utilisateur admin
sqlite3 data/recette.sqlite3 "SELECT username, email, is_admin FROM user WHERE id = 1;"
# Devrait afficher : admin|admin@recette.local|1

# Vérifier que les colonnes ont été ajoutées
sqlite3 data/recette.sqlite3 "PRAGMA table_info(recipe);" | grep user_id
sqlite3 data/recette.sqlite3 "PRAGMA table_info(event);" | grep user_id
```

### 6. Configuration de la SECRET_KEY

**IMPORTANT** : Générer une clé secrète unique pour les sessions.

```bash
# Générer une clé aléatoire
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copier la clé générée et l'ajouter dans votre fichier de configuration ou `.env` :

```bash
# Dans ~/recette/.env ou config.py
SECRET_KEY="la_cle_generee_ici"
```

### 7. Redémarrage de l'application

```bash
# Arrêter l'application
bash ~/recette/stop_recette.sh
# ou
pkill -f "uvicorn"

# Redémarrer l'application
bash ~/recette/start_recette.sh
# ou
cd ~/recette
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > recette.log 2>&1 &
```

---

## ✅ Tests post-déploiement

### 1. Vérifier la connexion
- Aller sur `http://recipe.e2pc.fr/login`
- ✅ La page de login s'affiche correctement
- ✅ Les styles sont chargés (Tailwind CSS)
- ✅ Le toggle langue FR/JP fonctionne

### 2. Se connecter avec l'admin par défaut
- **Username** : `admin`
- **Password** : `admin123`
- ✅ La connexion fonctionne
- ✅ Redirection vers `/recipes`

### 3. Vérifier le profil utilisateur
- Cliquer sur "Profil" dans la sidebar (en bas)
- ✅ Les informations s'affichent correctement
- ✅ Le badge "Admin" est visible

### 4. Tester l'inscription
- Se déconnecter
- Cliquer sur "S'inscrire"
- Créer un nouveau compte
- ✅ L'inscription fonctionne
- ✅ Connexion automatique après inscription

### 5. Vérifier les recettes et événements
- ✅ Les recettes existantes s'affichent
- ✅ Les événements existants s'affichent
- ✅ Toutes les fonctionnalités précédentes fonctionnent

### 6. Vérifier les logs
```bash
tail -f ~/recette/recette.log
```
- ✅ Pas d'erreurs critiques
- ✅ Les requêtes sont loggées

---

## 🔒 Sécurité - À FAIRE IMMÉDIATEMENT

### 1. Changer le mot de passe admin

```bash
# Option A - Via SQLite directement (hash bcrypt pour "nouveau_mot_de_passe")
python3 -c "import bcrypt; print(bcrypt.hashpw(b'nouveau_mot_de_passe', bcrypt.gensalt()).decode())"
# Copier le hash généré

sqlite3 data/recette.sqlite3 "UPDATE user SET password_hash = 'HASH_ICI' WHERE username = 'admin';"
```

**Option B - Via l'interface web (à implémenter)**
- Page profil → Changer le mot de passe (fonctionnalité future)

### 2. Vérifier la SECRET_KEY

```bash
# S'assurer qu'elle est unique et non publique
grep SECRET_KEY ~/recette/config.py
# ou
grep SECRET_KEY ~/recette/.env
```

---

## 🏗️ Architecture modulaire - Ce qui a changé

### Ancien système
```
app/models/
├── db.py (3114 lignes !)
└── recipe.py
```

### Nouveau système
```
app/models/
├── __init__.py              # Réexporte toutes les fonctions
├── db_core.py              # Connexion, normalisation (150 lignes)
├── db_recipes.py           # CRUD recettes (400 lignes)
├── db_translations.py      # Traductions (200 lignes)
├── db_events.py            # Événements (350 lignes)
├── db_shopping.py          # Listes de courses (250 lignes)
├── db_budget.py            # Budget (300 lignes)
├── db_catalog.py           # Catalogue (280 lignes)
├── db_conversions.py       # Conversions (220 lignes)
├── db_metadata.py          # Catégories/tags (180 lignes)
├── db_users.py             # Utilisateurs (150 lignes)
├── db_logging.py           # Logs (100 lignes)
└── README.md               # Documentation
```

### Compatibilité
✅ **100% compatible** - Tous les imports existants continuent de fonctionner :
```python
# Avant
from app.models.db import list_recipes, create_event

# Après (fonctionne toujours !)
from app.models import list_recipes, create_event
```

---

## 🧪 Tests unitaires

### Lancer les tests (optionnel)

```bash
# Sur votre machine locale
cd ~/Documents/DEV/Recette
pytest

# Avec couverture de code
pytest --cov=app

# Tests d'authentification
python test_auth.py
```

**Résultats attendus :**
- ✅ 23 tests dans `test_db_core.py` passent (normalisation)
- ⚠️ Certains tests peuvent échouer (schéma DB à mettre à jour)

---

## 📚 Documentation ajoutée

| Fichier | Description |
|---------|-------------|
| [docs/AUTH_SYSTEM.md](../docs/AUTH_SYSTEM.md) | Documentation complète du système d'authentification |
| [docs/GUIDE_TESTS.md](../docs/GUIDE_TESTS.md) | Guide d'utilisation de pytest |
| [app/models/README.md](../app/models/README.md) | Architecture modulaire des models |
| [deploy/NOTES_DEPLOIEMENT_V1_4.md](NOTES_DEPLOIEMENT_V1_4.md) | Notes précédentes (V1.4) |

---

## 🔄 Rollback (en cas de problème)

Si quelque chose ne fonctionne pas :

### 1. Restaurer la base de données

```bash
cd ~/recette
bash stop_recette.sh

# Restaurer la sauvegarde
cp data/recette.sqlite3.backup-YYYYMMDD-HHMMSS data/recette.sqlite3
```

### 2. Revenir à la version précédente

```bash
git checkout v1.4
pip install -r requirements.txt
bash start_recette.sh
```

---

## 🎯 Prochaines étapes (optionnelles)

### Court terme
1. 👥 **Filtrage par utilisateur** : Afficher seulement les recettes/événements de l'utilisateur connecté
2. 👨‍💼 **Interface d'administration** : Gérer les utilisateurs (activer/désactiver, réinitialiser mots de passe)
3. 📧 **Mot de passe oublié** : Reset par email

### Moyen terme
4. 💰 **Page catalogue des prix** : Interface pour gérer les prix des ingrédients
5. ⚙️ **Préférences utilisateur** : Langue/thème par défaut, avatar
6. 🧪 **Améliorer les tests** : Atteindre 80%+ de couverture de code

### Long terme
7. 📊 **Logs d'accès** : Statistiques d'utilisation
8. 🤖 **CI/CD** : Tests automatiques sur chaque commit
9. 📧 **Notifications** : Événements à venir, partage de recettes

---

## 📊 Statistiques de la version

- **Lignes ajoutées** : 4603
- **Lignes supprimées** : 3219
- **Fichiers modifiés** : 36
- **Nouveaux fichiers** : 18
- **Nouveaux modules** : 10
- **Tests unitaires** : 23+ tests
- **Dépendances** : +5

---

## 🆘 Support

### En cas de problème

1. **Consulter les logs**
   ```bash
   tail -f ~/recette/recette.log
   ```

2. **Vérifier la base de données**
   ```bash
   sqlite3 data/recette.sqlite3 "PRAGMA integrity_check;"
   ```

3. **Vérifier les permissions**
   ```bash
   ls -la ~/recette/data/recette.sqlite3
   # Doit être lisible/modifiable par l'utilisateur qui lance l'app
   ```

4. **Restaurer la sauvegarde** (voir section Rollback)

---

## ✅ Checklist de déploiement

- [ ] Sauvegarde de la base de données effectuée
- [ ] Code récupéré depuis GitHub (`git pull`)
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Migration SQL appliquée (table `user` créée)
- [ ] Vérification migration OK (table user existe)
- [ ] SECRET_KEY générée et configurée
- [ ] Application redémarrée
- [ ] Page de login accessible
- [ ] Connexion admin fonctionne (`admin` / `admin123`)
- [ ] Profil utilisateur s'affiche
- [ ] Recettes existantes visibles
- [ ] Événements existants visibles
- [ ] **Mot de passe admin changé** ⚠️ CRITIQUE !

---

**Déployé par** : Christian
**Date** : 3 décembre 2025
**Statut** : ✅ Prêt pour la production

---

## 🎉 Félicitations !

La version 1.5 apporte une base solide pour la gestion multi-utilisateur et une architecture modulaire qui facilitera grandement les évolutions futures.

**Bonnes pratiques de sécurité** :
- Changez le mot de passe admin immédiatement
- Utilisez une SECRET_KEY unique et forte
- Faites des sauvegardes régulières de la base de données
- Surveillez les logs pour détecter les activités suspectes

**Bonne continuation !** 🚀
