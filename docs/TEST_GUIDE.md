# 🧪 Guide de test - Fonctionnalité Budget

## 🚀 Démarrage

```bash
# Dans le répertoire du projet
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Puis ouvrir : http://localhost:8000

---

## ✅ Tests à effectuer

### 1. Test basique - Accès à la page budget

**FR (Euros)**
1. Accéder à `/events`
2. Sélectionner un événement existant
3. Cliquer sur "💰 Gérer le budget"
4. ✅ Vérifier : La page s'affiche sans erreur
5. ✅ Vérifier : Les montants sont affichés en **€**

**JP (Yens)**
1. Changer la langue avec le bouton "JP" en haut à droite
2. ✅ Vérifier : Les montants sont affichés en **¥**
3. ✅ Vérifier : Les catégories sont en japonais (会場, 装飾, etc.)

---

### 2. Test - Définir le budget prévisionnel

1. Sur la page budget, saisir un montant dans "Budget prévisionnel total"
   - Exemple FR : `5000` (pour 5000 €)
   - Exemple JP : `500000` (pour 500000 ¥)
2. Cliquer sur "Enregistrer"
3. ✅ Vérifier : Le montant apparaît dans la carte "Budget prévu"
4. ✅ Vérifier : La devise est correcte (€ ou ¥)

---

### 3. Test - Ajouter une dépense

1. Cliquer sur "+ Ajouter une dépense"
2. Remplir le formulaire :
   - **Catégorie** : Sélectionner "🏠 Location" (ou 会場 en JP)
   - **Description** : "Location salle de réception"
   - **Montant prévu** : 2000
   - **Montant réel** : Laisser vide pour l'instant
   - **Payé** : Ne PAS cocher
   - **Date de paiement** : Laisser vide
   - **Notes** : "Test note"
3. Cliquer sur "Ajouter"
4. ✅ Vérifier : La dépense apparaît dans le tableau
5. ✅ Vérifier : Le "Total prévu" inclut cette dépense
6. ✅ Vérifier : Le statut est "En attente" (ou 未払 en JP)

---

### 4. Test - Marquer une dépense comme payée

1. **Ajouter une nouvelle dépense** avec :
   - Catégorie : 🎨 Décoration (装飾)
   - Description : "Fleurs et décoration"
   - Montant prévu : 500
   - **Montant réel** : 480
   - **Cocher "Payé"**
   - Date de paiement : Date du jour
2. Cliquer sur "Ajouter"
3. ✅ Vérifier : Le montant réel (480) apparaît dans le tableau
4. ✅ Vérifier : Le statut est "✓ Payé" (ou 支払済 en JP)
5. ✅ Vérifier : Le "Total dépensé" est mis à jour (480)
6. ✅ Vérifier : La "Différence" est correcte (prévu - réel)

---

### 5. Test - Résumé budgétaire

Avec les dépenses ci-dessus :
- Budget prévu : 5000
- Dépenses prévues : 2500 (2000 + 500)
- Dépenses réelles : 480

✅ Vérifier les cartes :
- **Budget prévu** : 2500 (total des dépenses prévues)
- **Dépensé** : 480
- **Différence** : 2020 (en vert car positif)

---

### 6. Test - Prix des ingrédients (Liste de courses)

1. Retourner à la page de l'événement
2. Cliquer sur "📝 Liste de courses" (ou リストを編集)
3. Sélectionner un ingrédient et cliquer sur "✏️ Modifier"

**Saisir les prix prévisionnels :**
1. Prix prévu : 0.30 (€ ou ¥)
2. Cliquer sur "Enregistrer prix"
3. ✅ Vérifier : Pas d'erreur

**Saisir les prix réels (après achat) :**
1. Re-modifier le même ingrédient
2. Prix réel : 0.28
3. **Cocher "Acheté"** ⚠️ IMPORTANT
4. Cliquer sur "Enregistrer prix"
5. ✅ Vérifier : Le prix est sauvegardé

**Vérifier l'apprentissage automatique :**
1. Créer un nouvel événement
2. Ajouter la même recette
3. Générer la liste de courses
4. ⚠️ *Note : La suggestion de prix n'est pas encore visible dans l'UI, mais elle est sauvegardée dans la DB*

---

### 7. Test - Multidevise selon langue

**Basculer FR → JP :**
1. Sur la page budget (FR avec €)
2. Cliquer sur "JP"
3. ✅ Vérifier : Tous les montants passent de € à ¥
4. ✅ Vérifier : Les catégories sont traduites
5. ✅ Vérifier : Les labels sont en japonais

**Basculer JP → FR :**
1. Sur la page budget (JP avec ¥)
2. Cliquer sur "FR"
3. ✅ Vérifier : Tous les montants passent de ¥ à €
4. ✅ Vérifier : Tout est en français

---

### 8. Test - Supprimer une dépense

1. Dans le tableau des dépenses, cliquer sur "Supprimer"
2. Confirmer
3. ✅ Vérifier : La dépense disparaît
4. ✅ Vérifier : Les totaux sont mis à jour

---

## 🐛 Tests de cas limites

### Cas 1 : Budget sans dépenses
1. Créer un nouvel événement
2. Accéder au budget
3. ✅ Vérifier : Affichage "0.00" partout
4. ✅ Vérifier : Message "Aucune dépense enregistrée"

### Cas 2 : Checkbox non cochée
1. Ajouter une dépense SANS cocher "Payé"
2. ✅ Vérifier : Pas d'erreur 422
3. ✅ Vérifier : La dépense est créée avec statut "En attente"

### Cas 3 : Montant réel vide
1. Ajouter une dépense avec montant prévu mais montant réel vide
2. ✅ Vérifier : Affichage "-" dans la colonne "Réel"

### Cas 4 : Budget dépassé
1. Définir un budget prévu de 1000
2. Ajouter des dépenses réelles totales > 1000
3. ✅ Vérifier : La carte "Différence" passe en rouge
4. ✅ Vérifier : Le montant affiché est négatif

---

## 🔍 Vérifications dans la base de données

```bash
sqlite3 data/recette.sqlite3
```

### Vérifier les catégories
```sql
SELECT c.id, c.icon, t.lang, t.name
FROM expense_category c
JOIN expense_category_translation t ON t.category_id = c.id
ORDER BY c.id, t.lang;
```

**Attendu :** 7 catégories × 2 langues = 14 lignes

### Vérifier les dépenses
```sql
SELECT e.id, e.description, e.planned_amount, e.actual_amount, e.is_paid,
       t.name as category_name
