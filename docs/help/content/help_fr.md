# Guide d'utilisation - Recette App

## 📖 Gestion des recettes {#recipes}

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
- **Par Ingrédients** Tapez le nom de l'ingrédient et toutes les recettes utilisant l'ingrédient apparaitront

### 🌍 Nationalité du plat (drapeaux) {#nationality}

Chaque recette peut avoir une nationalité, affichée sous forme de drapeau emoji.

**Où le drapeau apparaît:**
- Dans la liste des recettes (coin de la carte ou à côté du nom)
- Dans la fiche détail de la recette (à côté des infos prep/cuisson)
- Dans le calendrier (remplace le point coloré si une nationalité est définie)

**Comment définir la nationalité:**

1. Ouvrez la fiche d'une recette
2. Cliquez sur "✏️ Modifier"
3. Dans la section infos générales, sélectionnez le pays dans le menu déroulant "Nationalité"
4. Cliquez sur "Enregistrer"

**Import automatique:**
Lors d'un import depuis URL ou PDF, l'IA détecte automatiquement la nationalité du plat et propose le code pays correspondant.

> **💡 Astuce:** Si la nationalité n'est pas reconnue automatiquement à l'import, vous pouvez la saisir manuellement dans la fiche recette.

### 🔗 Liaison entre recettes {#recipe-links}

Un ingrédient peut être lié à une autre recette. Utile quand une préparation est elle-même une recette de la base (ex: "Pâte feuilletée", "Sauce béchamel", "Bouillon de poulet").

**Comment lier un ingrédient à une recette:**

1. Ouvrez la fiche d'une recette en mode édition
2. Dans la liste des ingrédients, chaque ligne affiche un menu déroulant **"Lier à une recette"**
3. Sélectionnez la recette cible dans ce menu
4. Enregistrez

**Ce que ça change à l'affichage:**
- L'ingrédient lié affiche un badge **🔗 Nom de la recette** cliquable
- Cliquez sur le badge pour accéder directement à la recette liée

**Important:** La liaison est **visuelle uniquement**. Dans la liste de courses, les ingrédients de la recette liée ne sont **pas** ajoutés automatiquement. La quantité indiquée reste la quantité physique nécessaire (en g, ml, etc.).

> **💡 Exemple:** Dans la recette "Tarte aux pommes", l'ingrédient "250g pâte feuilletée" peut être lié à la recette "Pâte feuilletée". Le badge 🔗 permet de retrouver rapidement la recette de la pâte sans l'inclure automatiquement dans les courses.

---

## 📅 Calendrier des repas {#calendar}

Le calendrier permet de planifier les repas du quotidien, indépendamment des événements.

### Accéder au calendrier
Depuis le menu principal, cliquez sur "Calendrier".

### Ajouter un repas
1. Cliquez sur un jour dans le calendrier
2. Un panneau latéral s'ouvre avec le détail du jour
3. Cliquez sur "➕ Ajouter un repas"
4. Cherchez une recette dans la barre de recherche (autocomplétion)
5. Sélectionnez le moment (Petit-déjeuner / Déjeuner / Dîner / Autre)
6. Le repas s'affiche dans la cellule du calendrier avec le drapeau de la nationalité si défini

### Types de repas dans le calendrier
- **Repas personnel** : lié à une recette de votre base → affiche le drapeau 🌍
- **Repas événement** : provenant d'un événement planifié → affiché en violet
- **Texte libre** : une note rapide sans recette liée → affiché avec ⭐

### Naviguer
- Cliquez sur **◀ ▶** pour changer de mois
- Cliquez sur un jour pour voir le détail et les repas planifiés
- Cliquez sur un repas pour le supprimer

> **💡 Astuce:** Depuis le calendrier, vous pouvez créer un nouvel événement directement en cliquant sur "Créer un événement" dans le panneau d'un jour. Les dates sont pré-remplies.

---

## 🧾 Tickets de caisse {#receipts}

Cette fonction permet d'importer des tickets de caisse (PDF) pour mettre à jour automatiquement les prix du catalogue d'ingrédients.

### Comment ça marche
1. Vous photographiez ou scannez votre ticket de caisse en PDF
2. L'IA extrait les articles et prix
3. Vous validez les correspondances avec vos ingrédients
4. Les prix sont mis à jour dans le catalogue

