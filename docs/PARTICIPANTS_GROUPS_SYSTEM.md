# Système de Gestion des Participants et Groupes

**Version**: 1.6+
**Dernière mise à jour**: Décembre 2024

## 📋 Vue d'ensemble

Le système de participants et groupes permet de gérer les invités aux événements de manière flexible :
- Ajout individuel de participants
- Ajout de groupes entiers (tous les membres du groupe)
- Gestion multi-utilisateurs avec isolation des données
- Interface intuitive avec modal dual-list

## 🏗️ Architecture

### Base de données

#### Table `participants`
- `id` : Identifiant unique
- `nom` : Nom du participant (requis)
- `prenom` : Prénom (optionnel)
- `role` : Rôle/fonction (optionnel)
- `telephone` : Numéro de téléphone (optionnel)
- `email` : Email (optionnel)
- `adresse` : Adresse postale (optionnel)
- `user_id` : Propriétaire du participant (isolation multi-utilisateurs)
- `created_at` : Date de création
- `updated_at` : Date de dernière modification

#### Table `groups`
- `id` : Identifiant unique
- `nom` : Nom du groupe (requis)
- `description` : Description du groupe (optionnel)
- `user_id` : Propriétaire du groupe
- `created_at` : Date de création
- `updated_at` : Date de dernière modification

#### Table de liaison `group_participants`
- `group_id` : Référence au groupe
- `participant_id` : Référence au participant
- Relation many-to-many entre groupes et participants

#### Table de liaison `event_participants`
- `event_id` : Référence à l'événement
- `participant_id` : Référence au participant
- `added_via_group_id` : ID du groupe si ajouté via groupe (NULL sinon)
- Relation many-to-many entre événements et participants

## 🎨 Interface utilisateur

### Page détail d'événement

#### Bouton Participants
- Affiche le nombre de participants actuels
- Ouvre la modal de gestion au clic
- Position : À côté des boutons d'édition/organisation

#### Modal de gestion (dual-list)

**Colonne gauche - Ajout** :
1. **Ajouter un participant individuel**
   - Liste scrollable des participants disponibles
   - Affiche nom, prénom, rôle
   - Clic pour ajouter instantanément

2. **Ajouter tous les membres d'un groupe**
   - Liste scrollable des groupes disponibles
   - Affiche nom du groupe + nombre de membres
   - Clic pour ajouter tous les membres

**Colonne droite - Gestion** :
- Liste des participants inscrits à l'événement
- Indication si ajouté individuellement ou via groupe
- Clic pour retirer (avec confirmation visuelle)

### Comportements

#### Ajout individuel
- Mise à jour instantanée (pas de rechargement)
- Le participant disparaît de la liste "disponibles"
- Apparaît dans la liste "inscrits"

#### Ajout via groupe
- Rechargement de la page avec modal ouverte
- Tous les membres du groupe sont ajoutés
- Marqués comme "via groupe: [nom]"

#### Retrait
- **Participant individuel** : Retrait instantané
- **Participant via groupe** : Rechargement (pour recalcul cohérence)

## 🔌 API Endpoints

### Ajouter un participant
```
POST /api/events/{event_id}/participants/add
Body: participant_id=123
```

### Ajouter un groupe complet
```
POST /api/events/{event_id}/participants/add-group
Body: group_id=456
```

### Retirer un participant
```
POST /api/events/{event_id}/participants/{participant_id}/remove
```

## 💾 Fonctions de base de données

### `get_event_participants(event_id)`
Retourne la liste des participants d'un événement avec :
- Toutes les infos du participant
- `group_name` si ajouté via groupe (NULL sinon)

### `list_participants(user_id, is_admin)`
Liste les participants disponibles pour un utilisateur :
- Si admin : tous les participants
- Sinon : seulement ceux de l'utilisateur

### `list_groups(user_id, is_admin)`
Liste les groupes disponibles avec nombre de membres :
- Si admin : tous les groupes
- Sinon : seulement ceux de l'utilisateur

### `add_event_participant(event_id, participant_id, group_id=None)`
Ajoute un participant à un événement :
- `group_id` : NULL si ajout individuel, ID du groupe sinon

