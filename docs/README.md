# Documentation Recette App

Documentation complète du projet Recette.

## 🚀 Démarrage rapide (DEV)
```bash
source venv/bin/activate && python run.py
```

## 📁 Structure de la documentation

```
docs/
├── deployment/           # Notes de déploiement
│   ├── DEPLOYMENT.md    # Guide général de déploiement
│   ├── NOTES_DEPLOIEMENT.md
│   └── README.md
│
├── help/                 # Documentation de l'aide en ligne
│   └── README.md        # Guide modification page d'aide
│
└── [fichiers techniques]
```

## 📋 Documentation par fonctionnalité

### Système d'authentification
- [AUTH_SYSTEM.md](AUTH_SYSTEM.md) - Documentation complète du système d'authentification
- [AUTH_SETUP.md](AUTH_SETUP.md) - Configuration initiale

### Gestion des événements et participants
- [PARTICIPANTS_GROUPS_SYSTEM.md](PARTICIPANTS_GROUPS_SYSTEM.md) - Système de gestion des participants et groupes (V1.6+)

### Gestion des données
- [BUDGET_IMPLEMENTATION.md](BUDGET_IMPLEMENTATION.md) - Système de budget
- [INGREDIENT_CATALOG_IMPLEMENTATION.md](INGREDIENT_CATALOG_IMPLEMENTATION.md) - Catalogue des prix
- [UNIT_CONVERSION_README.md](UNIT_CONVERSION_README.md) - Conversions d'unités
- [README_normalisation_ingredients.md](README_normalisation_ingredients.md) - Normalisation

### Système de tags et catégories
- [CATEGORIES_TAGS_README.md](CATEGORIES_TAGS_README.md) - Guide d'utilisation
- [SYSTEME_CATEGORIES_TAGS_COMPLET.md](SYSTEME_CATEGORIES_TAGS_COMPLET.md) - Documentation complète

### API et intégrations
- [PRICE_API_GUIDE.md](PRICE_API_GUIDE.md) - Guide d'utilisation API prix

## 🧪 Documentation technique

### Tests
- [GUIDE_TESTS.md](GUIDE_TESTS.md) - Guide complet des tests
- [TEST_GUIDE.md](TEST_GUIDE.md) - Guide de tests

### Architecture
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Structure du projet
- [REFACTORING_DB_MODULES.md](REFACTORING_DB_MODULES.md) - Refactoring des modules DB

### Notes de version
- [OPTIMISATION_SQL_V1.10.md](OPTIMISATION_SQL_V1.10.md) - Optimisations SQL
- [RELEASE_NOTES_V1.9.md](RELEASE_NOTES_V1.9.md) - Notes de version 1.9
- [LIVRAISON_V1.11_CALCUL_COUT_RECETTES.md](LIVRAISON_V1.11_CALCUL_COUT_RECETTES.md) - Calcul coûts recettes

## 🔧 Documentation pour développeurs

### Règles du projet
Voir [.claude/project-rules.md](../.claude/project-rules.md) pour:
- Règles critiques (ne pas démarrer l'app, .gitignore)
- Format des commits
- Conventions de nommage
- Templates et snippets

### Aide en ligne
Voir [help/README.md](help/README.md) pour modifier la page d'aide.

## 📚 Ressources externes

- **GitHub**: [eppchris/Recette](https://github.com/eppchris/Recette)
- **URL Production**: http://recipe.e2pc.fr
- **Framework**: FastAPI + Alpine.js + Tailwind CSS
- **Base de données**: SQLite3

## 🔄 Mise à jour de la documentation

La documentation doit être mise à jour:
1. **À chaque nouvelle fonctionnalité** → Créer/mettre à jour le fichier concerné
2. **À chaque déploiement** → Mettre à jour NOTES_DEPLOIEMENT.md
3. **À chaque modification majeure** → Réviser la documentation technique

Voir [.claude/project-rules.md](../.claude/project-rules.md) pour le processus complet.

---

**Dernière mise à jour**: Version 1.6 - Décembre 2024