### Importer un ticket
1. Accédez à "Tickets de caisse" depuis le menu
2. Cliquez sur "📤 Importer un ticket"
3. Sélectionnez le fichier PDF
4. L'IA analyse le ticket et propose des correspondances avec vos ingrédients

### Valider les correspondances
1. Ouvrez un ticket importé depuis la liste
2. Pour chaque article détecté :
   - **Valider** : l'ingrédient correspond → le prix est enregistré
   - **Valider et appliquer** : valide ET met à jour le prix dans le catalogue
   - **Corriger** : si la correspondance est incorrecte, choisissez le bon ingrédient
3. Cliquez sur "Appliquer tous les prix validés" pour une mise à jour groupée

> **💡 Astuce:** Plus vous validez de tickets, plus le catalogue devient précis et les estimations de budget fiables.

---

## 📥 Import de recettes {#import}

Trois méthodes d'import sont disponibles pour enrichir votre base de recettes.

### Import depuis URL (recommandé)
Importez une recette directement depuis un site web (Marmiton, Cuisine Actuelle, etc.) :

1. Accédez à "Importer depuis URL" dans le menu
2. Collez l'URL de la page recette
3. Choisissez la langue cible (FR ou JP)
4. Cliquez sur "Analyser"
5. L'IA extrait : titre, ingrédients, étapes, temps, portions, **nationalité**
6. Vérifiez et corrigez les informations si besoin
7. Cliquez sur "Enregistrer"

### Import depuis PDF
Pour les recettes en format PDF (livres de cuisine numérisés, etc.) :

1. Accédez à "Importer depuis PDF" dans le menu
2. Sélectionnez le fichier PDF
3. L'IA analyse le PDF et extrait la recette
4. Vérifiez les informations et enregistrez

### Import CSV
Pour importer un lot de recettes en une fois :

1. Accédez à "Importer CSV" dans le menu
2. Préparez votre fichier CSV selon le format requis
3. Uploadez le fichier

> **💡 Astuce:** L'import URL est la méthode la plus simple et fiable. L'IA détecte automatiquement la langue et la nationalité du plat.

---

## 🏷️ Catégories et Tags {#categories}

Les catégories et tags permettent d'organiser et de retrouver facilement vos recettes.

### Différence entre catégories et tags
- **Catégories** : classification principale (ex: Plat principal, Dessert, Apéritif)
- **Tags** : mots-clés libres (ex: rapide, végétarien, sans gluten, recette de famille)

### Assigner des catégories/tags à une recette
1. Ouvrez la fiche d'une recette
2. Cliquez sur "✏️ Modifier"
3. Dans la section "Catégories" ou "Tags", cochez les entrées correspondantes
4. Enregistrez

### Gérer les catégories et tags (admin)
Accédez à "Administration des tags" depuis le menu :
- Créer de nouvelles catégories ou tags
- Modifier les noms et couleurs
- Supprimer les entrées inutilisées

### Filtrer par catégorie ou tag
Depuis la liste des recettes, utilisez les filtres pour afficher uniquement les recettes d'une catégorie ou d'un tag particulier.

---

## 🔍 Recherche par ingrédients {#search}

### Comment ça marche?
Cette fonctionnalité vous permet de trouver des recettes contenant **TOUS** les ingrédients que vous spécifiez.

### Mode d'emploi

1. Dans la page des recettes, trouvez le bloc vert "Recherche par ingrédients" 🥕
2. Entrez les ingrédients séparés par des virgules: `tomate, basilic, mozzarella`
3. Cliquez sur "Rechercher" ou appuyez sur Entrée
4. Seules les recettes contenant **tous ces ingrédients** s'afficheront
5. Cliquez sur "Effacer" pour revenir à la liste complète

> **💡 Astuce:** Si vous ne trouvez pas de recettes, essayez avec moins d'ingrédients ou vérifiez l'orthographe.

## 💰 Coût de la recette
Cette fonction permet de vérifier le prix de revient de la recette.
Via cette fonction, il est possible de mettre à jour les coût de chaque ingrédient, afin d'avoir un prix le plus prêt de la réalité.

---

## 👥 Gestion des participants et groupes {#participants}

