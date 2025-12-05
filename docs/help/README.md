# Système d'aide modifiable (V1.7+)

## 📖 Vue d'ensemble

⚠️ **ATTENTION**: Depuis la version 1.7, l'aide est désormais **modifiable par les administrateurs** via une interface web.

L'ancien système (contenu HTML en dur dans `help.html`) a été remplacé par un système Markdown modifiable.

## 📍 Fichiers concernés

### Nouveaux fichiers (V1.7+)
- **Contenu FR**: `docs/help/content/help_fr.md` (Markdown)
- **Contenu JP**: `docs/help/content/help_jp.md` (Markdown)
- **Template édition**: `app/templates/admin_help_edit.html`
- **Route d'édition**: `app/routes/auth_routes.py` (fonctions `/admin/help/edit`)

### Fichiers existants (modifiés)
- **Template HTML**: `app/templates/help.html` (charge maintenant le Markdown)
- **Route**: `app/routes/auth_routes.py` (fonction `help_page`)

## ✏️ Comment modifier le contenu

### Option 1: Via l'interface web (RECOMMANDÉ - V1.7+)

1. **Se connecter en tant qu'administrateur**
2. **Accéder à la page d'aide** (`/help`)
3. **Cliquer sur "✏️ Éditer l'aide"** (bouton jaune visible uniquement pour les admins)
4. **Modifier le contenu Markdown** dans l'éditeur
5. **Basculer sur "Aperçu"** pour voir le rendu
6. **Cliquer sur "💾 Enregistrer"**

✅ **Avantages**: Modification sans redéploiement, aperçu en temps réel, accessible en production

### Option 2: Modifier directement les fichiers Markdown

Éditer directement:
- `docs/help/content/help_fr.md` pour le français
- `docs/help/content/help_jp.md` pour le japonais

Nécessite un commit et redéploiement.

### Option 3: Modifier directement le fichier help.html (DÉPRÉCIÉ)

Le fichier est structuré en sections bilingues (FR/JP). Chaque section suit ce format:

```html
<section id="nom-section" class="help-section ...">
    <h2>Titre de la section</h2>

    {% if lang == 'fr' %}
    <div class="space-y-4">
        <!-- Contenu en français -->
    </div>
    {% else %}
    <div class="space-y-4">
        <!-- Contenu en japonais -->
    </div>
    {% endif %}
</section>
```

### Option 2: Ajouter une nouvelle section

1. **Ajouter le lien dans la table des matières** (ligne ~49):
```html
<a href="#ma-section" class="block text-sm text-blue-600">
    {{ '📱 Ma Section' if lang == 'fr' else '📱 マイセクション' }}
</a>
```

2. **Ajouter la section dans le contenu** (ligne ~90+):
```html
<section id="ma-section" class="help-section bg-white rounded-lg shadow p-6">
    <h2 class="text-2xl font-bold mb-4 flex items-center gap-2">
        <span>📱</span>
        {{ 'Ma Section' if lang == 'fr' else 'マイセクション' }}
    </h2>

    {% if lang == 'fr' %}
    <div class="space-y-4">
        <p>Contenu en français...</p>
    </div>
    {% else %}
    <div class="space-y-4">
        <p>日本語のコンテンツ...</p>
    </div>
    {% endif %}
</section>
```

## 🎨 Classes CSS utilisées

### Couleurs de fond
- Section normale: `bg-white dark:bg-gray-800`
- Section mise en avant: `bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-200`
- Section spéciale (ex: recherche): `bg-gradient-to-r from-green-50 to-blue-50`

### Badges
```html
<span class="text-xs bg-green-500 text-white px-2 py-1 rounded">
    {{ 'NOUVEAU' if lang == 'fr' else '新機能' }}
</span>
```

