# Système de Calcul de Coût des Ingrédients

## 📋 Vue d'ensemble

Le système de calcul de coût utilise un algorithme à **4 priorités** pour résoudre les conversions d'unités et calculer le prix des ingrédients dans une recette.

**Principe :** Partir de l'unité de la recette (ex: "pièce") et trouver un chemin vers une unité présente dans le catalogue des prix (ex: "kg"), en utilisant les conversions disponibles.

---

## 🔧 Architecture

### Fichiers principaux

| Fichier | Rôle |
|---------|------|
| `app/services/cost_calculator.py` | Algorithme de calcul de coût |
| `app/models/db_recipes.py` | Intégration dans `calculate_recipe_cost()` |
| `migrations/add_standard_unit_conversions.sql` | Conversions standard en base |

### Tables de base de données

| Table | Description | Exemple |
|-------|-------------|---------|
| `ingredient_price_catalog` | Prix de référence des ingrédients | carotte: 5€/kg |
| `unit_conversion` | Conversions standard par catégorie | g → kg (factor=0.001) |
| `ingredient_specific_conversions` | Conversions spécifiques à un ingrédient | carotte: pièce → kg (factor=0.06) |

---

## 🎯 Algorithme de Résolution

### Ordre de priorité

```
1. DIRECT
   ↓ recipe_unit == IPC.unit_fr ?
   ✅ Calcul immédiat

2. UC (Unit Conversion générique)
   ↓ recipe_unit → target_unit via category
   ✅ Si IPC existe pour target_unit

3. ISC (Ingredient Specific Conversion)
   ↓ recipe_unit → target_unit pour cet ingrédient
   ├─ 3a. Si IPC existe pour target_unit → ✅
   └─ 3b. Sinon: ISC → UC → target_unit2
      ✅ Si IPC existe pour target_unit2

4. Aucune solution
   ❌ Retourner status="missing_conversion"
```

### Exemple concret : Carottes

**Données :**
- Recette : `1 pièce`
- ISC : `pièce → kg` (factor=0.06)
- IPC : `kg = 5€` (qty=1.0)

**Résolution :**
1. DIRECT ? Non (`pièce ≠ kg`)
2. UC ? Non (pas de UC générique `pièce → ?`)
3. ISC ? Oui !
   - ISC : `pièce → kg` (factor=0.06)
   - Quantité convertie : `1 × 0.06 = 0.06 kg`
   - IPC direct sur `kg` ? Oui !
   - **Calcul :** `0.06 × (5€ / 1.0) = 0.30€` ✅

**Résultat :**
- Coût : `0.30€`
- Status : `"ok"`
- Chemin : `["isc", "isc->ipc"]`

---

## 📊 Catégories de Conversion

Le champ `conversion_category` dans `ingredient_price_catalog` détermine quelle catégorie de conversions utiliser.

### Catégories disponibles

| Catégorie | Unités | Exemples |
|-----------|--------|----------|
| `poids` | g, kg, mg | Légumes, viandes, farines |
| `volume` | ml, L, cl, c.s., c.c., tasse | Liquides, huiles, lait |
| `unite` | pièce, sachet, boîte | Œufs, sachets de levure |

### Conversions standard (52 au total)

#### Poids (14)
- `kg ↔ g` (1 kg = 1000 g)
- `g ↔ mg` (1 g = 1000 mg)

#### Volume (28)
- `L ↔ ml` (1 L = 1000 ml)
- `cl ↔ ml` (1 cL = 10 ml)
- `c.s. → ml` (1 c.s. ≈ 15 ml)
- `c.c. → ml` (1 c.c. ≈ 5 ml)
- `tasse → ml` (1 tasse = 250 ml)

#### Unité (3)
- `pièce → pièce` (identité)
- `sachet → sachet` (identité)
- `boîte → boîte` (identité)

---

## 🔄 Conversions Spécifiques

Pour les ingrédients qui changent de forme entre achat et utilisation.

### Quand créer une conversion spécifique ?

✅ **Créer une ISC quand :**
- L'ingrédient s'achète dans une unité (kg) mais se compte en unités discrètes (pièce)
- Il n'existe pas de conversion standard adaptée
- Exemple : 1 carotte (pièce) ≈ 60g = 0.06kg

❌ **NE PAS créer d'ISC pour :**
- Les conversions standard qui existent déjà (g → kg)
- Les ingrédients avec unité identique achat/usage

### Structure d'une ISC

```sql
INSERT INTO ingredient_specific_conversions
(ingredient_name_fr, from_unit, to_unit, factor, notes)
VALUES
('carotte', 'pièce', 'kg', 0.06, '1 pièce de carotte ≈ 60g');
```

**Convention du facteur :**
```
qty_to = qty_from × factor
```

Exemple : `1 pièce × 0.06 = 0.06 kg` ✅

### Exemples de conversions spécifiques

