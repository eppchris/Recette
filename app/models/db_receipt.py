"""
Module de gestion des tickets de caisse et de leurs articles
"""
import sqlite3
from typing import List, Dict, Optional
from .db_core import get_db, normalize_ingredient_name
from datetime import datetime


def create_receipt_upload(
    filename: str,
    receipt_name: Optional[str] = None,
    store_name: Optional[str] = None,
    receipt_date: Optional[str] = None,
    currency: str = "EUR",
    user_id: Optional[int] = None
) -> int:
    """
    Crée un nouvel enregistrement de ticket de caisse uploadé

    Args:
        filename: Nom du fichier PDF
        receipt_name: Nom personnalisé donné par l'utilisateur
        store_name: Nom du commerce (extrait du PDF)
        receipt_date: Date du ticket (format YYYY-MM-DD)
        currency: Devise (EUR, JPY, etc.)
        user_id: ID de l'utilisateur qui a uploadé

    Returns:
        ID du receipt créé
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO receipt_upload_history (
                filename, receipt_name, store_name, receipt_date, currency, user_id, status
            ) VALUES (?, ?, ?, ?, ?, ?, 'pending')
        """, (filename, receipt_name, store_name, receipt_date, currency, user_id))
        conn.commit()
        return cursor.lastrowid


def save_receipt_items(receipt_id: int, items: List[Dict]) -> int:
    """
    Sauvegarde les articles extraits d'un ticket avec leur matching

    Args:
        receipt_id: ID du receipt
        items: Liste des items avec:
            - receipt_item_text_original: Texte original de l'article
            - receipt_item_text_fr: Traduction française
            - receipt_price: Prix
            - receipt_quantity: Quantité (optionnel)
            - receipt_unit: Unité (optionnel)
            - matched_ingredient_id: ID de l'ingrédient matché (optionnel)
            - confidence_score: Score de confiance (optionnel)

    Returns:
        Nombre d'items sauvegardés
    """
    with get_db() as conn:
        cursor = conn.cursor()

        count = 0
        for item in items:
            cursor.execute("""
                INSERT INTO receipt_item_match (
                    receipt_id,
                    receipt_item_text_original,
                    receipt_item_text_fr,
                    receipt_price,
                    receipt_quantity,
                    receipt_unit,
                    matched_ingredient_id,
                    confidence_score,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (
                receipt_id,
                item['receipt_item_text_original'],
                item['receipt_item_text_fr'],
                item['receipt_price'],
                item.get('receipt_quantity'),
                item.get('receipt_unit'),
                item.get('matched_ingredient_id'),
                item.get('confidence_score', 0.0)
            ))
            count += 1

        # Mettre à jour le compteur total_items
        cursor.execute("""
            UPDATE receipt_upload_history
            SET total_items = ?
            WHERE id = ?
        """, (count, receipt_id))

        conn.commit()
        return count


def get_receipt_with_matches(receipt_id: int, lang: str = "fr") -> Optional[Dict]:
    """
    Récupère un ticket avec tous ses articles et les matches

    Args:
        receipt_id: ID du receipt
        lang: Langue pour les noms d'ingrédients (fr ou jp)

    Returns:
        Dict avec les infos du receipt et la liste des items matchés
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Récupérer les infos du receipt
        cursor.execute("""
            SELECT
                r.*,
                u.username
            FROM receipt_upload_history r
            LEFT JOIN user u ON r.user_id = u.id
            WHERE r.id = ?
        """, (receipt_id,))

        receipt = cursor.fetchone()
        if not receipt:
            return None

        receipt_dict = dict(receipt)

        # Récupérer les items avec leur matching
        name_col = 'ingredient_name_jp' if lang == 'jp' else 'ingredient_name_fr'
        unit_col = 'unit_jp' if lang == 'jp' else 'unit_fr'

        # Choisir la colonne de texte selon la langue
        text_col = 'receipt_item_text_fr' if lang == 'fr' else 'receipt_item_text_original'

        cursor.execute(f"""
            SELECT
                rim.id,
                rim.{text_col} as receipt_item_text,
                rim.receipt_item_text_original,
                rim.receipt_item_text_fr,
                rim.receipt_price,
                rim.receipt_quantity,
                rim.receipt_unit,
                rim.matched_ingredient_id,
                rim.confidence_score,
                rim.status,
                rim.validated_at,
                rim.notes,
                ipc.{name_col} as matched_ingredient_name,
                ipc.{unit_col} as matched_ingredient_unit,
                ipc.price_eur as catalog_price_eur,
                ipc.price_jpy as catalog_price_jpy,
                ipc.qty as catalog_qty
            FROM receipt_item_match rim
            LEFT JOIN ingredient_price_catalog ipc
                ON rim.matched_ingredient_id = ipc.id
            WHERE rim.receipt_id = ?
            ORDER BY rim.id
        """, (receipt_id,))

        items_list = [dict(row) for row in cursor.fetchall()]

        receipt_dict['matched_items_list'] = items_list
        return receipt_dict


def list_all_receipts(lang: str = "fr", limit: int = 50) -> List[Dict]:
    """
    Liste tous les tickets uploadés (les plus récents en premier)

    Args:
        lang: Langue pour l'affichage
        limit: Nombre maximum de résultats

    Returns:
        Liste des receipts avec leurs statistiques
    """
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                r.id,
                r.filename,
                r.receipt_name,
                r.store_name,
                r.receipt_date,
                r.upload_date,
                r.processed_at,
                r.status,
                r.currency,
                r.total_items,
                r.matched_items,
                r.validated_items,
                r.error_message,
                u.username,
                ROUND(CAST(r.matched_items AS REAL) / NULLIF(r.total_items, 0) * 100, 1) as match_percentage,
                ROUND(CAST(r.validated_items AS REAL) / NULLIF(r.total_items, 0) * 100, 1) as validation_percentage
            FROM receipt_upload_history r
            LEFT JOIN user u ON r.user_id = u.id
            ORDER BY r.upload_date DESC
            LIMIT ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]


