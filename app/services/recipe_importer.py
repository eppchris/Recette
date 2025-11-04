# app/services/recipe_importer.py
import csv
import sqlite3
import os
import re

from app.models.db import DB_PATH


def import_recipe_from_csv(file_path: str):
    """
    Importe un fichier CSV au format :
    - Ligne 1 : Titre de la recette
    - Ligne 2 : Langue de la recette (fr, jp)
    - Ligne 3 : Index (slug/identifiant unique)
    - Ligne 4 : Pays d'origine
    - Ligne 5 : Nombre de convives
    - Ligne 6 : Population cible (PRO, MASTER, etc.)
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
    
    # Normalisation : ja → jp
    if recipe_lang in ['ja', 'jp', 'jpn']:
        recipe_lang = 'jp'
    elif recipe_lang in ['fr', 'fra']:
        recipe_lang = 'fr'
    else:
        raise ValueError(f"Langue non supportée : {recipe_lang}. Utilisez 'fr' ou 'jp'")
    
    recipe_index = lines[2]
    recipe_country = lines[3]
    recipe_servings = int(lines[4]) if lines[4].isdigit() else 4
    recipe_population = lines[5]
    
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
        if len(parts) >= 3:
            ingredients.append({
                'name': parts[0].strip(),
                'qty': parts[1].strip() if len(parts) > 1 else '',
                'unit': parts[2].strip() if len(parts) > 2 else '',
                'comment': parts[3].strip() if len(parts) > 3 else ''
            })
    
    # Parser les étapes
    steps = []
    for line in lines[procedure_start:]:
        # Nettoyer les numéros au début (①, ②, 1., 2., etc.)
        clean_line = re.sub(r'^[①-⑳\d]+[\.\)）]?\s*', '', line)
        if clean_line:
            steps.append(clean_line)
    
    # Connexion à la base SQLite
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    try:
        # Vérifier si la recette existe déjà
        cur.execute("SELECT id FROM recipe WHERE slug=?", (recipe_index,))
        row = cur.fetchone()
        
        if row:
            recipe_id = row[0]
            # Supprimer les anciennes données pour cette langue
            cur.execute("DELETE FROM ingredient_i18n WHERE ingredient_id IN (SELECT id FROM ingredients WHERE recipe_id=?) AND lang=?", (recipe_id, recipe_lang))
            cur.execute("DELETE FROM step_i18n WHERE step_id IN (SELECT id FROM steps WHERE recipe_id=?) AND lang=?", (recipe_id, recipe_lang))
            cur.execute("DELETE FROM recipe_i18n WHERE recipe_id=? AND lang=?", (recipe_id, recipe_lang))
        else:
            # Créer la recette
            cur.execute("""
                INSERT INTO recipe (slug, recipe_name, recipe_type, country, servings_default)
                VALUES (?, ?, ?, ?, ?)
            """, (recipe_index, recipe_title, recipe_population, recipe_country, recipe_servings))
            recipe_id = cur.lastrowid
        
        # Insérer la traduction de la recette
        cur.execute("""
            INSERT OR REPLACE INTO recipe_i18n (recipe_id, lang, name, category, tags, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (recipe_id, recipe_lang, recipe_title, recipe_population, '', ''))
        
        # Insérer les ingrédients
        for position, ing in enumerate(ingredients, start=1):
            # Convertir la quantité en float si possible
            try:
                qty_float = float(ing['qty']) if ing['qty'] else None
            except ValueError:
                qty_float = None
            
            cur.execute("""
                INSERT INTO ingredients (recipe_id, position, qty, unit_code)
                VALUES (?, ?, ?, ?)
            """, (recipe_id, position, qty_float, ing['unit']))
            ing_id = cur.lastrowid
            
            cur.execute("""
                INSERT INTO ingredient_i18n (ingredient_id, lang, name)
                VALUES (?, ?, ?)
            """, (ing_id, recipe_lang, ing['name']))
        
        # Insérer les étapes
        for position, step_text in enumerate(steps, start=1):
            cur.execute("""
                INSERT INTO steps (recipe_id, position)
                VALUES (?, ?)
            """, (recipe_id, position))
            step_id = cur.lastrowid
            
            cur.execute("""
                INSERT INTO step_i18n (step_id, lang, text)
                VALUES (?, ?, ?)
            """, (step_id, recipe_lang, step_text))
        
        con.commit()
        print(f"✅ Import réussi : {recipe_title} ({recipe_lang}) - {len(ingredients)} ingrédients, {len(steps)} étapes")
        
    except Exception as e:
        con.rollback()
        raise e
    finally:
        con.close()