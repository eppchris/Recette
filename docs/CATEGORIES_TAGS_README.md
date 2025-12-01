# Système de catégories et tags - Documentation

## Vue d'ensemble

Système de catégorisation flexible pour les recettes avec :
- **Catégories** : Types de plats (Entrée, Plat principal, Dessert, etc.)
- **Tags** : Caractéristiques multiples (Viande, Végétarien, Rapide, etc.)
- **Bilingue** : Français / Japonais
- **Relations many-to-many** : Une recette peut avoir plusieurs catégories et tags

## ✅ Ce qui est fait

### 1. Migration SQL (`migrations/add_categories_and_tags.sql`)

**Tables créées** :
- `category` : 8 catégories pré-définies
- `tag` : 21 tags pré-définies avec couleurs
- `recipe_category` : Relation many-to-many
- `recipe_tag` : Relation many-to-many

**Données pré-chargées** :

**Catégories** :
1. Entrée / 前菜
2. Plat principal / メイン料理
3. Accompagnement / 付け合わせ
4. Dessert / デザート
5. Sauce / ソース
6. Boisson / 飲み物
7. Apéritif / アペリティフ
8. Petit-déjeuner / 朝食

**Tags (21 au total)** :
- Type de protéine : Viande, Poisson, Fruits de mer, Volaille
- Régimes : Végétarien, Végétalien, Sans gluten, Sans lactose
- Temps : Rapide (<30min), Moyen (30-60min), Long (>1h)
- Difficulté : Facile, Intermédiaire, Difficile
- Cuisine : Française, Japonaise, Italienne, Asiatique
- Occasions : Fête, Quotidien, Saison

### 2. Fonctions de base de données (`app/models/db.py`)

**10 fonctions ajoutées** (lignes 2338-2511) :

```python
# Récupération
get_all_categories()           # Toutes les catégories
get_all_tags()                 # Tous les tags
get_recipe_categories(recipe_id)  # Catégories d'une recette
get_recipe_tags(recipe_id)     # Tags d'une recette

# Modification
set_recipe_categories(recipe_id, category_ids)  # Définir les catégories
set_recipe_tags(recipe_id, tag_ids)            # Définir les tags

# Gestion des tags
create_tag(name_fr, name_jp, ...)  # Créer un nouveau tag
delete_tag(tag_id)                 # Supprimer un tag (non-système)

# Recherche
search_recipes_by_filters(search_text, category_ids, tag_ids, lang)
```

## 🚧 Ce qu'il reste à faire

### 3. Modifier l'interface utilisateur

#### A. Formulaire de création/édition de recette

**Fichier** : `app/templates/recipe_detail.html`

**Ajouter dans le formulaire** :

```html
<!-- Section Catégories -->
<div class="mb-4">
    <label class="block text-sm font-medium mb-2">
        <span x-show="lang === 'fr'">Catégories</span>
        <span x-show="lang === 'jp'">カテゴリー</span>
    </label>
    <div class="space-y-2">
        <template x-for="category in categories" :key="category.id">
            <label class="flex items-center">
                <input type="checkbox"
                       :value="category.id"
                       x-model="selectedCategories"
                       class="mr-2">
                <span x-text="lang === 'fr' ? category.name_fr : category.name_jp"></span>
            </label>
        </template>
    </div>
</div>

<!-- Section Tags -->
<div class="mb-4">
    <label class="block text-sm font-medium mb-2">
        <span x-show="lang === 'fr'">Tags</span>
        <span x-show="lang === 'jp'">タグ</span>
    </label>
    <div class="flex flex-wrap gap-2">
        <template x-for="tag in tags" :key="tag.id">
            <label class="inline-flex items-center px-3 py-1 rounded-full cursor-pointer"
                   :style="selectedTags.includes(tag.id) ? `background-color: ${tag.color}20; border: 2px solid ${tag.color}` : 'border: 2px solid #e5e7eb'">
                <input type="checkbox"
                       :value="tag.id"
                       x-model="selectedTags"
                       class="hidden">
                <span class="text-sm" x-text="lang === 'fr' ? tag.name_fr : tag.name_jp"></span>
            </label>
        </template>
    </div>
</div>
```

**Modifier la fonction Alpine.js** :

```javascript
function recipeDetail() {
    return {
        // ... variables existantes ...
        categories: [],
        tags: [],
        selectedCategories: [],
        selectedTags: [],

        async init() {
            // ... code existant ...

            // Charger les catégories et tags
            await this.loadCategoriesAndTags();

            if (this.recipeId) {
                await this.loadRecipe(this.recipeId);
            }
        },

        async loadCategoriesAndTags() {
            const [catResponse, tagResponse] = await Promise.all([
                fetch('/api/categories'),
                fetch('/api/tags')
            ]);
            this.categories = await catResponse.json();
            this.tags = await tagResponse.json();
        },

        async loadRecipe(id) {
            // ... code existant ...

            // Charger les catégories et tags de la recette
            const [catResponse, tagResponse] = await Promise.all([
                fetch(`/api/recipes/${id}/categories`),
                fetch(`/api/recipes/${id}/tags`)
            ]);
            const recipeCats = await catResponse.json();
            const recipeTags = await tagResponse.json();

            this.selectedCategories = recipeCats.map(c => c.id);
            this.selectedTags = recipeTags.map(t => t.id);
        },

        async saveRecipe() {
            // ... code existant pour sauvegarder la recette ...

            // Sauvegarder les catégories et tags
            if (this.recipeId) {
                await Promise.all([
                    fetch(`/api/recipes/${this.recipeId}/categories`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ category_ids: this.selectedCategories })
                    }),
                    fetch(`/api/recipes/${this.recipeId}/tags`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ tag_ids: this.selectedTags })
                    })
                ]);
            }
        }
    }
}
```

