# Notes de déploiement - Version 1.4

**Date** : 1er décembre 2025
**Version** : 1.4
**Tag Git** : v1.4

---

## Résumé des changements

Cette version apporte la normalisation automatique des ingrédients et l'ajustement automatique des listes de courses lors du changement du nombre de participants.

### Nouvelles fonctionnalités

- ✅ **Normalisation automatique des ingrédients** : minuscules, sans accents, au singulier
- ✅ **Régénération automatique des listes de courses** : lors du changement du nombre de participants
- ✅ **Ajustement proportionnel des quantités** : basé sur le nombre de participants
- ✅ **Amélioration des filtres de recettes** : meilleur système de filtrage par types d'événements

### Modifications techniques

- Nouvelle fonction `normalize_ingredient_name()` dans `app/models/db.py`
- Nouvelle fonction `update_event_recipes_multipliers()` dans `app/models/db.py`
- Logique d'ajustement automatique dans `app/routes/event_routes.py`
- Script de migration `migrations/normalize_ingredients.py` pour normaliser les données existantes

---

## Procédure de déploiement

### Prérequis

- Accès SSH au Synology (admin@192.168.1.14)
- Les scripts `start_recette.sh` et `stop_recette.sh` dans ~/recette
- Un environnement virtuel Python configuré dans ~/recette/venv

### Commande de déploiement

Depuis votre machine locale, dans le dossier du projet :

```bash
./deploy/deploy_synology_V1_4.sh
```

### Étapes automatisées

Le script effectue automatiquement :

1. ✅ **Vérification** des fichiers requis
2. ✅ **Création** de l'archive (sans données sensibles)
3. ✅ **Transfert** via SSH vers le Synology
4. ✅ **Backup** de la base de données avec timestamp
5. ✅ **Arrêt** de l'application
6. ✅ **Déploiement** des nouveaux fichiers
7. ✅ **Installation** des dépendances
8. ✅ **Migration** de la base de données (normalisation des ingrédients)
9. ✅ **Redémarrage** de l'application

### Migration de la base de données

⚠️ **Important** : Cette version inclut une migration qui :
- Normalise tous les noms d'ingrédients existants
- Fusionne les doublons (ex: "Oeuf", "œuf", "œufs" → "oeuf")
- Demande confirmation avant d'appliquer les changements

Le script de déploiement exécute automatiquement cette migration avec l'option `echo "oui"` pour confirmer.

---

## Tests post-déploiement

### 1. Vérifier le catalogue de prix

```
URL: http://192.168.1.14:8000/ingredient-catalog
```

✅ Vérifier qu'il n'y a plus de doublons
✅ Vérifier que les noms sont normalisés (minuscules, sans accents)

### 2. Tester l'ajustement automatique

1. Créer ou sélectionner un événement
2. Ajouter des recettes et générer une liste de courses
3. Modifier le nombre de participants
4. ✅ Vérifier que la liste de courses se met à jour automatiquement
5. ✅ Vérifier que le budget se met à jour aussi

### 3. Tester les filtres de recettes

```
URL: http://192.168.1.14:8000/recipes
```

✅ Tester les filtres par type d'événement
✅ Vérifier que les badges s'affichent correctement

---

## Rollback

En cas de problème, restaurer la sauvegarde :

```bash
ssh admin@192.168.1.14
cd recette

# Lister les sauvegardes
ls -lh backups/

# Arrêter l'application
bash stop_recette.sh

# Restaurer la sauvegarde
cp backups/recette_YYYYMMDD_HHMMSS.sqlite3 data/recette.sqlite3

# Redémarrer
bash start_recette.sh
```

---

## URLs de l'application

- **Local** : http://192.168.1.14:8000
- **Public** : http://recipe.e2pc.fr

---

## Logs

Pour consulter les logs en temps réel :

```bash
ssh admin@192.168.1.14
tail -f recette/logs/recette.log
```

---

## Fichiers modifiés

### Code principal
- `app/models/db.py` : Ajout des fonctions de normalisation et de mise à jour des multiplicateurs
- `app/routes/event_routes.py` : Logique d'ajustement automatique lors du changement de participants
- `app/templates/recipes_list.html` : Amélioration des filtres par type d'événement

### Migrations
- `migrations/normalize_ingredients.py` : Script de normalisation des ingrédients existants

### Documentation
- `docs/DEPLOY_v1.4.md` : Guide de déploiement détaillé
- `deploy/NOTES_DEPLOIEMENT_V1_4.md` : Ces notes

---

## Compatibilité

✅ **Compatible** avec les données de la v1.3
✅ Migration **non destructive** (demande confirmation)
✅ Les anciennes listes de courses continuent de fonctionner
⚠️  Une fois normalisé, le retour en arrière nécessite une restauration de sauvegarde

---

## Performance

- La normalisation initiale prend quelques secondes
- Aucun impact sur les performances en production
- Les mises à jour automatiques des listes de courses sont instantanées

---

**Déployé par** : Christian
**Date** : 1er décembre 2025
