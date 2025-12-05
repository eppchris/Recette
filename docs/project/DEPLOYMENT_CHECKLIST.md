# Checklist de Déploiement - Nouvelle Version

Utilisez cette checklist pour chaque nouvelle version déployée.

## ✅ Avant le développement

- [ ] Identifier le numéro de version: V{X}_{Y}
- [ ] Vérifier la version précédente pour éviter les conflits
- [ ] Lire les règles du projet: `.claude/project-rules.md`

## ✅ Pendant le développement

- [ ] Développer les fonctionnalités
- [ ] Tester en mode bilingue (FR et JP)
- [ ] Tester en mode clair et sombre
- [ ] Créer/modifier les migrations SQL si nécessaire
- [ ] Mettre à jour la page d'aide si nouvelles fonctionnalités
- [ ] Commits réguliers avec le bon format

## ✅ Préparation du déploiement

### 1. Script de déploiement
- [ ] Créer `deploy/deploy_synology_V{X}_{Y}.sh`
- [ ] Copier le template depuis la version précédente
- [ ] Mettre à jour le numéro de version partout dans le script
- [ ] Lister toutes les nouvelles fonctionnalités
- [ ] Vérifier la liste REQUIRED_FILES (ajouter nouveaux fichiers critiques)
- [ ] Mettre à jour la section de migration BDD si nécessaire
- [ ] Lister tous les commits inclus dans cette version
- [ ] Rendre le script exécutable: `chmod +x deploy/deploy_synology_V{X}_{Y}.sh`

### 2. Mise à jour .gitignore
- [ ] Ajouter l'exception pour le nouveau script:
  ```
  !deploy/deploy_synology_V{X}_{Y}.sh
  ```

### 3. Documentation
- [ ] Créer `deploy/NOTES_DEPLOIEMENT_V{X}_{Y}.md`
- [ ] Documenter les nouvelles fonctionnalités
- [ ] Lister tous les fichiers modifiés/créés
- [ ] Écrire la procédure de déploiement manuel
- [ ] Documenter la migration de base de données
- [ ] Créer la liste des tests post-déploiement
- [ ] Documenter la procédure de rollback

### 4. Vérification git
- [ ] `git status` - Vérifier tous les fichiers modifiés
- [ ] Vérifier qu'aucun fichier sensible n'est staged (.env, *.sqlite3, etc.)
- [ ] Vérifier que le script de déploiement n'est PAS ignoré

## ✅ Commit et Push

### 1. Commit des fonctionnalités
```bash
git add {fichiers des fonctionnalités}
git commit -m "Titre des fonctionnalités

Description:
- Feature 1
- Feature 2

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 2. Commit de la documentation
```bash
git add deploy/NOTES_DEPLOIEMENT_V{X}_{Y}.md
git commit -m "Documentation déploiement V{X}.{Y}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 3. Commit du script de déploiement
```bash
git add .gitignore deploy/deploy_synology_V{X}_{Y}.sh
git commit -m "Ajout script de déploiement V{X}.{Y}

- Script deploy_synology_V{X}_{Y}.sh avec toutes les fonctionnalités
- Ajout exception dans .gitignore

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 4. Push
- [ ] `git push origin main`
- [ ] Vérifier sur GitHub que tous les commits sont présents
- [ ] Vérifier que le script de déploiement est bien versionné

## ✅ Déploiement sur Synology

### Préparation
- [ ] Vérifier que le serveur SSH est accessible: `ssh admin@192.168.1.14`
- [ ] Vérifier l'espace disque disponible sur le NAS
- [ ] Planifier une fenêtre de maintenance (app sera down quelques minutes)

### Exécution
- [ ] Exécuter le script: `./deploy/deploy_synology_V{X}_{Y}.sh`
- [ ] Entrer le mot de passe SSH quand demandé
- [ ] Surveiller les étapes du déploiement
- [ ] Vérifier qu'il n'y a pas d'erreurs
- [ ] Attendre la confirmation "Application démarrée avec succès"

### En cas d'erreur SSH
Si le transfert SSH échoue:
1. [ ] Vérifier que l'archive est créée: `ls -lh /tmp/recette_v{X}_{Y}_deploy.tar.gz`
2. [ ] Transférer manuellement avec `scp`:
   ```bash
   scp /tmp/recette_v{X}_{Y}_deploy.tar.gz admin@192.168.1.14:recette/
   ```
3. [ ] Suivre les instructions dans `deploy/NOTES_DEPLOIEMENT_V{X}_{Y}.md`

## ✅ Tests post-déploiement

### Tests fonctionnels
Exécuter TOUS les tests listés dans le script de déploiement (section "Tests à effectuer").

Exemple pour V1.6:
- [ ] Page recettes : Tester la recherche par ingrédients
- [ ] Créer un événement multi-jours (ex: 5 jours)
- [ ] Désélectionner des jours (ex: week-end)
- [ ] Ajouter des recettes à l'événement
- [ ] Aller dans 'Organisation' pour voir la planification
- [ ] Aller dans 'Planification' pour drag & drop
- [ ] Vérifier que la liste de courses se génère automatiquement
- [ ] Cliquer sur 'Aide' (❓) dans la sidebar

### Tests de régression
- [ ] Login / Logout fonctionne
- [ ] Liste des recettes s'affiche correctement
- [ ] Création d'une recette fonctionne
- [ ] Liste des événements s'affiche
- [ ] Création d'un événement simple (1 jour) fonctionne toujours
- [ ] Budget et catalogue des prix fonctionnent
- [ ] Mode sombre fonctionne
- [ ] Changement de langue FR ↔ JP fonctionne
- [ ] Gestion des utilisateurs (admin) fonctionne

### Vérification base de données
```bash
ssh admin@192.168.1.14
cd recette
sqlite3 data/recette.sqlite3

