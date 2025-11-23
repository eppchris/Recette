# Guide de test - Système de catégories et tags

## ✅ Ce qui a été implémenté

### Backend
- ✅ Migration SQL avec 4 tables (category, tag, recipe_category, recipe_tag)
- ✅ 8 catégories pré-définies bilingues FR/JP
- ✅ 21 tags pré-définis avec couleurs
- ✅ 10 fonctions dans db.py
- ✅ 9 routes API dans recipe_routes.py

### Frontend
- ✅ Section catégories/tags dans le formulaire d'édition
- ✅ Affichage des catégories/tags dans la page détail
- ✅ Sauvegarde automatique lors de l'édition

## 🚀 Étapes de déploiement

### 1. Appliquer la migration

```bash
cd /Users/christianepp/Documents/DEV/Recette
sqlite3 data/recette.sqlite3 < migrations/add_categories_and_tags.sql
```

### 2. Vérifier que les données sont chargées

```bash
sqlite3 data/recette.sqlite3 "SELECT COUNT(*) FROM category;"
# Devrait retourner: 8

sqlite3 data/recette.sqlite3 "SELECT COUNT(*) FROM tag;"
# Devrait retourner: 21

sqlite3 data/recette.sqlite3 "SELECT name_fr, name_jp FROM category LIMIT 3;"
# Devrait afficher les catégories
```

### 3. Redémarrer l'application

```bash
# En mode développement
python3 main.py
```

## 🧪 Tests fonctionnels

### Test 1 : Charger les catégories et tags

1. Ouvrir le navigateur : `http://localhost:8000/recipes?lang=fr`
2. Cliquer sur une recette existante
3. Ouvrir la console du navigateur (F12)
4. Taper :
   ```javascript
   fetch('/api/categories').then(r => r.json()).then(console.log)
   fetch('/api/tags').then(r => r.json()).then(console.log)
   ```
5. ✅ Devrait afficher les 8 catégories et 21 tags

### Test 2 : Modifier une recette

1. Sur la page d'une recette, cliquer sur "Modifier"
2. Descendre jusqu'à la section "Catégories et Tags"
3. ✅ Vous devriez voir :
   - 8 checkboxes pour les catégories
   - 21 boutons colorés pour les tags
4. Sélectionner :
   - Catégorie : "Plat principal"
   - Tags : "Viande", "Facile", "Rapide"
5. Cliquer sur "Sauvegarder"
6. ✅ La page devrait se recharger et afficher les tags en haut

### Test 3 : Vérifier en base de données

```bash
# Remplacer 1 par l'ID de votre recette
sqlite3 data/recette.sqlite3 "SELECT category_id FROM recipe_category WHERE recipe_id = 1;"
sqlite3 data/recette.sqlite3 "SELECT tag_id FROM recipe_tag WHERE recipe_id = 1;"
```

✅ Devrait afficher les IDs des catégories et tags sélectionnés

### Test 4 : Test API direct

```bash
# Lister toutes les catégories
curl http://localhost:8000/api/categories

# Lister tous les tags
curl http://localhost:8000/api/tags

# Voir les catégories d'une recette (ID 1)
curl http://localhost:8000/api/recipes/1/categories

# Voir les tags d'une recette (ID 1)
curl http://localhost:8000/api/recipes/1/tags

# Assigner des catégories à une recette
curl -X POST http://localhost:8000/api/recipes/1/categories \
  -H "Content-Type: application/json" \
  -d '{"category_ids": [1, 2]}'

# Assigner des tags à une recette
curl -X POST http://localhost:8000/api/recipes/1/tags \
  -H "Content-Type: application/json" \
  -d '{"tag_ids": [5, 9, 12]}'
```

## 🎨 Vérification visuelle

### Catégories dans le formulaire
- ✅ Liste verticale avec checkboxes
- ✅ Nom en FR ou JP selon la langue
- ✅ Description en petit texte gris

### Tags dans le formulaire
- ✅ Grille de boutons colorés
- ✅ Changement visuel quand sélectionné (ring, plus opaque)
- ✅ Couleur de fond et bordure selon le tag

### Affichage dans la page détail
- ✅ Section sous le type et nombre de personnes
- ✅ Catégories : badges bleus arrondis
- ✅ Tags : badges avec couleur personnalisée

## 🐛 Problèmes possibles

### Erreur : "no such table: category"
**Cause** : Migration pas appliquée
**Solution** : Exécuter la migration SQL

### Les tags ne s'affichent pas dans le formulaire
**Cause** : Erreur JS dans la console
**Solution** : Ouvrir F12, regarder les erreurs, vérifier que `/api/tags` fonctionne

### Les tags ne se sauvegardent pas
**Cause** : L'ID de la recette est null
**Solution** : Vérifier que `{{ rec['id'] }}` retourne bien un nombre dans la page

## 📊 Statistiques utiles

```bash
# Nombre de recettes par catégorie
sqlite3 data/recette.sqlite3 "
SELECT c.name_fr, COUNT(rc.recipe_id) as nb_recettes
FROM category c
LEFT JOIN recipe_category rc ON c.id = rc.category_id
GROUP BY c.id
ORDER BY nb_recettes DESC;"

# Tags les plus utilisés
sqlite3 data/recette.sqlite3 "
SELECT t.name_fr, COUNT(rt.recipe_id) as nb_recettes
FROM tag t
LEFT JOIN recipe_tag rt ON t.id = rt.tag_id
GROUP BY t.id
ORDER BY nb_recettes DESC
LIMIT 10;"

# Recettes sans catégorie
sqlite3 data/recette.sqlite3 "
SELECT r.id, r.title_fr
FROM recipe r
LEFT JOIN recipe_category rc ON r.id = rc.recipe_id
WHERE rc.recipe_id IS NULL;"
```

## 🎯 Prochaines étapes (optionnel)

1. **Afficher dans la liste de recettes** : Ajouter les badges dans `recipes_list.html`
2. **Recherche par filtres** : Ajouter des boutons pour filtrer par catégorie/tag
3. **Page admin** : Créer/supprimer des tags personnalisés
4. **Suggestion IA** : Utiliser Groq pour suggérer des tags automatiquement

## 💾 Backup avant test

```bash
# Sauvegarder la base avant de tester
cp data/recette.sqlite3 data/recette_backup_$(date +%Y%m%d).sqlite3
```

## 🔄 Rollback si problème

```bash
# Supprimer les tables si besoin
sqlite3 data/recette.sqlite3 "
DROP TABLE IF EXISTS recipe_tag;
DROP TABLE IF EXISTS recipe_category;
DROP TABLE IF EXISTS tag;
DROP TABLE IF EXISTS category;"
```
