# LIVRAISON V1.11 - CALCUL DE COÛT DES RECETTES

**Date**: 2025-12-11
**Version**: 1.11
**Auteur**: Claude Code

---

## 🎯 RÉSUMÉ

Cette livraison introduit une nouvelle fonctionnalité majeure : **le calcul automatique du coût d'une recette** basé sur les prix du catalogue d'ingrédients. L'utilisateur peut désormais visualiser le coût total d'une recette et le coût par personne, avec conversions d'unités automatiques, exactement comme pour le budget des événements.

### Fonctionnalités principales :
- ✅ Bouton "💰 Coût" sur chaque page de détail de recette
- ✅ Calcul automatique du coût avec conversions d'unités
- ✅ Affichage du coût total et du coût par personne
- ✅ Adaptation automatique selon le nombre de portions
- ✅ Modal catalogue pour modifier les prix au besoin
- ✅ Liens cliquables sur les ingrédients
- ✅ Favicon (marmite) ajouté sur toutes les pages HTML

---

## 📋 FICHIERS MODIFIÉS

### Backend - Modèles et Business Logic

#### `app/models/db_recipes.py` (lignes 588-689)
**Modification** : Ajout de la fonction `calculate_recipe_cost()`

**Description** : Fonction principale pour calculer le coût d'une recette avec :
- Normalisation des noms d'ingrédients
- Calcul des quantités ajustées selon le nombre de portions
- Conversions d'unités automatiques via `calculate_ingredient_price()`
- Récupération des prix depuis `ingredient_price_catalog`
- Calcul du coût unitaire et total par ingrédient
- Agrégation du coût total de la recette

**Algorithme** :
1. Récupération de la recette et ses ingrédients
2. Calcul du ratio portions cibles / portions originales
3. Pour chaque ingrédient :
   - Ajustement de la quantité selon le ratio
   - Normalisation du nom d'ingrédient
   - Appel à `calculate_ingredient_price()` pour conversion d'unités
   - Calcul du coût planifié
4. Agrégation du coût total

**Retour** : Dictionnaire contenant :
- `recipe`: données de la recette
- `servings`: nombre de portions cible
- `original_servings`: nombre de portions original
- `ingredients`: liste des ingrédients avec coûts calculés
- `total_planned`: coût total de la recette
- `currency`: devise (EUR/JPY)

#### `app/models/__init__.py` (lignes 32, 195, 341)
**Modification** : Export de la nouvelle fonction

**Changements** :
- Import de `calculate_recipe_cost` depuis `db_recipes`
- Ajout dans `__all__`
- Ajout dans le namespace `db`

### Backend - Routes

#### `app/routes/recipe_routes.py` (lignes ~600-625)
**Modification** : Ajout de la route `/recipe/{slug}/cost`

**Description** : Route GET pour afficher la page de coût d'une recette

**Paramètres** :
- `slug`: identifiant de la recette
- `lang`: langue (fr/jp)
- `servings`: nombre de portions (optionnel)

**Comportement** :
- Appel à `calculate_recipe_cost()`
- Rendu du template `recipe_cost.html` avec toutes les données
- Gestion du cas 404 si recette introuvable

### Frontend - Templates

#### `app/templates/recipe_detail.html` (lignes ~171-176)
**Modification** : Ajout du bouton "💰 Coût"

**Description** : Bouton positionné à droite du bouton "Convertir"
- Lien dynamique avec slug, langue et nombre de portions
- Style cohérent avec les autres boutons (Tailwind CSS)
- Icône emoji 💰
- Libellé bilingue (Coût / コスト)

#### `app/templates/recipe_cost.html` (NOUVEAU - 345 lignes)
**Création** : Template complet pour l'affichage du coût d'une recette

**Structure** :
1. **En-tête** (lignes 1-21)
   - Méta tags, titre, Tailwind CSS, Alpine.js
   - Favicons