#### B. Affichage dans la liste de recettes

**Fichier** : `app/templates/recipes_list.html`

Ajouter sous le titre de chaque recette :

```html
<!-- Catégories -->
<div class="flex flex-wrap gap-1 mt-2">
    <template x-for="cat in recipe.categories" :key="cat.id">
        <span class="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
              x-text="lang === 'fr' ? cat.name_fr : cat.name_jp"></span>
    </template>
</div>

<!-- Tags -->
<div class="flex flex-wrap gap-1 mt-2">
    <template x-for="tag in recipe.tags" :key="tag.id">
        <span class="px-2 py-1 text-xs rounded"
              :style="`background-color: ${tag.color}20; color: ${tag.color}`"
              x-text="lang === 'fr' ? tag.name_fr : tag.name_jp"></span>
    </template>
</div>
```

### 4. Routes API à ajouter

**Fichier** : `app/routes/recipe_routes.py`

```python
from app.models.db import (
    get_all_categories, get_all_tags,
    get_recipe_categories, get_recipe_tags,
    set_recipe_categories, set_recipe_tags
)

# Routes pour les catégories et tags
@router.get("/api/categories")
async def api_get_categories():
    return get_all_categories()

@router.get("/api/tags")
async def api_get_tags():
    return get_all_tags()

@router.get("/api/recipes/{recipe_id}/categories")
async def api_get_recipe_categories(recipe_id: int):
    return get_recipe_categories(recipe_id)

@router.get("/api/recipes/{recipe_id}/tags")
async def api_get_recipe_tags(recipe_id: int):
    return get_recipe_tags(recipe_id)

@router.post("/api/recipes/{recipe_id}/categories")
async def api_set_recipe_categories(recipe_id: int, request: Request):
    data = await request.json()
    category_ids = data.get('category_ids', [])
    set_recipe_categories(recipe_id, category_ids)
    return {"status": "ok"}

@router.post("/api/recipes/{recipe_id}/tags")
async def api_set_recipe_tags(recipe_id: int, request: Request):
    data = await request.json()
    tag_ids = data.get('tag_ids', [])
    set_recipe_tags(recipe_id, tag_ids)
    return {"status": "ok"}
```

### 5. Améliorer la recherche

**Fichier** : `app/templates/recipes_list.html`

Ajouter des filtres en haut de la liste :

```html
<div class="bg-white border p-4 rounded mb-4">
    <!-- Recherche textuelle existante -->
    <input type="text" x-model="searchText"
           placeholder="Rechercher...">

    <!-- Filtre par catégories -->
    <div class="mt-4">
        <label class="block font-medium mb-2">Catégories</label>
        <div class="flex flex-wrap gap-2">
            <template x-for="cat in categories" :key="cat.id">
                <button @click="toggleCategory(cat.id)"
                        :class="selectedCategories.includes(cat.id) ? 'bg-blue-500 text-white' : 'bg-gray-200'"
                        class="px-3 py-1 rounded"
                        x-text="lang === 'fr' ? cat.name_fr : cat.name_jp"></button>
            </template>
        </div>
    </div>

    <!-- Filtre par tags -->
    <div class="mt-4">
        <label class="block font-medium mb-2">Tags</label>
        <div class="flex flex-wrap gap-2">
            <template x-for="tag in tags" :key="tag.id">
                <button @click="toggleTag(tag.id)"
                        :class="selectedTags.includes(tag.id) ? '' : 'opacity-50'"
                        :style="`background-color: ${tag.color}; color: white`"
                        class="px-3 py-1 rounded"
                        x-text="lang === 'fr' ? tag.name_fr : tag.name_jp"></button>
            </template>
        </div>
    </div>

    <button @click="search()" class="mt-4 bg-blue-500 text-white px-4 py-2 rounded">
        Rechercher
    </button>
</div>
```

### 6. Page d'administration des tags

**Créer** : `app/templates/tags_admin.html`

Page pour :
- Voir tous les tags
- Créer de nouveaux tags personnalisés
- Supprimer les tags non-système
- Modifier les couleurs

## 📋 Ordre de déploiement recommandé

1. **Appliquer la migration SQL** :
   ```bash
   sqlite3 data/recette.sqlite3 < migrations/add_categories_and_tags.sql
   ```

2. **Déployer le code** (db.py déjà mis à jour)

3. **Tester les fonctions** :
   ```python
   from app.models.db import get_all_categories, get_all_tags
   print(get_all_categories())  # Devrait afficher 8 catégories
   print(get_all_tags())        # Devrait afficher 21 tags
   ```

4. **Ajouter les routes API** (étape 4)

5. **Modifier l'interface** (étapes 3A et 3B)

6. **Améliorer la recherche** (étape 5)

7. **Créer la page admin** (étape 6) - optionnel

## 🎨 Personnalisation

### Ajouter une nouvelle catégorie :

```sql
INSERT INTO category (name_fr, name_jp, description_fr, description_jp, display_order)
VALUES ('Soupe', 'スープ', 'Soupes et potages', 'スープ', 9);
```

### Ajouter un nouveau tag :

```python
from app.models.db import create_tag
create_tag('Épicé', '辛い', 'Plat épicé', '辛い料理', '#FF6B6B')
```

## 🔍 Recherche avancée

Utiliser `search_recipes_by_filters()` :

```python
# Recherche de recettes végétariennes ET rapides
results = search_recipes_by_filters(
    tag_ids=[5, 9],  # Végétarien (ID 5) + Rapide (ID 9)
    lang='fr'
)

# Recherche de desserts avec "chocolat"
results = search_recipes_by_filters(
    search_text='chocolat',
    category_ids=[4],  # Dessert
    lang='fr'
)
```
