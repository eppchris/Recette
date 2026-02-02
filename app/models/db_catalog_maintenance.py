# app/models/db_catalog_maintenance.py
"""
Module de maintenance du catalogue d'ingredients
Detection et fusion des doublons
"""
from collections import defaultdict
from .db_core import get_db, normalize_ingredient_name


# ============================================================================
# UTILITAIRES
# ============================================================================

def _levenshtein_distance(s1: str, s2: str) -> int:
    """Distance d'edition entre deux chaines (pure Python)."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


_FR_STOPWORDS = {'de', 'du', 'des', 'le', 'la', 'les', 'l', 'd', 'au', 'aux', 'un', 'une'}


def _strip_stopwords(name: str) -> str:
    """Supprime les articles/prepositions francais pour comparaison.

    Ex: "cuisse de poulet" -> "cuisse poulet"
        "filet d'agneau"   -> "filet agneau"
    """
    name = name.replace("'", " ").replace("\u2019", " ")
    words = name.split()
    filtered = [w for w in words if w not in _FR_STOPWORDS]
    return ' '.join(filtered)


class _UnionFind:
    """Structure union-find pour regrouper les elements similaires."""

    def __init__(self, elements):
        self.parent = {e: e for e in elements}
        self.rank = {e: 0 for e in elements}

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1

    def groups(self):
        grps = defaultdict(list)
        for e in self.parent:
            grps[self.find(e)].append(e)
        return [g for g in grps.values() if len(g) >= 2]


# ============================================================================
# DETECTION DES DOUBLONS
# ============================================================================

def detect_duplicate_groups():
    """
    Detecte les groupes d'ingredients similaires/doublons dans le catalogue.

    Regles de regroupement :
    A) Meme nom normalise (ex: "Oignon" et "oignon")
    B) Distance Levenshtein <= 1 sur noms normalises ou les DEUX font > 5 chars
    C) Meme nom apres suppression des articles/prepositions (de, du, des, le, la...)

    Retourne une liste de groupes avec membres et nom canonique propose.
    """
    with get_db() as con:
        # Charger tous les ingredients du catalogue
        rows = con.execute("""
            SELECT c.id, c.ingredient_name_fr, c.ingredient_name_jp,
                   c.price_eur, c.price_jpy, c.qty, c.unit_fr, c.unit_jp,
                   c.conversion_category,
                   c.price_eur_source, c.price_eur_last_receipt_date,
                   c.price_jpy_source, c.price_jpy_last_receipt_date
            FROM ingredient_price_catalog c
            ORDER BY c.ingredient_name_fr
        """).fetchall()

        if not rows:
            return []

        # Construire les donnees des membres
        members_data = {}
        normalized_names = {}
        for row in rows:
            cid = row['id']
            name_fr = row['ingredient_name_fr']
            norm = normalize_ingredient_name(name_fr)
            normalized_names[cid] = norm

            # Compter le nombre de recettes utilisant ce nom
            recipe_count = con.execute("""
                SELECT COUNT(DISTINCT ri.recipe_id) as cnt
                FROM recipe_ingredient ri
                JOIN recipe_ingredient_translation rit
                    ON rit.recipe_ingredient_id = ri.id
                WHERE rit.lang = 'fr' AND LOWER(rit.name) = LOWER(?)
            """, (name_fr,)).fetchone()['cnt']

            members_data[cid] = {
                "catalog_id": cid,
                "ingredient_name_fr": name_fr,
                "ingredient_name_jp": row['ingredient_name_jp'],
                "normalized_name": norm,
                "recipe_count": recipe_count,
                "has_price_eur": row['price_eur'] is not None,
                "has_price_jpy": row['price_jpy'] is not None,
                "price_eur": row['price_eur'],
                "price_jpy": row['price_jpy'],
                "qty": row['qty'] or 1.0,
                "unit_fr": row['unit_fr'] or 'g',
                "unit_jp": row['unit_jp'] or 'g',
                "conversion_category": row['conversion_category'],
                "price_eur_source": row['price_eur_source'],
                "price_jpy_source": row['price_jpy_source'],
            }

    # Regrouper avec Union-Find
    all_ids = list(members_data.keys())
    uf = _UnionFind(all_ids)

    # Pre-calculer les noms sans articles/prepositions pour la regle C
    stripped_names = {cid: _strip_stopwords(norm) for cid, norm in normalized_names.items()}

    for i in range(len(all_ids)):
        for j in range(i + 1, len(all_ids)):
            id_i, id_j = all_ids[i], all_ids[j]
            norm_i = normalized_names[id_i]
            norm_j = normalized_names[id_j]

            # Regle A : meme nom normalise
            if norm_i == norm_j:
                uf.union(id_i, id_j)
                continue

            # Regle B : Levenshtein <= 1 (les DEUX noms > 5 chars)
            # Evite les faux positifs comme oeuf/boeuf, lait/lard, miso/miel
            if len(norm_i) > 5 and len(norm_j) > 5:
                if _levenshtein_distance(norm_i, norm_j) <= 1:
                    uf.union(id_i, id_j)
                    continue

            # Regle C : meme nom sans articles/prepositions (de, du, des, le, la...)
            # Ex: "cuisse de poulet" == "cuisse poulet"
            strip_i = stripped_names[id_i]
            strip_j = stripped_names[id_j]
            if strip_i == strip_j and len(strip_i) > 3:
                uf.union(id_i, id_j)

    # Former les groupes
    raw_groups = uf.groups()
    result = []

    for group_idx, group_ids in enumerate(raw_groups):
        members = [members_data[cid] for cid in group_ids]

        # Trier : plus de recettes > plus de prix > nom le plus long
        def member_score(m):
            price_count = int(m['has_price_eur']) + int(m['has_price_jpy'])
            return (m['recipe_count'], price_count, len(m['ingredient_name_fr']))

        members.sort(key=member_score, reverse=True)

        # Proposer le nom canonique : celui du meilleur membre
        best = members[0]
        canonical_fr = best['ingredient_name_fr']
        # Chercher un nom JP parmi tous les membres
        canonical_jp = best.get('ingredient_name_jp')
        if not canonical_jp:
            for m in members[1:]:
                if m.get('ingredient_name_jp'):
                    canonical_jp = m['ingredient_name_jp']
                    break

        result.append({
            "group_id": group_idx,
            "members": members,
            "canonical_name_fr": canonical_fr,
            "canonical_name_jp": canonical_jp or "",
        })

    # Trier les groupes : ceux avec le plus de membres en premier
    result.sort(key=lambda g: len(g['members']), reverse=True)

    return result


# ============================================================================
# FUSION DES DOUBLONS
# ============================================================================

def merge_ingredient_group(member_catalog_ids, canonical_name_fr, canonical_name_jp=None, keeper_id=None):
    """
    Fusionne un groupe d'ingredients doublons en un seul.

    1. Selectionne le "keeper" (entree choisie par l'utilisateur, ou la plus complete)
    2. Fusionne les prix manquants depuis les autres
    3. Renomme avec le nom canonique
    4. Met a jour recipe_ingredient_translation
    5. Met a jour ingredient_specific_conversions
    6. Supprime les doublons du catalogue

    Retourne un dict avec les statistiques de fusion.
    """
    with get_db() as con:
        # 1. Charger toutes les entrees membres
        placeholders = ','.join(['?' for _ in member_catalog_ids])
        rows = con.execute(f"""
            SELECT * FROM ingredient_price_catalog WHERE id IN ({placeholders})
        """, member_catalog_ids).fetchall()

        members = [dict(row) for row in rows]
        if len(members) < 2:
            return {"recipes_updated": 0, "catalog_entries_removed": 0,
                    "conversions_updated": 0, "keeper_id": None}

        # 2. Selectionner le keeper
        if keeper_id is not None:
            # Keeper choisi par l'utilisateur
            keeper = None
            others = []
            for m in members:
                if m['id'] == keeper_id:
                    keeper = m
                else:
                    others.append(m)
            if keeper is None:
                # Fallback : keeper_id invalide, prendre le plus complet
                keeper = members[0]
                others = members[1:]
        else:
            # Auto-selection : le plus complet
            def score_member(m):
                score = 0
                if m['price_eur'] is not None:
                    score += 2
                if m['price_jpy'] is not None:
                    score += 2
                if m.get('conversion_category'):
                    score += 1
                if m.get('ingredient_name_jp'):
                    score += 1
                if m.get('price_eur_source'):
                    score += 1
                if m.get('price_jpy_source'):
                    score += 1
                return score

            members.sort(key=score_member, reverse=True)
            keeper = members[0]
            others = members[1:]

        # 3. Fusionner les donnees manquantes dans le keeper
        merge_fields = [
            'price_eur', 'price_jpy', 'qty', 'unit_fr', 'unit_jp',
            'conversion_category', 'ingredient_name_jp',
            'price_eur_source', 'price_eur_last_receipt_date',
            'price_jpy_source', 'price_jpy_last_receipt_date'
        ]
        merged_updates = {}
        for field in merge_fields:
            if keeper.get(field) is None:
                for other in others:
                    if other.get(field) is not None:
                        merged_updates[field] = other[field]
                        break

        # 4. Mettre a jour le keeper avec le nom canonique + donnees fusionnees
        set_clauses = ["ingredient_name_fr = ?", "updated_at = CURRENT_TIMESTAMP"]
        params = [canonical_name_fr]

        if canonical_name_jp:
            set_clauses.append("ingredient_name_jp = ?")
            params.append(canonical_name_jp)

        for field, value in merged_updates.items():
            set_clauses.append(f"{field} = ?")
            params.append(value)

        params.append(keeper['id'])
        con.execute(f"""
            UPDATE ingredient_price_catalog
            SET {', '.join(set_clauses)}
            WHERE id = ?
        """, params)

        # 5. Mettre a jour recipe_ingredient_translation (FR)
        recipes_updated = 0
        for member in members:
            old_name = member['ingredient_name_fr']
            if old_name.lower() != canonical_name_fr.lower():
                cursor = con.execute("""
                    UPDATE recipe_ingredient_translation
                    SET name = ?
                    WHERE lang = 'fr' AND LOWER(name) = LOWER(?)
                """, (canonical_name_fr, old_name))
                recipes_updated += cursor.rowcount

        # 6. Mettre a jour recipe_ingredient_translation (JP)
        if canonical_name_jp:
            for member in members:
                old_jp = member.get('ingredient_name_jp')
                if old_jp and old_jp != canonical_name_jp:
                    cursor = con.execute("""
                        UPDATE recipe_ingredient_translation
                        SET name = ?
                        WHERE lang = 'jp' AND LOWER(name) = LOWER(?)
                    """, (canonical_name_jp, old_jp))
                    recipes_updated += cursor.rowcount

        # 7. Mettre a jour ingredient_specific_conversions (gerer conflits UNIQUE)
        conversions_updated = 0
        for member in members:
            old_name = member['ingredient_name_fr']
            if old_name.lower() != canonical_name_fr.lower():
                # Recuperer les conversions de cet ancien nom
                old_convs = con.execute("""
                    SELECT id, from_unit, to_unit
                    FROM ingredient_specific_conversions
                    WHERE LOWER(ingredient_name_fr) = LOWER(?)
                """, (old_name,)).fetchall()

                for conv in old_convs:
                    # Verifier si le keeper a deja cette conversion
                    existing = con.execute("""
                        SELECT id FROM ingredient_specific_conversions
                        WHERE LOWER(ingredient_name_fr) = LOWER(?)
                          AND LOWER(from_unit) = LOWER(?)
                          AND LOWER(to_unit) = LOWER(?)
                    """, (canonical_name_fr, conv['from_unit'],
                          conv['to_unit'])).fetchone()

                    if existing:
                        # Conflit : supprimer l'ancienne (garder celle du keeper)
                        con.execute("""
                            DELETE FROM ingredient_specific_conversions
                            WHERE id = ?
                        """, (conv['id'],))
                    else:
                        # Pas de conflit : renommer
                        con.execute("""
                            UPDATE ingredient_specific_conversions
                            SET ingredient_name_fr = ?
                            WHERE id = ?
                        """, (canonical_name_fr, conv['id']))
                        conversions_updated += 1

        # 8. Supprimer les autres entrees du catalogue
        other_ids = [m['id'] for m in others]
        if other_ids:
            placeholders = ','.join(['?' for _ in other_ids])
            con.execute(f"""
                DELETE FROM ingredient_price_catalog WHERE id IN ({placeholders})
            """, other_ids)

        return {
            "recipes_updated": recipes_updated,
            "catalog_entries_removed": len(other_ids),
            "conversions_updated": conversions_updated,
            "keeper_id": keeper['id']
        }
