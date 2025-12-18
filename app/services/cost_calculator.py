"""
Module de calcul du coût estimé des ingrédients
Utilise les conversions d'unités (standard et spécifiques) pour calculer le prix
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


@dataclass
class CostResult:
    """Résultat du calcul de coût pour un ingrédient"""
    cost: float
    status: str  # "ok", "missing_data", "missing_price", "missing_conversion"
    debug: Dict[str, Any]


def compute_estimated_cost_for_ingredient(
    conn,
    ingredient_name_fr: str,
    recipe_qty: float,
    recipe_unit: str,
    currency: str = "EUR",
    lang: str = "fr",
) -> CostResult:
    """
    Calcule le coût estimé pour un ingrédient d'une recette.

    Algorithme de résolution (par ordre de priorité) :
    1. DIRECT : recipe_unit == IPC.unit_fr → calcul immédiat
    2. UC (Unit Conversion générique) : recipe_unit → target_unit via category
    3. ISC (Ingredient Specific Conversion) : recipe_unit → target_unit pour cet ingrédient
    4. ISC + UC (chaîne) : recipe_unit → ISC → UC → target_unit

    Args:
        conn: Connexion à la base de données SQLite
        ingredient_name_fr: Nom de l'ingrédient (clé stable en français)
        recipe_qty: Quantité utilisée dans la recette
        recipe_unit: Unité canonique de la recette (ex: "ml", "g", "pièce")
        currency: "EUR" ou "JPY"

    Returns:
        CostResult avec:
        - cost: Coût calculé (0.0 si non calculable)
        - status: "ok", "missing_data", "missing_price", "missing_conversion"
        - debug: Détails pour troubleshooting
    """
    currency = currency.upper().strip()
    if currency not in ("EUR", "JPY"):
        return CostResult(
            cost=0.0,
            status="invalid_currency",
            debug={"currency": currency},
        )

    price_field = "price_eur" if currency == "EUR" else "price_jpy"

    debug: Dict[str, Any] = {
        "ingredient_name_fr": ingredient_name_fr,
        "recipe_qty": recipe_qty,
        "recipe_unit": recipe_unit,
        "currency": currency,
        "price_field": price_field,
        "path": [],
    }

    # -----------------------------
    # 1) Charger toutes les lignes IPC pour cet ingrédient
    # -----------------------------
    ipc_rows = conn.execute(
        f"""
        SELECT id, ingredient_name_fr, unit_fr, {price_field} AS price, qty, conversion_category
        FROM ingredient_price_catalog
        WHERE LOWER(ingredient_name_fr) = LOWER(?)
        """,
        (ingredient_name_fr,),
    ).fetchall()

    if not ipc_rows:
        debug["path"].append("ipc_missing")
        return CostResult(cost=0.0, status="missing_data", debug=debug)

    # La catégorie devrait être cohérente pour l'ingrédient; prendre la première non-null
    category = None
    for r in ipc_rows:
        if r["conversion_category"] is not None:
            category = r["conversion_category"]
            break
    debug["conversion_category"] = category

    # Helper: trouver une ligne IPC par unité avec prix non-null
    def find_ipc_by_unit(unit_code: str):
        """Cherche une ligne IPC avec cette unité et un prix défini"""
        for r in ipc_rows:
            if r["unit_fr"].lower() == unit_code.lower() and r["price"] is not None:
                return r
        return None

    # Helper: calculer le coût à partir d'une ligne IPC et d'une quantité déjà convertie
    def compute_cost(ipc_row, qty_in_ipc_unit: float) -> Tuple[float, str]:
        """Calcule le coût: (qty / pack_qty) * pack_price"""
        pack_qty = ipc_row["qty"] if ipc_row["qty"] is not None else 1.0
        pack_price = ipc_row["price"]

        if pack_price is None:
            return 0.0, "missing_price"

        if pack_qty == 0:
            return 0.0, "invalid_pack_qty"

        # Prix unitaire = prix du paquet / quantité du paquet
        unit_cost = pack_price / pack_qty
        total_cost = qty_in_ipc_unit * unit_cost

        return total_cost, "ok"

    # -----------------------------
    # 2) DIRECT (recipe_unit == IPC.unit_fr)
    # -----------------------------
    ipc_direct = find_ipc_by_unit(recipe_unit)
    if ipc_direct is not None:
        debug["path"].append("direct")
        debug["ipc_unit"] = ipc_direct["unit_fr"]
        debug["ipc_id"] = ipc_direct["id"]
        debug["pack_qty"] = ipc_direct["qty"]
        debug["pack_price"] = ipc_direct["price"]
        cost, status = compute_cost(ipc_direct, recipe_qty)
        return CostResult(cost=cost, status=status, debug=debug)

    # -----------------------------
    # 3) UC générique (recipe_unit → target_unit) via category
    # -----------------------------
    if category is not None:
        uc = conn.execute(
            """
            SELECT from_unit, to_unit, factor
            FROM unit_conversion
            WHERE category = ?
              AND LOWER(from_unit) = LOWER(?)
            LIMIT 1
            """,
            (category, recipe_unit),
        ).fetchone()

        if uc is not None:
            target_unit = uc["to_unit"]
            factor = uc["factor"]
            converted_qty = recipe_qty * factor
            debug["path"].append("uc")
            debug["uc_from"] = recipe_unit
            debug["uc_to"] = target_unit
            debug["uc_factor"] = factor
            debug["qty_after_uc"] = converted_qty

            ipc_uc = find_ipc_by_unit(target_unit)
            if ipc_uc is not None:
                debug["ipc_unit"] = ipc_uc["unit_fr"]
                debug["ipc_id"] = ipc_uc["id"]
                debug["pack_qty"] = ipc_uc["qty"]
                debug["pack_price"] = ipc_uc["price"]
                cost, status = compute_cost(ipc_uc, converted_qty)
                return CostResult(cost=cost, status=status, debug=debug)

    # -----------------------------
    # 4) ISC spécifique (recipe_unit → target_unit)
    # -----------------------------
    isc = conn.execute(
        """
        SELECT from_unit, to_unit, factor
        FROM ingredient_specific_conversions
        WHERE LOWER(ingredient_name_fr) = LOWER(?)
          AND LOWER(from_unit) = LOWER(?)
        LIMIT 1
        """,
        (ingredient_name_fr, recipe_unit),
    ).fetchone()

    if isc is not None:
        target_unit = isc["to_unit"]
        factor = isc["factor"]
        converted_qty = recipe_qty * factor
        debug["path"].append("isc")
        debug["isc_from"] = recipe_unit
        debug["isc_to"] = target_unit
        debug["isc_factor"] = factor
        debug["qty_after_isc"] = converted_qty

        # 4a) Essayer IPC direct sur l'unité cible de ISC
        ipc_isc = find_ipc_by_unit(target_unit)
        if ipc_isc is not None:
            debug["path"].append("isc->ipc")
            debug["ipc_unit"] = ipc_isc["unit_fr"]
            debug["ipc_id"] = ipc_isc["id"]
            debug["pack_qty"] = ipc_isc["qty"]
            debug["pack_price"] = ipc_isc["price"]
            cost, status = compute_cost(ipc_isc, converted_qty)
            return CostResult(cost=cost, status=status, debug=debug)

        # 4b) Sinon: ISC puis UC (target_unit → target_unit2) via category
        if category is not None:
            uc2 = conn.execute(
                """
                SELECT from_unit, to_unit, factor
                FROM unit_conversion
                WHERE category = ?
                  AND LOWER(from_unit) = LOWER(?)
                LIMIT 1
                """,
                (category, target_unit),
            ).fetchone()

            if uc2 is not None:
                target_unit2 = uc2["to_unit"]
                factor2 = uc2["factor"]
                converted_qty2 = converted_qty * factor2
                debug["path"].append("isc->uc")
                debug["uc2_from"] = target_unit
                debug["uc2_to"] = target_unit2
                debug["uc2_factor"] = factor2
                debug["qty_after_isc_uc"] = converted_qty2

                ipc_isc_uc = find_ipc_by_unit(target_unit2)
                if ipc_isc_uc is not None:
                    debug["path"].append("isc->uc->ipc")
                    debug["ipc_unit"] = ipc_isc_uc["unit_fr"]
                    debug["ipc_id"] = ipc_isc_uc["id"]
                    debug["pack_qty"] = ipc_isc_uc["qty"]
                    debug["pack_price"] = ipc_isc_uc["price"]
                    cost, status = compute_cost(ipc_isc_uc, converted_qty2)
                    return CostResult(cost=cost, status=status, debug=debug)

    # -----------------------------
    # 5) Aucune solution : créer une ISC par défaut
    # -----------------------------
    # Si on arrive ici, c'est qu'on a :
    # - Un ingrédient dans le catalogue (IPC existe)
    # - Une unité de recette différente de l'unité catalogue
    # - Aucune conversion (ni UC ni ISC) trouvée
    #
    # Solution : créer une ISC avec facteur par défaut = 1.0
    # L'utilisateur pourra ensuite l'ajuster

    # Trouver une ligne IPC pour déterminer l'unité cible
    if ipc_rows and category is not None:
        # Prendre la première ligne IPC avec prix
        target_ipc = None
        for r in ipc_rows:
            if r["price"] is not None:
                target_ipc = r
                break

        if target_ipc is not None:
            catalog_unit = target_ipc["unit_fr"]

            # Créer la conversion spécifique avec facteur par défaut = 1.0
            try:
                # Message selon la langue
                date_str = __import__('datetime').datetime.now().strftime('%Y-%m-%d')
                if lang == 'jp':
                    note_msg = f"⚠️ 自動作成された変換 - 調整が必要！（作成日：{date_str}）"
                else:
                    note_msg = f"⚠️ Conversion automatique créée - À AJUSTER ! (créée le {date_str})"

                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ingredient_specific_conversions
                    (ingredient_name_fr, from_unit, to_unit, factor, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    ingredient_name_fr,
                    recipe_unit,
                    catalog_unit,
                    1.0,
                    note_msg
                ))
                conn.commit()

                debug["path"].append("isc_auto_created")
                debug["auto_isc_from"] = recipe_unit
                debug["auto_isc_to"] = catalog_unit
                debug["auto_isc_factor"] = 1.0
                debug["warning"] = f"Conversion automatique créée: {recipe_unit} → {catalog_unit} (factor=1.0). AJUSTER !"

                # Maintenant calculer avec cette nouvelle conversion
                converted_qty = recipe_qty * 1.0

                debug["ipc_unit"] = catalog_unit
                debug["ipc_id"] = target_ipc["id"]
                debug["pack_qty"] = target_ipc["qty"]
                debug["pack_price"] = target_ipc["price"]

                cost, status = compute_cost(target_ipc, converted_qty)

                # Status spécial pour indiquer qu'une conversion a été créée
                return CostResult(cost=cost, status="isc_created", debug=debug)

            except Exception as e:
                debug["path"].append("isc_creation_failed")
                debug["error"] = str(e)

    # Si vraiment aucune solution (pas d'IPC non plus)
    debug["path"].append("no_solution")
    return CostResult(cost=0.0, status="missing_conversion", debug=debug)


def compute_estimated_cost_for_recipe(
    conn,
    recipe_lines,
    currency: str = "EUR",
) -> Tuple[float, list]:
    """
    Calcule le coût total estimé pour une recette.

    Args:
        conn: Connexion à la base de données SQLite
        recipe_lines: Liste de dicts avec ingredient_name_fr, quantity, unit
        currency: "EUR" ou "JPY"

    Returns:
        Tuple (total_cost, details_list)
        - total_cost: Somme des coûts calculés avec succès
        - details_list: Liste des détails par ingrédient (cost, status, debug)
    """
    total = 0.0
    details = []

    for line in recipe_lines:
        ingredient_name_fr = line["ingredient_name_fr"]
        qty = float(line["quantity"])
        unit = str(line["unit"])

        res = compute_estimated_cost_for_ingredient(
            conn=conn,
            ingredient_name_fr=ingredient_name_fr,
            recipe_qty=qty,
            recipe_unit=unit,
            currency=currency,
        )

        details.append({
            "ingredient_name_fr": ingredient_name_fr,
            "qty": qty,
            "unit": unit,
            "currency": currency,
            "cost": res.cost,
            "status": res.status,
            "debug": res.debug,
        })

        # N'ajouter au total que si le calcul a réussi
        if res.status == "ok":
            total += res.cost

    return total, details