### Encadrés
```html
<!-- Astuce -->
<div class="bg-blue-50 dark:bg-blue-900/30 p-4 rounded-lg border border-blue-200">
    <p class="font-semibold">💡 Astuce</p>
    <p class="mt-1">Contenu de l'astuce...</p>
</div>

<!-- Exemple -->
<div class="bg-yellow-50 dark:bg-yellow-900/30 p-4 rounded-lg border border-yellow-200">
    <p class="font-semibold">📌 Exemple</p>
    <p class="mt-1">Contenu de l'exemple...</p>
</div>

<!-- Note -->
<div class="bg-green-50 dark:bg-green-900/30 p-4 rounded-lg border border-green-200">
    <p class="font-semibold">✨ Note</p>
    <p class="mt-1">Contenu de la note...</p>
</div>
```

## 🔧 Modifier la FAQ

La section FAQ utilise des éléments `<details>`:

```html
<details class="bg-white dark:bg-gray-800 p-4 rounded-lg">
    <summary class="font-semibold cursor-pointer">
        Question en français / 日本語の質問
    </summary>
    <p class="mt-2 text-gray-600 dark:text-gray-400">
        Réponse en français / 日本語の回答
    </p>
</details>
```

## 🌐 Traductions

Pour ajouter du contenu bilingue, utilisez:

```html
{{ 'Texte français' if lang == 'fr' else 'テキスト日本語' }}
```

## 📝 Exemples de modifications courantes

### Ajouter une astuce

```html
<div class="bg-blue-50 dark:bg-blue-900/30 p-4 rounded-lg border border-blue-200">
    <p class="font-semibold">💡 {{ 'Astuce' if lang == 'fr' else 'ヒント' }}</p>
    <p class="mt-1">
        {{ 'Votre astuce en français' if lang == 'fr' else 'あなたのヒント' }}
    </p>
</div>
```

### Ajouter une liste numérotée

```html
<ol class="list-decimal ml-6 mt-2 space-y-2">
    <li>Première étape</li>
    <li>Deuxième étape</li>
    <li>Troisième étape</li>
</ol>
```

### Ajouter une liste à puces

```html
<ul class="list-disc ml-6 mt-2 space-y-1">
    <li>Premier point</li>
    <li>Deuxième point</li>
    <li>Troisième point</li>
</ul>
```

### Ajouter un bloc de code

```html
<div class="mt-2 p-3 bg-white dark:bg-gray-800 rounded border border-gray-300">
    <code class="text-sm">votre code ici</code>
</div>
```

## 🚀 Tester vos modifications

1. Sauvegardez le fichier `help.html`
2. Le serveur Uvicorn redémarre automatiquement avec `--reload`
3. Rafraîchissez la page: `http://localhost:8000/help?lang=fr`
4. Testez les deux langues: `?lang=fr` et `?lang=jp`

## 📍 Emojis utiles

- 📖 Recettes
- 🔍 Recherche
- 📅 Événements
- 📆 Multi-jours
- 🗓️ Planification
- 🛒 Liste de courses
- 💰 Budget
- 📚 Catalogue
- ❓ Aide/Question
- 💡 Astuce
- 📌 Exemple
- ✨ Note
- ⚠️ Attention
- ✅ Succès
- ❌ Erreur
- 🎯 Objectif
- 🚀 Nouveau

## 🎨 Personnaliser les couleurs

Pour changer les couleurs d'une section:

**Bleu (par défaut)**
```html
class="bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-200 dark:border-blue-700"
```

**Vert**
```html
class="bg-green-50 dark:bg-green-900/20 border-2 border-green-200 dark:border-green-700"
```

**Jaune**
```html
class="bg-yellow-50 dark:bg-yellow-900/20 border-2 border-yellow-200 dark:border-yellow-700"
```

**Rouge**
```html
class="bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-700"
```

## 📚 Ressources

- Tailwind CSS: https://tailwindcss.com/docs
- Alpine.js: https://alpinejs.dev/
- Emojis: https://emojipedia.org/

## ⚡ Déploiement

Après modification, commitez et déployez:

```bash
git add app/templates/help.html
git commit -m "Mise à jour de la page d'aide"
git push
./deploy/deploy_synology_V1_6.sh
```
