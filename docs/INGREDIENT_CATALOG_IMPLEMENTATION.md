# 🍅 Implémentation du Catalogue des Prix des Ingrédients

## ✅ Ce qui est terminé

### 1. Base de données ✅
- **Table `ingredient_price_catalog`** créée avec 158 ingrédients synchronisés
  - Colonnes: `id`, `ingredient_name`, `price_eur`, `price_jpy`, `unit`, `last_updated`
  - Tous les ingrédients des recettes sont déjà importés (sans prix)

- **Table `expense_ingredient_detail`** créée
  - Stocke le détail de chaque ingrédient pour une dépense
  - Colonnes: `expense_id`, `shopping_list_item_id`, `ingredient_name`, `quantity`, `unit`
  - `planned_unit_price`, `actual_unit_price`, `planned_total`, `actual_total`

- **Trigger automatique** `update_catalog_after_actual_price`
  - Met à jour automatiquement le catalogue quand un prix réel est saisi
  - Utilise la devise de l'événement (EUR ou JPY)

- **Catégorie "Ingrédients"** ajoutée
  - ID: `8`
  - Icon: `🍅`
  - Nom FR: "Ingrédients"
  - Nom JP: "食材"

### 2. Fonctions DB ajoutées ✅
Fichier: `app/models/db.py` (lignes 1537-1754)

**Gestion du catalogue:**
- `list_ingredient_catalog(search, lang)`: Liste tous les ingrédients (avec recherche)
- `get_ingredient_from_catalog(ingredient_id)`: Récupère un ingrédient par ID
- `update_ingredient_catalog_price(id, price_eur, price_jpy, unit)`: Met à jour les prix
- `sync_ingredients_from_recipes()`: Synchronise avec les recettes
- `get_ingredient_price_for_currency(name, currency)`: Récupère le prix pour une devise

**Gestion des détails de dépense:**
- `save_expense_ingredient_details(expense_id, ingredients_data)`: Sauvegarde le détail
- `get_expense_ingredient_details(expense_id)`: Récupère le détail

### 3. Template modifié ✅
- **Champ "Budget prévisionnel total" supprimé** de `event_budget.html`
- Ne reste que: Budget prévu | Dépensé | Différence (calculés automatiquement)

### 4. Migration SQL ✅
- Fichier: `migrations/add_ingredient_catalog.sql`
- Script d'application: `apply_ingredient_catalog_migration.py`
- Migration appliquée avec succès

---

## 🚧 Ce qui reste à implémenter

### 5. Page de gestion du catalogue (À FAIRE)

**Créer:** `app/templates/ingredient_catalog.html`
```html
- Tableau de tous les ingrédients
- Colonnes: Nom | Prix € | Prix ¥ | Unité
- Édition inline ou modal
- Recherche par nom
- Bouton "🔄 Synchroniser depuis les recettes"
```

**Créer:** Route dans `app/routes/` (nouveau fichier ou ajouter à existant)
```python
@router.get("/ingredient-catalog")
async def ingredient_catalog_page(request: Request, lang: str = "fr", search: str = None):
    ingredients = db.list_ingredient_catalog(search, lang)
    return templates.TemplateResponse("ingredient_catalog.html", {
        "request": request,
        "lang": lang,
        "ingredients": ingredients
    })

@router.post("/ingredient-catalog/{ingredient_id}/update")
async def update_ingredient_price(
    ingredient_id: int,
    price_eur: Optional[float] = Form(None),
    price_jpy: Optional[float] = Form(None),
    unit: str = Form(...),
):
    db.update_ingredient_catalog_price(ingredient_id, price_eur, price_jpy, unit)
    return RedirectResponse("/ingredient-catalog", status_code=303)

@router.post("/ingredient-catalog/sync")
async def sync_catalog():
    count = db.sync_ingredients_from_recipes()
    # Afficher message: "{count} ingrédients ajoutés"
    return RedirectResponse("/ingredient-catalog", status_code=303)
```

**Ajouter:** Lien dans le menu principal (templates/base ou header)

---

### 6. Modification du formulaire de dépense (À FAIRE)

**Dans `event_budget.html` - Formulaire d'ajout:**

Détecter quand catégorie = 8 (Ingrédients) et afficher un comportement différent:

```html
<!-- JavaScript Alpine.js -->
<div x-data="{ selectedCategory: null }">
    <select name="category_id" @change="selectedCategory = $event.target.value">
        {% for category in categories %}
        <option value="{{ category.id }}">{{ category.icon }} {{ category.name }}</option>
        {% endfor %}
    </select>

    <!-- Formulaire normal pour autres catégories -->
    <div x-show="selectedCategory != 8">
        <input type="number" name="planned_amount" ...>
        <input type="number" name="actual_amount" ...>
    </div>

    <!-- Modal spécial pour Ingrédients (catégorie 8) -->
    <div x-show="selectedCategory == 8">
        <button type="button" @click="openIngredientModal()">
            📝 {{ 'Saisir les prix des ingrédients' if lang == 'fr' else '食材の価格を入力' }}
        </button>
    </div>
</div>
```

---

### 7. Modal de saisie des prix des ingrédients (À FAIRE)

**Créer modal dans `event_budget.html`:**

