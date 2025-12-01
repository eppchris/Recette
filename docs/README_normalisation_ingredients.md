# Normalisation des Ingrédients - Version 1.4

## Contexte

Le catalogue des prix d'ingrédients contenait de nombreux doublons dus aux variations orthographiques :
- Variations d'accents : "Saké" vs "sake"
- Variations de casse : "Oeuf" vs "œuf"
- Singulier/pluriel : "œufs" vs "œuf"

Ces doublons créaient de la confusion et compliquaient la gestion des prix.

## Solution Implémentée

### 1. Fonction de normalisation (`normalize_ingredient_name`)

Ajoutée dans [app/models/db.py](../app/models/db.py) (lignes 15-48)

**Règles de normalisation :**
- Minuscules
- Sans accents (é→e, è→e, à→a, ô→o, œ→oe, etc.)
- Au singulier (suppression du 's' final si présent)

**Exemples :**
```python
"Œufs" → "oeuf"
"Saké" → "sake"
"Tomates" → "tomate"
"Farine de blé" → "farine de ble"
```

### 2. Script de migration

Le script [normalize_ingredients.py](normalize_ingredients.py) effectue :

**Étape 1 : Nettoyage du catalogue (`ingredient_price_catalog`)**
- Identifie les doublons par nom normalisé
- Fusionne les doublons en gardant la ligne la plus complète (avec prix)
- Normalise tous les noms restants

**Étape 2 : Normalisation des recettes (`recipe_ingredient_translation`)**
- Normalise tous les noms d'ingrédients français dans les recettes

### 3. Mise à jour de la synchronisation

La fonction `sync_ingredients_from_recipes()` a été mise à jour pour :
- Utiliser les noms normalisés lors de la vérification des doublons
- Insérer les nouveaux ingrédients avec des noms normalisés
- Éviter les futurs doublons

## Résultats de l'Exécution

### Catalogue de prix
- **Avant** : 151 ingrédients (avec doublons)
- **Après** : 146 ingrédients (doublons fusionnés)
- **Doublons supprimés** : 5 lignes
  - "sauce soja" (2 variantes)
  - "sesame blanc" (2 variantes)
  - "sake" (3 variantes)
  - "sauce de haricots fermente" (2 variantes)

### Recettes
- **Ingrédients traités** : 257
- **Ingrédients normalisés** : 213
- **Exemples** :
  - "Saumon" → "saumon"
  - "Céleri" → "celeri"
  - "Sauce soja" → "sauce soja"
  - "Farine de blé" → "farine de ble"

## Utilisation Future

### Réexécuter la normalisation (si nécessaire)
```bash
cd /Users/christianepp/Documents/DEV/Recette
python3 migrations/normalize_ingredients.py
```

### Comportement automatique
Désormais, lorsque vous :
- Synchronisez les ingrédients depuis les recettes (bouton "Synchroniser")
- Ajoutez de nouveaux ingrédients dans les recettes

Les noms seront automatiquement normalisés pour éviter les doublons.

## Notes Importantes

1. **Irréversible** : Cette migration modifie directement les données. Un backup de la base a été fait avant l'exécution.

2. **Impact sur l'affichage** : Les noms d'ingrédients sont maintenant en minuscules et sans accents dans l'interface.

3. **Japonais non affecté** : La normalisation ne s'applique qu'aux noms français. Les noms japonais restent inchangés.

4. **Catalogue manuel** : Vous devrez peut-être ajuster manuellement certains prix dans le catalogue après la fusion des doublons.

## Date d'Exécution

- **Date** : 2025-12-01
- **Durée** : ~2 secondes
- **Statut** : ✅ Succès

## Fichiers Modifiés

1. [app/models/db.py](../app/models/db.py)
   - Ajout de `normalize_ingredient_name()` (ligne 15)
   - Mise à jour de `sync_ingredients_from_recipes()` (ligne 1748)

2. [migrations/normalize_ingredients.py](normalize_ingredients.py)
   - Nouveau script de migration

3. Base de données : `data/recette.sqlite3`
   - Tables modifiées : `ingredient_price_catalog`, `recipe_ingredient_translation`
