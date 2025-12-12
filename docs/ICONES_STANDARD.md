# Icônes Standardisées - Application Recette

**Date**: 11 décembre 2025
**Version**: 1.0

---

## 🎨 Standard d'Icônes

Toutes les icônes de l'application suivent le format : **icône emoji + texte**

### Format Standard

```html
<button class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300">
  ✏️ Modifier
</button>
```

---

## 📋 Référence des Icônes par Action

### Actions Principales

| Action | Icône | Français | Japonais | Couleur |
|--------|-------|----------|----------|---------|
| **Modifier / Éditer** | ✏️ | Modifier | 編集 | Bleu |
| **Supprimer** | 🗑️ | Supprimer | 削除 | Rouge |
| **Copier / Dupliquer** | 📋 | Copier | コピー | Jaune/Orange |
| **Ajouter / Nouveau** | ➕ | Ajouter | 追加 | Vert |
| **Enregistrer** | 💾 | Enregistrer | 保存 | Vert |
| **Annuler** | ❌ | Annuler | キャンセル | Gris |
| **Valider / Confirmer** | ✅ | Valider | 確認 | Vert |
| **Activer** | ✅ | Activer | 有効化 | Vert |
| **Désactiver** | 🔴 | Désactiver | 無効化 | Orange |
| **Mot de passe** | 🔑 | Mot de passe | パスワード | Bleu |
| **Rechercher** | 🔍 | Rechercher | 検索 | Bleu |
| **Imprimer** | 🖨️ | Imprimer | 印刷 | Gris |
| **Télécharger** | ⬇️ | Télécharger | ダウンロード | Bleu |

### Navigation

| Action | Icône | Français | Japonais |
|--------|-------|----------|----------|
| **Retour** | ← | Retour | 戻る |
| **Suivant** | → | Suivant | 次へ |
| **Monter** | ⬆️ | Monter | 上へ |
| **Descendre** | ⬇️ | Descendre | 下へ |

### États et Informations

| Type | Icône | Usage |
|------|-------|-------|
| **Recettes** | 🍳 | Navigation, headers |
| **Événements** | 📅 | Navigation, headers |
| **Shopping List** | 🛒 | Navigation, headers |
| **Budget** | 💰 | Navigation, headers |
| **Ingrédients** | 🥕 | Recherche ingrédients |
| **Catalogue** | 📊 | Catalogue prix |
| **Aide** | ❓ | Navigation aide |
| **Profil** | 👤 | Profil utilisateur |
| **Admin** | ⭐ | Badge admin |
| **Déconnexion** | 🚪 | Logout |

---

## 🎨 Classes CSS Standardisées

### Boutons avec Icônes

```html
<!-- Modifier (Bleu) -->
<button class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 text-sm">
  ✏️ {{ 'Modifier' if lang == 'fr' else '編集' }}
</button>

<!-- Supprimer (Rouge) -->
<button class="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 text-sm">
  🗑️ {{ 'Supprimer' if lang == 'fr' else '削除' }}
</button>

<!-- Copier (Jaune/Orange) -->
<button class="text-yellow-600 dark:text-yellow-400 hover:text-yellow-800 dark:hover:text-yellow-300 text-sm">
  📋 {{ 'Copier' if lang == 'fr' else 'コピー' }}
</button>

<!-- Ajouter (Vert) -->
<button class="text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-300 text-sm">
  ➕ {{ 'Ajouter' if lang == 'fr' else '追加' }}
</button>
```

### Tailles d'Icônes

```css
.icon-sm   { font-size: 1rem; }     /* Petites icônes dans texte */
.icon-md   { font-size: 1.25rem; }  /* Icônes standards */
.icon-lg   { font-size: 1.5rem; }   /* Grandes icônes */
.icon-xl   { font-size: 2rem; }     /* Très grandes icônes */
.icon-xxl  { font-size: 4rem; }     /* Empty states */
```

---

## 📝 Exemples d'Usage

### Tableau avec Actions

```html
<td class="px-4 py-4 text-right">
  <div class="flex items-center justify-end gap-3">
    <!-- Modifier -->
    <button class="text-blue-600 dark:text-blue-400 hover:text-blue-800 text-sm">
      ✏️ {{ 'Modifier' if lang == 'fr' else '編集' }}
    </button>

    <!-- Copier -->
    <button class="text-yellow-600 dark:text-yellow-400 hover:text-yellow-800 text-sm">
      📋 {{ 'Copier' if lang == 'fr' else 'コピー' }}
    </button>

    <!-- Supprimer -->
    <button class="text-red-600 dark:text-red-400 hover:text-red-800 text-sm">
      🗑️ {{ 'Supprimer' if lang == 'fr' else '削除' }}
    </button>
  </div>
</td>
```

### Boutons d'Action Principaux

```html
<!-- Bouton Nouveau -->
<button class="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
  <span class="text-xl">➕</span>
  <span>{{ 'Nouvel événement' if lang == 'fr' else '新規イベント' }}</span>
</button>

<!-- Bouton Enregistrer -->
<button class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
  <span class="text-xl">💾</span>
  <span>{{ 'Enregistrer' if lang == 'fr' else '保存' }}</span>
</button>
```

---

## ⚠️ À Éviter

❌ **Icônes seules sans texte** (sauf cas spécifiques avec title/tooltip)
```html
<!-- Mauvais -->
<button>🗑️</button>

<!-- Bon -->
<button>🗑️ Supprimer</button>
```

❌ **Icônes incohérentes pour la même action**
```html
<!-- Mauvais -->
<button>✏️ Modifier</button>  <!-- Dans une page -->
<button>📝 Modifier</button>  <!-- Dans une autre page -->

<!-- Bon -->
<button>✏️ Modifier</button>  <!-- Partout -->
```

❌ **Couleurs non standardisées**
```html
<!-- Mauvais -->
<button class="text-purple-600">🗑️ Supprimer</button>

<!-- Bon -->
<button class="text-red-600">🗑️ Supprimer</button>
```

---

## 🔄 Migration

### Pages Harmonisées

- [x] ingredient_catalog.html ✅ (référence)
- [x] ingredient_specific_conversions.html ✅
- [x] unit_conversions.html ✅
- [x] events_list.html ✅
- [x] recipes_list.html ✅ (déjà conforme)
- [x] recipe_detail.html ✅
- [x] event_detail.html ✅
- [x] tags_admin.html ✅ (3 sections: catégories, tags, types d'événements)
- [x] admin_users.html ✅
- [x] admin_help_edit.html ✅

### Checklist de Conformité

Pour chaque bouton d'action :
- [ ] Icône emoji présente
- [ ] Texte explicite (FR/JP)
- [ ] Couleur standardisée
- [ ] Classes CSS cohérentes
- [ ] Dark mode supporté
- [ ] Taille appropriée au contexte

---

## 📊 Résumé par Couleur

| Couleur | Actions | Classes CSS |
|---------|---------|-------------|
| **Bleu** | Modifier, Rechercher, Télécharger, Info | `text-blue-600 dark:text-blue-400` |
| **Rouge** | Supprimer, Annuler, Danger | `text-red-600 dark:text-red-400` |
| **Vert** | Ajouter, Enregistrer, Valider, Success | `text-green-600 dark:text-green-400` |
| **Jaune/Orange** | Copier, Warning | `text-yellow-600 dark:text-yellow-400` |
| **Gris** | Annuler, Neutre | `text-gray-600 dark:text-gray-400` |
| **Violet** | Tags, Catégories | `text-purple-600 dark:text-purple-400` |

---

**Date de dernière mise à jour** : 11 décembre 2025