```html
<!-- Modal ingrédients -->
<div x-show="showIngredientPricing" class="fixed inset-0 bg-black bg-opacity-50 z-50">
    <div class="bg-white max-w-4xl mx-auto mt-20 rounded-lg p-6">
        <h3>{{ 'Prix des ingrédients' if lang == 'fr' else '食材の価格' }}</h3>

        <table>
            <thead>
                <tr>
                    <th>Ingrédient</th>
                    <th>Quantité</th>
                    <th>Unité</th>
                    <th>Prix unitaire prévu</th>
                    <th>Total prévu</th>
                </tr>
            </thead>
            <tbody>
                {% for item in shopping_list_items %}
                <tr>
                    <td>{{ item.ingredient_name }}</td>
                    <td>{{ item.quantity }}</td>
                    <td>{{ item.unit }}</td>
                    <td>
                        <input type="number"
                               name="ingredient_{{ item.id }}_price"
                               value="{{ get_price_from_catalog(item.ingredient_name, event.currency) }}"
                               step="0.01">
                    </td>
                    <td class="calculated">{{ item.quantity × prix }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="total">
            Total prévu: <span id="totalPlanned">0.00</span> {{ currency }}
        </div>

        <button type="button" @click="saveIngredientPricing()">Enregistrer</button>
        <button type="button" @click="showIngredientPricing = false">Annuler</button>
    </div>
</div>
```

---

### 8. Routes pour gérer la dépense "Ingrédients" (À FAIRE)

**Modifier `app/routes/event_routes.py`:**

```python
@router.post("/events/{event_id}/expenses/add")
async def event_add_expense(...):
    # ... code existant ...

    # NOUVEAU: Si catégorie_id == 8 (Ingrédients)
    if category_id == 8:
        # Récupérer les ingrédients depuis la liste de courses
        shopping_items = db.get_event_shopping_list(event_id, lang)

        # Calculer les totaux depuis les prix saisis
        ingredients_data = []
        total_planned = 0

        for item in shopping_items:
            price_key = f"ingredient_{item['id']}_price"
            unit_price = request.form.get(price_key)

            if unit_price:
                unit_price = float(unit_price)
                total = item['quantity'] * unit_price
                total_planned += total

                ingredients_data.append({
                    'shopping_list_item_id': item['id'],
                    'ingredient_name': item['ingredient_name'],
                    'quantity': item['quantity'],
                    'unit': item['unit'],
                    'planned_unit_price': unit_price,
                    'actual_unit_price': None
                })

        # Créer la dépense avec le total calculé
        expense_id = db.create_event_expense(
            event_id=event_id,
            category_id=8,
            description=description,
            planned_amount=total_planned,
            ...
        )

        # Sauvegarder le détail des ingrédients
        db.save_expense_ingredient_details(expense_id, ingredients_data)

    else:
        # Comportement normal pour autres catégories
        expense_id = db.create_event_expense(...)
```

---

### 9. Modification pour ajouter prix réels (À FAIRE)

Même logique que ci-dessus, mais dans le formulaire de modification:
- Afficher le modal avec colonnes: Prix prévu (lecture seule) | Prix réel (éditable)
- Calculer le total réel
- Mettre à jour `expense_ingredient_detail` avec `actual_unit_price`
- Le trigger mettra à jour automatiquement le catalogue

---

### 10. Intégration dans l'import de recettes (À FAIRE)

**Modifier le service d'import de recettes:**

Après avoir importé une recette, vérifier si tous les ingrédients sont dans le catalogue:

```python
# Dans le service d'import
def import_recipe_from_json(...):
    # ... import de la recette ...

    # Synchroniser le catalogue
    db.sync_ingredients_from_recipes()
```

---

## 📊 Résumé de l'état

| Tâche | État | Fichiers |
|-------|------|----------|
| Tables DB | ✅ Terminé | migrations/add_ingredient_catalog.sql |
| Fonctions DB | ✅ Terminé | app/models/db.py (1537-1754) |
| Catégorie Ingrédients | ✅ Ajoutée | ID=8 en DB |
| Suppression budget total | ✅ Terminé | app/templates/event_budget.html |
| Page catalogue | ⏸️ À faire | app/templates/ingredient_catalog.html + route |
| Formulaire détection catégorie | ⏸️ À faire | app/templates/event_budget.html (JS) |
| Modal saisie prix | ⏸️ À faire | app/templates/event_budget.html |
| Routes spéciales | ⏸️ À faire | app/routes/event_routes.py |
| Intégration import | ⏸️ À faire | Service d'import |

---

## 🎯 Prochaines actions recommandées

1. **Tester ce qui est fait:** Vérifier que la base de données fonctionne
2. **Créer la page catalogue** (plus simple, permet de saisir les prix manuellement)
3. **Implémenter le modal** dans le formulaire de dépense
4. **Tester le workflow complet** : Créer dépense Ingrédients → Saisir prix → Voir total

---

## 🧪 Tests à effectuer

```bash
# Vérifier que le catalogue contient les ingrédients
sqlite3 data/recette.sqlite3 "SELECT COUNT(*) FROM ingredient_price_catalog;"
# Résultat attendu: 158

# Vérifier la catégorie Ingrédients
sqlite3 data/recette.sqlite3 "SELECT c.id, t.name FROM expense_category c JOIN expense_category_translation t ON t.category_id = c.id WHERE c.id = 8;"
# Résultat attendu: 8|Ingrédients (FR), 8|食材 (JP)

# Tester une fonction Python
python -c "from app.models import db; print(len(db.list_ingredient_catalog()))"
# Résultat attendu: 158
```

---

Date: 2025-11-17
Développeur: Claude + Christian
