#!/usr/bin/env python3
"""
Script de remplissage du lexique :
- Génère la lecture hiragana (よみがな) pour chaque nom japonais
- Vérifie et corrige les traductions FR ↔ JP
- Met à jour ingredient_price_catalog en base

Usage : python scripts/fill_lexique_hiragana.py [--dry-run] [--batch-size N]
"""
import sys
import os
import json
import argparse
import time

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from groq import Groq
from app.models.db_core import get_db

BATCH_SIZE = 30  # ingrédients par appel API
MODEL = "llama-3.3-70b-versatile"


def get_all_ingredients():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, ingredient_name_fr, ingredient_name_jp, ingredient_name_jp_reading
            FROM ingredient_price_catalog
            ORDER BY ingredient_name_fr
        """)
        return [dict(r) for r in cursor.fetchall()]


def update_ingredient(ingredient_id: int, new_jp: str, new_reading: str, dry_run: bool):
    if dry_run:
        return
    with get_db() as conn:
        conn.execute("""
            UPDATE ingredient_price_catalog
            SET ingredient_name_jp = ?,
                ingredient_name_jp_reading = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_jp, new_reading or None, ingredient_id))
        conn.commit()


def process_batch(client: Groq, batch: list) -> list:
    """
    Envoie un lot d'ingrédients à Groq.
    Retourne une liste de dicts avec : id, jp_corrected, reading, changed
    """
    items_json = json.dumps([
        {"id": i["id"], "fr": i["ingredient_name_fr"], "jp": i["ingredient_name_jp"] or ""}
        for i in batch
    ], ensure_ascii=False)

    prompt = f"""Tu es un expert culinaire bilingue français-japonais.

Pour chaque ingrédient ci-dessous, tu dois :
1. Vérifier que la traduction japonaise (jp) correspond bien au nom français (fr).
   - Si jp est vide ou incorrect, propose la traduction correcte (nom usuel japonais, en kanji/kana).
   - Si jp est déjà correct, garde-le tel quel.
2. Donner la lecture hiragana complète (よみがな) du nom japonais final.
   - Si le nom jp est entièrement en hiragana/katakana (pas de kanji), le reading = le nom jp lui-même.
   - Pour les katakana, convertis en hiragana dans le reading.

Réponds UNIQUEMENT avec un tableau JSON valide, sans texte avant ou après.
Format : [{{"id": N, "jp": "traduction japonaise finale", "reading": "lecture hiragana", "note": "explication si correction"}}]

Ingrédients à traiter :
{items_json}"""

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=MODEL,
        max_tokens=4000,
        temperature=0.1,
    )

    raw = response.choices[0].message.content.strip()

    # Extraire le JSON (parfois encadré de ```json ... ```)
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


def main():
    parser = argparse.ArgumentParser(description="Remplir hiragana + vérifier traductions du lexique")
    parser.add_argument("--dry-run", action="store_true", help="Affiche les résultats sans écrire en DB")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--only-empty", action="store_true", help="Traite uniquement les ingrédients sans hiragana")
    args = parser.parse_args()

    client = Groq(api_key=Config.GROQ_API_KEY)

    all_items = get_all_ingredients()
    if args.only_empty:
        items = [i for i in all_items if not i["ingredient_name_jp_reading"]]
    else:
        items = all_items

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Traitement de {len(items)} ingrédients par lots de {args.batch_size}")
    print("=" * 60)

    corrections = []
    errors = []
    total_updated = 0

    for start in range(0, len(items), args.batch_size):
        batch = items[start:start + args.batch_size]
        end = min(start + args.batch_size, len(items))
        print(f"\nLot {start + 1}–{end} / {len(items)}...")

        try:
            results = process_batch(client, batch)
        except Exception as e:
            print(f"  ❌ Erreur API : {e}")
            errors.extend([i["id"] for i in batch])
            time.sleep(2)
            continue

        # Indexer les résultats par id
        results_by_id = {r["id"]: r for r in results}

        for ing in batch:
            result = results_by_id.get(ing["id"])
            if not result:
                print(f"  ⚠️  Pas de résultat pour id={ing['id']} ({ing['ingredient_name_fr']})")
                continue

            new_jp = result.get("jp", ing["ingredient_name_jp"] or "")
            new_reading = result.get("reading", "")
            note = result.get("note", "")

            old_jp = ing["ingredient_name_jp"] or ""
            jp_changed = new_jp.strip() != old_jp.strip()

            # Affichage
            status = "✅" if not jp_changed else "🔄"
            print(f"  {status} {ing['ingredient_name_fr']}")
            print(f"       JP: {old_jp or '—'} → {new_jp}  |  よみ: {new_reading}")
            if jp_changed and note:
                print(f"       📝 {note}")
                corrections.append({
                    "fr": ing["ingredient_name_fr"],
                    "old_jp": old_jp,
                    "new_jp": new_jp,
                    "reading": new_reading,
                    "note": note
                })

            update_ingredient(ing["id"], new_jp.strip(), new_reading.strip(), args.dry_run)
            total_updated += 1

        # Petite pause entre lots pour ne pas saturer l'API
        if end < len(items):
            time.sleep(0.5)

    print("\n" + "=" * 60)
    print(f"{'[DRY RUN] ' if args.dry_run else ''}Terminé : {total_updated} ingrédients traités")

    if corrections:
        print(f"\n🔄 {len(corrections)} traductions corrigées :")
        for c in corrections:
            print(f"  • {c['fr']}: «{c['old_jp']}» → «{c['new_jp']}»  ({c['note']})")

    if errors:
        print(f"\n❌ {len(errors)} IDs en erreur : {errors}")


if __name__ == "__main__":
    main()
