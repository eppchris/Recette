# run.py — point d'entrée Flask avec sélecteur FR/JA

import os, sqlite3, contextlib
from flask import Flask, render_template, request, session, redirect, url_for

# --- Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

# --- Config DB
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "recette_dev.sqlite3")

@contextlib.contextmanager
def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()

# --- Sélecteur de langue (FR/JA) + libellés (réponse à tes points 2 & 3)
STRINGS = {
    "fr": {
        "recipes": "Recettes", "all": "Toutes les recettes",
        "type": "Type", "servings": "Portions", "tags": "Tags",
        "ingredients": "Ingrédients", "steps": "Étapes", "source": "Source",
        "lang_fr": "Français", "lang_ja": "日本語",
    },
    "ja": {
        "recipes": "レシピ", "all": "すべてのレシピ",
        "type": "種類", "servings": "人数", "tags": "タグ",
        "ingredients": "材料", "steps": "手順", "source": "出典",
        "lang_fr": "Français", "lang_ja": "日本語",
    },
}
def S(key: str) -> str:
    lang = session.get("lang", "fr")
    return STRINGS.get(lang, STRINGS["fr"]).get(key, key)

@app.before_request
def choose_lang():
    lang = request.args.get("lang")
    if lang in ("fr", "ja"):
        session["lang"] = lang
    if "lang" not in session:
        session["lang"] = "fr"

# --- Requêtes SQLite (adaptées à TES tables : recipe, recipe_i18n, ingredients, ingredient_i18n, steps, step_i18n)
def list_recipes(lang: str):
    with get_db() as con:
        return con.execute("""
          SELECT
            r.id,
            r.slug,
            r.recipe_type           AS type,
            r.servings_default      AS servings,
            COALESCE(ri.name, r.recipe_name) AS name,   -- fallback si pas de i18n
            ri.category,
            ri.tags
          FROM recipe r
          LEFT JOIN recipe_i18n ri
            ON ri.recipe_id = r.id AND ri.lang = ?
          ORDER BY name COLLATE NOCASE;
        """, (lang,)).fetchall()

def get_recipe_by_slug(slug: str, lang: str):
    with get_db() as con:
        rec = con.execute("""
          SELECT
            r.id,
            r.slug,
            r.recipe_type           AS type,
            r.servings_default      AS servings,
            COALESCE(ri.name, r.recipe_name) AS name,
            ri.category,
            ri.tags,
            ri.source
          FROM recipe r
          LEFT JOIN recipe_i18n ri
            ON ri.recipe_id = r.id AND ri.lang = ?
          WHERE r.slug = ?
        """, (lang, slug)).fetchone()
        if not rec:
            return None

        ings = con.execute("""
          SELECT
            ing.id,
            ing.position,
            ing.qty,
            ing.unit_code,
            COALESCE(ii.name, '') AS name
          FROM ingredients ing
          LEFT JOIN ingredient_i18n ii
            ON ii.ingredient_id = ing.id AND ii.lang = ?
          WHERE ing.recipe_id = ?
          ORDER BY ing.position
        """, (lang, rec["id"])).fetchall()

        steps = con.execute("""
          SELECT
            s.position,
            COALESCE(si.text, '') AS text
          FROM steps s
          LEFT JOIN step_i18n si
            ON si.step_id = s.id AND si.lang = ?
          WHERE s.recipe_id = ?
          ORDER BY s.position
        """, (lang, rec["id"])).fetchall()

        return rec, ings, steps

# --- Routes
@app.route("/")
def home():
    return redirect(url_for("recipes"))

@app.route("/recipes")
def recipes():
    rows = list_recipes(session["lang"])
    return render_template("recipes_list.html", rows=rows, S=S, lang=session["lang"])

@app.route("/recipes/<slug>")
def recipe_detail(slug):
    data = get_recipe_by_slug(slug, session["lang"])
    if not data:
        return redirect(url_for("recipes"))
    rec, ings, steps = data
    return render_template("recipe_detail.html", rec=rec, ings=ings, steps=steps, S=S, lang=session["lang"])

# --- Lancement (flask --app run run / python run.py)
if __name__ == "__main__":
    app.run(debug=True)
