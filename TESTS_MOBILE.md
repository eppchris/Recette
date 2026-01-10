# Guide de test mobile pour Recette App

## Méthode 1 : Test sur smartphone réel (recommandé) 📱

### Étapes de configuration

1. **Lancer le serveur en mode test mobile**
   ```bash
   ./run_mobile_test.sh
   ```

2. **Sur votre smartphone**
   - Connectez-vous au **même réseau WiFi** que votre ordinateur
   - Le script affichera l'URL à utiliser (ex: `http://192.168.1.33:8000`)
   - Ouvrez cette URL dans le navigateur de votre smartphone

3. **Points à tester**
   - ✅ Navigation mobile (menu hamburger)
   - ✅ Tableaux scrollables horizontalement
   - ✅ Formulaires et saisie tactile
   - ✅ Mode sombre/clair
   - ✅ Rotation portrait/paysage
   - ✅ Performance de chargement
   - ✅ Taille des boutons et zones tactiles

### Problèmes courants et solutions

**❌ "Impossible de se connecter"**
- Vérifiez que smartphone et ordinateur sont sur le même WiFi
- Désactivez temporairement le pare-feu de votre ordinateur
- Sur Mac: Préférences Système > Sécurité > Pare-feu

**❌ "Connexion refusée"**
- Vérifiez que le serveur est bien lancé
- Vérifiez l'adresse IP affichée par le script

---

## Méthode 2 : DevTools du navigateur (test rapide) 💻

1. **Ouvrir DevTools**
   - Chrome/Edge: `F12` ou `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
   - Firefox: `F12` ou `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)

2. **Activer le mode responsive**
   - Cliquez sur l'icône 📱 en haut à gauche des DevTools
   - Ou `Cmd+Shift+M` (Mac) / `Ctrl+Shift+M` (Windows)

3. **Sélectionner un appareil**
   - iPhone SE, iPhone 12/13/14 Pro, iPhone 14 Pro Max
   - Samsung Galaxy S20/S21
   - iPad Air, iPad Mini

4. **Tester les interactions tactiles**
   - Activez le mode "Touch" dans DevTools
   - Testez le scroll, les clics, les hover states

### Limitations de cette méthode
- ⚠️ Ne simule pas parfaitement le comportement réel
- ⚠️ Performance différente d'un vrai smartphone
- ⚠️ Gestes tactiles simulés, pas réels

---

## Méthode 3 : Tunneling avec ngrok (test à distance) 🌐

Si vous voulez tester depuis n'importe où (pas besoin du même WiFi):

1. **Installer ngrok**
   ```bash
   brew install ngrok  # Mac
   # ou téléchargez depuis https://ngrok.com/download
   ```

2. **Lancer votre application localement**
   ```bash
   python main.py
   ```

3. **Créer un tunnel**
   ```bash
   ngrok http 8000
   ```

4. **Utiliser l'URL publique fournie**
   - ngrok vous donnera une URL type: `https://abc123.ngrok.io`
   - Utilisez cette URL sur n'importe quel smartphone

⚠️ **Note de sécurité**: L'URL ngrok est accessible publiquement. Ne partagez pas de données sensibles et arrêtez le tunnel après les tests.

---

## Checklist de test mobile 📋

### Interface utilisateur
- [ ] Le menu hamburger s'ouvre/ferme correctement
- [ ] Tous les textes sont lisibles (taille de police)
- [ ] Les boutons ont une taille suffisante (minimum 44x44px)
- [ ] Pas de débordement horizontal (pas de scroll horizontal involontaire)
- [ ] Les tableaux sont scrollables horizontalement quand nécessaire
- [ ] Les espacements sont corrects sur petit écran

### Navigation
- [ ] Le fil d'Ariane (breadcrumb) est visible et fonctionnel
- [ ] Les liens et boutons répondent au toucher
- [ ] Le retour en arrière fonctionne
- [ ] La navigation entre sections est fluide

### Formulaires
- [ ] Les champs de saisie sont suffisamment grands
- [ ] Le clavier virtuel ne masque pas les champs actifs
- [ ] Les sélecteurs (dropdowns) fonctionnent correctement
- [ ] La validation des formulaires est claire

### Performance
- [ ] Les pages se chargent en moins de 3 secondes
- [ ] Pas de lag lors du scroll
- [ ] Les images se chargent correctement
- [ ] Le mode sombre/clair bascule instantanément

### Fonctionnalités spécifiques
- [ ] Import de recettes (PDF, URL)
- [ ] Calcul de coûts
- [ ] Gestion des événements
- [ ] Logs d'accès (tableaux complexes)
- [ ] Conversions d'unités

### Responsive
- [ ] Portrait (orientation verticale)
- [ ] Paysage (orientation horizontale)
- [ ] Différentes tailles d'écran (petit, moyen, grand)

---

## Pages critiques à tester en priorité

1. **[recipes_list.html](app/templates/recipes_list.html)** - Page principale
2. **[recipe_detail.html](app/templates/recipe_detail.html)** - Détail recette
3. **[access_logs.html](app/templates/access_logs.html)** - Tableaux complexes
4. **[event_detail.html](app/templates/event_detail.html)** - Gestion événements
5. **[shopping_list.html](app/templates/shopping_list.html)** - Liste courses

---

## Améliorations suggérées selon les résultats

### Si les tableaux posent problème
- Envisager un affichage en cartes pour mobile
- Ajouter des colonnes collapsibles
- Améliorer le scroll horizontal avec indicateurs

### Si les formulaires sont difficiles à utiliser
- Augmenter la taille des champs
- Améliorer l'espacement vertical
- Ajouter des labels flottants

### Si la navigation est confuse
- Rendre le menu plus visible
- Ajouter un bouton "retour" fixe
- Améliorer le fil d'Ariane

### Si les performances sont lentes
- Optimiser les images
- Lazy loading pour les tableaux longs
- Pagination pour les listes

---

## Capture d'écran et documentation des bugs

Lorsque vous trouvez un problème:

1. Prenez une capture d'écran sur votre smartphone
2. Notez:
   - Le modèle de smartphone
   - Le navigateur utilisé (Safari, Chrome, etc.)
   - L'action qui cause le problème
   - Le comportement attendu vs. observé

3. Pour partager: AirDrop les captures vers votre Mac ou envoyez-les par email

---

## Commandes utiles

```bash
# Lancer en mode test mobile (recommandé)
./run_mobile_test.sh

# Lancer normalement (localhost uniquement)
python main.py

# Vérifier votre IP locale
ifconfig | grep "inet " | grep -v 127.0.0.1

# Tester la connectivité depuis le smartphone
# Sur smartphone, ouvrez http://[VOTRE_IP]:8000/health
```

---

## Notes de sécurité

- ⚠️ Le mode test mobile rend l'application accessible sur votre réseau local
- ✅ C'est sécurisé sur un réseau WiFi privé/domestique
- ❌ Ne le faites pas sur un WiFi public
- 🔒 La protection par mot de passe reste active si configurée dans `.env`

---

**Besoin d'aide ?** Vérifiez les logs dans le terminal où le serveur tourne.
