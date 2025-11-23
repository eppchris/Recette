# 💰 Implémentation de la gestion budgétaire - Version 1.2

## ✅ Statut : Implémentation terminée et testée

Date : 17 novembre 2025

---

## 📋 Résumé des fonctionnalités

### 1. Budget prévisionnel par événement
- Définir un budget total pour l'événement
- Devise automatique selon la langue : **€ pour FR**, **¥ pour JP**
- Affichage du budget prévu vs réel avec différence colorée

### 2. Gestion des dépenses hors ingrédients
- **7 catégories système multilingues** (FR/JP) :
  - 🏠 Location / 会場
  - 🎨 Décoration / 装飾
  - 🍽️ Matériel / 材料
  - 🚗 Transport / 交通
  - 👥 Personnel / 人員
  - 🎵 Animation / 演出
  - 📋 Autre / その他

- Pour chaque dépense :
  - Montant prévu
  - Montant réel (optionnel)
  - Statut payé/non payé
  - Date de paiement
  - Notes

### 3. Prix des ingrédients (liste de courses)
- Prix unitaire prévisionnel
- Prix unitaire réel
- Case "Acheté" pour déclencher la sauvegarde dans l'historique
- **Apprentissage automatique** : les prix réels sont sauvegardés via trigger SQL

### 4. Résumé budgétaire complet
- Total prévu (dépenses + ingrédients)
- Total réel (dépenses + ingrédients)
- Différence (avec couleur verte/rouge)
- Suivi en temps réel

---

## 🗂️ Structure de la base de données

### Tables créées par la migration

```sql
-- Budget de l'événement
ALTER TABLE event ADD COLUMN budget_planned REAL DEFAULT NULL;

-- Catégories de dépenses (multilingue)
CREATE TABLE expense_category (
    id INTEGER PRIMARY KEY,
    is_system BOOLEAN,
    icon TEXT,
    created_at DATETIME
);

CREATE TABLE expense_category_translation (
    category_id INTEGER,
    lang TEXT,
    name TEXT,
    PRIMARY KEY (category_id, lang)
);

-- Dépenses d'événement
CREATE TABLE event_expense (
    id INTEGER PRIMARY KEY,
    event_id INTEGER,
    category_id INTEGER,
    description TEXT,
    planned_amount REAL,
    actual_amount REAL,
    is_paid BOOLEAN,
    paid_date DATE,
    notes TEXT
);

-- Historique des prix d'ingrédients
CREATE TABLE ingredient_price_history (
    id INTEGER PRIMARY KEY,
    ingredient_name_normalized TEXT,
    ingredient_name_display TEXT,
    unit_price REAL,
    unit TEXT,
    source TEXT,
    last_used_date DATE,
    usage_count INTEGER
);

-- Prix sur les items de liste de courses
ALTER TABLE shopping_list_item ADD COLUMN planned_unit_price REAL;
ALTER TABLE shopping_list_item ADD COLUMN actual_unit_price REAL;
ALTER TABLE shopping_list_item ADD COLUMN is_purchased BOOLEAN;
```

### Triggers automatiques

```sql
-- Sauvegarde automatique des prix réels dans l'historique
CREATE TRIGGER save_actual_price_to_history
AFTER UPDATE OF actual_unit_price, is_purchased ON shopping_list_item
WHEN NEW.actual_unit_price IS NOT NULL AND NEW.is_purchased = 1
BEGIN
    -- Insertion ou mise à jour de l'historique des prix
END;
```

---

## 🔧 Fichiers modifiés

### Backend

#### `app/models/db.py` (lignes 1043-1496)
Nouvelles fonctions :
- `get_event_budget_planned(event_id)`
- `update_event_budget_planned(event_id, budget_planned)`
- `list_expense_categories(lang)`
- `create_expense_category(name_fr, name_jp, icon)`
- `update_expense_category(category_id, ...)`
- `delete_expense_category(category_id)`
- `get_event_expenses(event_id, lang)`
- `create_event_expense(event_id, category_id, ...)`
- `update_event_expense(expense_id, ...)`
- `delete_event_expense(expense_id)`
- `get_event_budget_summary(event_id)`
- `get_ingredient_price_suggestions(ingredient_name, unit)`
- `update_ingredient_price_from_shopping_list(...)`

#### `app/routes/event_routes.py` (lignes 439-621)
Nouvelles routes :
- `GET /events/{event_id}/budget` - Page de gestion du budget
- `POST /events/{event_id}/budget/planned` - Mise à jour budget
- `POST /events/{event_id}/expenses/add` - Ajout dépense
- `POST /events/{event_id}/expenses/{expense_id}/update` - Modification
- `POST /events/{event_id}/expenses/{expense_id}/delete` - Suppression
- `GET /api/ingredient-price-suggestion` - Suggestions de prix
- `POST /api/shopping-list/items/{item_id}/update-prices` - MAJ prix

### Frontend

#### `app/templates/event_detail.html` (ligne 176-180)
- Ajout du bouton "💰 Gérer le budget / 予算管理"

#### `app/templates/event_budget.html` (nouveau fichier)
- Page complète de gestion budgétaire
- Support multilingue FR/JP
- Devises adaptées (€/¥)
- Formulaire d'ajout de dépenses
- Tableau récapitulatif

#### `app/templates/shopping_list.html` (lignes 227-250)
- Champs de prix prévisionnel et réel
- Case à cocher "Acheté"
- Devises adaptées (€/¥)

