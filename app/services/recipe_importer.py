import csv, re, sqlite3, os
from app.models.db import DB_PATH

def import_recipe_from_csv(file_path: str):
    """
    Importe un fichier CSV complet :
    - Nom du fichier : <index>_<lang>_<nom>.csv
    - Contient : entête recette, ingrédients, étapes
    """

    # 1. Extraire les métadonnées du nom de fichier
    filename = os.path.basename(file_path)
    match = re.match(r"(\d+)_(\w{2})_(.+)\.csv", filename)
    if not match:
        raise ValueError("Nom de fichier invalide (attendu: <index>_<lang>_<nom>.csv)")
    index, lang, recipe_name = match.groups()
    lang = lang.lower()

    # 2. Lire le CSV
    with open(file_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        rows = [r for r in reader if any(r)]

    section = None
    meta = {}
    ingredients = []
    steps = []

    for row in rows:
        if not row:
            continue
        head = row[0].strip().lower()
        if head == "ingredients":
            section = "ingredients"
            continue
        elif head == "procedure" or head == "procédure":
            section = "steps"
            continue

        if section is None:
            # Lecture entête
            if len(row) >= 2:
                meta[row[0].strip()] = row[1].strip()
        elif section == "ingredients":
            if len(row) >= 3:
                ingredients.append({
                    "name": row[0].strip(),
                    "qty": row[1].strip(),
                    "unit": row[2].strip(),
                    "comment": row[3].strip() if len(row) > 3 else ""
                })
        elif section == "steps":
            steps.append(row[0].strip())

    # 3. Connexion à la base SQLite
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # Création ou récupération recette
    cur.execute("SELECT id FROM recipe WHERE slug=?", (index,))
    row = cur.fetchone()
    if row:
        recipe_id = row[0]
    else:
        cur.execute("""
            INSERT INTO recipe (slug, recipe_name, recipe_type, country, servings_default)
            VALUES (?, ?, ?, ?, ?)
        """, (
            index,
            meta.get("Nom de la recette", recipe_name),
            meta.get("Type", "Plat"),
            meta.get("Pays", "Japon"),
            int(meta.get("Nombre de convive", 2))
        ))
        recipe_id = cur.lastrowid

    # 4. Traduction recette
    cur.execute("""
        INSERT OR REPLACE INTO recipe_i18n (recipe_id, lang, name, category)
        VALUES (?, ?, ?, ?)
    """, (
        recipe_id,
        lang,
        meta.get("Nom de la recette", recipe_name),
        meta.get("Type", "Plat")
    ))

    # 5. Ingrédients
    for i, ing in enumerate(ingredients, start=1):
        cur.execute("""
            INSERT INTO ingredients (recipe_id, position, qty, unit_code)
            VALUES (?, ?, ?, ?)
        """, (recipe_id, i, ing["qty"], ing["unit"]))
        ing_id = cur.lastrowid
        cur.execute("""
            INSERT INTO ingredient_i18n (ingredient_id, lang, name)
            VALUES (?, ?, ?)
        """, (ing_id, lang, ing["name"]))

    # 6. Étapes
    for i, step in enumerate(steps, start=1):
        cur.execute("""
            INSERT INTO steps (recipe_id, position)
            VALUES (?, ?)
        """, (recipe_id, i))
        step_id = cur.lastrowid
        cur.execute("""
            INSERT INTO step_i18n (step_id, lang, text)
            VALUES (?, ?, ?)
        """, (step_id, lang, step))

    con.commit()
    con.close()

    print(f"✅ Import réussi : {recipe_name} ({lang})")
