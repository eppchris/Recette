# Guide d'utilisation - Recette App

## 📖 Gestion des recettes

### Consulter les recettes
Accédez à la liste complète des recettes depuis le menu principal. Chaque recette affiche:
- Le nom et l'image de la recette
- Le nombre de portions par défaut
- Le type de recette (PRO, MASTER, PERSO, etc.)
- Le créateur de la recette

### Filtrer les recettes
Plusieurs options de filtrage sont disponibles:
- **Par type d'événement:** Cliquez sur les boutons (Apéritif, Plat, Dessert, etc.)
- **Par créateur:** Utilisez le menu déroulant pour voir les recettes d'un utilisateur
- **Par recherche textuelle:** Tapez le nom de la recette dans la barre de recherche

---

## 🔍 Recherche par ingrédients

### Comment ça marche?
Cette fonctionnalité vous permet de trouver des recettes contenant **TOUS** les ingrédients que vous spécifiez.

### Mode d'emploi
1. Dans la page des recettes, trouvez le bloc vert "Recherche par ingrédients" 🥕
2. Entrez les ingrédients séparés par des virgules: `tomate, basilic, mozzarella`
3. Cliquez sur "Rechercher" ou appuyez sur Entrée
4. Seules les recettes contenant **tous ces ingrédients** s'afficheront
5. Cliquez sur "Effacer" pour revenir à la liste complète

> **💡 Astuce:** Si vous ne trouvez pas de recettes, essayez avec moins d'ingrédients ou vérifiez l'orthographe.

---

## 📅 Gestion des événements

### Créer un événement
1. Cliquez sur "Nouvel événement" depuis la liste des événements
2. Remplissez les informations: nom, type, date(s), lieu, nombre de convives
3. Ajoutez des notes si nécessaire
4. Cliquez sur "Enregistrer"

### Copier un événement
Créez rapidement un nouvel événement à partir d'un événement existant:
1. Dans la liste des événements, cliquez sur "Copier" à côté de l'événement à dupliquer
2. Le formulaire se pré-remplit avec toutes les informations de l'événement source
3. Modifiez le nom, les dates, le lieu et toute autre information nécessaire
4. Le nombre de jours de l'événement source est conservé
5. Entrez la date de début: la date de fin se calcule automatiquement
6. Validez pour créer le nouvel événement

**Ce qui est copié:**
- ✅ Toutes les recettes avec leurs quantités ajustées
- ✅ Le budget prévu et la devise
- ✅ L'organisation/planification des recettes (si même nombre de jours)

**Ce qui n'est PAS copié:**
- ❌ Les dépenses effectuées
- ❌ La liste de courses (elle sera regénérée automatiquement)

> **💡 Astuce:** Si vous avez désélectionné des jours dans l'événement source (ex: week-ends), seuls les jours sélectionnés seront pris en compte pour la copie de la planification.

### Ajouter des recettes à un événement
1. Ouvrez l'événement
2. Cliquez sur "Ajouter une recette"
3. Sélectionnez la recette dans la liste
4. Ajustez le nombre de portions si nécessaire

---

## 📆 Événements multi-jours

### Créer un événement sur plusieurs jours
1. Lors de la création, sélectionnez une **date de début** et une **date de fin**
2. Un calendrier s'affiche avec toutes les dates entre début et fin
3. Les dates sont sélectionnées par défaut (en bleu)
4. **Cliquez sur une date** pour la désélectionner (ex: week-ends, jours fériés)
   - 🔵 Date sélectionnée (jour travaillé)
   - ⚪ Date désélectionnée (jour non travaillé)
5. Le nombre de jours se calcule automatiquement

> **📌 Exemple:** Un séminaire du lundi 10 au vendredi 14 juin:
> - Date début: 10/06 - Date fin: 14/06
> - 5 dates affichées (lundi au vendredi)
> - Toutes sélectionnées → 5 jours travaillés

---

## 🗓️ Planification des recettes

### Organisation (lecture seule)
Visualisez la planification de vos recettes par jour:
1. Ouvrez un événement multi-jours
2. Cliquez sur "Organisation" dans le menu
3. Voyez les recettes organisées par date

### Planification (drag & drop)
Organisez vos recettes par jour avec le drag & drop:
1. Cliquez sur "Planification" depuis l'organisation
2. Vous voyez 2 colonnes:
   - **Gauche:** Recettes disponibles
   - **Droite:** Dates de l'événement
3. **Glissez-déposez** une recette de gauche vers une date à droite
4. Déplacez les recettes d'une date à l'autre
5. Cliquez sur ❌ pour retirer une recette d'une date
6. Cliquez sur "Enregistrer" pour sauvegarder

**✨ Fonctionnalités:**
- Défilement indépendant des deux colonnes
- Visualisation en temps réel
- Réorganisation facile

---

## 🛒 Liste de courses

### Génération automatique
La liste de courses est générée automatiquement à partir des recettes de l'événement:
- Les ingrédients sont regroupés et additionnés
- Les unités sont converties automatiquement quand possible
- La liste se met à jour si vous changez le nombre de convives

### Utilisation
1. Ouvrez un événement
2. Cliquez sur "Liste de courses"
3. Cochez les articles achetés
4. Modifiez les quantités si nécessaire

---

## 💰 Gestion du budget

### Définir le budget
1. Ouvrez un événement
2. Cliquez sur "Budget"
3. Définissez le budget prévu
4. Choisissez la devise (€ ou ¥)

