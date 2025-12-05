# Documentation Recette App

Documentation complète du projet Recette.

## 📁 Structure de la documentation

```
docs/
├── project/              # Documentation du projet
│   ├── TODO.md          # Liste des tâches et évolutions futures
│   └── DEPLOYMENT_CHECKLIST.md  # Checklist de déploiement
│
├── deployment/           # Notes de déploiement
│   ├── DEPLOYMENT.md    # Guide général de déploiement
│   ├── NOTES_DEPLOIEMENT_V1_3.md
│   ├── NOTES_DEPLOIEMENT_V1_4.md
│   ├── NOTES_DEPLOIEMENT_V1_5.md
│   └── README.md
│
├── help/                 # Documentation de l'aide en ligne
│   └── README.md        # Guide modification page d'aide
│
└── [fichiers techniques]
```

## 📋 Documentation projet

### [TODO.md](project/TODO.md)
Liste structurée de toutes les tâches et évolutions futures:
- Amélioration aide en ligne
- Nouvelles fonctionnalités recettes
- Évolutions budget
- Backlog des idées

### [DEPLOYMENT_CHECKLIST.md](project/DEPLOYMENT_CHECKLIST.md)
Checklist complète pour chaque déploiement:
- Étapes avant/pendant/après développement
- Préparation du déploiement
- Tests post-déploiement
- Procédure de rollback

## 🚀 Documentation déploiement

### [DEPLOYMENT.md](deployment/DEPLOYMENT.md)
Guide général de déploiement sur Synology.

### Notes de déploiement par version
- [V1.3](deployment/NOTES_DEPLOIEMENT_V1_3.md) - Base de données intégrée
- [V1.4](deployment/NOTES_DEPLOIEMENT_V1_4.md) - Catalogue des prix
- [V1.5](deployment/NOTES_DEPLOIEMENT_V1_5.md) - Système d'authentification

## 📖 Documentation fonctionnelle

### Système d'authentification
- [AUTH_SYSTEM.md](AUTH_SYSTEM.md) - Documentation complète du système d'authentification
- [AUTH_SETUP.md](AUTH_SETUP.md) - Configuration initiale

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

### Corrections et améliorations
- [CORRECTION_FORMS.md](CORRECTION_FORMS.md) - Corrections formulaires
- [NEXT_STEPS.md](NEXT_STEPS.md) - Prochaines étapes

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
1. **À chaque nouvelle fonctionnalité** → Mettre à jour le fichier concerné
2. **À chaque déploiement** → Créer/mettre à jour NOTES_DEPLOIEMENT_V{X}_{Y}.md
3. **À chaque modification majeure** → Réviser la documentation technique

Voir `project/DEPLOYMENT_CHECKLIST.md` pour le processus complet.

---

**Dernière mise à jour**: Version 1.6 - Décembre 2024
