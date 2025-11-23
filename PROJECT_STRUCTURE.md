# Structure du Projet Recette

## Vue d'ensemble

```
Recette/
├── app/                    # Code source de l'application
│   ├── models/            # Modèles de base de données
│   ├── routes/            # Routes FastAPI
│   ├── services/          # Services métier
│   └── templates/         # Templates Jinja2
│
├── data/                  # Fichiers de données
│   └── recette.sqlite3   # Base de données SQLite
│
├── migrations/            # Migrations de base de données
│   ├── *.sql             # Scripts SQL de migration
│   └── *.md              # Documentation des migrations
│
├── static/               # Fichiers statiques (images, CSS, JS)
│   └── uploads/         # Images uploadées
│
├── tests/                # Tests unitaires et d'intégration
│   ├── test_*.py        # Tests
│   └── verify_*.py      # Scripts de vérification
│
├── scripts/              # Scripts utilitaires
│   ├── apply_*.py       # Scripts d'application de migrations
│   └── init_db.py       # Initialisation de la base de données
│
├── deploy/               # Scripts de déploiement
│   ├── deploy*.sh       # Scripts de déploiement
│   ├── start_recette.sh # Démarrage de l'application
│   ├── stop_recette.sh  # Arrêt de l'application
│   └── recette.service  # Service systemd
│
├── docs/                 # Documentation
│   ├── AUTH_SETUP.md
│   ├── BUDGET_IMPLEMENTATION.md
│   ├── INGREDIENT_CATALOG_IMPLEMENTATION.md
│   └── TEST_GUIDE.md
│
├── logs/                 # Logs de l'application
│
├── venv/                 # Environnement virtuel Python
│
├── config.py            # Configuration de l'application
├── main.py              # Point d'entrée de l'application
├── requirements.txt     # Dépendances Python
└── README.md            # Documentation principale

```

## Fichiers à la racine

- **config.py**: Configuration centralisée (chemins, base de données, etc.)
- **main.py**: Point d'entrée FastAPI
- **init_db.py**: Script d'initialisation de la base de données
- **requirements.txt**: Dépendances Python
- **.env**: Variables d'environnement (non versionné)
- **.gitignore**: Fichiers à ignorer par Git

## Répertoires principaux

### `/app` - Code source
Contient tout le code de l'application FastAPI:
- Routes pour les recettes, événements, catalogue
- Modèles de base de données
- Services métier (importateur de recettes, etc.)
- Templates HTML

### `/migrations` - Base de données
Scripts SQL pour les migrations de schéma:
- `add_unit_conversions.sql`: Système de conversion d'unités
- `make_catalog_bilingual.sql`: Catalogue bilingue FR/JP
- Documentation des migrations

### `/tests` - Tests
Tous les fichiers de test et vérification:
- Tests unitaires
- Tests d'intégration
- Scripts de vérification des fonctionnalités

### `/scripts` - Utilitaires
Scripts d'administration et maintenance:
- Application de migrations
- Initialisation de la base de données
- Scripts de maintenance

### `/deploy` - Déploiement
Tout ce qui concerne le déploiement:
- Scripts de déploiement Synology
- Service systemd
- Scripts start/stop

### `/docs` - Documentation
Documentation technique et guides:
- Guides d'implémentation
- Documentation de configuration
- Guides de test

## Commandes utiles

### Développement
```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Initialiser la base de données
python init_db.py

# Démarrer l'application
python main.py
```

### Tests
```bash
# Lancer tous les tests
python -m pytest tests/

# Test spécifique
python tests/test_unit_conversion.py
```

### Migrations
```bash
# Appliquer une migration
sqlite3 data/recette.sqlite3 < migrations/add_unit_conversions.sql

# Ou utiliser le script
python scripts/apply_budget_migration.py
```

### Déploiement
```bash
# Déployer sur Synology
./deploy/deploy_synology.sh

# Démarrer le service
./deploy/start_recette.sh

# Arrêter le service
./deploy/stop_recette.sh
```

## Bonnes pratiques

1. **Migrations**: Toujours créer un script SQL dans `/migrations` pour les changements de schéma
2. **Tests**: Ajouter des tests dans `/tests` pour toute nouvelle fonctionnalité
3. **Documentation**: Documenter les nouvelles fonctionnalités dans `/docs`
4. **Scripts**: Les scripts utilitaires vont dans `/scripts`, pas à la racine
5. **Logs**: Les logs sont automatiquement créés dans `/logs`
