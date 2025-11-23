# 🎯 Prochaines étapes - Catalogue des Ingrédients

## ✅ Ce qui est opérationnel MAINTENANT

Tout le backend est prêt! Vous pouvez dès maintenant:

### 1. Utiliser les fonctions Python directement

```python
from app.models import db

# Lister tous les ingrédients
ingredients = db.list_ingredient_catalog()
print(f"{len(ingredients)} ingrédients dans le catalogue")

# Mettre à jour un prix
db.update_ingredient_catalog_price(
    ingredient_id=1,
    price_eur=2.50,
    price_jpy=350,
    unit="kg"
)

# Synchroniser avec les recettes
new_count = db.sync_ingredients_from_recipes()
print(f"{new_count} nouveaux ingrédients ajoutés")

# Récupérer le prix pour une devise
price_info = db.get_ingredient_price_for_currency("Tomate", "EUR")
if price_info:
    print(f"Prix: {price_info['price']}€ / {price_info['unit']}")
```

### 2. Accéder aux données via SQL

```bash
# Liste complète des ingrédients
sqlite3 data/recette.sqlite3 "SELECT * FROM ingredient_price_catalog LIMIT 10;"

# Mettre à jour un prix manuellement
sqlite3 data/recette.sqlite3 "UPDATE ingredient_price_catalog SET price_eur = 2.50, price_jpy = 350 WHERE ingredient_name = 'Tomate';"

# Voir les ingrédients avec prix
sqlite3 data/recette.sqlite3 "SELECT ingredient_name, price_eur, price_jpy, unit FROM ingredient_price_catalog WHERE price_eur IS NOT NULL;"
```

---

## 🚀 Approche simple pour finir rapidement

Plutôt que de créer un modal complexe immédiatement, voici une approche progressive:

### Phase 1: Page catalogue simple (1-2h de dev)

**Créer une page basique pour gérer les prix manuellement:**

1. Template HTML simple avec tableau
2. Route GET pour afficher
3. Route POST pour mettre à jour

Avantage: Permet de saisir les prix immédiatement, utilisable tout de suite

### Phase 2: Utilisation dans les dépenses (2-3h de dev)

**Deux approches possibles:**

#### Option A - Simple (recommandé)
- Catégorie "Ingrédients" fonctionne comme les autres
- On saisit manuellement le total prévu/réel
- Note dans la description: "Voir liste de courses pour détail"

#### Option B - Avancé
- Modal spécial qui s'ouvre pour catégorie Ingrédients
- Liste tous les items de la liste de courses
- Calcul automatique du total

**Recommandation:** Commencer par Option A, puis évoluer vers Option B quand nécessaire

---

## 📝 Code minimal pour Page Catalogue

### 1. Créer `app/routes/catalog_routes.py`

```python
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.models import db
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/ingredient-catalog")
async def ingredient_catalog(request: Request, lang: str = "fr", search: Optional[str] = None):
    ingredients = db.list_ingredient_catalog(search, lang)
    return templates.TemplateResponse("ingredient_catalog.html", {
        "request": request,
        "lang": lang,
        "ingredients": ingredients,
        "search": search or ""
    })

@router.post("/ingredient-catalog/sync")
async def sync_catalog(lang: str = Form("fr")):
    count = db.sync_ingredients_from_recipes()
    # TODO: Afficher message flash "{count} ingrédients ajoutés"
    return RedirectResponse(f"/ingredient-catalog?lang={lang}", status_code=303)

@router.post("/ingredient-catalog/{ingredient_id}/update")
async def update_price(
    ingredient_id: int,
    lang: str = Form("fr"),
    price_eur: Optional[str] = Form(None),
    price_jpy: Optional[str] = Form(None),
    unit: str = Form(...)
):
    # Convertir les prix (gérer chaînes vides)
    eur = float(price_eur) if price_eur and price_eur.strip() else None
    jpy = float(price_jpy) if price_jpy and price_jpy.strip() else None

    db.update_ingredient_catalog_price(ingredient_id, eur, jpy, unit)
    return RedirectResponse(f"/ingredient-catalog?lang={lang}", status_code=303)
```

### 2. Enregistrer dans `main.py`

```python
from app.routes import catalog_routes

app.include_router(catalog_routes.router)
```

### 3. Template minimaliste `app/templates/ingredient_catalog.html`

