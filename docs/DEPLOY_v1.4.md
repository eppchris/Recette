# Guide de déploiement - Version 1.4

**Date** : 1er décembre 2025
**Version** : 1.4
**Tag Git** : v1.4

## Résumé des changements

Cette version apporte la normalisation des ingrédients et l'ajustement automatique des listes de courses lors du changement du nombre de participants.

### Nouvelles fonctionnalités
- Normalisation automatique des noms d'ingrédients (minuscules, sans accents, singulier)
- Régénération automatique de la liste de courses lors du changement du nombre de participants
- Ajustement automatique des quantités proportionnellement au nombre de participants
- Amélioration du système de filtrage des recettes par types d'événements

### Modifications de la base de données
- Nouvelle fonction `normalize_ingredient_name()` dans le code
- Nouvelle fonction `update_event_recipes_multipliers()` dans le code
- **IMPORTANT** : Les données existantes doivent être normalisées avec le script de migration

---

## Procédure de déploiement

### 1. Sauvegarde de la production

**AVANT TOUTE CHOSE**, faire une sauvegarde complète :

```bash
# Sur le serveur de production
cd /chemin/vers/Recette
cp data/recette.sqlite3 data/recette.sqlite3.backup-$(date +%Y%m%d-%H%M%S)
```

### 2. Récupération du code

```bash
# Sur le serveur de production
cd /chemin/vers/Recette
git fetch origin
git checkout v1.4
```

### 3. Installation des dépendances

```bash
# Vérifier si de nouvelles dépendances ont été ajoutées
pip install -r requirements.txt
```

### 4. Migration de la base de données

**IMPORTANT** : Cette étape normalise tous les noms d'ingrédients dans la base de données.

```bash
# Exécuter le script de normalisation
python3 migrations/normalize_ingredients.py
```

Ce script va :
1. Normaliser tous les noms d'ingrédients dans le catalogue de prix
2. Fusionner les doublons (ex: "Oeuf", "œuf", "œufs" → "oeuf")
3. Normaliser tous les noms d'ingrédients dans les recettes

**Le script est interactif et demandera confirmation avant d'appliquer les changements.**

Exemple de sortie attendue :
```
================================================================================
SCRIPT DE NORMALISATION DES INGRÉDIENTS
================================================================================

Ce script va :
  1. Normaliser et fusionner les doublons dans le catalogue de prix
  2. Normaliser tous les ingrédients dans les recettes

Règles de normalisation :
  • Minuscules
  • Sans accents (é→e, œ→oe, etc.)
  • Au singulier (œufs→oeuf, tomates→tomate)

⚠️  Continuer ? (oui/non) : oui

[... détails de la normalisation ...]

✅ NORMALISATION TERMINÉE AVEC SUCCÈS !
```

### 5. Vérification post-migration

```bash
# Vérifier que la base de données n'est pas corrompue
sqlite3 data/recette.sqlite3 "SELECT COUNT(*) FROM ingredient_price_catalog;"
sqlite3 data/recette.sqlite3 "SELECT COUNT(*) FROM recipe_ingredient_translation;"
```

Les deux commandes doivent retourner un nombre (pas d'erreur).

### 6. Redémarrage de l'application

```bash
# Arrêter l'application actuelle
sudo systemctl stop recette
# ou
pkill -f "python3 main.py"

# Redémarrer l'application
sudo systemctl start recette
# ou
python3 main.py
```

### 7. Vérification fonctionnelle

Vérifier les fonctionnalités suivantes :

1. **Catalogue de prix**
   - Aller sur `/ingredient-catalog`
   - Vérifier qu'il n'y a plus de doublons (ex: "Oeuf" et "œuf")
   - Vérifier que les noms sont normalisés (minuscules, sans accents)

2. **Modification du nombre de participants**
   - Créer ou sélectionner un événement avec une liste de courses existante
   - Modifier le nombre de participants
   - Vérifier que la liste de courses se met à jour automatiquement
   - Vérifier que le budget se met à jour aussi

3. **Filtres des recettes**
   - Aller sur `/recipes`
   - Vérifier que les filtres par type d'événement fonctionnent

---

## Rollback (en cas de problème)

Si quelque chose ne fonctionne pas :

### 1. Restaurer la base de données

```bash
cd /chemin/vers/Recette
# Trouver la sauvegarde
ls -lh data/recette.sqlite3.backup-*

# Restaurer
cp data/recette.sqlite3.backup-YYYYMMDD-HHMMSS data/recette.sqlite3
```

### 2. Revenir à la version précédente

```bash
git checkout v1.3  # ou la version précédente
sudo systemctl restart recette
```

---

## Notes importantes

### Compatibilité

- ✅ Cette version est compatible avec les données de la v1.3
- ✅ Le script de migration est **non destructif** : il demande confirmation
- ✅ Les anciennes listes de courses continuent de fonctionner
- ⚠️  Une fois normalisé, le retour en arrière nécessite une restauration de la sauvegarde

### Performance

- La normalisation peut prendre quelques secondes selon le nombre d'ingrédients
- Aucun impact sur les performances en production

### Impact utilisateur

- ✅ Aucune interruption de service pendant la migration (si faite hors ligne)
- ✅ Les utilisateurs verront immédiatement les bénéfices :
  - Plus de doublons dans le catalogue
  - Mise à jour automatique des listes de courses

---

## Support

En cas de problème :
1. Consulter les logs : `tail -f logs/recette.log`
2. Vérifier l'intégrité de la base : `sqlite3 data/recette.sqlite3 "PRAGMA integrity_check;"`
3. Restaurer la sauvegarde si nécessaire (voir section Rollback)

---

## Checklist de déploiement

- [ ] Sauvegarde de la base de données effectuée
- [ ] Code récupéré (git checkout v1.4)
- [ ] Dépendances installées
- [ ] Script de normalisation exécuté avec succès
- [ ] Vérification post-migration OK
- [ ] Application redémarrée
- [ ] Tests fonctionnels OK
- [ ] Catalogue de prix vérifié (pas de doublons)
- [ ] Modification du nombre de participants testée
- [ ] Filtres des recettes vérifiés

---

**Déploiement préparé par** : Claude
**Date** : 1er décembre 2025