2. **Scripts Alpine.js** (lignes 22-136)
   - `catalogModal`: gestion du modal de catalogue
   - `_toNumber()`: conversion sécurisée en nombre
   - `formatPrice()`: formatage des prix avec devise
   - `formatQty()`: formatage des quantités
   - `openCatalogModal()`: ouverture du modal avec données
   - `saveCatalogPrice()`: sauvegarde des modifications (POST)
   - `deleteCatalogPrice()`: suppression d'un prix (DELETE)

3. **Navigation** (lignes 138-152)
   - Barre de navigation avec retour à la recette
   - Sélecteur de nombre de portions

4. **En-tête de page** (lignes 154-173)
   - Titre de la recette
   - Emoji et nom
   - Libellé "Estimation des coûts"

5. **Cartes de résumé** (lignes 175-205)
   - Coût total de la recette
   - Coût par personne
   - Affichage conditionnel si coût calculable

6. **Tableau des ingrédients** (lignes 207-277)
   - Colonnes : Ingrédient, Catalogue, Recette, Prévu
   - Ingrédients cliquables (ouvre modal catalogue)
   - Affichage des quantités, unités et prix
   - Notes si présentes
   - Formatage conditionnel (quantités nulles = "-")

7. **Modal catalogue** (lignes 279-343)
   - Formulaire de modification de prix
   - Champs : ingrédient, quantité, unité, prix
   - Boutons : Enregistrer, Supprimer, Annuler
   - Gestion des erreurs
   - Rechargement automatique après modification

**Points techniques** :
- Utilise Alpine.js pour la réactivité
- Helpers de formatage sécurisé pour éviter erreurs JS
- Structure copiée de `event_budget.html` (fonctionnalité similaire)
- Modal intégré pour édition des prix catalogue
- Gestion des valeurs nulles et cas limites

#### Favicons ajoutés sur 17 templates
**Modification** : Ajout des liens favicon dans toutes les pages standalone

**Templates modifiés** :
- `recipe_cost.html` (nouveau)
- `access_logs.html`
- `event_budget.html`
- `event_copy_form.html`
- `event_detail.html`
- `event_form.html`
- `event_organization.html`
- `event_planning.html`
- `events_list.html`
- `help.html`
- `ingredient_catalog.html`
- `ingredient_specific_conversions.html`
- `login.html`
- `profile.html`
- `register.html`
- `shopping_list.html`
- `unit_conversions.html`

**Code ajouté** (après `<title>`) :
```html
<!-- Favicons -->
<link rel="icon" type="image/x-icon" href="/static/favicon.ico?v=2">
<link rel="icon" type="image/png" sizes="32x32" href="/static/favicon-32x32.png?v=2">
<link rel="icon" type="image/png" sizes="16x16" href="/static/favicon-16x16.png?v=2">
<link rel="apple-touch-icon" sizes="64x64" href="/static/favicon-64x64.png?v=2">
```

---

## 🆕 NOUVEAUX FICHIERS

Les fichiers suivants sont déjà présents dans le dépôt (untracked par git) et font partie des livraisons précédentes ou de cette livraison :

### Documentation
- `LIVRAISON_V1.8_MONITORING_PERFORMANCE.md`
- `LIVRAISON_V1.9_V1.10_FINAL.md`
- `LIVRAISON_V1.11_IMPORT_URL_DESCRIPTION.md`
- `RELEASE_NOTES_V1.9.md`
- `V1.9_SUMMARY.md`
- `OPTIMISATION_SQL_V1.10.md`
- `docs/MONITORING_PERFORMANCE.md`
- `docs/USER_GUIDE_MONITORING.md`

### Application
- `app/routes/monitoring_routes.py` (routes de monitoring)
- `app/services/web_recipe_importer.py` (import de recettes depuis URL)
- `app/templates/event_copy_form.html`
- `app/templates/import_url.html`
- `app/templates/recipe_cost.html` ⭐ **(CETTE LIVRAISON)**

### Assets statiques
- `app/static/` (répertoire)
- `static/favicon.ico`
- `static/favicon-16x16.png`
- `static/favicon-32x32.png`
- `static/favicon-64x64.png`
- `static/favicon.svg`
- `static/favicon-emoji.html`