### Ajouter des prix aux ingrédients
Directement depuis la liste de courses:
- Cliquez sur le bouton "💰" à côté d'un ingrédient
- Entrez le prix unitaire et la quantité
- Le total se calcule automatiquement
- Les prix sont sauvegardés dans le catalogue

### Suivi des dépenses
Ajoutez des dépenses par catégorie:
- Ingrédients (calculé automatiquement)
- Logistique, matériel, personnel, etc.
- Visualisez le budget utilisé vs prévu

---

## 📚 Catalogue des prix

### À quoi sert le catalogue?
Le catalogue conserve les prix des ingrédients pour:
- Suggestions automatiques lors de nouveaux événements
- Estimation rapide des budgets
- Historique des prix dans différentes devises

### Gérer le catalogue
Accédez au catalogue depuis le menu principal:
- Ajouter de nouveaux ingrédients avec leurs prix
- Modifier les prix existants
- Définir des prix en € et en ¥
- Synchroniser avec les ingrédients des recettes

---

## ✅ Vérification des recettes et des coûts

### 🔍 Étape 1 : Vérifier les recettes

Pour garantir des calculs de coût corrects, vérifiez chaque recette:

1. **Ouvrez chaque recette** depuis la liste des recettes
2. **Vérifiez les unités des ingrédients**
   - L'unité doit correspondre à l'usage réel (ml, g, c.s., pièce, etc.)
   - Exemple : dashi → ml (dans la recette)
3. **Notez les ingrédients** qui nécessitent une attention particulière

### 💰 Étape 2 : Vérifier le catalogue des prix

Pour chaque ingrédient utilisé dans vos recettes:

1. **Accédez au catalogue des prix**
2. **Vérifiez l'unité d'achat** de chaque ingrédient
   - L'unité doit correspondre à l'emballage réel
   - Exemple : dashi → 30g (sachet), beurre → 250g (plaquette)
3. **Vérifiez le prix et la quantité**
   - Prix : montant payé à l'achat
   - Quantité : contenu de l'emballage
   - Exemple : dashi 30g = 5.01€

### 🔄 Étape 3 : Gérer les conversions spécifiques

Certains ingrédients changent de forme entre achat et utilisation:

**Quand utiliser les conversions spécifiques?**
- L'ingrédient s'achète dans une unité (g) mais s'utilise dans une autre (ml)
- Il n'existe pas de conversion standard volume↔poids pour cet ingrédient
- Exemple : dashi en poudre (g) → bouillon liquide (ml)

**Comment ajouter une conversion spécifique:**

1. Accédez à "**Conversions spécifiques par ingrédient**" depuis le menu
2. Cliquez sur "**➕ Ajouter**"
3. Remplissez les informations:
   - **Ingrédient** : nom exact (ex: dashi)
   - **De** : unité du catalogue (ex: g)
   - **Vers** : unité de la recette (ex: ml)
   - **Facteur** : ratio de conversion (ex: 33 = 1g → 33ml)
   - **Notes** : explication (ex: "30g de poudre → 1000ml de bouillon")

**Exemples de conversions spécifiques:**
- **Dashi** : 1g → 33ml (30g de poudre = 1000ml de bouillon)
- **Bouillon cube** : 1 cube → 500ml (1 cube = 500ml de bouillon)
- **Champignon de paris** : 1g → 1 boîte (conversion conditionnement)

### 💡 Étape 4 : Vérifier le coût des recettes

Une fois les conversions configurées:

1. **Ouvrez une recette**
2. Cliquez sur l'onglet "**💰 Coût**" (si disponible) ou consultez le détail
3. **Vérifiez la cohérence des montants**:
   - Le coût total doit être réaliste
   - Le coût par personne doit être cohérent
   - Les ingrédients avec conversions spécifiques doivent afficher le bon prix

**Exemple de vérification (dashi):**
- ✅ Recette : 250ml de dashi
- ✅ Catalogue : 30g = 5.01€
- ✅ Conversion : 1g → 33ml
- ✅ Calcul : 250ml ÷ 33 = 7.58g → 7.58g × (5.01€/30g) = **1.27€**
- ❌ Si vous voyez 41.75€ → la conversion spécifique n'est pas configurée

### 📊 Étape 5 : Vérifier le budget des événements

Pour les événements existants:

1. **Ouvrez un événement**
2. Cliquez sur "**Budget**"
3. **Vérifiez la liste de courses** et les prix calculés
4. Les prix doivent correspondre aux quantités réelles nécessaires
5. Si un prix semble incorrect, vérifiez:
   - Le prix dans le catalogue
   - L'existence d'une conversion spécifique si nécessaire
   - Les unités utilisées (recette vs catalogue)

---

## ❓ Questions fréquentes

### Puis-je modifier le nombre de convives après avoir créé l'événement?
Oui! La liste de courses et les quantités se mettent à jour automatiquement.

### La recherche par ingrédients trouve-t-elle les recettes avec AU MOINS un ingrédient ou TOUS les ingrédients?
TOUS les ingrédients! C'est une logique ET. Si vous cherchez "tomate, basilic", seules les recettes contenant tomate ET basilic apparaîtront.

### Puis-je planifier des recettes sur certains jours seulement?
Oui! Lors de la création de l'événement, désélectionnez les jours où vous ne travaillez pas (week-ends, jours fériés). Seules les dates sélectionnées apparaîtront dans la planification.

### Les prix du catalogue sont-ils obligatoires?
Non, ils sont optionnels. Le catalogue sert surtout à gagner du temps en suggérant des prix lors de nouveaux événements.

---

*Dernière mise à jour: Version 1.11 - 11 décembre 2025*