### Corrections appliquées

1. **Plantage corrigé** : Gestion des valeurs NULL dans les templates
2. **Devises multilingues** :
   - `{% set currency = '€' if lang == 'fr' else '¥' %}`
   - Appliqué sur tous les montants affichés
3. **Format sécurisé** : Utilisation de variables Jinja2 au lieu de :class Alpine.js

---

## 🧪 Tests effectués

### Test 1 : Fonctions DB
```bash
python test_budget_feature.py
```
✅ 13/13 fonctions disponibles
✅ 7 catégories FR/JP chargées
✅ Résumé budgétaire fonctionnel

### Test 2 : Templates
```bash
python test_templates.py
```
✅ event_budget.html (FR/JP)
✅ shopping_list.html (FR/JP)

### Test 3 : Import application
```bash
python -c "import main"
```
✅ Application démarre sans erreur

---

## 🚀 Utilisation

### Démarrage du serveur
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Accès à la fonctionnalité
1. Naviguer vers `/events`
2. Sélectionner un événement
3. Cliquer sur "💰 Gérer le budget"

### Workflow typique

#### 1. Planification (avant l'événement)
- Définir le budget prévisionnel total
- Ajouter les dépenses prévues (location, décoration, etc.)
- Générer la liste de courses
- Saisir les prix prévisionnels des ingrédients

#### 2. Pendant/Après l'événement
- Ajouter les montants réels payés pour chaque dépense
- Cocher "Payé" avec la date
- Sur la liste de courses :
  - Saisir le prix réel payé
  - Cocher "Acheté"
  - → Le prix est automatiquement sauvegardé dans l'historique

#### 3. Analyse
- Consulter le résumé budgétaire
- Comparer prévu vs réel
- Les prix réels deviennent des suggestions pour les prochains événements

---

## 💡 Fonctionnalités avancées

### Apprentissage des prix
Lorsqu'un ingrédient est acheté (case cochée + prix réel saisi), le système :
1. Normalise le nom de l'ingrédient (gestion accents, ligatures)
2. Sauvegarde le prix dans `ingredient_price_history`
3. Incrémente le compteur d'utilisation
4. Met à jour la date de dernière utilisation

Pour les prochains événements :
- Les suggestions de prix sont basées sur l'historique
- Tri par date récente et fréquence d'utilisation

### Multidevise automatique
- Langue FR → Euro (€)
- Langue JP → Yen (¥)
- Pas besoin de configuration manuelle

### Catégories personnalisables
Les fonctions DB permettent d'ajouter des catégories personnalisées :
```python
db.create_expense_category(
    name_fr="Photographe",
    name_jp="写真家",
    icon="📷"
)
```

---

## 📊 Migration de la base de données

### Fichiers
- `migrations/add_budget_management.sql` - Script SQL complet
- `apply_budget_migration.py` - Script d'application avec vérifications

### Application
```bash
python apply_budget_migration.py
```

Vérifications automatiques :
✅ Tables créées
✅ Colonnes ajoutées
✅ Catégories système insérées
✅ Traductions FR/JP
✅ Triggers activés

---

## 🔒 Sécurité et validation

### Validations côté serveur
- Montants >= 0
- Catégories existantes
- Événements existants
- Transactions atomiques

### Triggers SQL
- Mise à jour automatique de `updated_at`
- Normalisation des noms d'ingrédients
- Gestion des doublons dans l'historique

---

## 📝 Notes techniques

### Gestion des ingrédients
Le système utilise `ingredient_aggregator.py` pour :
- Normaliser les noms (œuf/oeuf/Œuf → "oeuf")
- Gérer les accents et ligatures
- Convertir les unités
- Choisir le meilleur nom d'affichage

### Architecture
- **Backend** : FastAPI + SQLite
- **Frontend** : Jinja2 + Alpine.js + TailwindCSS
- **Pattern** : MVC avec DB layer séparé
- **I18n** : Support natif FR/JP

---

## 🎯 Prochaines étapes possibles

### Court terme
- [ ] Export Excel du résumé budgétaire
- [ ] Graphiques de visualisation (prévu vs réel)
- [ ] Alertes quand budget dépassé

### Moyen terme
- [ ] Import automatique de prix depuis API externe
- [ ] Historique des budgets par type d'événement
- [ ] Prévisions basées sur ML

### Long terme
- [ ] Multi-devises avec taux de change
- [ ] Partage de budget entre co-organisateurs
- [ ] Facturation automatique

---

## 🐛 Debugging

### Si la page budget ne s'affiche pas
```python
# Vérifier que la migration a été appliquée
python apply_budget_migration.py

# Vérifier les fonctions DB
python test_budget_feature.py

# Vérifier les templates
python test_templates.py
```

### Si les prix ne se sauvegardent pas
1. Vérifier que `is_purchased` est coché
2. Vérifier que `actual_unit_price` est renseigné
3. Vérifier les logs pour les erreurs de trigger SQL

### Si les catégories ne s'affichent pas
```sql
SELECT * FROM expense_category;
SELECT * FROM expense_category_translation;
```

---

## 📞 Support

Pour toute question ou problème :
1. Consulter les logs de l'application
2. Vérifier les scripts de test
3. Consulter la documentation FastAPI/SQLite

---

**Version** : 1.2
**Date de release** : 2025-11-17
**Auteur** : Claude (avec Christian Epp)
