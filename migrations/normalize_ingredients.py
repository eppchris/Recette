#!/usr/bin/env python3
"""
Script de normalisation des ingrédients

Ce script :
1. Normalise tous les noms d'ingrédients dans le catalogue (ingredient_price_catalog)
2. Fusionne les doublons dans le catalogue (garde la ligne avec le plus d'infos)
3. Normalise tous les noms d'ingrédients dans les recettes (recipe_ingredient_translation)

Usage:
    python3 migrations/normalize_ingredients.py
"""

import sys
import os

# Ajouter le répertoire parent au PYTHONPATH pour pouvoir importer app.models.db
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.db import get_db, normalize_ingredient_name


def normalize_catalog():
    """
    Nettoie le catalogue des prix :
    1. Normalise tous les noms d'ingrédients
    2. Fusionne les doublons en gardant la ligne la plus complète
    """
    print("\n" + "="*80)
    print("ÉTAPE 1 : NETTOYAGE DU CATALOGUE DES PRIX")
    print("="*80)

    with get_db() as conn:
        cursor = conn.cursor()

        # Récupérer tous les ingrédients du catalogue
        cursor.execute("""
            SELECT id, ingredient_name_fr, ingredient_name_jp, unit_fr, unit_jp,
                   price_eur, price_jpy, qty, conversion_category
            FROM ingredient_price_catalog
            ORDER BY id
        """)
        ingredients = cursor.fetchall()

        print(f"\n✓ {len(ingredients)} ingrédients trouvés dans le catalogue")

        # Grouper par nom normalisé
        normalized_groups = {}
        for ing in ingredients:
            normalized = normalize_ingredient_name(ing['ingredient_name_fr'])
            if normalized not in normalized_groups:
                normalized_groups[normalized] = []
            normalized_groups[normalized].append(dict(ing))

        # Identifier les doublons
        duplicates = {k: v for k, v in normalized_groups.items() if len(v) > 1}

        if duplicates:
            print(f"\n⚠️  {len(duplicates)} groupes de doublons trouvés :")
            for norm_name, group in duplicates.items():
                print(f"\n  • '{norm_name}' ({len(group)} variantes) :")
                for ing in group:
                    has_price = '✓' if (ing['price_eur'] or ing['price_jpy']) else '✗'
                    print(f"    - ID {ing['id']}: \"{ing['ingredient_name_fr']}\" [{has_price} prix]")

            # Pour chaque groupe de doublons, garder le meilleur
            print("\n📊 Fusion des doublons...")
            ids_to_delete = []

            for norm_name, group in duplicates.items():
                # Trier par priorité : d'abord ceux avec prix, puis par ID (plus récent)
                def sort_key(ing):
                    has_price_eur = 1 if ing['price_eur'] else 0
                    has_price_jpy = 1 if ing['price_jpy'] else 0
                    has_qty = 1 if ing['qty'] and ing['qty'] != 1 else 0
                    has_conversion_cat = 1 if ing['conversion_category'] else 0
                    return (has_price_eur + has_price_jpy, has_qty, has_conversion_cat, -ing['id'])

                sorted_group = sorted(group, key=sort_key, reverse=True)
                keeper = sorted_group[0]  # Garder le plus complet
                to_delete = sorted_group[1:]  # Supprimer les autres

                print(f"\n  • Groupe '{norm_name}':")
                print(f"    → GARDER ID {keeper['id']}: \"{keeper['ingredient_name_fr']}\"")

                # Mettre à jour le keeper avec le nom normalisé
                cursor.execute("""
                    UPDATE ingredient_price_catalog
                    SET ingredient_name_fr = ?
                    WHERE id = ?
                """, (norm_name, keeper['id']))

                for ing in to_delete:
                    print(f"    → SUPPRIMER ID {ing['id']}: \"{ing['ingredient_name_fr']}\"")
                    ids_to_delete.append(ing['id'])

            # Supprimer les doublons
            if ids_to_delete:
                placeholders = ','.join('?' * len(ids_to_delete))
                cursor.execute(f"""
                    DELETE FROM ingredient_price_catalog
                    WHERE id IN ({placeholders})
                """, ids_to_delete)
                print(f"\n✓ {len(ids_to_delete)} doublons supprimés")
        else:
            print("\n✓ Aucun doublon trouvé")

        # Normaliser tous les noms restants (ceux qui n'étaient pas des doublons)
        print("\n📝 Normalisation des noms restants...")
        cursor.execute("SELECT id, ingredient_name_fr FROM ingredient_price_catalog")
        all_ingredients = cursor.fetchall()

        updated = 0
        for ing in all_ingredients:
            normalized = normalize_ingredient_name(ing['ingredient_name_fr'])
            if normalized != ing['ingredient_name_fr']:
                cursor.execute("""
                    UPDATE ingredient_price_catalog
                    SET ingredient_name_fr = ?
                    WHERE id = ?
                """, (normalized, ing['id']))
                updated += 1

        if updated > 0:
            print(f"✓ {updated} noms normalisés")
        else:
            print("✓ Tous les noms étaient déjà normalisés")

        conn.commit()
        print("\n✅ Catalogue nettoyé avec succès !")


