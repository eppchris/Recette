# Base de données Recette

## Base de données active

**Fichier principal:** `recette.sqlite3`

Cette base de données contient toutes les données de l'application :
- Recettes
- Ingrédients (catalogue bilingue FR/JP)
- Événements
- Budget
- Tickets de caisse
- Utilisateurs
- etc.

## Fichiers associés

- `recette.sqlite3-wal` : Write-Ahead Log (WAL) - fichier temporaire SQLite
- `recette.sqlite3-shm` : Shared Memory - fichier temporaire SQLite

⚠️ **NE PAS supprimer les fichiers -wal et -shm** : ils font partie du fonctionnement normal de SQLite en mode WAL.

## Configuration

La base de données est configurée dans :
- `config.py` : `DB_PATH = str(DATA_DIR / "recette.sqlite3")`
- `app/models/db_core.py` : utilise `data/recette.sqlite3`

## Backups

Les backups sont stockés dans `/backups/` à la racine du projet.

## Anciennes bases (supprimées)

- ❌ `recette.db` (racine) - supprimée le 2025-01-07
- ❌ `recipes.db` - supprimée le 2025-01-07
