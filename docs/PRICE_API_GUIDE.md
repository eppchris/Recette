# 📊 Guide d'utilisation des APIs de prix

## ⚠️ IMPORTANT : Mode Opt-In uniquement

Les APIs de prix externes sont **complètement optionnelles** et **séparées** du code principal. Elles :
- ✅ N'affectent PAS le fonctionnement normal de l'application
- ✅ Ne modifient JAMAIS automatiquement la base de données
- ✅ Sont utilisées UNIQUEMENT sur demande explicite
- ✅ Peuvent être testées sans risque via `test_price_api.py`

---

## 🏗️ Architecture

```
app/services/price_providers/
├── base.py               # Interface commune
├── manual.py            # Prix locaux (toujours actif)
├── rakuten.py           # API Rakuten (Japon) - opt-in
└── openfoodfacts.py     # API Open Food Facts (France) - opt-in
```

---

## 🔧 Configuration

### 1️⃣ Rakuten API (Japon) - **Recommandé**

#### Inscription (gratuite)
1. Aller sur https://webservice.rakuten.co.jp/app/create
2. Créer un compte développeur
3. Créer une application pour obtenir l'**Application ID**

#### Configuration
Ajouter dans `.env` :
```bash
RAKUTEN_APP_ID=votre_application_id_ici
```

#### Limites
- **Gratuit** : 10,000 requêtes/jour
- **Payant** : Plans disponibles pour plus de requêtes

---

### 2️⃣ Open Food Facts (France/International)

#### Configuration
**Aucune !** L'API est gratuite et sans authentification.

#### Limitations
- ❌ **Ne fournit PAS de prix** (uniquement données produit)
- ✅ Utile pour vérifier l'existence d'un produit
- ✅ Peut servir de base pour estimation IA

---

## 🧪 Tester sans risque

### Script de test (READ-ONLY)

```bash
python3 test_price_api.py
```

Ce script :
- ✅ Teste les APIs configurées
- ✅ Affiche les résultats trouvés
- ✅ **NE MODIFIE PAS** la base de données
- ✅ Permet de vérifier que les APIs fonctionnent

### Exemple de sortie

```
🔍 Recherche: Riz (kg) - Langue: jp
--------------------------------------------------------------------------------
✅ 2 résultat(s) trouvé(s):

  [1] Source: Base de données locale
      Prix: 2.5€ / 425¥
      Unité: kg (qty: 1.0)
      Confiance: 100%
      Notes: Prix saisi manuellement

  [2] Source: Rakuten Ichiba
      Prix: 2.8€ / 448¥
      Unité: kg (qty: 1.0)
      Confiance: 70%
      URL: https://item.rakuten.co.jp/...
      Notes: Produit: 国産米 コシヒカリ 5kg
```

---

## 📖 Utilisation dans l'application

### Option 1 : Via script Python séparé

Créer un script `update_prices_from_api.py` :

```python
from app.services.price_service import PriceService
from app.models import db

# Initialiser avec APIs externes
service = PriceService(enable_external=True)

# Rechercher un prix
result = service.search_price("Riz", unit="kg", lang="jp")

if result and result.price_jpy:
    print(f"Prix trouvé: {result.price_jpy}¥")

    # Demander confirmation avant mise à jour
    confirm = input("Mettre à jour en base ? (o/n): ")
    if confirm.lower() == 'o':
        db.update_ingredient_catalog_price(
            ingredient_id=123,
            price_jpy=result.price_jpy
        )
```

### Option 2 : Via interface web (future)

Ajouter un bouton "🔍 Rechercher prix en ligne" dans le catalogue :
- L'utilisateur clique sur le bouton
- Une fenêtre modale affiche les résultats
- L'utilisateur choisit quel prix utiliser
- Mise à jour manuelle uniquement

---

## 🎯 Bonnes pratiques

### ✅ À FAIRE
- Tester avec `test_price_api.py` d'abord
- Vérifier les résultats avant mise à jour
- Utiliser `prefer_local=True` pour privilégier les prix manuels
- Configurer uniquement les APIs nécessaires

### ❌ À NE PAS FAIRE
- Ne JAMAIS mettre à jour automatiquement sans validation
- Ne pas exposer les clés API dans le code (utiliser `.env`)
- Ne pas faire confiance aveuglément aux prix API (vérifier la cohérence)

---

## 🔐 Sécurité

### Variables d'environnement (`.env`)

```bash
# APIs de prix (optionnelles)
RAKUTEN_APP_ID=your_app_id_here
```

**Ajouter au `.gitignore` :**
```gitignore
.env
*.env
```

---

## 📈 Roadmap future

- [ ] Interface web pour recherche manuelle
- [ ] Cache des résultats API (éviter requêtes répétées)
- [ ] Historique des prix pour tendances
- [ ] Alertes si prix change significativement
- [ ] Support d'autres APIs (Amazon, Auchan, etc.)

---

## 🆘 Dépannage

### Rakuten retourne "Unauthorized"
→ Vérifier que `RAKUTEN_APP_ID` est correct dans `.env`

### Aucun résultat trouvé
→ Essayer avec le nom en japonais pour Rakuten
→ Vérifier l'orthographe de l'ingrédient

### Erreur "database is locked"
→ Fermer DB Browser ou tout autre programme utilisant la base

---

## 📞 Support

Pour toute question :
1. Vérifier ce guide
2. Tester avec `test_price_api.py`
3. Consulter les logs d'erreur
