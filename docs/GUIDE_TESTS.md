# Guide d'utilisation des tests

**Date** : 1er décembre 2025
**Version** : 1.0

---

## 🧪 **Qu'est-ce qu'un test ?**

Un **test** est un script Python qui vérifie automatiquement que ton code fonctionne correctement.

**Analogie** : Imagine que tu fabriques une voiture. Les tests, c'est ta checklist de contrôle qualité :
- ✅ Le moteur démarre ?
- ✅ Les freins fonctionnent ?
- ✅ Les phares s'allument ?

**En programmation**, au lieu de tester manuellement en cliquant partout, tu écris du code qui teste ton code.

---

## 📦 **Installation**

Les dépendances de test sont déjà dans `requirements.txt` :

```bash
# Installer les dépendances
pip install -r requirements.txt

# Vérifier que pytest est installé
pytest --version
```

---

## 🚀 **Lancer les tests**

### **Tous les tests**
```bash
pytest
```

### **Tests d'un seul fichier**
```bash
pytest tests/test_db_core.py
```

### **Un seul test**
```bash
pytest tests/test_db_core.py::test_normalize_ingredient_name
```

### **Avec plus de détails (verbose)**
```bash
pytest -v
```

### **Avec couverture de code**
```bash
pytest --cov=app

# Générer un rapport HTML
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### **Seulement les tests marqués "unit"**
```bash
pytest -m unit
```

### **Ignorer les tests lents**
```bash
pytest -m "not slow"
```

---

## 📁 **Structure des tests**

```
tests/
├── conftest.py                  # Configuration partagée (fixtures)
├── test_db_core.py              # Tests pour db_core.py (23 tests ✅)
├── test_db_conversions_new.py   # Tests pour db_conversions.py
├── test_db_recipes_new.py       # Tests pour db_recipes.py
└── ...                          # Autres tests
```

### **conftest.py**
Contient les "fixtures" (fonctions partagées par tous les tests) :
- `temp_db` : Base de données temporaire pour chaque test
- `sample_recipe_data` : Données d'exemple pour créer des recettes

### **pytest.ini**
Configuration de pytest (options par défaut, markers, etc.)

---

## ✍️ **Comment écrire un test ?**

### **Structure d'un test**

```python
# tests/test_mon_module.py

import pytest
from app.models.mon_module import ma_fonction

def test_ma_fonction_fonctionne():
    """Description de ce que teste ce test"""
    # 1. ARRANGE - Préparer les données
    input_value = "test"

    # 2. ACT - Exécuter la fonction
    result = ma_fonction(input_value)

    # 3. ASSERT - Vérifier le résultat
    assert result == "resultat_attendu"
```

### **Exemple concret : Tester normalize_ingredient_name**

```python
def test_normalize_oeuf():
    """Teste que 'Œufs' devient 'oeuf'"""
    result = normalize_ingredient_name("Œufs")
    assert result == "oeuf"
```

### **Test avec une base de données temporaire**

```python
@pytest.mark.database
def test_list_recipes(temp_db):
    """Teste list_recipes avec une DB vide"""
    # temp_db est une connexion SQLite temporaire
    recipes = list_recipes("fr")
    assert len(recipes) == 0
```

### **Test paramétré (plusieurs cas)**

```python
@pytest.mark.parametrize("input,expected", [
    ("Œufs", "oeuf"),
    ("Tomates", "tomate"),
    ("Ail", "ail"),
])
def test_normalize(input, expected):
    result = normalize_ingredient_name(input)
    assert result == expected
```

### **Test d'erreur**

```python
def test_conversion_invalide():
    """Vérifie qu'une erreur est levée"""
    with pytest.raises(Exception):
        convert_unit(100, "g", "L")  # Impossible
```

---

## 🎯 **Les markers (organiser les tests)**

Les **markers** permettent d'étiqueter les tests :

```python
@pytest.mark.unit         # Test unitaire rapide
@pytest.mark.database     # Nécessite une DB
@pytest.mark.slow         # Test lent
@pytest.mark.integration  # Test d'intégration
```

**Utilisation** :
```bash
# Seulement les tests unitaires
pytest -m unit

