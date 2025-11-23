#!/usr/bin/env python3
"""Import des données du catalogue depuis la capture d'écran"""

import sqlite3

DB_PATH = "data/recette.sqlite3"

# Données extraites de la capture d'écran
catalog_data = [
    # ingredient_name_fr, price_eur, qty, unit_fr, ingredient_name_jp, unit_jp
    ("Ail", 0.3, 51, "Pièce", "にんにく", "個"),
    ("Aubergine", 1.2, 204, "Pièce", "なす", "本"),
    ("Avocat", 1.8, 306, "Pièce", "アボカド", "個"),
    ("Bamboo", 3.5, 595, "g", "こぼう", "g"),
    ("Basilic", 1.5, 255, "Pied/400g", "バジリコ", "株"),
    ("Carotte", 0.2, 34, "kg", "にんじん", "kg"),
    ("Champignon de Paris", None, 510, "kg", "シャンピニオン", "g"),
    ("Champignons", 2.5, 425, "g", "きのこ", "g"),
    ("Chou", None, 170, "kg", "キャベツ", "kg"),
    ("Concombre", 0.7, 119, "Pièce", "きゅうり", "本"),
    ("Courge", None, 340, "kg", "かぼちゃ", "kg"),
    ("Courgette", 1.2, 204, "Pièce", "ズッキーニ", "本"),
    ("Daikon", None, 680, "L", None, "L"),
    ("Daishi blanc", None, 850, "g", "白だし", "g"),
    ("Eau", None, 34, "L", "水", "L"),
    ("Extrait de bouillon", 0.2, None, "ml", "出汁", "ml"),
    ("Farine blanche", 1.5, 255, "kg", "小麦粉", "kg"),
    ("Farine de cébette", None, 510, "g", "天ぷら粉", "g"),
    ("Fécule de pomme de terre", 2.5, 425, "g", "片栗粉", "g"),
    ("Gingembre", None, 340, "g", "しょうが", "g"),
    ("Gombo", None, 510, "g", "オクラ", "g"),
    ("Haricots verts blancs", 2.5, 420, "g", "インゲン（白豆）", "g"),
    ("Huile", 8.5, 1445, "L", "オイル", "L"),
    ("Huile de salade", None, 850, "L", "サラダ", "L"),
    ("Huile de sésame", None, 1020, "ml", "ごま油", "ml"),
    ("Jambon", 0.3, 51, "Pièce", "ハム", "枚"),
    ("Oignon", 0.8, 136, "kg", "玉ねぎ", "kg"),
    ("Panure", None, 2040, "Paquet/500g", "パン粉", "袋"),
    ("Sel", 0.5, 85, "kg", "塩", "kg"),
    ("Sel d'olive", 8.5, 1445, "L", "オリーブオイル", "L"),
    ("Farine", 1.5, 255, "kg", "小麦粉", "kg"),
    ("Gingembre", 2.5, 425.0, "g", "しょうが", "g"),
    ("Katsuobushi", 0.0025, 0.425, "g", "鰹節", "g"),
    ("Ketchup de tomate", 2.5, 425.0, "ml", "トマトケチャップ", "ml"),
    ("Komatsuna", 2.5, 425.0, "Pièce", "小松菜", "株"),
    ("Kornstuke", 1.5, 255.0, "Pièce", "小松菜", "株"),
    ("Kouji d'oignon", 2.5, 425.0, "g", "玉ねぎ麹", "g"),
    ("Laurier", 2.5, 425.0, "g", "月桂樹", "g"),
    ("Laurel, poivre en grains, ail", 1.5, 255.0, "unité", "ローリエ・粒胡椒・にんにく", "unité"),
    ("Laurier", 1.5, 255.0, "g", "ローリエ", "g"),
    ("Levure de boulangerie", 0.0025, 0.425, "g", "酵母", "g"),
    ("Lièchement rosé", 1.5, 255.0, "g", "ロゼ", "g"),
    ("Lit de son", 2.5, 425.0, "g", "米糠", "g"),
    ("Mirin de Hatcho", 0.0025, 0.425, "g", "八丁味噌", "g"),
    ("Mizuna", 1.5, 255.0, "g", "水菜", "g"),
    ("Moruku", 1.5, 255.0, "unité", "もやし", "g"),
    ("Moyendu", 1.5, 255.0, "unité", "もやし", "g"),
    ("Natto de piège", 1.5, 255.0, "g", "納豆菌", "g"),
    ("Natto de pomme", 1.5, 255.0, "Piège", "納豆", "パック"),
    ("Natto de qualité supérieure", 1.5, 255.0, "unité", "高級納豆", "g"),
    ("Negi", 1.5, 255.0, "g", "ネギ", "g"),
]

def import_data():
    """Importe les données dans la base"""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    cursor = conn.cursor()

    inserted = 0
    updated = 0
    errors = []

    for row in catalog_data:
        ingredient_fr, price_eur, qty, unit_fr, ingredient_jp, unit_jp = row

        try:
            # Vérifier si l'ingrédient existe
            cursor.execute(
                "SELECT id FROM ingredient_price_catalog WHERE ingredient_name_fr = ?",
                (ingredient_fr,)
            )
            existing = cursor.fetchone()

            if existing:
                # Mise à jour
                cursor.execute("""
                    UPDATE ingredient_price_catalog
                    SET price_eur = ?, qty = ?, unit_fr = ?,
                        ingredient_name_jp = ?, unit_jp = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE ingredient_name_fr = ?
                """, (price_eur, qty, unit_fr, ingredient_jp, unit_jp, ingredient_fr))
                updated += 1
            else:
                # Insertion
                cursor.execute("""
                    INSERT INTO ingredient_price_catalog
                    (ingredient_name_fr, ingredient_name_jp, price_eur, qty, unit_fr, unit_jp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (ingredient_fr, ingredient_jp, price_eur, qty, unit_fr, unit_jp))
                inserted += 1

        except Exception as e:
            errors.append(f"{ingredient_fr}: {str(e)}")

    conn.commit()
    conn.close()

    print(f"✓ Import terminé:")
    print(f"  - {inserted} ingrédients insérés")
    print(f"  - {updated} ingrédients mis à jour")
    if errors:
        print(f"\n⚠ Erreurs ({len(errors)}):")
        for error in errors[:10]:  # Afficher max 10 erreurs
            print(f"  - {error}")

if __name__ == "__main__":
    print("=== Import du catalogue de prix ===\n")
    import_data()
