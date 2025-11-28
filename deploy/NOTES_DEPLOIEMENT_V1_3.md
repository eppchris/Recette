# Notes de Déploiement - Version 1.3

## Date : 2025-11-25

## Nouvelles Fonctionnalités

### 1. Gestion Complète du Budget des Ingrédients

#### Interface de Budget Simplifiée
- **Ligne de résumé permanente** : Affichage constant des montants prévu/réel des ingrédients
- **Saisie unique** : Un seul champ pour le montant total réel (plus simple que par ingrédient)
- **Calculs automatiques** : Le budget prévu et dépensé incluent automatiquement les ingrédients
- **Catégorie dédiée** : Nouvelle catégorie "🥕 Ingrédients" / "食材" (ID 9)

#### Modifications de la Base de Données
```sql
-- Nouvelle colonne pour stocker le montant réel total des ingrédients
ALTER TABLE event ADD COLUMN ingredients_actual_total REAL DEFAULT 0;

-- Colonne existante pour les prix unitaires prévus
-- (déjà présente : planned_unit_price dans shopping_list_item)

-- Nouvelle catégorie de dépense
INSERT INTO expense_category (id, icon, is_system) VALUES (9, '🥕', 1);
INSERT INTO expense_category_translation (category_id, lang, name)
VALUES (9, 'fr', 'Ingrédients'), (9, 'jp', '食材');
```

#### Workflow Utilisateur
1. Ouvrir la page Budget d'un événement
2. La ligne de résumé affiche automatiquement le montant prévu (calculé depuis le catalogue)
3. Après les courses, saisir le montant total payé dans le champ "Réel"
4. Cliquer sur "Enregistrer"
5. Les totaux en haut de page (Budget prévu, Dépensé, Différence) sont mis à jour automatiquement

### 2. Système de Conversions d'Unités Amélioré

#### Import depuis CSV
- Nouveau fichier : `data/Unit_conversion.csv` (33 conversions)
- Script d'import : `import_unit_conversions.py`
- Catégories : comptage (10), poids (8), volume (15)

#### Nouvelle Règle de Conversion
- **Avant** : Erreur si l'unité n'était pas dans la table de conversion
- **Après** : Conservation de l'unité d'origine si aucune conversion trouvée
- Exemple : "pièce" reste "pièce" au lieu de générer une erreur

#### Gestion des Erreurs
- Messages utilisateur en français/japonais pour les contraintes UNIQUE
- Pas de plantage si tentative de doublon de conversion

### 3. Corrections de Bugs Critiques

#### Prix des Ingrédients à 0€
- **Problème** : Les ingrédients affichaient 0€ dans le budget malgré des entrées dans le catalogue
- **Cause** : Recherche sensible à la casse ("ail" vs "Ail")
- **Solution** : Utilisation de `LOWER()` dans les requêtes SQL pour recherche insensible à la casse

#### Arrondi des Prix Unitaires
- **Problème** : Affichage de prix comme 0.006666666€
- **Solution** : Arrondi supérieur à 2 décimales avec `Math.ceil(unitPrice * 100) / 100`

#### Liste de Courses et Changement de Langue
- **Problème** : La liste de courses ne se régénérait pas au changement de langue
- **Solution** : Détection automatique de la langue et régénération si nécessaire

#### Suppression de Recettes d'un Événement
- **Problème** : La liste de courses n'était pas mise à jour après suppression de recettes
- **Solution** : Suppression automatique de la liste lors de modifications des recettes/portions

### 4. Import de recettes depuis PDF avec IA
- Ajout d'un système d'import de recettes depuis des fichiers PDF
- Extraction automatique du texte avec **PyPDF2**
- Analyse intelligente avec l'API Groq (LLM) pour extraire :
  - Nom de la recette
  - Langue détectée (français ou japonais)
  - Nombre de personnes
  - Liste des ingrédients (nom, quantité, unité, notes)
  - Étapes de préparation
- Interface en deux étapes :
  1. Upload et analyse du PDF
  2. Vérification/modification avant sauvegarde

### 2. Corrections de Régressions

#### Bouton de Traduction
- **Problème** : Le bouton de traduction ne s'affichait pas après import PDF
- **Solution** : Ajout de la vérification `has_translation` pour afficher le bouton correctement
- **Comportement** : Comme pour l'import CSV, seule la langue détectée est créée, l'autre langue reste vide et propose la traduction automatique

#### Édition des Recettes
- **Problème** : Impossible d'ajouter/supprimer des ingrédients et des étapes en mode édition
- **Solution** : Ajout des boutons et des fonctions JavaScript manquantes :
  - `addIngredient()` / `removeIngredient()`
  - `addStep()` / `removeStep()`

## Fichiers Modifiés

1. **requirements.txt** - Ajout de `PyPDF2>=3.0.0`
2. **app/services/pdf_recipe_extractor.py** - NOUVEAU : Service d'extraction PDF
3. **app/routes/recipe_routes.py** - Ajout des routes d'import PDF + correction `has_translation`
4. **app/templates/import_recipes.html** - Interface unifiée CSV/PDF
5. **app/templates/recipe_detail.html** - Corrections boutons d'édition
6. **app/templates/base.html** - Menu unifié "Import"
7. **deploy/deploy_synology_V1_3.sh** - NOUVEAU : Script de déploiement

