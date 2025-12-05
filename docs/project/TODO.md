# TODO - Recette App

## 📋 Vue d'ensemble

### V1.7 (Prochaine version)
- [ ] Aide: Ajouter bouton retour
- [ ] Aide: Rendre modifiable par admin (🔥 priorité)
- [ ] Aide: Mise à jour automatique avec versions

### V1.8+
- [ ] Recettes composées (recette comme ingrédient) - 🔵 À SPÉCIFIER
- [ ] Images dans les étapes de recette
- [ ] Clarifier système de versioning

### V2.0
- [ ] Scan ticket de caisse pour prix - 🔵 À SPÉCIFIER

### Backlog
- [ ] Harmoniser navigation (boutons retour, icônes, cohérence UI)
- [ ] Export PDF planification
- [ ] Notifications événements
- [ ] Copie événements avec planning
- [ ] Filtres avancés recherche ingrédients
- [ ] Autocomplete ingrédients
- [ ] Dashboard statistiques

---

## 📝 Détails

**Légende:** 🔴 À faire | 🟡 En cours | 🟢 Terminé | 🔵 À spécifier | ⏸️ En pause
**Priorité:** 🔥 Haute | ⚡ Moyenne | 💡 Basse

---

## 📖 Aide en ligne (Manuel utilisateur)

### 🔴 Revoir l'aide en ligne et ajouter un bouton de retour
**Priorité:** ⚡ Moyenne
**Version cible:** V1.7