def get_receipt_by_id(receipt_id: int) -> Optional[Dict]:
    """
    Récupère les informations d'un receipt par son ID

    Args:
        receipt_id: ID du receipt

    Returns:
        Dict avec les infos du receipt ou None
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                r.*,
                u.username
            FROM receipt_upload_history r
            LEFT JOIN user u ON r.user_id = u.id
            WHERE r.id = ?
        """, (receipt_id,))

        result = cursor.fetchone()
        return dict(result) if result else None


def delete_receipt(receipt_id: int) -> bool:
    """
    Supprime un ticket et tous ses items (CASCADE)

    Args:
        receipt_id: ID du receipt à supprimer

    Returns:
        True si supprimé, False sinon
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM receipt_upload_history WHERE id = ?", (receipt_id,))
        conn.commit()
        return cursor.rowcount > 0


def update_receipt_status(receipt_id: int, status: str, error_message: Optional[str] = None):
    """
    Met à jour le statut d'un receipt

    Args:
        receipt_id: ID du receipt
        status: Nouveau statut (pending, processed, error)
        error_message: Message d'erreur si applicable
    """
    with get_db() as conn:
        cursor = conn.cursor()

        if status == 'processed':
            cursor.execute("""
                UPDATE receipt_upload_history
                SET status = ?, processed_at = CURRENT_TIMESTAMP, error_message = ?
                WHERE id = ?
            """, (status, error_message, receipt_id))
        else:
            cursor.execute("""
                UPDATE receipt_upload_history
                SET status = ?, error_message = ?
                WHERE id = ?
            """, (status, error_message, receipt_id))

        conn.commit()


def validate_match(match_id: int, validated: bool = True, notes: Optional[str] = None):
    """
    Valide ou rejette un match d'ingrédient

    Args:
        match_id: ID du match
        validated: True pour valider, False pour rejeter
        notes: Notes optionnelles
    """
    with get_db() as conn:
        cursor = conn.cursor()

        new_status = 'validated' if validated else 'rejected'

        cursor.execute("""
            UPDATE receipt_item_match
            SET status = ?, validated_at = CURRENT_TIMESTAMP, notes = ?
            WHERE id = ?
        """, (new_status, notes, match_id))

        conn.commit()


def update_match_ingredient(match_id: int, new_ingredient_id: int, confidence_score: float = 1.0):
    """
    Met à jour l'ingrédient matché pour un item (correction manuelle)

    Args:
        match_id: ID du match
        new_ingredient_id: Nouvel ID d'ingrédient
        confidence_score: Score de confiance (défaut 1.0 pour match manuel)
    """
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE receipt_item_match
            SET matched_ingredient_id = ?, confidence_score = ?
            WHERE id = ?
        """, (new_ingredient_id, confidence_score, match_id))

        conn.commit()


