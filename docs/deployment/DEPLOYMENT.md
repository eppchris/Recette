# Guide de Déploiement - Synology DS213+

Ce guide vous aide à déployer l'application **Recette FR/JP** sur votre NAS Synology DS213+.

## Prérequis

- Synology DS213+ avec DSM installé
- Accès SSH activé sur le NAS
- Python 3 installé via DSM Package Center
- Connexion réseau stable
- Clé API Groq (pour la traduction automatique)

## Architecture de Déploiement

L'application sera installée dans `/volume1/web/recette/` avec la structure suivante:

```
/volume1/web/recette/
├── app/                    # Code de l'application
├── data/                   # Base de données SQLite
├── logs/                   # Fichiers de logs
├── static/                 # Fichiers statiques
├── venv/                   # Environnement virtuel Python
├── main_prod.py           # Point d'entrée production
├── config_prod.py         # Configuration production
├── requirements.txt       # Dépendances Python
├── .env                   # Variables d'environnement
├── start_recette.sh       # Script de démarrage
└── stop_recette.sh        # Script d'arrêt
```

## Étapes de Déploiement

### 1. Préparer le NAS

Connectez-vous en SSH à votre NAS:

```bash
ssh admin@<IP_DU_NAS>
```

Installez Python 3 via DSM Package Center si ce n'est pas déjà fait.

### 2. Déployer les Fichiers depuis Votre Machine

Depuis votre machine de développement, exécutez le script de déploiement:

```bash
chmod +x deploy_synology.sh
./deploy_synology.sh admin@192.168.1.14 /volume1/web/recette
```

Ce script va:
- Créer la structure de répertoires
- Copier tous les fichiers de l'application
- Copier la base de données de développement vers `recette_prod.sqlite3`

### 3. Configurer l'Environnement sur le NAS

Connectez-vous en SSH au NAS:

```bash
ssh admin@192.168.1.14
cd /volume1/web/recette
```

#### A. Créer l'environnement virtuel Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### B. Créer le fichier .env

```bash
nano .env
```

Copiez le template de production et remplissez les valeurs:

```bash
cp .env.production.example .env
nano .env
```

Configuration complète du `.env`:

```env
# Environnement
ENV=prod

# Clé API Groq pour la traduction automatique
GROQ_API_KEY=votre_clé_api_groq_ici

# Port de l'application
PORT=8000

# Niveau de log
LOG_LEVEL=info

# 🔒 PROTECTION PAR MOT DE PASSE (NOUVEAU)
REQUIRE_PASSWORD=True
SHARED_PASSWORD=RecipeTakachan2026
SECRET_KEY=CHANGEZ_CETTE_CLE_SECRETE_ICI
```

**⚠️ Important - Générer une clé secrète unique:**

```bash
# Sur le NAS, générer une clé aléatoire sécurisée
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Copiez le résultat et remplacez SECRET_KEY dans .env
```

Sauvegardez avec `Ctrl+O`, puis quittez avec `Ctrl+X`.

#### C. Vérifier les permissions

```bash
chmod +x start_recette.sh
chmod +x stop_recette.sh
chmod 644 .env
```

### 4. Démarrer l'Application

#### Option A: Démarrage Manuel

```bash
cd /volume1/web/recette
./start_recette.sh
```

L'application sera accessible sur: `http://<IP_DU_NAS>:8000/recipes`

Pour arrêter l'application:

```bash
cd /volume1/web/recette
./stop_recette.sh
```

#### Option B: Démarrage Automatique (Tâche Planifiée DSM)

1. Connectez-vous à DSM via le navigateur
2. Ouvrez **Panneau de configuration** > **Planificateur de tâches**
3. Créez une nouvelle tâche déclenchée: **Créer** > **Tâche déclenchée** > **Script défini par l'utilisateur**
4. Configuration:
   - **Nom**: Démarrage Recette
   - **Utilisateur**: root (ou votre utilisateur admin)
   - **Événement**: Démarrage
   - **Script**:
     ```bash
     /volume1/web/recette/start_recette.sh
     ```
5. Enregistrez

### 5. Vérification

#### Vérifier que l'application fonctionne:

```bash
# Vérifier le processus
ps aux | grep uvicorn

# Vérifier les logs
tail -f /volume1/web/recette/logs/recette.log
```

#### Tester via le navigateur:

- Liste des recettes: `http://<IP_DU_NAS>:8000/recipes`
- Health check: `http://<IP_DU_NAS>:8000/health`

### 6. Configuration du Pare-feu (Optionnel)

Si vous souhaitez accéder à l'application depuis l'extérieur:

1. Dans DSM: **Panneau de configuration** > **Sécurité** > **Pare-feu**
2. Modifiez les règles pour autoriser le port 8000
3. Configurez la redirection de port sur votre routeur (port 8000 vers IP du NAS)

## Accès à l'Application

### Accès Local

- **URL**: `http://<IP_DU_NAS>:8000/recipes`
- **Version française**: `http://<IP_DU_NAS>:8000/recipes?lang=fr`
- **Version japonaise**: `http://<IP_DU_NAS>:8000/recipes?lang=jp`

### Accès via Reverse Proxy (Optionnel)

Si vous avez configuré un reverse proxy (nginx ou Apache) sur le NAS, vous pouvez créer une configuration pour accéder via un sous-domaine:

Exemple de configuration nginx:

```nginx
server {
    listen 80;
    server_name recettes.votre-domaine.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Maintenance

### Consulter les Logs

```bash
# Logs applicatifs
tail -f /volume1/web/recette/logs/recette.log

# Logs d'erreur
tail -f /volume1/web/recette/logs/recette_error.log
```

### Mettre à Jour l'Application

1. Arrêtez l'application:
   ```bash
   ./stop_recette.sh
   ```

2. Depuis votre machine de développement, redéployez:
   ```bash
   ./deploy_synology.sh admin@<IP_DU_NAS> /volume1/web/recette
   ```

3. Sur le NAS, mettez à jour les dépendances si nécessaire:
   ```bash
   cd /volume1/web/recette
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. Redémarrez l'application:
   ```bash
   ./start_recette.sh
   ```

### Sauvegarder la Base de Données

```bash
# Créer une sauvegarde
cp /volume1/web/recette/data/recette_prod.sqlite3 \
   /volume1/web/recette/data/recette_prod_backup_$(date +%Y%m%d).sqlite3

# Configurer une sauvegarde automatique quotidienne
# Via Planificateur de tâches DSM
```

## Troubleshooting

### L'application ne démarre pas

1. Vérifiez les logs:
   ```bash
   cat /volume1/web/recette/logs/recette.log
   ```

2. Vérifiez que Python 3 est installé:
   ```bash
   python3 --version
   ```

3. Vérifiez que les dépendances sont installées:
   ```bash
   cd /volume1/web/recette
   source venv/bin/activate
   pip list
   ```

### Erreur "Port 8000 already in use"

Un autre service utilise le port 8000. Changez le port dans `.env`:

```bash
nano .env
# Modifiez: PORT=8001
```

Redémarrez l'application.

### La traduction ne fonctionne pas

Vérifiez que la clé API Groq est correctement configurée:

```bash
cat /volume1/web/recette/.env
```

Testez le endpoint de vérification:

```bash
curl http://localhost:8000/api/translation/status
```

## Performances

Le DS213+ étant un modèle avec des ressources limitées:

- **2 workers** configurés par défaut (peut être réduit à 1 si nécessaire)
- **Base SQLite** (légère, adaptée pour usage personnel/familial)
- Pour améliorer les performances, évitez d'autres applications gourmandes en ressources

## 🔒 Sécurité et Authentification

### Protection par Mot de Passe

L'application est maintenant protégée par mot de passe en production :

- **Page de connexion** : `/login`
- **Mot de passe par défaut** : `RecipeTakachan2026` (à partager avec vos amis)
- **Session** : 24 heures
- **Déconnexion** : `/logout?lang=fr`

### Configuration de Sécurité

- ✅ Le fichier `.env` contient des informations sensibles (clé API, mot de passe)
- ✅ Permissions 644 appliquées sur `.env`
- ✅ Sessions sécurisées avec cookies HTTPOnly
- ✅ Protection activée uniquement en production (désactivée en dev)
- ✅ Les logs ne contiennent pas d'informations sensibles

### Accès HTTPS (Fortement Recommandé)

Pour sécuriser les connexions, utilisez HTTPS via le reverse proxy Synology:

1. **Control Panel → Application Portal → Reverse Proxy**
2. Créez une nouvelle règle:
   - **Source**: HTTPS, port 443
   - **Destination**: HTTP, localhost:8000
3. Activez un certificat SSL (Let's Encrypt recommandé)

Votre app sera accessible via : `https://recette.votre-nas.com`

### Documentation Complète

Pour plus de détails sur l'authentification, consultez [AUTH_SETUP.md](AUTH_SETUP.md)

## Support

Pour toute question ou problème, consultez les logs et vérifiez:

1. Les permissions des fichiers
2. La configuration du .env
3. La disponibilité de l'API Groq
4. L'espace disque disponible sur le NAS

---

**Version**: 1.0
**Date**: 2025-11-09
**Compatible**: Synology DS213+ (ARM)