### Créer un participant

1. Accédez à la page "Participants" depuis le menu principal
2. Cliquez sur "➕ Nouveau participant"
3. Remplissez les informations:

   - **Nom** (obligatoire)
   - **Prénom**
   - **Rôle** (ex: Invité, Staff, Intervenant)
   - **Téléphone**
   - **Email**
   - **Adresse**

4. Cliquez sur "Enregistrer"

### Créer un groupe de participants

Les groupes permettent d'organiser vos participants (ex: "Famille Dupont", "Équipe Marketing"):

1. Dans la page "Participants", cliquez sur "➕ Nouveau groupe"
2. Entrez le nom du groupe (obligatoire)
3. Ajoutez une description (optionnel)
4. Cliquez sur "Enregistrer"

### Ajouter des participants à un groupe

Depuis la page de détail du groupe:

1. **Cliquez sur le nom du groupe** pour accéder à sa page de détail
2. **Section "Ajouter des participants"** (en haut):
   - Cochez les participants que vous souhaitez ajouter au groupe
   - Les participants déjà membres n'apparaissent pas dans cette liste
3. **Section "Membres actuels"** (en bas):
   - Liste de tous les membres du groupe
   - Cliquez sur ❌ pour retirer un membre

### Voir les groupes d'un participant

Depuis la page de détail du participant:

1. **Cliquez sur le nom du participant** pour accéder à sa page de détail
2. **Section "Groupes"** affiche tous les groupes dont il est membre
3. Vous pouvez retirer le participant d'un groupe en cliquant sur ❌

> **💡 Astuce:** Un participant peut appartenir à plusieurs groupes simultanément.

### Isolation multi-utilisateurs

Chaque utilisateur voit uniquement ses propres participants et groupes. L'administrateur voit tous les participants et groupes de tous les utilisateurs.

---

## 📅 Gestion des événements {#events}

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

### Gérer les participants d'un événement

Ajoutez et gérez les participants inscrits à votre événement:

1. **Ouvrez un événement** depuis la liste des événements
2. **Cliquez sur le bouton "Participants (X)"** en haut de la page
3. Une **fenêtre modale** s'ouvre avec deux colonnes:

   **Colonne de gauche - Ajouter des participants:**
   - **Participants individuels:** Cochez la case à côté du nom pour ajouter une personne
   - **Groupes entiers:** Cochez la case à côté du nom du groupe pour ajouter tous ses membres d'un coup
   - Les participants/groupes déjà inscrits n'apparaissent pas dans cette liste

   **Colonne de droite - Participants inscrits:**
   - Liste de tous les participants déjà inscrits à l'événement
   - **Indication de provenance:**
     - Si ajouté individuellement: nom seul
     - Si ajouté via un groupe: "via groupe: [Nom du groupe]"
   - **Retirer un participant:** Cliquez sur la croix ❌ rouge à côté du nom

4. **Sauvegarde automatique:** Les ajouts et retraits sont enregistrés immédiatement

> **💡 Astuce:** Si vous retirez un participant qui a été ajouté via un groupe, la page se rechargera pour éviter les incohérences. Les participants ajoutés individuellement peuvent être retirés instantanément.

> **📌 Note:** Vous devez d'abord créer vos participants et groupes depuis le menu "Participants" avant de pouvoir les ajouter à un événement.

---

## 📆 Événements multi-jours {#multiday}

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

## 🗓️ Planification des recettes {#planning}

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

## 🛒 Liste de courses {#shopping}

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

## 💰 Gestion du budget {#budget}

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

## 📚 Catalogue des prix {#catalog}

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
2. **Consultez le coût calculé automatiquement** dans la page de détail de la recette
   - Le coût total de la recette s'affiche automatiquement
   - Le coût par portion est calculé en fonction du nombre de personnes
   - **Objectif principal** : vérifier que les montants par ingrédient sont corrects
3. **Vérifiez la cohérence des montants**:
   - Le coût total doit être réaliste
   - Le coût par personne doit être cohérent
   - Les ingrédients avec conversions spécifiques doivent afficher le bon prix
   - Si un montant semble incorrect, vérifiez le prix et l'unité dans le catalogue

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

*Dernière mise à jour: Version 2.5 - Mars 2026*