def normalize_recipes():
    """
    Normalise tous les noms d'ingrédients dans les recettes
    """
    print("\n" + "="*80)
    print("ÉTAPE 2 : NORMALISATION DES INGRÉDIENTS DANS LES RECETTES")
    print("="*80)

    with get_db() as conn:
        cursor = conn.cursor()

        # Récupérer tous les ingrédients français des recettes
        cursor.execute("""
            SELECT recipe_ingredient_id, name
            FROM recipe_ingredient_translation
            WHERE lang = 'fr'
            ORDER BY recipe_ingredient_id
        """)
        ingredients = cursor.fetchall()

        print(f"\n✓ {len(ingredients)} ingrédients français trouvés dans les recettes")

        # Normaliser chaque nom
        print("\n📝 Normalisation en cours...")
        updated = 0
        changes = []

        for ing in ingredients:
            original = ing['name']
            normalized = normalize_ingredient_name(original)

            if normalized != original:
                cursor.execute("""
                    UPDATE recipe_ingredient_translation
                    SET name = ?
                    WHERE recipe_ingredient_id = ? AND lang = 'fr'
                """, (normalized, ing['recipe_ingredient_id']))
                updated += 1
                changes.append((original, normalized))

        if changes:
            print(f"\n✓ {updated} ingrédients normalisés :")
            # Afficher quelques exemples
            for i, (old, new) in enumerate(changes[:10]):
                print(f"  • \"{old}\" → \"{new}\"")
            if len(changes) > 10:
                print(f"  ... et {len(changes) - 10} autres")
        else:
            print("\n✓ Tous les ingrédients étaient déjà normalisés")

        conn.commit()
        print("\n✅ Ingrédients des recettes normalisés avec succès !")


def main():
    """Point d'entrée principal"""
    print("\n" + "="*80)
    print("SCRIPT DE NORMALISATION DES INGRÉDIENTS")
    print("="*80)
    print("\nCe script va :")
    print("  1. Normaliser et fusionner les doublons dans le catalogue de prix")
    print("  2. Normaliser tous les ingrédients dans les recettes")
    print("\nRègles de normalisation :")
    print("  • Minuscules")
    print("  • Sans accents (é→e, œ→oe, etc.)")
    print("  • Au singulier (œufs→oeuf, tomates→tomate)")

    response = input("\n⚠️  Continuer ? (oui/non) : ").strip().lower()
    if response not in ['oui', 'o', 'yes', 'y']:
        print("\n❌ Annulé")
        return

    try:
        # Étape 1 : Nettoyer le catalogue
        normalize_catalog()

        # Étape 2 : Normaliser les recettes
        normalize_recipes()

        print("\n" + "="*80)
        print("✅ NORMALISATION TERMINÉE AVEC SUCCÈS !")
        print("="*80)
        print("\nVous pouvez maintenant vérifier le catalogue des prix.")
        print("Les doublons ont été fusionnés et tous les noms sont normalisés.\n")

    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