| Ingrédient | from_unit | to_unit | factor | Explication |
|------------|-----------|---------|--------|-------------|
| Carotte | pièce | kg | 0.06 | 1 pièce ≈ 60g |
| Œuf | pièce | kg | 0.06 | 1 œuf ≈ 60g |
| Bouillon cube | cube | ml | 500 | 1 cube = 500ml de bouillon |
| Dashi (poudre) | g | ml | 33.33 | 30g poudre = 1000ml bouillon |

---

## 💰 Formule de Calcul du Coût

```python
# Données du catalogue
pack_price = 5.0€      # Prix du paquet
pack_qty = 1.0         # Quantité du paquet
unit = "kg"            # Unité du catalogue

# Calcul du prix unitaire
unit_price = pack_price / pack_qty
# unit_price = 5.0 / 1.0 = 5.0€/kg

# Quantité nécessaire (après conversion)
qty_needed = 0.06 kg   # Après ISC: 1 pièce → 0.06 kg

# Coût total
cost = qty_needed × unit_price
# cost = 0.06 × 5.0 = 0.30€
```

---

## 📈 Statuts de Résultat

| Status | Signification | Action utilisateur |
|--------|---------------|-------------------|
| `"ok"` | Calcul réussi | Aucune |
| `"missing_data"` | Ingrédient absent du catalogue | Ajouter dans catalogue |
| `"missing_conversion"` | Aucune conversion trouvée | Créer ISC ou UC |
| `"missing_price"` | Prix NULL dans catalogue | Remplir le prix |
| `"invalid_currency"` | Devise non supportée | Utiliser EUR ou JPY |

---

## 🛠️ Guide d'Utilisation

### 1. Ajouter un nouvel ingrédient

```sql
-- 1. Ajouter dans le catalogue
INSERT INTO ingredient_price_catalog
(ingredient_name_fr, unit_fr, price_eur, qty, conversion_category)
VALUES
('pomme de terre', 'kg', 3.50, 1.0, 'poids');
```

### 2. Ajouter une conversion spécifique

```sql
-- Si la recette utilise "pièce" mais le catalogue est en "kg"
INSERT INTO ingredient_specific_conversions
(ingredient_name_fr, from_unit, to_unit, factor, notes)
VALUES
('pomme de terre', 'pièce', 'kg', 0.15, '1 pomme de terre moyenne ≈ 150g');
```

### 3. Tester le calcul

```python
from app.services.cost_calculator import compute_estimated_cost_for_ingredient
import sqlite3

conn = sqlite3.connect('data/recette.sqlite3')
conn.row_factory = sqlite3.Row

result = compute_estimated_cost_for_ingredient(
    conn=conn,
    ingredient_name_fr="pomme de terre",
    recipe_qty=2.0,
    recipe_unit="pièce",
    currency="EUR"
)

print(f"Coût: {result.cost}€")
print(f"Status: {result.status}")
print(f"Chemin: {result.debug['path']}")
```

---

## 🐛 Débogage

### Afficher le chemin de résolution

Le champ `debug` du `CostResult` contient toutes les étapes :

```python
result.debug = {
    'ingredient_name_fr': 'carotte',
    'recipe_qty': 1.0,
    'recipe_unit': 'pièce',
    'currency': 'EUR',
    'path': ['isc', 'isc->ipc'],  # ← Chemin de résolution
    'conversion_category': 'poids',
    'isc_from': 'pièce',
    'isc_to': 'kg',
    'isc_factor': 0.06,
    'qty_after_isc': 0.06,
    'ipc_unit': 'kg',
    'pack_qty': 1.0,
    'pack_price': 5.0
}
```

### Script de test

Utiliser `test_carrot_cost.py` comme modèle :

```bash
python test_carrot_cost.py
```

---

## 🎯 Bonnes Pratiques

### 1. Choix de l'unité du catalogue

✅ **Utiliser l'unité d'achat réelle**
- Carottes : `kg` (on achète au kilo)
- Lait : `L` (on achète au litre)
- Œufs : `pièce` (on achète à la pièce)

### 2. Définir la catégorie correctement

| Si ingrédient | Catégorie |
|---------------|-----------|
| Se pèse | `poids` |
| Se mesure en volume | `volume` |
| Se compte | `unite` |

### 3. Préférer les conversions standard

❌ **Ne pas créer d'ISC pour :**
```sql
-- Mauvais : déjà dans unit_conversion
INSERT INTO ingredient_specific_conversions
VALUES ('carotte', 'g', 'kg', 0.001, '...');
```

✅ **Créer ISC seulement pour :**
```sql
-- Bon : conversion spécifique nécessaire
INSERT INTO ingredient_specific_conversions
VALUES ('carotte', 'pièce', 'kg', 0.06, '...');
```

---

## 📚 Références

- Code source : `app/services/cost_calculator.py`
- Tests : `test_carrot_cost.py`
- Migration : `migrations/add_standard_unit_conversions.sql`
- Intégration : `app/models/db_recipes.py:calculate_recipe_cost()`

---

*Dernière mise à jour : 17 décembre 2024 - Version 2.2*