**Description:**
- Revoir la structure et le contenu de la page d'aide actuelle
- Ajouter un bouton de retour vers la page précédente (ou vers l'accueil)
- Améliorer la navigation dans l'aide

**Détails techniques:**
- Fichier: `app/templates/help.html`
- Ajouter un bouton "← Retour" en haut de la page
- Utiliser `history.back()` ou rediriger vers `/recipes`

**À faire:**
- [ ] Analyser l'aide actuelle et identifier les améliorations
- [ ] Ajouter bouton de retour dans le header
- [ ] Tester la navigation
- [ ] Mettre à jour la documentation

---

### 🔴 L'aide en ligne doit être modifiable par l'utilisateur
**Priorité:** 🔥 Haute
**Version cible:** V1.7

**Description:**
L'aide doit pouvoir être éditée directement depuis l'interface web par les administrateurs, sans passer par le code source.

**Solutions possibles:**
1. **Markdown éditable** - Stocker l'aide en fichiers .md modifiables via une interface admin
2. **Éditeur WYSIWYG** - Interface d'édition visuelle (ex: TinyMCE, CKEditor)
3. **Base de données** - Stocker le contenu de l'aide en BDD avec interface d'édition

**Recommandation:**
Option 1 (Markdown) - Plus simple, versionnable, format texte

**Détails techniques:**
- Créer une interface admin `/admin/help/edit`
- Stocker l'aide dans `docs/help/content_fr.md` et `docs/help/content_jp.md`
- Parser le markdown côté backend (librairie `markdown`)
- Système de sauvegarde/historique des modifications
- Prévisualisation avant sauvegarde

**À faire:**
- [ ] Choisir la solution technique (discussion avec utilisateur)
- [ ] Concevoir l'interface d'édition
- [ ] Implémenter le backend (routes, parsing markdown)
- [ ] Implémenter le frontend (éditeur + preview)
- [ ] Ajouter système de versioning/historique
- [ ] Restreindre accès aux admins seulement
- [ ] Tester et documenter

---

### 🔴 L'aide en ligne devient le manuel utilisateur
**Priorité:** ⚡ Moyenne
**Version cible:** Continu

**Description:**
L'aide doit être mise à jour à chaque évolution du projet. Elle devient la référence officielle pour les utilisateurs.

**Process à mettre en place:**
1. Pour chaque nouvelle fonctionnalité → Mettre à jour l'aide
2. Pour chaque modification → Réviser la section correspondante
3. Versionner l'aide avec l'application (snapshot par version)

**Détails techniques:**
- Ajouter "Mise à jour aide" dans `DEPLOYMENT_CHECKLIST.md`
- Créer un template de section d'aide
- Historique des versions de l'aide (ex: `docs/help/archive/v1_6.md`)

**À faire:**
- [ ] Définir le template de section d'aide
- [ ] Ajouter étape "Mise à jour aide" dans la checklist déploiement
- [ ] Mettre en place système de versioning de l'aide
- [ ] Documenter le process dans `.claude/project-rules.md`

---

## 🍽️ Recettes

### 🔵 Pouvoir mettre une autre recette dans les ingrédients
**Priorité:** ⚡ Moyenne
**Version cible:** V1.8
**Statut:** À spécifier

**Description:**
Permettre d'utiliser une recette comme ingrédient d'une autre recette (recettes composées).

**Exemple d'usage:**
- Recette "Pâte à tarte" utilisée dans "Tarte aux pommes"
- Recette "Sauce tomate" utilisée dans "Lasagnes"
- Recette "Pâte à crêpes" utilisée dans "Crêpes Suzette"

**Questions à clarifier:**

1. **Structure de données:**
   - Comment identifier qu'un ingrédient est une recette?
   - Nouvelle table `recipe_recipe` (relation recette → sous-recette)?
   - Ou ajouter un champ `linked_recipe_id` dans `recipe_ingredient`?

2. **Calcul des quantités:**
   - Si "Tarte aux pommes" (8 parts) utilise "Pâte à tarte" (6 parts), comment ajuster?
   - Calcul automatique des proportions?
   - Multiplicateur manuel?

3. **Liste de courses:**
   - Décomposer automatiquement les sous-recettes en ingrédients de base?
   - Ou laisser "Pâte à tarte" comme un seul item?
   - Option "Développer sous-recettes" dans la liste de courses?

4. **Budget:**
   - Calculer le coût des sous-recettes automatiquement?
   - Ou prix forfaitaire pour la sous-recette?

5. **Interface utilisateur:**
   - Comment sélectionner une recette comme ingrédient?
   - Autocomplete avec distinction ingrédients/recettes?
   - Icône spéciale pour les recettes-ingrédients (ex: 📖)?

6. **Profondeur:**
   - Limiter la profondeur? (recette → sous-recette → sous-sous-recette)
   - Max 2 niveaux? 3 niveaux?

7. **Affichage:**
   - Dans la page de détail d'une recette, comment afficher les sous-recettes?
   - Lien cliquable vers la sous-recette?
   - Sections expandables?

**À spécifier:**
- [ ] Répondre aux questions ci-dessus
- [ ] Définir la structure de base de données
- [ ] Définir l'algorithme de calcul des quantités
- [ ] Concevoir les maquettes UI
- [ ] Évaluer la complexité technique

**À faire (après spécification):**
- [ ] Créer migration BDD
- [ ] Modifier modèle `db_recipes.py`
- [ ] Créer API pour lier recettes
- [ ] Modifier interface d'ajout d'ingrédient
- [ ] Implémenter calcul quantités récursif
- [ ] Mettre à jour liste de courses
- [ ] Mettre à jour calcul budget
- [ ] Ajouter tests
- [ ] Documenter dans l'aide

---

### 🔴 Pouvoir ajouter une image dans les opérations d'une recette
**Priorité:** 💡 Basse
**Version cible:** V1.9

**Description:**
Permettre d'illustrer les étapes d'une recette avec des photos (ex: montage d'un gâteau, pliage d'une pâte).

**Détails techniques:**

1. **Structure de données:**
   - Ajouter colonne `image_url` dans table `recipe_operation`
   - Ou nouvelle table `recipe_operation_image` (si plusieurs images par étape)

2. **Upload d'images:**
   - Utiliser le système d'upload existant (même que recettes)
   - Stocker dans `static/images/operations/`
   - Générer thumbnails automatiquement
   - Compression d'images pour performance

3. **Interface:**
   - Bouton "📷 Ajouter image" sur chaque étape
   - Drag & drop d'image
   - Prévisualisation avant upload
   - Option de suppression d'image

4. **Affichage:**
   - Image au-dessus ou à côté du texte de l'étape
   - Lightbox pour agrandir l'image
   - Galerie si plusieurs images par étape

**À faire:**
- [ ] Modifier schéma BDD (migration)
- [ ] Créer endpoint upload image opération
- [ ] Modifier interface d'édition de recette
- [ ] Ajouter gestion d'upload dans le formulaire
- [ ] Implémenter affichage des images dans `recipe_detail.html`
- [ ] Ajouter lightbox pour zoom
- [ ] Gérer suppression d'images
- [ ] Optimiser taille/compression des images
- [ ] Tester upload et affichage
- [ ] Mettre à jour l'aide

---

## 💰 Budget

### 🔵 Scanner un ticket de caisse pour mettre à jour les tarifs
**Priorité:** 💡 Basse
**Version cible:** V2.0
**Statut:** À spécifier

**Description:**
Permettre de scanner/uploader une photo de ticket de caisse et extraire automatiquement les prix des articles pour mettre à jour le catalogue.

**Technologies possibles:**
1. **OCR (Optical Character Recognition)**
   - Tesseract.js (JavaScript, côté client)
   - Google Cloud Vision API (payant, très précis)
   - AWS Textract (payant)
   - Tesseract Python (gratuit, côté serveur)

2. **IA/ML pour l'extraction structurée**
   - GPT-4 Vision (payant, très intelligent)
   - Florence-2 (open source)
   - Modèles spécialisés tickets de caisse

**Questions à clarifier:**

1. **Format d'entrée:**
   - Photo prise depuis l'app (mobile)?
   - Upload d'image depuis ordinateur?
   - Qualité d'image requise?

2. **Reconnaissance:**
   - Quels formats de tickets? (Carrefour, Auchan, Lidl, etc.)
   - Différents pays? (FR, JP)
   - Langues différentes?

3. **Mapping ingrédients:**
   - Comment associer "Tomates rondes 1kg" du ticket à "Tomate" dans la BDD?
   - IA pour matching intelligent?
   - Confirmation manuelle par l'utilisateur?
   - Suggestions avec score de confiance?

4. **Gestion des erreurs OCR:**
   - Que faire si l'OCR se trompe?
   - Interface de correction?
   - Validation manuelle obligatoire?

5. **Unités et quantités:**
   - Extraire prix au kilo automatiquement?
   - Gérer "3 pour 5€"?
   - Promotions et remises?

6. **Historique:**
   - Conserver l'image du ticket?
   - Tracer la source des prix (ticket scanné le XX/XX)?
   - RGPD: anonymiser les infos personnelles du ticket?

**Architecture proposée:**

1. **Frontend:**
   - Upload image (drag & drop)
   - Prévisualisation du ticket
   - Interface de validation/correction des articles détectés

2. **Backend:**
   - Endpoint `/api/budget/scan-ticket`
   - OCR pour extraire texte
   - Parser le texte pour identifier articles et prix
   - IA pour matcher articles → ingrédients catalogue
   - Retourner suggestions avec score de confiance

3. **Validation utilisateur:**
   - Liste des correspondances trouvées
   - Possibilité de corriger/ajuster
   - Validation pour mettre à jour le catalogue

**À spécifier:**
- [ ] Choisir la technologie OCR (budget, précision, vie privée)
- [ ] Définir le process de matching article → ingrédient
- [ ] Concevoir les maquettes UI (upload, validation)
- [ ] Évaluer la complexité et le coût (si API payante)
- [ ] Définir le format de stockage des données extraites
- [ ] Stratégie de gestion des erreurs

**À faire (après spécification):**
- [ ] Intégrer librairie OCR
- [ ] Créer parser de tickets
- [ ] Implémenter algorithme de matching
- [ ] Créer interface d'upload
- [ ] Créer interface de validation/correction
- [ ] Stocker historique des scans (optionnel)
- [ ] Mettre à jour catalogue automatiquement
- [ ] Gérer RGPD (anonymisation)
- [ ] Tester avec différents formats de tickets
- [ ] Documenter dans l'aide

---

## 🔧 Améliorations techniques

### 🔴 Versioning des scripts de déploiement
**Priorité:** ⚡ Moyenne
**Version cible:** V1.7

**Description:**
Clarifier le système de versioning - actuellement "V1_6" est utilisé 2 fois. Définir une convention claire.

**Solutions possibles:**

1. **Option A: Version = Numéro séquentiel**
   - V1.6 = Sixième version majeure de la V1
   - V1.7 = Version suivante
   - Incrémenter à chaque déploiement

2. **Option B: Version = Date**
   - V2024_12 = Décembre 2024
   - V2025_01 = Janvier 2025
   - Plus facile à retrouver dans le temps

3. **Option C: Semantic Versioning**
   - V1.6.0 = Major.Minor.Patch
   - V1.6.1 = Hotfix
   - V1.7.0 = Nouvelles features
   - V2.0.0 = Breaking changes

**À faire:**
- [ ] Décider de la convention (discussion avec utilisateur)
- [ ] Mettre à jour `.claude/project-rules.md`
- [ ] Mettre à jour `DEPLOYMENT_CHECKLIST.md`
- [ ] Documenter dans un VERSIONING.md

---

## 📱 Fonctionnalités futures (backlog)

### 💡 Export PDF de la planification d'événement
**Priorité:** 💡 Basse
**Version cible:** TBD

**Description:**
Exporter la planification d'un événement multi-jours en PDF imprimable.

**À faire:**
- [ ] À spécifier

---

### 💡 Notifications pour événements à venir
**Priorité:** 💡 Basse
**Version cible:** TBD

**Description:**
Envoyer des rappels par email X jours avant un événement.

**À faire:**
- [ ] À spécifier

---

### 💡 Copie d'événements avec planification
**Priorité:** 💡 Basse
**Version cible:** TBD

**Description:**
Dupliquer un événement complet avec toute sa planification.

**À faire:**
- [ ] À spécifier

---

### 💡 Filtres avancés dans recherche par ingrédients
**Priorité:** 💡 Basse
**Version cible:** TBD

**Description:**
- Logique OU (au moins un ingrédient)
- Exclusion d'ingrédients (sans gluten, sans lactose)
- Combinaisons ET/OU

**À faire:**
- [ ] À spécifier

---

### 💡 Suggestions d'ingrédients (autocomplete)
**Priorité:** 💡 Basse
**Version cible:** TBD

**Description:**
Autocomplete lors de la saisie d'ingrédients dans la recherche, avec suggestions basées sur les ingrédients existants.

**À faire:**
- [ ] À spécifier

---

## 📊 Statistiques & rapports

### 💡 Statistiques d'utilisation
**Priorité:** 💡 Basse
**Version cible:** TBD

**Description:**
- Recettes les plus utilisées
- Événements par mois
- Budget moyen par événement
- Dashboard admin

**À faire:**
- [ ] À spécifier

---

## 🐛 Bugs connus

_Aucun bug connu actuellement_

---

## ✅ Historique des versions

### Version 1.6 - Décembre 2024 ✅
**Commits:** 8fe57aa, 21318f5, 0fb31d8, 1eaa87d

**Fonctionnalités:**
- ✅ Recherche de recettes par ingrédients multiples (logique ET)
- ✅ Gestion événements multi-jours avec sélection de dates
- ✅ Organisation et planification des recettes par jour
- ✅ Interface drag & drop pour la planification
- ✅ Page d'aide complète bilingue (FR/JP)
- ✅ Auto-génération liste de courses si vide
- ✅ Documentation: Règles projet et checklist déploiement

### Version 1.5 - Novembre 2024 ✅
**Fonctionnalités:**
- ✅ Système d'authentification multi-utilisateur
- ✅ Gestion des utilisateurs (admin)
- ✅ Hash sécurisé des mots de passe avec passlib
- ✅ Refactoring: db.py → 10 modules spécialisés

---

**Dernière mise à jour:** Version 1.6 - Décembre 2024