FROM event_expense e
JOIN expense_category c ON c.id = e.category_id
JOIN expense_category_translation t ON t.category_id = c.id AND t.lang = 'fr'
WHERE e.event_id = 1;  -- Remplacer 1 par l'ID de votre événement test
```

### Vérifier l'historique des prix
```sql
SELECT ingredient_name_display, unit_price, unit, usage_count, last_used_date
FROM ingredient_price_history
ORDER BY last_used_date DESC;
```

**Test du trigger :**
- Après avoir coché "Acheté" sur un ingrédient
- ✅ Vérifier : Une ligne apparaît dans cette table

---

## 📊 Résultat attendu complet

Après tous les tests, vous devriez avoir :

**Page Budget :**
- Budget prévisionnel défini
- 2-3 dépenses (certaines payées, d'autres non)
- Résumé cohérent (prévu vs réel)
- Couleurs appropriées (vert/rouge selon dépassement)

**Liste de courses :**
- Prix prévisionnels sur quelques ingrédients
- Prix réels sur les ingrédients "achetés"

**Base de données :**
- `expense_category` : 7 catégories
- `expense_category_translation` : 14 traductions
- `event_expense` : Plusieurs dépenses test
- `ingredient_price_history` : Au moins 1 entrée

---

## ⚠️ Problèmes connus résolus

✅ **Plantage avec valeurs NULL** - Corrigé avec valeurs par défaut
✅ **Erreur 422 sur checkbox** - Corrigé avec conversion string → bool
✅ **Devise fixe** - Corrigé avec devise selon langue (€/¥)

---

## 🎯 Critères de validation

La fonctionnalité est **validée** si :

1. ✅ Aucune erreur 500 ou 422
2. ✅ Toutes les pages s'affichent correctement
3. ✅ Les devises changent selon la langue (€/¥)
4. ✅ Les traductions FR/JP sont correctes
5. ✅ Les calculs budgétaires sont justes
6. ✅ Les prix des ingrédients sont sauvegardés dans l'historique
7. ✅ Le passage FR ↔ JP fonctionne sans perte de données

---

## 🚀 Si tout fonctionne

**Prochaines étapes :**
1. Tester avec des données réelles sur plusieurs événements
2. Valider les workflows complets (planification → achat → analyse)
3. Documenter les cas d'usage métier
4. Déployer en production après validation complète

**Améliorations futures possibles :**
- Auto-suggestion de prix dans l'UI (déjà en DB)
- Export Excel du résumé budgétaire
- Graphiques de visualisation
- Alertes de dépassement budgétaire

---

**Bon test ! 🎉**

Si vous rencontrez un problème, consultez les logs du serveur ou utilisez :
```bash
python verify_budget_ready.py
```
