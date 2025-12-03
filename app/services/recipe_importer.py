# app/services/recipe_importer.py
import sqlite3
import re
import unicodedata

from app.models.db_core import DB_PATH


def slugify(text: str) -> str:
    """
    Convertit un texte en slug URL-friendly

    Exemples:
        "Saumon mariné" -> "saumon-marine"
        "なす の辛味噌炒え" -> "nasu-no-xinwei-chao"
        "Blinis" -> "blinis"
    """
    # Normaliser les caractères unicode
    text = unicodedata.normalize('NFKD', text)
    # Convertir en minuscules
    text = text.lower()
    # Remplacer les espaces et caractères spéciaux par des tirets
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    # Supprimer les tirets en début et fin
    text = text.strip('-')

    # Si le slug est vide (par exemple pour des caractères japonais uniquement)
    # ou trop court, garder le texte original
    if not text or len(text) < 2:
        text = re.sub(r'[^\w]+', '-', unicodedata.normalize('NFKD', text.lower()))
        text = text.strip('-')

    return text[:50]  # Limiter à 50 caractères


def import_recipe_from_csv(file_path: str):
    """
    Importe un fichier CSV au format :
    - Ligne 1 : Titre de la recette
    - Ligne 2 : Langue de la recette (fr, jp)
    - Ligne 3 : Index (slug/identifiant unique)
    - Ligne 4 : Pays d'origine
    - Ligne 5 : Nombre de convives
    - Ligne 6 : Type de recette (PRO, MASTER, etc.)
    - Ligne 7 : "ingredients"
    - Lignes suivantes : Nom;Quantité;Unité;Commentaire
    - Ligne X : "Procedure" ou "Procédure"
    - Lignes suivantes : Étapes numérotées
    """
    
    # Lire tout le fichier
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    if len(lines) < 7:
        raise ValueError("Fichier CSV incomplet (moins de 7 lignes)")
    
    # Parser l'en-tête
    recipe_title = lines[0]
    recipe_lang = lines[1].lower().strip()
    
    # Normalisation de la langue
    if recipe_lang in ['ja', 'jp', 'jpn']:
        recipe_lang = 'jp'
    elif recipe_lang in ['fr', 'fra']:
        recipe_lang = 'fr'
    else:
        raise ValueError(f"Langue non supportée : {recipe_lang}. Utilisez 'fr' ou 'jp'")
    
    recipe_slug = lines[2]
    recipe_country = lines[3]
    recipe_servings = int(lines[4]) if lines[4].isdigit() else 4
    recipe_type = lines[5]
    
    # Trouver la section ingredients
    ingredients_start = None
    procedure_start = None
    
    for i, line in enumerate(lines):
        if line.lower() == 'ingredients':
            ingredients_start = i + 1
        elif line.lower() in ['procedure', 'procédure']:
            procedure_start = i + 1
            break
    
    if ingredients_start is None or procedure_start is None:
        raise ValueError("Sections 'ingredients' ou 'Procedure' introuvables")
    
    # Parser les ingrédients
    ingredients = []
    for line in lines[ingredients_start:procedure_start-1]:
        parts = line.split(';')
        if len(parts) >= 1 and parts[0].strip():
            ingredients.append({
                'name': parts[0].strip(),
                'quantity': parts[1].strip() if len(parts) > 1 else '',
                'unit': parts[2].strip() if len(parts) > 2 else '',
                'notes': parts[3].strip() if len(parts) > 3 else ''
            })
    
    # Parser les étapes
    steps = []
    for line in lines[procedure_start:]:
        clean_line = re.sub(r'^[①-⑳\d]+[\.\)）]?\s*', '', line)
        if clean_line:
            steps.append(clean_line)
    
    # Connexion à la base SQLite
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    try:
        # Vérifier si la recette existe déjà
        cur.execute("SELECT id FROM recipe WHERE slug = ?", (recipe_slug,))
        row = cur.fetchone()
        
        if row:
            recipe_id = row[0]
            print(f"📝 Ajout/Mise à jour de la langue {recipe_lang} pour : {recipe_title}")
            
            # Vérifier si cette langue existe déjà
            cur.execute("SELECT COUNT(*) FROM recipe_translation WHERE recipe_id = ? AND lang = ?", (recipe_id, recipe_lang))
            lang_exists = cur.fetchone()[0] > 0
            
            if lang_exists:
                print(f"   ⚠️  Langue {recipe_lang} existe déjà, mise à jour...")
                cur.execute("DELETE FROM recipe_ingredient_translation WHERE recipe_ingredient_id IN (SELECT id FROM recipe_ingredient WHERE recipe_id = ?) AND lang = ?", (recipe_id, recipe_lang))
                cur.execute("DELETE FROM step_translation WHERE step_id IN (SELECT id FROM step WHERE recipe_id = ?) AND lang = ?", (recipe_id, recipe_lang))
                cur.execute("DELETE FROM recipe_translation WHERE recipe_id = ? AND lang = ?", (recipe_id, recipe_lang))
            else:
                print(f"   ✨ Nouvelle langue {recipe_lang} ajoutée")
            
            cur.execute("UPDATE recipe SET country = ?, servings_default = ? WHERE id = ?", (recipe_country, recipe_servings, recipe_id))
            
        else:
            print(f"✨ Création d'une nouvelle recette : {recipe_title} ({recipe_lang})")
            cur.execute("INSERT INTO recipe (slug, country, servings_default) VALUES (?, ?, ?)", (recipe_slug, recipe_country, recipe_servings))
            recipe_id = cur.lastrowid
        
        # Insérer la traduction de la recette
        cur.execute("INSERT INTO recipe_translation (recipe_id, lang, name, recipe_type) VALUES (?, ?, ?, ?)", (recipe_id, recipe_lang, recipe_title, recipe_type))
        
        # Récupérer les recipe_ingredient existants
        cur.execute("SELECT id FROM recipe_ingredient WHERE recipe_id = ? ORDER BY position", (recipe_id,))
        existing_recipe_ingredients = [row[0] for row in cur.fetchall()]
        
        # Insérer les ingrédients
        for position, ing in enumerate(ingredients, start=1):
            quantity_float = None
            if ing['quantity']:
                try:
                    quantity_float = float(ing['quantity'])
                except ValueError:
                    pass
            
            if position <= len(existing_recipe_ingredients):
                recipe_ingredient_id = existing_recipe_ingredients[position - 1]
                cur.execute("UPDATE recipe_ingredient SET quantity = ? WHERE id = ?", (quantity_float, recipe_ingredient_id))
            else:
                cur.execute("INSERT INTO recipe_ingredient (recipe_id, position, quantity) VALUES (?, ?, ?)", (recipe_id, position, quantity_float))
                recipe_ingredient_id = cur.lastrowid
            
            cur.execute("INSERT INTO recipe_ingredient_translation (recipe_ingredient_id, lang, name, unit, notes) VALUES (?, ?, ?, ?, ?)",
                       (recipe_ingredient_id, recipe_lang, ing['name'], ing['unit'] if ing['unit'] else None, ing['notes'] if ing['notes'] else None))
        
        # Récupérer les steps existants
        cur.execute("SELECT id FROM step WHERE recipe_id = ? ORDER BY position", (recipe_id,))
        existing_steps = [row[0] for row in cur.fetchall()]
        
        # Insérer les étapes
        for position, step_text in enumerate(steps, start=1):
            if position <= len(existing_steps):
                step_id = existing_steps[position - 1]
            else:
                cur.execute("INSERT INTO step (recipe_id, position) VALUES (?, ?)", (recipe_id, position))
                step_id = cur.lastrowid
            
            cur.execute("INSERT INTO step_translation (step_id, lang, text) VALUES (?, ?, ?)", (step_id, recipe_lang, step_text))
        
        con.commit()
        print(f"✅ Import réussi : {recipe_title} ({recipe_lang}) - {len(ingredients)} ingrédients, {len(steps)} étapes")
        
    except Exception as e:
        con.rollback()
        print(f"❌ Erreur lors de l'import : {str(e)}")
        raise e
    finally:
        con.close()