### Scripts et migrations
- `scripts/generate_favicon.py`
- `scripts/generate_favicon_kawaii.py`
- `scripts/generate_favicon_v2.py`
- `scripts/sync_prod_to_dev.sh`
- `scripts/test_sql_optimizations.py`
- `scripts/verify_monitoring_setup.sh`
- `migrations/add_client_performance_log.sql`
- `migrations/add_performance_indexes.sql`
- `migrations/add_recipe_description.sql`
- `migrations/add_response_size_to_access_log.sql`

### Backups
- `backups/` (répertoire)

---

## 🗑️ FICHIERS SUPPRIMÉS

- `deploy/deploy_synology.sh` (ancien script de déploiement)

---

## 🔧 DÉPENDANCES TECHNIQUES

### Tables de base de données utilisées :
- ✅ `ingredient_price_catalog` : prix des ingrédients au catalogue
- ✅ `unit_conversion` : table de conversions d'unités génériques
- ✅ `ingredient_specific_conversions` : conversions spécifiques par ingrédient
- ✅ `recipe` : données des recettes
- ✅ `recipe_ingredient` : ingrédients des recettes

### Fonctions réutilisées :
- `calculate_ingredient_price()` depuis `app/models/db_catalog.py`
- `get_ingredient_aggregator()` depuis `app/services/ingredient_aggregator.py`
- `get_recipe_by_slug()` depuis `app/models/db_recipes.py`

### Bibliothèques frontend :
- Tailwind CSS (déjà présent)
- Alpine.js (déjà présent)

---

## 🧪 TESTS EFFECTUÉS

### Tests fonctionnels :
1. ✅ Affichage du bouton "💰 Coût" sur page de détail de recette
2. ✅ Calcul du coût d'une recette avec prix catalogue
3. ✅ Adaptation du coût selon le nombre de portions
4. ✅ Conversions d'unités automatiques (ex: 200g → 0.2kg)
5. ✅ Affichage du coût total et coût par personne
6. ✅ Ouverture du modal catalogue en cliquant sur un ingrédient
7. ✅ Modification d'un prix catalogue depuis le modal
8. ✅ Rechargement automatique après modification
9. ✅ Gestion des ingrédients sans prix (affichage "-")
10. ✅ Favicon visible sur toutes les pages HTML

### Cas testés :
- Recette avec tous les ingrédients ayant un prix catalogue ✅
- Recette avec certains ingrédients sans prix ✅
- Changement du nombre de portions (1, 4, 8) ✅
- Ingrédients avec conversions d'unités complexes ✅
- Modal catalogue : modification, suppression ✅

---

## 📸 CAPTURES D'ÉCRAN

