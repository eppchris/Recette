# 🐛 Correction - Gestion des champs vides dans les formulaires

## Problème identifié

Erreur 422 lors de la soumission de formulaires avec des champs numériques vides.

### Détails techniques

FastAPI avec `actual_amount: Optional[float] = Form(None)` échoue quand le champ HTML est vide mais envoyé comme chaîne vide `""` au lieu de `None`.

```
❌ AVANT:
- Champ vide dans le form → envoi de ""
- FastAPI essaie float("") → ValueError
- Erreur 422: "unable to parse string as a number"
```

## Solution appliquée

Recevoir tous les champs optionnels comme `Optional[str]` et convertir manuellement.

### Code corrigé

```python
# Avant (causait l'erreur)
actual_amount: Optional[float] = Form(None)

# Après (corrigé)
actual_amount: Optional[str] = Form(None)

# Conversion sécurisée
actual_amount_float = None
if actual_amount and actual_amount.strip():
    try:
        actual_amount_float = float(actual_amount)
    except ValueError:
        actual_amount_float = None
```

## Routes corrigées

### 1. POST /events/{event_id}/expenses/add
- `actual_amount`: Optional[str] → float
- `is_paid`: Optional[str] → bool
- `paid_date`: Optional[str] → str (nettoyage vide)

### 2. POST /events/{event_id}/expenses/{expense_id}/update
- `planned_amount`: Optional[str] → float
- `actual_amount`: Optional[str] → float
- `is_paid`: Optional[str] → bool
- `paid_date`: Optional[str] → str (nettoyage vide)

### 3. POST /api/shopping-list/items/{item_id}/update-prices
- `planned_unit_price`: Optional[str] → float
- `actual_unit_price`: Optional[str] → float
- `is_purchased`: Optional[str] → bool

## Cas gérés

✅ Champ vide: `""` → `None`
✅ Champ avec espaces: `"  "` → `None`
✅ Valeur valide: `"123.45"` → `123.45`
✅ Valeur invalide: `"abc"` → `None` (sans crash)
✅ Checkbox non cochée: `None` → `False`
✅ Checkbox cochée: `"1"` → `True`

## Test de validation

```bash
python -m py_compile app/routes/event_routes.py
python -c "import main"
```

✅ Aucune erreur de syntaxe
✅ Application démarre correctement

## Impact

**Avant:**
- ❌ Impossible d'ajouter une dépense sans montant réel
- ❌ Erreur 422 systématique sur champs vides

**Après:**
- ✅ Champs optionnels vraiment optionnels
- ✅ Soumission de formulaire robuste
- ✅ Gestion gracieuse des erreurs de conversion

---

Date: 2025-11-17
Fichier modifié: app/routes/event_routes.py
Lignes concernées: 495-682