# Tout sauf les tests lents
pytest -m "not slow"

# Tests de base de données
pytest -m database
```

---

## 📊 **Résultats actuels**

### **Tests fonctionnels** ✅

| Fichier | Tests | Statut | Temps |
|---------|-------|--------|-------|
| `test_db_core.py` | 23 | ✅ 100% | 0.09s |

**Détails** :
- ✅ Normalisation des ingrédients (11 tests)
- ✅ Connexion à la base de données (4 tests)
- ✅ Tests paramétrés (8 tests)

### **Tests à corriger** ⚠️

Les tests `test_db_conversions_new.py` et `test_db_recipes_new.py` échouent car le schéma de la base de données de test doit être mis à jour.

**Erreur typique** :
```
sqlite3.OperationalError: no such column: from_unit_fr
```

**Solution** : Mettre à jour le schéma dans `conftest.py` pour qu'il corresponde à la vraie base de données.

---

## 🔧 **Fixtures utiles**

### **temp_db**
Crée une base de données SQLite temporaire pour chaque test.

```python
def test_avec_db(temp_db):
    # temp_db est une connexion SQLite
    temp_db.execute("INSERT INTO recipe (slug) VALUES ('test')")
    temp_db.commit()
```

**Avantages** :
- Isolation totale (chaque test a sa propre DB)
- Nettoyage automatique
- Pas de pollution de la vraie base

### **sample_recipe_data**
Fournit des données d'exemple.

```python
def test_avec_donnees(sample_recipe_data):
    # sample_recipe_data est un dict
    assert sample_recipe_data['slug'] == 'test-recipe'
```

---

## 📈 **Couverture de code**

La **couverture** indique quel % de ton code est testé.

```bash
pytest --cov=app --cov-report=term-missing
```

**Exemple de résultat** :
```
Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
app/models/db_core.py            45      0   100%
app/models/db_recipes.py        156     89    43%   120-145, 200-250
app/models/db_conversions.py     98     12    88%   45-52
-----------------------------------------------------------
TOTAL                          1242    456    63%
```

**Interprétation** :
- `db_core.py` : 100% testé ✅
- `db_recipes.py` : 43% testé (lignes 120-145 et 200-250 non testées) ⚠️
- **Objectif** : 80%+ de couverture

---

## 💡 **Bonnes pratiques**

### **1. Nom des tests**
```python
# ✅ BON - Descriptif
def test_convert_grammes_to_kilogrammes():

# ❌ MAUVAIS - Pas clair
def test1():
```

### **2. Un test = une chose**
```python
# ✅ BON - Test unitaire ciblé
def test_normalize_removes_accents():
    assert normalize_ingredient_name("épinards") == "epinard"

# ❌ MAUVAIS - Teste trop de choses
def test_everything():
    assert normalize_ingredient_name("épinards") == "epinard"
    assert convert_unit(100, "g", "kg") == 0.1
    # ...
```

### **3. Tests indépendants**
Chaque test doit pouvoir s'exécuter seul, dans n'importe quel ordre.

```python
# ✅ BON - Indépendant
def test_list_recipes(temp_db):
    temp_db.execute("INSERT INTO recipe (slug) VALUES ('test')")
    recipes = list_recipes("fr")
    assert len(recipes) == 1

# ❌ MAUVAIS - Dépend d'un autre test
def test_list_recipes_bad():
    # Suppose qu'une recette existe déjà
    recipes = list_recipes("fr")
    assert len(recipes) > 0  # Fragile !
```

### **4. Docstrings**
```python
def test_normalize_oeuf():
    """Teste que 'Œufs' devient 'oeuf' (ligature œ → oe, pluriel → singulier)"""
    result = normalize_ingredient_name("Œufs")
    assert result == "oeuf"