def apply_validated_prices(receipt_id: int, currency: str = "EUR") -> int:
    """
    Applique les prix validés au catalogue des ingrédients

    Args:
        receipt_id: ID du receipt
        currency: Devise (EUR ou JPY)

    Returns:
        Nombre de prix mis à jour
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Récupérer la date du ticket
        cursor.execute("SELECT receipt_date FROM receipt_upload_history WHERE id = ?", (receipt_id,))
        receipt_date_row = cursor.fetchone()
        receipt_date = receipt_date_row['receipt_date'] if receipt_date_row else None

        # Récupérer tous les items validés
        cursor.execute("""
            SELECT
                matched_ingredient_id,
                receipt_price,
                receipt_quantity,
                receipt_unit
            FROM receipt_item_match
            WHERE receipt_id = ?
            AND status = 'validated'
            AND matched_ingredient_id IS NOT NULL
        """, (receipt_id,))

        validated_items = cursor.fetchall()
        count = 0

        for item in validated_items:
            ingredient_id = item['matched_ingredient_id']
            price = item['receipt_price']
            quantity = item['receipt_quantity'] if item['receipt_quantity'] else 1.0
            unit = item['receipt_unit']

            # Mettre à jour le catalogue
            if currency == "EUR":
                cursor.execute("""
                    UPDATE ingredient_price_catalog
                    SET price_eur = ?,
                        qty = ?,
                        price_eur_source = 'receipt',
                        price_eur_last_receipt_date = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (price, quantity, receipt_date, ingredient_id))
            else:  # JPY
                cursor.execute("""
                    UPDATE ingredient_price_catalog
                    SET price_jpy = ?,
                        qty = ?,
                        price_jpy_source = 'receipt',
                        price_jpy_last_receipt_date = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (price, quantity, receipt_date, ingredient_id))

            # Marquer l'item comme appliqué
            cursor.execute("""
                UPDATE receipt_item_match
                SET status = 'applied'
                WHERE receipt_id = ? AND matched_ingredient_id = ?
            """, (receipt_id, ingredient_id))

            count += 1

        # Marquer le receipt comme traité
        cursor.execute("""
            UPDATE receipt_upload_history
            SET status = 'processed', processed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (receipt_id,))

        conn.commit()
        return count


def get_all_catalog_ingredients_for_dropdown(lang: str = "fr") -> List[Dict]:
    """
    Récupère tous les ingrédients du catalogue pour un dropdown

    Args:
        lang: Langue (fr ou jp)

    Returns:
        Liste des ingrédients avec id et nom
    """
    with get_db() as conn:
        cursor = conn.cursor()

        name_col = 'ingredient_name_jp' if lang == 'jp' else 'ingredient_name_fr'

        cursor.execute(f"""
            SELECT id, {name_col} as name
            FROM ingredient_price_catalog
            ORDER BY {name_col}
        """)

        return [dict(row) for row in cursor.fetchall()]
