#!/usr/bin/env python3
"""Mise à jour complète du catalogue de prix depuis le screenshot"""

import sqlite3

DB_PATH = "data/recette.sqlite3"

# Données extraites du screenshot (toutes les lignes visibles)
catalog_data = [
    # (ingredient_name_fr, price_eur, price_jpy, qty, unit_fr, ingredient_name_jp, unit_jp)
    ("Ail", 0.3, 51, 1, "Pièce", "にんにく", "個"),
    ("Aubergine", 1.2, 204, 1, "Pièce", "なす", "本"),
    ("Avocat", 1.8, 306, 1, "Pièce", "アボカド", "個"),
    ("Bamboo", 3.5, 595, 100, "g", "こぼう", "g"),
    ("Basilic", 1.5, 255, 1, "Pied (<300g)", "バジリコ", "株"),
    ("Carotte", 0.2, 34, 1, "kg", "にんじん", "kg"),
    ("Champignon de Paris", None, 510, 1, "kg", "シャンピニオン", "g"),
    ("Champignons", 2.5, 425, 250, "g", "きのこ", "g"),
    ("Chou", None, 170, 1, "kg", "キャベツ", "kg"),
    ("Concombre", 0.7, 119, 1, "Pièce", "きゅうり", "本"),
    ("Courge", None, 340, 1, "kg", "かぼちゃ", "kg"),
    ("Courgette", 1.2, 204, 1, "Pièce", "ズッキーニ", "本"),
    ("Daishi", None, 680, 1, "L", "出汁", "L"),
    ("Daishi blanc", None, 850, 500, "g", "白だし", "g"),
    ("Eau", 0.2, 34, 1, "L", "水", "L"),
    ("Extrait de bouillon", None, 510, 100, "ml", "出汁", "ml"),
    ("Farine de blé", 1.5, 255, 1, "kg", "小麦粉", "kg"),
    ("Farine de cébette", None, 510, 100, "g", "天ぷら粉", "g"),
    ("Fécule de pomme de terre", 2.5, 425, 200, "g", "片栗粉", "g"),
    ("Gingembre", None, 340, 100, "g", "しょうが", "g"),
    ("Gombo", None, 510, 100, "g", "オクラ", "g"),
    ("Haricots verts (seiches)", 2.5, 425, 500, "g", "インゲン（乾燥）", "g"),
    ("Huile", 8.5, 1445, 1, "L", "オイル", "L"),
    ("Huile de salade", None, 850, 1, "L", "サラダ油", "L"),
    ("Huile de sésame", None, 1020, 500, "ml", "ごま油", "ml"),
    ("Oeuf", 0.3, 51, 1, "Pièce", "卵", "個"),
    ("Oignon", 0.8, 136, 1, "kg", "玉ねぎ", "kg"),
    ("Saumon", None, 2040, 1, "Filet (<200g)", "鮭", "g"),
    ("Sel", 0.5, 85, 1, "kg", "塩", "kg"),
    ("Huile d'olive", 8.5, 1445, 1, "L", "オリーブオイル", "L"),
    ("Jambon", 1.5, 255, 1, "kg", "ハム", "kg"),
    ("Jus de gingembre", 2.5, 425.0, 1, "ml", "生姜汁", "ml"),
    ("Katsuobushi", 0.0025, 0.425, 1, "g", "鰹節", "g"),
    ("Ketchup", 0.0025, 0.425, 1, "g", "ケチャップ", "g"),
    ("Ketchup de tomate", 2.5, 425.0, 1, "ml", "トマトケチャップ", "ml"),
    ("Komatsuna", 2.5, 425.0, 1, "g", "小松菜", "g"),
    ("Koji de sauce soja", 1.5, 255.0, 1, "unité", "醤油麹", "g"),
    ("Koji d'oignon", 1.5, 255.0, 1, "unité", "玉ねぎ麹", "g"),
    ("Komatsuna", 1.5, 255.0, 1, "株", "小松菜", "株"),
    ("Kornstuke", 1.5, 255.0, 1, "cm", "小松菜", "cm"),
    ("Kuzu d'oignon", 2.5, 425.0, 1, "g", "玉ねぎ葛", "g"),
    ("Laurier", 1.5, 255.0, 1, "g", "ローリエ", "g"),
    ("Laurier, poivre en grains, ail", 1.5, 255.0, 1, "unité", "ローリエ・粒胡椒・にんにく", "unité"),
    ("Lauriers", 1.5, 255.0, 1, "g", "ローリエ", "g"),
    ("Levure chimique", 0.0025, 0.425, 1, "g", "ベーキングパウダー", "g"),
    ("Lit de son", 2.5, 425.0, 1, "g", "糠床", "g"),
    ("Lotus", 1.5, 255.0, 1, "g", "れんこん", "g"),
    ("Légumes de votre choix", 1.5, 255.0, 1, "unité", "お好み野菜", "unité"),
    ("Mirin", 2.5, 425.0, 1, "ml", "みりん", "ml"),
    ("Miso de Hatcho", 0.0025, 0.425, 1, "g", "八丁味噌", "g"),
    ("Miso de soja", 0.0025, 0.425, 1, "g", "味噌", "g"),
    ("Mizuku", 1.5, 255.0, 1, "unité", "もずく", "g"),
    ("Moyashi", 1.5, 255.0, 1, "unité", "もやし", "g"),
    ("Natto de piège", 1.5, 255.0, 1, "g", "納豆菌", "g"),
    ("Natto de pomme", 1.5, 255.0, 1, "Piège", "納豆", "パック"),
    ("Natto de qualité supérieure", 1.5, 255.0, 1, "unité", "玉露納豆", "g"),
    ("Negi", 1.5, 255.0, 1, "g", "ネギ", "g"),
    ("Oignon", 0.0025, 0.425, 1, "unité", "玉ねぎ", "個"),
    ("Oignon nouveau", 1.5, 255.0, 1, "個", "新玉ねぎ", "個"),
    ("Oignon ou feuille de votre choix", 1.5, 255.0, 1, "unité", "ネギまたはお好み野菜", "unité"),
    ("Shiso", 1.5, 255.0, 1, "unité", "しそ", "g"),
    ("Panko italien", 1.5, 255.0, 1, "g", "パン粉 イタリア", "g"),
    ("Piment", 1.5, 255.0, 1, "本", "唐辛子", "本"),
    ("Poivre", 0.0025, 0.425, 1, "unité", "胡椒", "g"),
    ("Poivre en grains", 0.0025, 0.425, 1, "粒", "粒胡椒", "粒"),
    ("Poivre noir frais émoché", 1.5, 255.0, 1, "unité", "フレッシュ粒胡椒", "個"),
    ("Poivron doux", 1.5, 255.0, 1, "unité", "ピーマン", "g"),
    ("Pomme de terre nouvelle", 1.5, 255.0, 1, "unité", "新じゃが", "g"),
    ("Poudre de curry", 0.0025, 0.425, 1, "g", "カレー粉", "g"),
    ("Poudre grill", 0.0025, 0.425, 1, "g", "焼き肉たれ", "g"),
    ("Purée de sauce de poisson", 2.5, 425.0, 1, "ml", "魚醤ペースト", "ml"),
    ("Pâte de soja", 1.5, 255.0, 1, "g", "味噌", "g"),
    ("Raisins de Corinthe", 1.5, 255.0, 1, "g", "干しぶどう", "g"),
    ("Shiiso verte", 1.5, 255.0, 1, "枚", "青しそ", "枚"),
    ("Sel de roch et mochi et au blé", 1.5, 255.0, 1, "unité", "ロックソルト＆もちと小麦", "g"),
    ("Saké", 2.5, 425.0, 1, "ml", "酒", "ml"),
    ("Sauce concentrée hiro", 2.5, 425.0, 1, "ml", "ヒロソース", "ml"),
    ("Sauce de poisson", 2.5, 425.0, 1, "ml", "魚醤", "ml"),
    ("Sauce pour noodles maison", 0.0025, 0.425, 1, "ml", "麺つゆの素", "ml"),
    ("Sauce pour viande grillée maison", 1.5, 255.0, 1, "unité", "自家製焼き肉のタレ", "ml"),
    ("Sauce soja", 2.5, 425.0, 1, "ml", "醤油", "ml"),
    ("Sauce soja claire", 2.5, 425.0, 1, "ml", "薄口醤油", "ml"),
    ("Saumon", 2.5, 425.0, 1, "unité", "鮭", "g"),
    ("Sel fin", 0.0025, 0.425, 1, "g", "塩", "g"),
    ("Sel fin", 0.0025, 0.425, 1, "pinches", "食塩", "g"),
    ("Shimeji séché", 1.5, 255.0, 1, "g", "しめじ", "g"),
    ("Shimoji", 0.0025, 0.425, 1, "g", "しめじ", "g"),
    ("Shouyu soi de deux", 2.5, 425.0, 1, "ml", "醤油", "ml"),
    ("Shouyu soji", 1.5, 255.0, 1, "ml", "醤油麹", "ml"),
    ("Sirop", 0.0025, 0.425, 1, "g", "シロップ", "g"),
    ("Sucre en poudre", 0.0025, 0.425, 1, "g", "砂糖", "g"),
    ("Sucre de mascarpone", 1.5, 255.0, 1, "g", "砂糖（白砂糖）", "g"),
    ("Sésame", 0.0025, 0.425, 1, "unité", "ごま", "g"),
    ("Sésame noir", 0.0025, 0.425, 1, "g", "黒ごま", "g"),
    ("Sésame grillé", 0.0025, 0.425, 1, "g", "入り胡麻", "g"),
    ("Tofu", 1.5, 255.0, 1, "丁", "豆腐", "g"),
    ("Tomate", 1.5, 255.0, 1, "kg", "トマト", "g"),
    ("Tomate", 1.5, 255.0, 1, "unité", "トマト", "g"),
    ("Tranches de poulet", 1.5, 255.0, 1, "g", "鶏肉", "g"),
    ("Viande de porc", None, 1020, 1, "kg", "豚肉", "g"),
    ("Viande de porc hachée", None, 1020, 1, "kg", "豚挽肉", "g"),
]

