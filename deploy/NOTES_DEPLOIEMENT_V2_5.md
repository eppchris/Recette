# Notes de déploiement - Version 2.5

**Date**: 10 janvier 2026
**Commit**: `9fe52b5`
**Déploiement**: Synology DS213+ (192.168.1.14)

---

## 📦 Résumé des changements

Version majeure avec **3 fonctionnalités principales** :

1. **🎫 Système de tickets de caisse** avec OCR Gemini Vision API
2. **👥 Adaptation automatique** des listes de courses au nombre de convives
3. **🐛 Corrections critiques** (Jinja2, alignement, interface)

---

## 🎫 1. Système de tickets de caisse

### Fonctionnalités
- Upload de tickets (PDF, images JPG/PNG)
- OCR automatique via Gemini Vision API
- Traduction bidirectionnelle FR↔JP
- Matching intelligent des articles vers le catalogue
- Validation en 1 clic → mise à jour du prix catalogue
- Badge rouge 🎫 pour identifier les prix issus de tickets

### Nouveaux fichiers
```
app/models/db_receipt.py                    # Modèle données
app/services/receipt_extractor.py           # OCR Gemini Vision
app/services/ingredient_matcher.py          # Matching algorithme
app/templates/receipt_upload.html           # Interface upload
app/templates/receipt_list.html             # Liste tickets
app/templates/receipt_review.html           # Révision et validation
```

### Nouvelles routes (9)
```python
/receipt-list                               # Liste des tickets
/receipt-upload                             # Upload formulaire
/receipt-upload-process                     # Traitement upload
/receipt-review/{receipt_id}                # Révision ticket
/receipt-match/{match_id}/validate          # Validation simple
/receipt-match/{match_id}/validate-and-apply # Validation + MAJ prix
/receipt-match/{match_id}/update-ingredient # Changer ingrédient
/receipt-apply-prices/{receipt_id}          # Appliquer tous les prix
/receipt-delete/{receipt_id}                # Supprimer ticket
```

### Base de données (Migrations 008, 009, 010)

**Migration 008** - Tables principales :
```sql
CREATE TABLE receipt_upload_history (
    id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL,
    upload_date TIMESTAMP,
    receipt_date DATE,
    store_name TEXT,
    currency TEXT DEFAULT 'EUR',
    total_amount REAL,
    status TEXT DEFAULT 'pending'  -- pending, processed, error
);

CREATE TABLE receipt_item_match (
    id INTEGER PRIMARY KEY,
    receipt_id INTEGER,
    receipt_item_text TEXT NOT NULL,
    receipt_price REAL,
    receipt_quantity REAL,
    receipt_unit TEXT,
    matched_ingredient_id INTEGER,
    confidence_score REAL,
    status TEXT DEFAULT 'pending',  -- pending, validated, applied
    validated_at TIMESTAMP,
    FOREIGN KEY (receipt_id) REFERENCES receipt_upload_history(id) ON DELETE CASCADE,
    FOREIGN KEY (matched_ingredient_id) REFERENCES ingredient_price_catalog(id)
);
```

**Migration 009** - Colonnes bilingues :
```sql
ALTER TABLE receipt_item_match RENAME COLUMN receipt_item_text TO receipt_item_text_original;
ALTER TABLE receipt_item_match ADD COLUMN receipt_item_text_fr TEXT;
UPDATE receipt_item_match SET receipt_item_text_fr = receipt_item_text_original WHERE receipt_item_text_fr IS NULL;
```

**Migration 010** - Tracking source des prix :
```sql
ALTER TABLE ingredient_price_catalog ADD COLUMN price_eur_source TEXT DEFAULT 'manual';
ALTER TABLE ingredient_price_catalog ADD COLUMN price_eur_last_receipt_date TEXT;
ALTER TABLE ingredient_price_catalog ADD COLUMN price_jpy_source TEXT DEFAULT 'manual';
ALTER TABLE ingredient_price_catalog ADD COLUMN price_jpy_last_receipt_date TEXT;
```

