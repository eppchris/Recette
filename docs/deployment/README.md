# Scripts de Déploiement

Ce répertoire contient les différentes versions des scripts de déploiement pour l'application Recette FR/JP.

## Versions Disponibles

### v1 - Version initiale (2025-11-13)
- **Fichier**: `deploy_synology_v1.sh`
- **Description**: Script de déploiement pour Synology DS213+
- **Fonctionnalités**:
  - Création de la structure de répertoires sur le NAS
  - Transfert via SSH (sans SCP/SFTP)
  - Copie de la base de données dev vers prod
  - Configuration des permissions
  - Instructions post-déploiement
- **Usage**: `./deploy_synology_v1.sh <user@synology-ip> [destination-path]`
- **Exemple**: `./deploy_synology_v1.sh admin@192.168.1.14 recette`

## Notes de Déploiement

### Configuration Requise sur le Synology
1. Python 3 installé via DSM Package Center
2. Accès SSH activé
3. Port 8000 disponible (ou modifier dans le script)

### Variables d'Environnement à Configurer
Après déploiement, créer le fichier `.env` sur le NAS :
```bash
ENV=prod
GROQ_API_KEY=votre_clé_api_groq
REQUIRE_PASSWORD=True
SHARED_PASSWORD=RecipeTakachan2026
SECRET_KEY=<générer avec: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'>
PORT=8000
LOG_LEVEL=info
```

### Fichiers Exclus du Déploiement
- `.git/` et `.gitignore`
- `__pycache__/` et `*.pyc`
- `.env` (à créer manuellement sur le NAS)
- `venv/` (à créer sur le NAS)
- `data/recette_dev.sqlite3` (copié vers `recette_prod.sqlite3`)
- Archives `*.tar.gz`

### Processus Post-Déploiement
1. Se connecter en SSH au NAS
2. Créer l'environnement virtuel Python
3. Installer les dépendances depuis `requirements.txt`
4. Créer le fichier `.env` avec les bonnes variables
5. Lancer l'application avec `./start_recette.sh`
6. Accéder via `http://<ip-synology>:8000/recipes`

### Sécurité
- Protection par mot de passe activée en production (`REQUIRE_PASSWORD=True`)
- Sessions sécurisées avec clé secrète unique
- HTTPS configuré via reverse proxy Synology
- Logs rotatifs dans `/logs` (max 10MB par fichier, 5 backups)
