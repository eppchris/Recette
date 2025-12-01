# Système de Conversion d'Unités

## Vue d'ensemble

Le système de conversion d'unités permet de gérer automatiquement les différences entre:
- **Unités de recette**: c.s., c.c., g, ml (unités pratiques pour cuisiner)
- **Unités d'achat**: L, kg (unités standards pour les prix)

## Architecture

### Table `unit_conversion`

Contient les facteurs de conversion entre unités:

```sql
CREATE TABLE unit_conversion (
    id INTEGER PRIMARY KEY,
    from_unit TEXT NOT NULL,
    to_unit TEXT NOT NULL,
    factor REAL NOT NULL,        -- Multiplicateur: from_value × factor = to_value
    category TEXT,                -- volume, poids, poids-huile, etc.
    notes TEXT,
    UNIQUE(from_unit, to_unit)
);
```

### Exemples de conversions

| From      | To   | Factor  | Explication               |
|-----------|------|---------|---------------------------|
| ml        | L    | 0.001   | 1 ml = 0.001 L           |
| c.s.      | ml   | 15      | 1 c.s. = 15 ml           |
| c.s.      | L    | 0.015   | 1 c.s. = 0.015 L         |
| g         | kg   | 0.001   | 1 g = 0.001 kg           |
| tasse (farine) | kg | 0.120 | 1 tasse farine = 120 g  |

## Fonctions Python

### `convert_unit(quantity, from_unit, to_unit)`

Convertit une quantité d'une unité à une autre.

**Exemple:**
```python
from app.models import db

# Convertir 3 cuillères à soupe en litres
result = db.convert_unit(3, 'c.s.', 'L')
# result = 0.045 (L)
```

### `calculate_ingredient_price(ingredient_name, quantity, recipe_unit, currency)`

Calcule automatiquement le prix en convertissant les unités si nécessaire.

**Exemple:**
```python
# Recette demande 3 c.s. d'huile
# Catalogue: huile d'olive à 8.50 €/L
result = db.calculate_ingredient_price("Huile d'olive", 3, "c.s.", "EUR")

# result = {
#     'total_price': 0.3825,           # Prix total en €
#     'unit_price': 8.50,              # Prix du catalogue (€/L)
#     'catalog_unit': 'L',             # Unité du catalogue
#     'converted_quantity': 0.045,     # 3 c.s. = 0.045 L
#     'recipe_quantity': 3,            # Quantité originale
#     'recipe_unit': 'c.s.'            # Unité originale
# }
```

## Conversions disponibles

### Volume
- ml ↔ L
- c.s. → ml, L
- c.c. → ml, L
- tasse → ml
- カップ (tasse japonaise) → ml

### Poids
- g ↔ kg

### Conversions spécifiques par ingrédient

#### Huile (densité ~0.92)
- c.s. (huile) → g (13.8g), kg (0.0138kg)
- c.c. (huile) → g (4.6g), kg (0.0046kg)

#### Farine (densité ~0.6)
- c.s. (farine) → g (8g), kg (0.008kg)
- tasse (farine) → g (120g), kg (0.120kg)

#### Sucre (densité ~0.85)
- c.s. (sucre) → g (12.5g), kg (0.0125kg)
- tasse (sucre) → g (200g), kg (0.200kg)

## Utilisation dans l'application

### Lors du calcul de budget d'événement

Quand un utilisateur crée un budget, le système:

1. Récupère les ingrédients de la recette avec leurs unités (ex: "3 c.s.")
2. Cherche le prix dans le catalogue (ex: "8.50 €/L")
3. **Convertit automatiquement** l'unité de recette vers l'unité du catalogue
4. Calcule le prix total

**Sans conversion** (avant):
- Recette: 3 c.s. d'huile
- Catalogue: 8.50 €/L
- ❌ Incohérence → calcul incorrect

**Avec conversion** (maintenant):
- Recette: 3 c.s. d'huile
- Conversion: 3 c.s. = 0.045 L
- Catalogue: 8.50 €/L
- ✅ Prix: 0.045 × 8.50 = 0.38 €

## Ajouter de nouvelles conversions

### Via SQL

```sql
INSERT INTO unit_conversion (from_unit, to_unit, factor, category, notes)
VALUES ('cuillère à café', 'ml', 5, 'volume', '1 c.c. = 5 ml');
```

### Conversions bidirectionnelles

La vue `v_unit_conversions_bidirectional` génère automatiquement les conversions inverses:

```sql
-- Si vous avez: c.s. → ml (facteur 15)
-- La vue ajoute automatiquement: ml → c.s. (facteur 0.0667)
```

## Tests

Exécuter les tests:

```bash
python test_unit_conversion.py
```

## Limitations

- **Conversions en chaîne**: Le système ne supporte que les conversions directes
  - ❌ c.s. → ml → L nécessite deux conversions
  - ✅ c.s. → L doit être ajouté explicitement

- **Unités spécifiques**: Pour les conversions dépendant de l'ingrédient (densité),
  utiliser des unités spécifiques comme "c.s. (huile)" au lieu de "c.s."

## Migration appliquée

✅ Migration: `migrations/add_unit_conversions.sql`
- Table créée: `unit_conversion`
- 37 conversions ajoutées
- Vue bidirectionnelle créée
- Index ajoutés pour performance