### Configuration requise

**IMPORTANT** : Ajouter la clé API Gemini dans `.env` :

```bash
# Sur le Synology
cd ~/recette
nano .env

# Ajouter la ligne :
GEMINI_API_KEY=AIza...votre_clé...

# Obtenir la clé sur :
# https://makersuite.google.com/app/apikey
```

### Algorithme de matching

**Principe** : Matching basé sur le premier mot normalisé

```python
# Normalisation : minuscules, sans accents, sans œ/æ
"Poireau (ou Ail en feuille)" → "poireau"
"Carotte bio" → "carotte"

# Match 100% si :
# 1. Nom complet identique
# 2. Premier mot identique
```

**Exemples** :
- ✅ "Poireau" (ticket) → "Poireau" (catalogue) = 100%
- ✅ "Poireau (ou Ail)" → "Poireau" = 100%
- ✅ "Carotte bio" → "Carotte" = 100%
- ❌ "Jambonneau fumé" ≠ "Eau" (ancien bug corrigé)

---

## 👥 2. Adaptation automatique aux convives

### Principe

Calcul automatique du multiplicateur :
```
multiplicateur_final = (event.attendees / recipe.servings_default) × manual_multiplier
```

### Exemple

```
Événement : 12 convives
Recette A : 4 portions par défaut → multiplicateur = 12/4 = 3.0
  - 2 œufs × 3 = 6 œufs
  - 200g farine × 3 = 600g farine

Recette B : 6 portions par défaut → multiplicateur = 12/6 = 2.0
  - 3 œufs × 2 = 6 œufs

Total agrégé : 6 + 6 = 12 œufs
```

### Arrondissement intelligent

**Pour unités indivisibles** (œufs, paquets) :
```python
math.ceil(2.3) → 3 œufs  # Arrondi AU SUPÉRIEUR
math.ceil(1.8) → 2 paquets
```

**Pour g, kg, ml, L** (précision conservée) :
```python
237.5g → 237.5g  # Pas d'arrondissement
0.6kg → 0.6kg
```

### Fichiers modifiés

```python
# app/models/db_events.py (lignes 393-485)
def get_event_recipes_with_ingredients(event_id, lang):
    # Récupère servings_default et event_attendees
    # Calcule multiplicateur automatiquement
    auto_multiplier = event_attendees / servings_default
    final_multiplier = auto_multiplier * manual_multiplier

# app/services/ingredient_aggregator.py (lignes 413-427)
def aggregate_ingredients(recipes_ingredients, lang):
    # Ligne 425 : Arrondissement supérieur pour unités vides
    if not standard_unit:
        purchase_qty = math.ceil(total_quantity_standard)
```

### Tests automatisés

Fichier : `tests/test_event_attendees_adaptation.py`

3 tests avec **100% de succès** :
- ✅ Test 1 : Calcul multiplicateur (12 convives / 4 portions = ×3)
- ✅ Test 2 : Arrondissement supérieur (2.3 œufs → 3)
- ✅ Test 3 : Agrégation multi-recettes

Exécution :
```bash
python tests/test_event_attendees_adaptation.py
```

---

## 🐛 3. Corrections critiques

### 3.1 Erreurs Jinja2/Alpine.js (CRITIQUE)

**Symptôme** : Plantage de la page `/ingredient-catalog`

**Cause** : Mélange des syntaxes Jinja2 et Alpine.js
```html
<!-- AVANT (ERREUR) -->
<span x-text="count + ' {{ \'texte\' if lang == \'fr\' }}'"></span>

<!-- APRÈS (CORRIGÉ) -->
<span x-text="count"></span>
{{ ' texte' if lang == 'fr' }}
```

**Fichier** : `app/templates/ingredient_catalog.html`
- Ligne 195 : Séparation count Alpine.js et texte Jinja2
- Lignes 289, 312 : Utilisation de template literals JavaScript