### `remove_event_participant(event_id, participant_id)`
Retire un participant d'un événement

### `add_group_to_event(event_id, group_id)`
Ajoute tous les membres d'un groupe à un événement

## 🔐 Sécurité et isolation

### Multi-utilisateurs
- Chaque participant/groupe a un `user_id` propriétaire
- Les utilisateurs ne voient que leurs propres données
- Exception : admin voit tout

### Permissions
- Seul le propriétaire peut modifier ses participants/groupes
- Admin peut tout modifier
- Vérification côté backend + frontend

## 🎯 Cas d'usage

### Exemple 1 : Dîner familial
1. Créer un groupe "Famille"
2. Ajouter les membres (Papa, Maman, Enfant1, Enfant2)
3. Lors de la création d'un événement "Dîner dimanche"
4. Cliquer "Participants" → Ajouter le groupe "Famille"
5. Tous les membres sont automatiquement ajoutés

### Exemple 2 : Événement mixte
1. Événement "Soirée jeux"
2. Ajouter le groupe "Amis proches" (5 personnes)
3. Ajouter individuellement "Jean" et "Marie" (invités ponctuels)
4. Total : 7 participants
5. Distinction claire dans l'interface

## 📝 Règles métier

### Doublons
- Un participant ne peut être ajouté qu'une fois par événement
- Même s'il est dans plusieurs groupes ajoutés

### Suppression
- Supprimer un groupe ne supprime PAS les participants de l'événement
- Les participants restent marqués comme ajoutés via ce groupe

### Modification de groupe
- Modifier les membres d'un groupe n'affecte PAS les événements passés
- Seuls les nouveaux ajouts utilisent la composition actuelle

## 🌍 Internationalisation

### Français
- "Participants"
- "Ajouter un participant"
- "Ajouter tous les membres d'un groupe"
- "Participants inscrits"
- "via groupe:"
- "Ajouté individuellement"

### Japonais
- "参加者"
- "参加者を追加"
- "グループの全メンバーを追加"
- "登録済み参加者"
- "グループ経由:"
- "個別に追加"

## 🎨 Mode sombre

Toutes les interfaces supportent le mode sombre :
- Cartes participants : `bg-gray-50 dark:bg-gray-700`
- Hover ajout : `hover:bg-blue-50 dark:hover:bg-blue-900/20`
- Hover retrait : `hover:bg-red-50 dark:hover:bg-red-900/20`

## 🔧 Technologies utilisées

- **Frontend** : Alpine.js pour la réactivité
- **CSS** : Tailwind avec classes dark mode
- **Backend** : FastAPI avec endpoints REST
- **DB** : SQLite avec relations many-to-many

## 📊 Exemple de code

### Template (Alpine.js)
```html
<div x-data="{
  eventParticipants: [],
  allParticipants: [],
  allGroups: [],
  async addParticipant(id) { ... },
  async addGroup(id) { ... },
  async removeParticipant(id) { ... }
}">
```

### Route FastAPI
```python
@router.get("/events/{event_id}/detail")
async def event_detail(event_id: int):
    event_participants = db.get_event_participants(event_id)
    all_participants = db.list_participants(user_id, is_admin)
    all_groups = db.list_groups(user_id, is_admin)
    return templates.TemplateResponse(...)
```

## 🐛 Débogage

### La liste des participants est vide
- Vérifier `user_id` dans la session
- Vérifier que les participants ont le bon `user_id`
- Vérifier les permissions (admin vs user)

### Le groupe ne s'ajoute pas
- Vérifier que le groupe a des membres
- Vérifier les contraintes de clés étrangères
- Regarder les logs d'erreur SQL

### Modal ne se rouvre pas après ajout de groupe
- Vérifier le paramètre `?modal=open` dans l'URL
- Vérifier `window.modalOpen` dans le script

---

**Fichiers concernés** :
- [app/routes/event_routes.py](../app/routes/event_routes.py)
- [app/templates/event_detail.html](../app/templates/event_detail.html)
- [app/models/db_participants.py](../app/models/db_participants.py)
- [app/models/db_groups.py](../app/models/db_groups.py)