*(Les captures d'écran ont été vérifiées lors des tests)*

### Vue d'ensemble :
- Page de détail de recette avec bouton "💰 Coût"
- Page de coût avec tableau des ingrédients
- Cartes de résumé (coût total / coût par personne)
- Modal catalogue pour édition des prix

---

## 🚀 PROCÉDURE DE DÉPLOIEMENT

### 1. Pré-requis
- Python 3.9+
- FastAPI
- Base de données SQLite avec tables existantes
- Table `ingredient_price_catalog` avec données

### 2. Mise à jour du code
```bash
# Pull des dernières modifications
git pull origin main

# Aucune migration SQL nécessaire (utilise tables existantes)
```

### 3. Vérifications post-déploiement
```bash
# Démarrer l'application
python main.py

# Vérifier les logs au démarrage
# Aucune erreur d'import ne doit apparaître

# Tester l'accès aux routes :
# - GET /recipe/{slug} → bouton "💰 Coût" visible
# - GET /recipe/{slug}/cost → page de coût s'affiche
```

### 4. Tests fonctionnels en production
1. Ouvrir une recette (ex: `/recipe/tarte-aux-pommes?lang=fr`)
2. Cliquer sur le bouton "💰 Coût"
3. Vérifier l'affichage du tableau des ingrédients
4. Vérifier les coûts calculés
5. Changer le nombre de portions
6. Cliquer sur un ingrédient pour ouvrir le modal
7. Vérifier que le favicon s'affiche

---

## ⚠️ POINTS D'ATTENTION

### 1. Données requises
- La table `ingredient_price_catalog` doit contenir des prix pour les ingrédients
- Sans prix catalogue, les coûts s'affichent comme "-"
- Les conversions d'unités dépendent des tables `unit_conversion` et `ingredient_specific_conversions`

### 2. Performance
- Le calcul de coût appelle `calculate_ingredient_price()` pour chaque ingrédient
- Pour recettes avec beaucoup d'ingrédients, le temps de calcul peut être notable
- Pas de mise en cache implémentée (calcul à chaque affichage)

### 3. Devise
- Devise automatiquement choisie selon la langue (EUR pour français, JPY pour japonais)
- Les prix doivent être dans la bonne devise dans la table catalogue

### 4. Conversions d'unités
- Utilise le même mécanisme que le budget des événements
- Si conversion impossible, le prix n'est pas calculé
- Dépend de la complétude des tables de conversion

---

## 🔄 COMPATIBILITÉ

### Versions compatibles :
- ✅ Python 3.9+
- ✅ FastAPI (version actuelle du projet)
- ✅ SQLite 3
- ✅ Navigateurs modernes (Chrome, Firefox, Safari, Edge)

### Rétrocompatibilité :
- ✅ Aucune modification des routes existantes
- ✅ Aucune modification du schéma de base de données
- ✅ Aucun impact sur les fonctionnalités existantes
- ✅ Ajout purement additif (nouvelle route, nouveau template)

---

## 📊 MÉTRIQUES

### Lignes de code ajoutées :
- Backend : ~120 lignes (db_recipes.py + recipe_routes.py + __init__.py)
- Frontend : ~345 lignes (recipe_cost.html)
- Autres templates : ~5 lignes × 17 fichiers = ~85 lignes (favicons)
- **Total : ~550 lignes**

### Fichiers modifiés : 23 fichiers
### Fichiers créés : 1 fichier (recipe_cost.html)

---

## 📝 NOTES DE DÉVELOPPEMENT

### Historique des problèmes rencontrés :
1. **Fonction non trouvée** : Oubli d'export dans `__init__.py` → Ajout dans imports, `__all__` et namespace `db`
2. **Double slash dans URL** : Variable `slug` manquante dans contexte → Ajout dans template context
3. **Unité incorrecte** : Confusion entre `recipe_unit` et `catalog_unit` → Correction dans template
4. **Assets non chargés** : Chemins incorrects pour Tailwind/Alpine → Correction des paths
5. **Erreur d'import** : Mauvais nom de fonction (`calculate_ingredient_cost_with_conversion` vs `calculate_ingredient_price`) → Correction
6. **Données catalogue manquantes** : Initialement cherché dans mauvaise table → Utilisation de `calculate_ingredient_price()` qui interroge `ingredient_price_catalog`
7. **Bug devise en japonais** : Devise hardcodée en `'EUR'` au lieu d'utiliser la variable `currency` → Correction dans `db_recipes.py:676` et ajout de `original_servings` dans le contexte du template

### Décisions techniques :
- Réutilisation de `calculate_ingredient_price()` plutôt que réécriture de la logique de conversion
- Copie de la structure de `event_budget.html` pour cohérence UI
- Helpers de formatage sécurisé (`_toNumber`, `formatPrice`, `formatQty`) pour éviter erreurs JS avec valeurs nulles
- Alpine.js pour réactivité frontend (cohérent avec le reste de l'application)
- Gestion dynamique de la devise selon la langue (EUR pour français, JPY pour japonais)

---

## 👥 CRÉDITS

**Développement** : Claude Code
**Demandé par** : christianepp
**Date** : 2025-12-11

---

## 📞 SUPPORT

En cas de problème :
1. Vérifier les logs de l'application
2. Vérifier que la table `ingredient_price_catalog` contient des données
3. Vérifier les tables de conversion d'unités
4. Consulter ce document de livraison
5. Contacter le développeur

---

**FIN DU DOCUMENT DE LIVRAISON V1.11**