### 3.2 Alignement colonnes catalogue

**Symptôme** : Colonnes désalignées en mode édition

**Cause** : Utilisation de `colspan="7"` qui casse la structure

**Solution** : 7 colonnes individuelles en lecture ET édition
```html
<!-- AVANT -->
<td colspan="7">
    <form>...</form>
</td>

<!-- APRÈS -->
<form>
    <td>Nom</td>
    <td><input price_eur /></td>
    <td><input price_jpy /></td>
    ...
</form>
```

**Fichier** : `app/templates/ingredient_catalog.html` (lignes 273-422)

### 3.3 Badge prix ticket 🎫

**Changement** : Badge vert → rouge pour meilleure visibilité

```html
<!-- AVANT -->
class="bg-green-100 text-green-700"

<!-- APRÈS -->
class="bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300"
```

**Fichier** : `app/templates/ingredient_catalog.html` (lignes 288, 311)

### 3.4 Simplification interface tickets

**Suppression** : Colonne "Statut" redondante avec "Valid."

**Fichier** : `app/templates/receipt_list.html`
- Avant : 6 colonnes (Nom, Date, Art., Valid., Statut, Actions)
- Après : 5 colonnes (Nom, Date, Art., Valid., Actions)

---

## 📊 Statistiques de déploiement

### Fichiers
- **32 fichiers modifiés**
- **13 nouveaux fichiers**
- **6 fichiers déplacés** (tests/)

### Lignes de code
- **+3 615 lignes** ajoutées
- **-309 lignes** supprimées
- **Net : +3 306 lignes**

### Base de données
- **3 migrations SQL** (008, 009, 010)
- **2 nouvelles tables**
- **4 nouvelles colonnes** dans ingredient_price_catalog

### Dépendances
- **google-generativeai** (nouveau)
- **Pillow** (upgrade)

---

## ✅ Checklist de déploiement

### Avant déploiement

- [x] Tests automatisés passés (100%)
- [x] Migrations SQL validées
- [x] Script de déploiement créé
- [x] Commit poussé sur GitHub (9fe52b5)
- [x] Documentation complète

### Pendant déploiement

- [ ] Backup base de données créé
- [ ] Application arrêtée
- [ ] Fichiers déployés
- [ ] Migrations 008, 009, 010 appliquées
- [ ] Dépendances installées
- [ ] GEMINI_API_KEY ajoutée dans .env
- [ ] Application redémarrée
- [ ] Tests de démarrage OK

### Après déploiement

- [ ] Test upload ticket
- [ ] Test validation et badge 🎫
- [ ] Test adaptation convives
- [ ] Test arrondissement œufs
- [ ] Test mode grille/liste
- [ ] Test alignement colonnes catalogue
- [ ] Test sur mobile

---

## 🔧 Commandes de déploiement

### Déploiement complet
```bash
cd ~/Documents/DEV/Recette
./deploy/deploy_synology_V2_5.sh
```

### Vérifications post-déploiement

```bash
# SSH vers Synology
ssh admin@192.168.1.14

# Vérifier l'application
cd ~/recette
ps aux | grep uvicorn

# Vérifier les logs
tail -f logs/recette.log

# Vérifier les migrations
sqlite3 data/recette.sqlite3 "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'receipt%';"

# Résultat attendu :
# receipt_upload_history
# receipt_item_match

# Vérifier les colonnes de tracking
sqlite3 data/recette.sqlite3 "PRAGMA table_info(ingredient_price_catalog);" | grep source

# Résultat attendu :
# 12|price_eur_source|...
# 13|price_eur_last_receipt_date|...
# 14|price_jpy_source|...
# 15|price_jpy_last_receipt_date|...
```

---

## ⚠️ Points d'attention

### 1. Clé API Gemini OBLIGATOIRE