```html
<!DOCTYPE html>
<html>
<head>
    <title>Catalogue des prix</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 p-8">
    <div class="max-w-7xl mx-auto">
        <div class="flex justify-between items-center mb-6">
            <h1 class="text-2xl font-bold">
                📊 {{ 'Catalogue des prix' if lang == 'fr' else '価格カタログ' }}
            </h1>
            <form method="POST" action="/ingredient-catalog/sync">
                <input type="hidden" name="lang" value="{{ lang }}">
                <button class="px-4 py-2 bg-blue-600 text-white rounded">
                    🔄 {{ 'Synchroniser' if lang == 'fr' else '同期' }}
                </button>
            </form>
        </div>

        <!-- Recherche -->
        <form method="GET" class="mb-4">
            <input type="hidden" name="lang" value="{{ lang }}">
            <input type="text" name="search" value="{{ search }}"
                   placeholder="{{ 'Rechercher...' if lang == 'fr' else '検索...' }}"
                   class="px-4 py-2 border rounded">
        </form>

        <!-- Tableau -->
        <div class="bg-white rounded-lg shadow overflow-hidden">
            <table class="w-full">
                <thead class="bg-gray-100">
                    <tr>
                        <th class="px-4 py-2 text-left">Ingrédient</th>
                        <th class="px-4 py-2 text-left">Prix €</th>
                        <th class="px-4 py-2 text-left">Prix ¥</th>
                        <th class="px-4 py-2 text-left">Unité</th>
                        <th class="px-4 py-2">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for ing in ingredients %}
                    <tr class="border-t" x-data="{ editing: false }">
                        <!-- Vue normale -->
                        <td class="px-4 py-2">{{ ing.ingredient_name }}</td>
                        <td class="px-4 py-2">{{ ing.price_eur if ing.price_eur else '-' }}</td>
                        <td class="px-4 py-2">{{ ing.price_jpy if ing.price_jpy else '-' }}</td>
                        <td class="px-4 py-2">{{ ing.unit }}</td>
                        <td class="px-4 py-2 text-center">
                            <button @click="editing = !editing" class="text-blue-600">
                                ✏️ {{ 'Modifier' if lang == 'fr' else '編集' }}
                            </button>
                        </td>
                    </tr>
                    <!-- Formulaire édition -->
                    <tr x-show="editing" x-data="{ editing: false }">
                        <td colspan="5" class="px-4 py-4 bg-gray-50">
                            <form method="POST" action="/ingredient-catalog/{{ ing.id }}/update" class="flex gap-4">
                                <input type="hidden" name="lang" value="{{ lang }}">
                                <input type="number" name="price_eur" value="{{ ing.price_eur or '' }}"
                                       placeholder="Prix €" step="0.01" class="px-2 py-1 border rounded">
                                <input type="number" name="price_jpy" value="{{ ing.price_jpy or '' }}"
                                       placeholder="Prix ¥" step="0.01" class="px-2 py-1 border rounded">
                                <input type="text" name="unit" value="{{ ing.unit }}"
                                       class="px-2 py-1 border rounded w-24">
                                <button type="submit" class="px-4 py-1 bg-green-600 text-white rounded">
                                    💾 Enregistrer
                                </button>
                                <button type="button" @click="editing = false"
                                        class="px-4 py-1 bg-gray-500 text-white rounded">
                                    Annuler
                                </button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <p class="mt-4 text-gray-600">
            {{ ingredients|length }} ingrédients •
            <a href="/events?lang={{ lang }}" class="text-blue-600">← Retour</a>
        </p>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
</body>
</html>
```

### 4. Ajouter lien dans le menu

Modifier le header/menu principal pour ajouter:
```html
<a href="/ingredient-catalog?lang={{ lang }}">📊 Catalogue</a>
```

---

## 🎯 Résultat attendu

Avec ce code minimal (environ 150 lignes au total):

✅ Page catalogue fonctionnelle
✅ Édition inline des prix
✅ Synchronisation depuis les recettes
✅ Recherche d'ingrédients
✅ Support FR/JP

**Temps estimé:** 30min - 1h de mise en place

Ensuite, vous pourrez utiliser ces prix dans vos dépenses!

---

## 💡 Utilisation pratique

**Workflow recommandé pour l'instant:**

1. Aller sur "📊 Catalogue"
2. Saisir les prix manuellement pour les ingrédients fréquents
3. Créer une dépense normale "🍅 Ingrédients"
4. Montant = Total calculé manuellement ou depuis liste de courses

**Plus tard (Phase 2):**
- Le modal s'ouvrira automatiquement
- Calcul automatique depuis la liste de courses
- Mise à jour automatique du catalogue

---

**Voulez-vous que je crée ces 3 fichiers maintenant?** (routes, template, mise à jour main.py)