## Changement Technique Important : pdfplumber → PyPDF2

### Pourquoi ce changement ?

**Problème avec pdfplumber** :
- La bibliothèque `pdfplumber` dépend de `pypdfium2`
- `pypdfium2` nécessite `git` pour l'installation (dépendance `ctypesgen` depuis GitHub)
- Le Synology DS213+ n'a pas `git` installé et accessible via SSH
- Erreur lors du déploiement : `ERROR: Cannot find command 'git'`

**Solution avec PyPDF2** :
- PyPDF2 est une bibliothèque pure Python
- Aucune dépendance système requise
- Installation simple via pip sans compilation
- Fonctionnalité d'extraction de texte identique pour notre cas d'usage

### Code Modifié

**Avant (pdfplumber)** :
```python
import pdfplumber

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        text += page.extract_text()
```

**Après (PyPDF2)** :
```python
import PyPDF2

with open(pdf_path, 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    for page in pdf_reader.pages:
        text += page.extract_text()
```

## Prérequis Déploiement

### 1. Migrations de Base de Données

**IMPORTANT** : Exécuter ces commandes SQL sur le serveur avant de démarrer l'application :

```bash
ssh admin@192.168.1.14
cd recette
sqlite3 data/recette.sqlite3
```

Puis dans sqlite3 :
```sql
-- Ajouter la colonne pour le montant réel des ingrédients
ALTER TABLE event ADD COLUMN ingredients_actual_total REAL DEFAULT 0;

-- Ajouter la colonne pour le prix total réel par ingrédient (si pas déjà fait)
ALTER TABLE shopping_list_item ADD COLUMN actual_total_price REAL DEFAULT 0;

-- Créer la catégorie Ingrédients (si pas déjà fait)
INSERT OR IGNORE INTO expense_category (id, icon, is_system) VALUES (9, '🥕', 1);
INSERT OR IGNORE INTO expense_category_translation (category_id, lang, name)
VALUES (9, 'fr', 'Ingrédients'), (9, 'jp', '食材');

-- Vérifier les conversions d'unités
SELECT COUNT(*) FROM unit_conversion;
-- Devrait retourner 33 (ou plus)
```

### 2. Import des Conversions d'Unités

Si la table `unit_conversion` est vide ou incomplète :
```bash
cd recette
source venv/bin/activate
python import_unit_conversions.py
```

Cela importera les 33 conversions depuis `data/Unit_conversion.csv`.

### 3. Variables d'Environnement
Le fichier `.env` sur le serveur doit contenir :
```bash
GROQ_API_KEY=votre_clé_api_groq
```

Sans cette clé, l'import PDF ne fonctionnera pas (l'analyse IA échouera).

### 4. Vérification Post-Déploiement

1. **Tester la gestion du budget** :
   - Ouvrir un événement et aller sur la page Budget
   - Vérifier que la ligne de résumé des ingrédients est visible
   - Modifier un prix unitaire prévu et enregistrer
   - Saisir un montant réel total et enregistrer
   - Vérifier que les totaux en haut sont corrects

2. **Tester les conversions d'unités** :
   - Créer une liste de courses pour un événement
   - Vérifier que les unités sont correctement converties
   - Tester avec des unités japonaises (大さじ, 小さじ, カップ)

3. **Tester les prix du catalogue** :
   - Vérifier que les ingrédients ont des prix (pas 0€)
   - Tester avec des noms en minuscules et majuscules
   - Ouvrir le modal de catalogue depuis la liste de courses

4. **Tester l'import PDF** :
   - Aller sur http://recipe.e2pc.fr/import?lang=fr
   - Choisir "Import PDF (IA)"
   - Uploader un PDF de recette
   - Vérifier que l'analyse fonctionne

5. **Tester la traduction** :
   - Ouvrir une recette importée en PDF
   - Changer de langue
   - Vérifier que le bouton "Traduction" s'affiche
   - Cliquer et vérifier que la traduction fonctionne

6. **Tester l'édition** :
   - Ouvrir une recette
   - Cliquer sur "Modifier"
   - Vérifier les boutons "+" pour ajouter ingrédients/étapes
   - Vérifier les boutons "✕" pour supprimer

## Commande de Déploiement

```bash
cd /Users/christianepp/Documents/DEV/Recette
./deploy/deploy_synology_V1_3.sh
```

Le script effectue automatiquement :
1. Vérification des fichiers requis
2. Backup de la base de données
3. Transfert des fichiers
4. Installation de PyPDF2 et autres dépendances
5. Redémarrage de l'application
6. Vérification du bon fonctionnement

## Compatibilité

- ✅ **Synology DS213+** : Fonctionne (pas de dépendance git requise)
- ✅ **Python 3.7+** : Compatible
- ✅ **Pas de dépendances système** : Fonctionne sur tout environnement Python

## Rollback

En cas de problème, restaurer la version précédente :
```bash
ssh admin@192.168.1.14
cd recette
bash stop_recette.sh
# Restaurer depuis le backup
cp backups/code_backup_YYYYMMDD_HHMMSS/app/* app/
pip install -r requirements.txt
bash start_recette.sh
```