```

---

## 🐛 **Débugger les tests**

### **Voir l'erreur complète**
```bash
pytest -vv tests/test_db_core.py
```

### **S'arrêter au premier échec**
```bash
pytest -x
```

### **Entrer en mode debug**
```python
def test_debug():
    result = ma_fonction("test")
    import pdb; pdb.set_trace()  # Pause ici
    assert result == "attendu"
```

Puis :
```bash
pytest --pdb  # Entre en mode debug à chaque échec
```

### **Afficher les print()**
```bash
pytest -s  # Montre les print() pendant les tests
```

---

## 🎓 **Exemple complet : Tester convert_unit**

```python
# tests/test_conversions.py

import pytest
from app.models.db_conversions import convert_unit

class TestConvertUnit:
    """Tests pour les conversions d'unités"""

    @pytest.mark.database
    def test_grammes_to_kg(self, temp_db):
        """1000g = 1kg"""
        result = convert_unit(1000, "g", "kg")
        assert result == 1.0

    @pytest.mark.database
    def test_litres_to_ml(self, temp_db):
        """1L = 1000mL"""
        result = convert_unit(1, "L", "mL")
        assert result == 1000.0

    @pytest.mark.database
    def test_invalid_conversion(self, temp_db):
        """Impossible de convertir g en L"""
        with pytest.raises(Exception):
            convert_unit(100, "g", "L")

# Lancer :
# pytest tests/test_conversions.py -v
```

---

## 📚 **Ressources**

### **Documentation**
- [pytest officiel](https://docs.pytest.org/)
- [pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [pytest markers](https://docs.pytest.org/en/stable/mark.html)

### **Commandes utiles**

```bash
# Lister tous les tests sans les exécuter
pytest --collect-only

# Exécuter les tests modifiés depuis le dernier commit
pytest --lf  # last-failed

# Mode watch (relance auto quand fichier modifié)
pytest-watch

# Paralléliser les tests (plus rapide)
pytest -n auto  # Nécessite pytest-xdist
```

---

## 🎯 **Prochaines étapes**

### **Court terme**
1. ✅ Tests de base créés pour `db_core.py`
2. ⏳ Corriger le schéma de DB dans `conftest.py`
3. ⏳ Faire passer les tests de `db_conversions.py`
4. ⏳ Faire passer les tests de `db_recipes.py`

### **Moyen terme**
5. ⏳ Ajouter des tests pour `db_events.py`
6. ⏳ Ajouter des tests pour `db_shopping.py`
7. ⏳ Ajouter des tests pour `db_budget.py`
8. ⏳ Atteindre 80% de couverture

### **Long terme**
9. ⏳ Tests d'intégration (endpoints API)
10. ⏳ Tests fonctionnels (E2E avec Selenium)
11. ⏳ Intégration CI/CD (GitHub Actions)

---

## ❓ **FAQ**

### **Pourquoi mes tests échouent ?**
- Vérifie que le schéma de la DB de test correspond à la vraie DB
- Vérifie que les fixtures sont bien utilisées
- Lis le message d'erreur (ligne, fichier, erreur)

### **Dois-je tester TOUT ?**
Non ! Concentre-toi sur :
1. Les **fonctions critiques** (conversions, calculs)
2. Les **bugs fréquents** (pour éviter qu'ils reviennent)
3. La **logique complexe** (plusieurs conditions, boucles)

### **Combien de temps ça prend ?**
- Écrire 1 test : 2-5 minutes
- Exécuter 100 tests : 2-5 secondes
- **Gain de temps** : Énorme sur la durée !

### **Les tests ralentissent le développement ?**
Au début oui (tu apprends). Mais après :
- Tu **gagnes du temps** (pas de tests manuels)
- Tu as **confiance** pour modifier le code
- Tu **évites les régressions**

---

**Dernière mise à jour** : 1er décembre 2025, 22:30
**Auteur** : Claude Code
**Statut** : ✅ Infrastructure de test opérationnelle