Sans la clé, l'upload de tickets plantera.

**Obtention** :
1. Aller sur https://makersuite.google.com/app/apikey
2. Créer un projet Google Cloud
3. Activer l'API Gemini
4. Générer une clé API
5. Ajouter dans `.env` : `GEMINI_API_KEY=AIza...`

### 2. Changement nombre de convives

**Comportement** : Modification du nombre de convives → régénération automatique de la liste de courses

**Impact** : Les modifications manuelles de la liste sont **perdues**

**Solution** : Informer l'utilisateur avant de changer le nombre de convives

### 3. Performance OCR

**Gemini Vision API** : Temps de réponse variable (2-10 secondes)

**Recommandation** : Ajouter un indicateur de chargement visuel

### 4. Formats supportés

**Tickets** : PDF, JPG, PNG, JPEG
**Taille max** : À définir (limites Gemini)
**Langues** : FR, JP (détection automatique)

---

## 🔄 Rollback en cas de problème

### 1. Restaurer la base de données

```bash
ssh admin@192.168.1.14
cd ~/recette
bash stop_recette.sh

# Lister les backups
ls -lh backups/recette_pre_v2_5_*.sqlite3

# Restaurer
cp backups/recette_pre_v2_5_YYYYMMDD_HHMMSS.sqlite3 data/recette.sqlite3

bash start_recette.sh
```

### 2. Restaurer le code

```bash
cd ~/recette

# Lister les backups de code
ls -lh backups/code_backup_*

# Restaurer
BACKUP_DIR="backups/code_backup_YYYYMMDD_HHMMSS"
rm -rf app
cp -r "$BACKUP_DIR/app" .

bash stop_recette.sh
bash start_recette.sh
```

### 3. Revenir à V2.4

```bash
# Sur la machine locale
cd ~/Documents/DEV/Recette
git checkout e3d194c  # Commit avant V2.5

# Redéployer V2.4
./deploy/deploy_synology_V2_4.sh
```

---

## 📚 Documentation complémentaire

### Fichiers de référence

- **Tests** : `tests/test_event_attendees_adaptation.py`
- **Mobile** : `TESTS_MOBILE.md`
- **Data** : `data/README.md`
- **Commit** : https://github.com/eppchris/Recette/commit/9fe52b5

### Guides utilisateur

À créer pour la V2.5 :
- [ ] Guide upload tickets de caisse
- [ ] Guide adaptation convives
- [ ] FAQ erreurs OCR

---

## 📝 Notes développeur

### Architecture système de tickets

```
1. Upload (receipt_upload.html)
   ↓
2. Extraction OCR (receipt_extractor.py)
   ↓ Gemini Vision API
3. Matching (ingredient_matcher.py)
   ↓ Normalisation + premier mot
4. Révision (receipt_review.html)
   ↓ Utilisateur valide
5. Application (catalog_routes.py)
   ↓ UPDATE ingredient_price_catalog
6. Badge visible (ingredient_catalog.html)
```

### Pipeline adaptation convives

```
1. db_events.get_event_recipes_with_ingredients()
   ↓ Récupère servings_default, attendees
2. Calcul multiplicateur
   ↓ attendees / servings_default × manual_multiplier
3. ingredient_aggregator.aggregate_ingredients()
   ↓ Applique multiplicateur aux quantités
4. Conversion unités
   ↓ g→kg, ml→L selon seuils
5. Arrondissement
   ↓ math.ceil() pour unités vides
6. Liste de courses finale
```

### Améliorations futures

**V2.6 potentielle** :
- [ ] Export liste de courses en PDF
- [ ] Historique des prix (graphiques)
- [ ] Suggestions ingrédients basées sur tickets
- [ ] Multi-upload de tickets (batch)
- [ ] Statistiques dépenses par période

---

**Déploiement préparé le** : 10 janvier 2026
**Par** : Claude Sonnet 4.5
**Pour** : Christian EPP
