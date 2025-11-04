# app/models/db.py
import os, sqlite3, contextlib

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "recette_dev.sqlite3"))

@contextlib.contextmanager
def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()

def _table_exists(con, name: str) -> bool:
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None

def list_recipes(lang: str):
    with get_db() as con:
        if _table_exists(con, "recipe_i18n"):
            sql = """
              SELECT r.id, r.slug, r.recipe_type AS type, r.servings_default AS servings,
                     COALESCE(ri.name, r.recipe_name) AS name, ri.category, ri.tags
              FROM recipe r
              LEFT JOIN recipe_i18n ri ON ri.recipe_id=r.id AND ri.lang=?
              ORDER BY name COLLATE NOCASE;"""
            return con.execute(sql, (lang,)).fetchall()
        else:
            sql = """
              SELECT r.id, r.slug, r.recipe_type AS type, r.servings_default AS servings,
                     r.recipe_name AS name, NULL AS category, NULL AS tags
              FROM recipe r
              ORDER BY name COLLATE NOCASE;"""
            return con.execute(sql).fetchall()

def get_recipe_by_slug(slug: str, lang: str):
    with get_db() as con:
        has_ri = _table_exists(con, "recipe_i18n")
        has_ing = _table_exists(con, "ingredients")
        has_ii  = _table_exists(con, "ingredient_i18n")
        has_s   = _table_exists(con, "steps")
        has_si  = _table_exists(con, "step_i18n")

        if has_ri:
            rec = con.execute("""
              SELECT r.id, r.slug, r.recipe_type AS type, r.servings_default AS servings,
                     COALESCE(ri.name, r.recipe_name) AS name, ri.category, ri.tags, ri.source
              FROM recipe r
              LEFT JOIN recipe_i18n ri ON ri.recipe_id=r.id AND ri.lang=?
              WHERE r.slug=?;""", (lang, slug)).fetchone()
        else:
            rec = con.execute("""
              SELECT r.id, r.slug, r.recipe_type AS type, r.servings_default AS servings,
                     r.recipe_name AS name, NULL AS category, NULL AS tags, NULL AS source
              FROM recipe r WHERE r.slug=?;""", (slug,)).fetchone()
        if not rec:
            return None

        if has_ing:
            if has_ii:
                ings = con.execute("""
                  SELECT ing.id, ing.position, ing.qty, ing.unit_code,
                         COALESCE(ii.name,'') AS name
                  FROM ingredients ing
                  LEFT JOIN ingredient_i18n ii ON ii.ingredient_id=ing.id AND ii.lang=?
                  WHERE ing.recipe_id=? ORDER BY ing.position;""", (lang, rec["id"])).fetchall()
            else:
                ings = con.execute("""
                  SELECT ing.id, ing.position, ing.qty, ing.unit_code, '' AS name
                  FROM ingredients ing
                  WHERE ing.recipe_id=? ORDER BY ing.position;""", (rec["id"],)).fetchall()
        else:
            ings = []

        if has_s:
            if has_si:
                steps = con.execute("""
                  SELECT s.position, COALESCE(si.text,'') AS text
                  FROM steps s
                  LEFT JOIN step_i18n si ON si.step_id=s.id AND si.lang=?
                  WHERE s.recipe_id=? ORDER BY s.position;""", (lang, rec["id"])).fetchall()
            else:
                steps = con.execute("""
                  SELECT s.position, '' AS text
                  FROM steps s WHERE s.recipe_id=? ORDER BY s.position;""", (rec["id"],)).fetchall()
        else:
            steps = []

        return rec, ings, steps