# Vérifier les nouvelles tables/colonnes selon la migration
# Exemple pour V1.6:
PRAGMA table_info(event);  -- Vérifier date_debut, date_fin, nombre_jours
SELECT name FROM sqlite_master WHERE type='table' AND name IN ('event_date', 'event_recipe_planning');
```

### Vérification des backups
- [ ] Vérifier qu'un backup a été créé: `ls -la ~/recette/backups/`
- [ ] Vérifier la date du backup (doit être récent)
- [ ] Vérifier la taille du backup (cohérente avec la base actuelle)

## ✅ Monitoring post-déploiement

### Première heure
- [ ] Vérifier les logs: `tail -f ~/recette/logs/*.log`
- [ ] Surveiller l'utilisation CPU/mémoire
- [ ] Tester plusieurs fonctionnalités
- [ ] Vérifier qu'il n'y a pas d'erreurs JavaScript (console navigateur)

### Premier jour
- [ ] Vérifier que l'application est toujours en ligne
- [ ] Demander des retours utilisateurs
- [ ] Surveiller les logs pour des erreurs inhabituelles

## ✅ Documentation finale

- [ ] Mettre à jour le README principal si nécessaire
- [ ] Documenter les problèmes rencontrés et leurs solutions
- [ ] Archiver les notes de déploiement
- [ ] Créer un tag Git si version majeure:
  ```bash
  git tag -a v{X}.{Y} -m "Version {X}.{Y} - Description"
  git push origin v{X}.{Y}
  ```

## 🚨 Rollback (en cas de problème critique)

Si un problème majeur survient:

1. [ ] Se connecter au Synology: `ssh admin@192.168.1.14`
2. [ ] Arrêter l'application: `cd recette && bash stop_recette.sh`
3. [ ] Restaurer la base de données:
   ```bash
   cp backups/recette_pre_v{X}_{Y}_*.sqlite3 data/recette.sqlite3
   ```
4. [ ] Restaurer le code:
   ```bash
   rm -rf app
   cp -r backups/code_backup_*/app ./
   ```
5. [ ] Redémarrer: `bash start_recette.sh`
6. [ ] Vérifier que l'ancienne version fonctionne
7. [ ] Investiguer le problème dans un environnement de dev

## 📊 Métriques de déploiement

| Métrique | Cible | Réel |
|----------|-------|------|
| Temps de déploiement | < 5 min | ___ min |
| Downtime | < 2 min | ___ min |
| Erreurs rencontrées | 0 | ___ |
| Tests réussis | 100% | ___% |

## 📝 Notes spécifiques à cette version

Version: V________

Date: ___________

Déployé par: ___________

Notes:
-
-
-

Problèmes rencontrés:
-
-

Solutions appliquées:
-
-

---

**Template créé pour**: Projet Recette
**Dernière mise à jour**: Décembre 2025
