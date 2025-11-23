# Configuration de l'Authentification

Ce document explique comment configurer la protection par mot de passe pour l'application Recette.

## Vue d'ensemble

L'application supporte une protection par mot de passe partagé qui peut être activée/désactivée selon l'environnement :

- **Développement** : Protection **désactivée** par défaut (pour faciliter le développement)
- **Production** : Protection **activée** par défaut (pour sécuriser l'accès)

## Configuration

### 1. Fichier `.env` (Développement)

```env
# Protection par mot de passe (désactivée en développement)
REQUIRE_PASSWORD=False
SECRET_KEY=dev-secret-key-for-sessions
```

Pour activer la protection en développement, changez `REQUIRE_PASSWORD=True`.

### 2. Fichier `.env` (Production)

Créez un fichier `.env` à partir de `.env.production.example` :

```bash
cp .env.production.example .env
```

Puis modifiez les valeurs :

```env
# Protection par mot de passe (production uniquement)
REQUIRE_PASSWORD=True
SHARED_PASSWORD=RecipeTakachan2026
SECRET_KEY=votre-clé-secrète-unique-ici
```

**Important :**
- Changez `SECRET_KEY` pour une valeur aléatoire unique en production
- Le `SHARED_PASSWORD` est le mot de passe que tous les utilisateurs utiliseront

### 3. Générer une clé secrète sécurisée

Pour générer une clé secrète aléatoire :

```python
import secrets
print(secrets.token_urlsafe(32))
```

Ou en ligne de commande :

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Utilisation

### Connexion

1. Accédez à l'application : `http://votre-nas:8000/`
2. Vous serez redirigé vers `/login`
3. Entrez le mot de passe partagé : `RecipeTakachan2026`
4. Vous serez redirigé vers la liste des recettes

### Déconnexion

Accédez à `/logout?lang=fr` (ou `?lang=jp` pour le japonais)

### Session

- La session dure **24 heures**
- Après 24h, vous devrez vous reconnecter
- La session est stockée dans un cookie sécurisé

## Routes Publiques (sans authentification)

Ces routes sont accessibles sans mot de passe :

- `/login` - Page de connexion
- `/logout` - Déconnexion
- `/static/*` - Fichiers statiques (CSS, JS, images)
- `/health` - Health check (production uniquement)

Toutes les autres routes nécessitent une authentification.

## Sécurité

### Points forts

✅ Session sécurisée avec cookie HTTPOnly
✅ Mot de passe configurable via variable d'environnement
✅ Protection activable/désactivable selon l'environnement
✅ Timeout de session (24h)

### Limites actuelles

⚠️ Mot de passe partagé (tous les utilisateurs utilisent le même)
⚠️ Pas de gestion d'utilisateurs individuels
⚠️ Pas de reset de mot de passe

### Recommandations

1. **Utilisez HTTPS** : Configurez votre NAS pour utiliser HTTPS avec un certificat SSL
2. **Changez la clé secrète** : Utilisez une valeur aléatoire unique en production
3. **Mot de passe fort** : Utilisez un mot de passe complexe et partagez-le de manière sécurisée
4. **Sauvegardes** : Faites des sauvegardes régulières de votre base de données

## Dépannage

### "Mot de passe incorrect"

- Vérifiez que vous avez bien configuré `SHARED_PASSWORD` dans le fichier `.env`
- Vérifiez qu'il n'y a pas d'espaces avant/après le mot de passe
- Le mot de passe est sensible à la casse

### Redirection infinie vers `/login`

- Vérifiez que `SECRET_KEY` est bien configuré
- Vérifiez que le middleware de session est bien ajouté
- Essayez de vider les cookies de votre navigateur

### Protection désactivée alors qu'elle devrait être active

- Vérifiez que `REQUIRE_PASSWORD=True` dans le fichier `.env`
- Redémarrez l'application après modification du `.env`
- Vérifiez les logs au démarrage : vous devriez voir "🔒 Protection par mot de passe activée"

## Migration future vers authentification multi-utilisateurs

Le système est conçu pour faciliter une future migration vers un système d'authentification complet avec :

- Comptes utilisateurs individuels
- Préférences par utilisateur (langue, pays)
- Recettes privées/partagées
- Gestion des droits

Les tables de la base de données ont déjà un champ `user_id` (nullable) préparé pour cette évolution.
