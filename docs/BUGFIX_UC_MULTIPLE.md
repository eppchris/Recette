# 🐛 Correction Bug: Conversions UC Multiples

**Date:** 18 décembre 2024
**Version:** 2.2.1
**Fichier modifié:** `app/services/cost_calculator.py`

---

## 📋 Description du Bug

L'algorithme de calcul de coût ne testait que la **PREMIÈRE** conversion UC (Unit Conversion) disponible au lieu de tester **TOUTES** les conversions possibles.

### Comportement Incorrect (Avant)

Quand plusieurs conversions UC existaient depuis une même unité source :
1. L'algo prenait la première conversion (`LIMIT 1` dans la requête SQL)
2. Si aucun IPC (prix catalogue) n'existait pour l'unité cible, il abandonnait la branche UC
3. Il passait directement à ISC ou à la création automatique
4. Il ne testait **JAMAIS** les autres conversions UC disponibles

### Exemple Concret : Le Sucre

**Données en base :**
```sql
-- Conversions UC disponibles
cs → g   (factor=15.0)    ← Première conversion trouvée
cs → kg  (factor=0.015)   ← Jamais testée !

-- Catalogue IPC
sucre → kg (3.00€)  ← Seule unité disponible
```

**Calcul de 1 cs de sucre :**
- ❌ **AVANT** : Prenait `cs → g`, ne trouvait pas d'IPC pour `g`, créait une ISC avec factor=1.0 → **3.00€** (incorrect)
- ✅ **APRÈS** : Essaie `cs → g` (échec), puis `cs → kg` (succès) → **0.045€** (correct)

---

## 🔧 Correction Appliquée

### Changement dans `cost_calculator.py` (ligne 130-165)

**AVANT :**
```python
uc = conn.execute(
    """
    SELECT from_unit, to_unit, factor
    FROM unit_conversion
    WHERE category = ?
      AND LOWER(from_unit) = LOWER(?)
    LIMIT 1  ← PROBLÈME ICI
    """,
    (category, recipe_unit),
).fetchone()

if uc is not None:
    # Tester cette conversion
    # Si échec, abandonner la branche UC
```

**APRÈS :**
```python
uc_rows = conn.execute(
    """
    SELECT from_unit, to_unit, factor
    FROM unit_conversion
    WHERE category = ?
      AND LOWER(from_unit) = LOWER(?)
    ORDER BY from_unit, to_unit
    """,  ← Pas de LIMIT, récupère TOUTES les conversions
    (category, recipe_unit),
).fetchall()

for uc in uc_rows:  ← Boucle sur TOUTES les conversions
    # Vérifier si un IPC existe pour cette unité cible
    ipc_uc = find_ipc_by_unit(target_unit)
    if ipc_uc is not None:
        # Conversion réussie, retourner le résultat
        return CostResult(...)
```

### Impact

L'algorithme essaie maintenant **TOUTES** les conversions UC possibles et retourne dès qu'il trouve une conversion qui mène à un IPC existant.

---

## ✅ Tests de Régression

### Test Créé : `test_uc_multiple_conversions.py`

Ce test vérifie que :
1. L'algo trouve les 2 conversions UC disponibles (`cs → g` et `cs → kg`)
2. Il essaie `cs → g` (ne trouve pas d'IPC pour `g`)
3. Il continue avec `cs → kg` (trouve un IPC pour `kg`)
4. Le calcul est correct : `1 cs × 0.015 = 0.015 kg → 0.045€`

**Résultat :**
```
✅ TEST RÉUSSI!
   L'algorithme a correctement essayé toutes les UC disponibles
   et a utilisé cs → kg (0.015) au lieu de s'arrêter à cs → g
```

---

## 🔍 Actions Complémentaires

### ISC Auto-créées Incorrectes Supprimées

Les ISC créées automatiquement avec `factor=1.0` à cause de ce bug ont été supprimées :

```sql
DELETE FROM ingredient_specific_conversions
WHERE notes LIKE '%Conversion automatique créée%'
  AND factor = 1.0;
```

---

## 📊 Impact

### Ingrédients Affectés

Tous les ingrédients qui :
- Ont plusieurs conversions UC disponibles depuis la même unité source
- Ont un catalogue IPC dans une unité accessible par une UC "secondaire"
- N'ont pas d'IPC pour la première UC testée

**Exemples typiques :**
- Cuillères à soupe → g/kg (catalogue en kg seulement)
- Cuillères à café → ml/L (catalogue en L seulement)
- Pièces → g/kg (dépend du catalogue)

### Bénéfices

1. **Précision** : Calculs corrects au lieu de factor=1.0 par défaut
2. **Moins d'ISC inutiles** : Pas de création automatique si une UC fonctionne
3. **Robustesse** : L'algo explore toutes les possibilités avant d'abandonner

---

## 🔜 Recommandations

### Pour l'Utilisateur

1. Vérifier les ISC existantes avec `factor=1.0` et les ajuster ou supprimer
2. Privilégier les UC génériques quand c'est possible
3. Créer des ISC seulement pour des cas spécifiques (ex: 1 pomme = 150g)

### Pour le Développement

1. Considérer un tri intelligent des UC (prioriser celles qui mènent directement au catalogue)
2. Ajouter des métriques sur le nombre de tentatives UC avant succès
3. Documenter les "chemins de conversion" standards recommandés

---

## 📚 Fichiers Modifiés

| Fichier | Type | Description |
|---------|------|-------------|
| `app/services/cost_calculator.py` | **Modifié** | Correction de la boucle UC (ligne 130-165) |
| `test_uc_multiple_conversions.py` | **Nouveau** | Test de régression |
| `docs/BUGFIX_UC_MULTIPLE.md` | **Nouveau** | Cette documentation |

---

*Dernière mise à jour : 18 décembre 2024*
