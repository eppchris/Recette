# app/models/db_core.py
"""
Module de base pour la gestion de la base de données
Contient les utilitaires, la connexion et l'initialisation
"""
import os
import sqlite3
import contextlib
import unicodedata


# ============================================================================
# NORMALISATION DES NOMS D'INGRÉDIENTS
# ============================================================================

def normalize_ingredient_name(name: str) -> str:
    """
    Normalise un nom d'ingrédient français :
    - Minuscules
    - Sans accents (é→e, è→e, à→a, ô→o, œ→oe, etc.)
    - Au singulier (suppression du 's' final si présent)

    Exemples:
        "Œufs" → "oeuf"
        "Saké" → "sake"
        "Tomates" → "tomate"
        "Ail" → "ail"
    """
    if not name:
        return ""

    # 1. Mettre en minuscules
    name = name.lower().strip()

    # 2. Remplacer œ par oe (avant la normalisation NFD)
    name = name.replace('œ', 'oe')

    # 3. Supprimer les accents via décomposition Unicode
    # NFD = Canonical Decomposition (é → e + ´)
    name = unicodedata.normalize('NFD', name)
    # Garder seulement les caractères non-diacritiques
    name = ''.join(char for char in name if unicodedata.category(char) != 'Mn')

    # 4. Mettre au singulier (enlever le 's' final s'il y en a un)
    # Mais pas si le mot se termine par 'ss' ou si c'est un mot court
    if len(name) > 3 and name.endswith('s') and not name.endswith('ss'):
        name = name[:-1]

    return name


# ============================================================================
# CONFIGURATION DE LA BASE DE DONNÉES
# ============================================================================

# Déterminer le chemin de la base de données selon l'environnement
env = os.getenv("ENV", "dev")
db_name = "recette.sqlite3"  # Nom unifié pour dev et prod
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", db_name))


def _init_db():
    """Initialise la base de données avec le mode WAL"""
    try:
        con = sqlite3.connect(DB_PATH, timeout=30.0)
        con.execute("PRAGMA journal_mode=WAL").fetchone()
        con.close()
    except sqlite3.OperationalError:
        # Si la base est verrouillée, on continue quand même
        # (peut-être ouverte dans DB Browser ou autre)
        pass


# Appeler l'initialisation au chargement du module
_init_db()


@contextlib.contextmanager
def get_db():
    """Context manager pour obtenir une connexion à la base de données"""
    con = None
    try:
        con = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
        con.row_factory = sqlite3.Row

        # Configurer le busy_timeout pour cette connexion
        con.execute("PRAGMA busy_timeout=30000")  # 30 secondes en millisecondes

        # Optimisations pour réduire les disk I/O errors
        # Entourer les PRAGMA d'un try/except pour éviter les erreurs I/O fatales
        try:
            con.execute("PRAGMA synchronous=NORMAL")
            con.execute("PRAGMA temp_store=MEMORY")
            con.execute("PRAGMA cache_size=-64000")  # 64MB cache
        except sqlite3.OperationalError as pragma_error:
            # Si les PRAGMA échouent, on continue quand même
            print(f"Warning: PRAGMA configuration failed: {pragma_error}")

        yield con
        con.commit()
    except sqlite3.OperationalError as e:
        if con:
            try:
                con.rollback()
            except:
                pass
        # Log l'erreur mais avec plus de contexte
        print(f"Database error: {e}")
        raise
    except Exception as e:
        if con:
            con.rollback()
        raise
    finally:
        if con:
            try:
                con.close()
            except:
                pass