def update_catalog():
    """Supprime toutes les données et les remplace par les nouvelles"""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    cursor = conn.cursor()

    try:
        # Supprimer toutes les données existantes
        cursor.execute("DELETE FROM ingredient_price_catalog")
        print(f"✓ {cursor.rowcount} anciennes lignes supprimées")

        # Insérer les nouvelles données
        inserted = 0
        errors = []

        for row in catalog_data:
            ingredient_fr, price_eur, price_jpy, qty, unit_fr, ingredient_jp, unit_jp = row

            try:
                cursor.execute("""
                    INSERT INTO ingredient_price_catalog
                    (ingredient_name_fr, ingredient_name_jp, price_eur, price_jpy, qty, unit_fr, unit_jp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (ingredient_fr, ingredient_jp, price_eur, price_jpy, qty, unit_fr, unit_jp))
                inserted += 1
            except Exception as e:
                errors.append(f"{ingredient_fr}: {str(e)}")

        conn.commit()
        print(f"✓ {inserted} nouveaux ingrédients insérés")

        if errors:
            print(f"\n⚠ Erreurs ({len(errors)}):")
            for error in errors[:10]:
                print(f"  - {error}")

    except Exception as e:
        print(f"✗ Erreur: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("=== Mise à jour complète du catalogue de prix ===\n")
    update_catalog()
