"""
Service d'extraction et d'analyse de tickets de caisse depuis des fichiers PDF
Utilise Google Gemini Vision pour l'analyse directe des PDFs
"""

import json
import logging
from typing import Dict, Optional
import google.generativeai as genai
from config import Config

logger = logging.getLogger(__name__)


class ReceiptExtractor:
    """Extracteur de tickets de caisse depuis des fichiers PDF"""

    def __init__(self):
        """Initialise l'extracteur avec Gemini Vision"""
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY non configurée - impossible d'analyser les tickets")

        genai.configure(api_key=Config.GEMINI_API_KEY)
        # Utiliser gemini-flash-latest (modèle stable et disponible)
        self.gemini_model = genai.GenerativeModel('gemini-flash-latest')
        logger.info("✅ Gemini Vision configuré pour l'analyse de tickets (modèle: gemini-flash-latest)")

    def extract_receipt_from_pdf(self, pdf_path: str, currency_hint: str = "EUR") -> Optional[Dict]:
        """
        Extrait et analyse un ticket de caisse depuis un PDF avec Gemini Vision

        Args:
            pdf_path: Chemin vers le fichier PDF
            currency_hint: Devise probable (EUR ou JPY)

        Returns:
            Dictionnaire avec les données structurées du ticket:
            {
                'store_name': str ou None,
                'date': str (YYYY-MM-DD) ou None,
                'currency': str,
                'items': [
                    {
                        'name': str,
                        'price': float,
                        'quantity': float ou None,
                        'unit': str ou None
                    }
                ]
            }
        """
        try:
            logger.info(f"Analyse du ticket PDF avec Gemini Vision (devise: {currency_hint})...")

            # Uploader le PDF vers Gemini
            uploaded_file = genai.upload_file(pdf_path)
            logger.info(f"PDF uploadé: {uploaded_file.name}")

            # Prompt pour Gemini
            prompt = f"""Analyse ce ticket de caisse et extrait les informations en JSON.

IMPORTANT:
- Extrait UNIQUEMENT les articles alimentaires (ingrédients, produits alimentaires)
- Ignore les totaux, sous-totaux, taxes, TVA, moyens de paiement
- Détecte la devise (EUR, JPY, USD, etc.) - probablement {currency_hint}
- Détecte la langue du ticket (français ou japonais)
- Pour chaque article, fournis le texte ORIGINAL du ticket ET sa traduction
- Extrait aussi: prix, quantité (si présent), unité (kg, g, L, ml, pièce)
- Extrait le nom du commerce si présent
- Extrait la date du ticket si présente (format YYYY-MM-DD)

Retourne UNIQUEMENT un objet JSON valide:
{{
  "store_name": "nom du commerce ou null",
  "date": "YYYY-MM-DD ou null",
  "currency": "{currency_hint}",
  "items": [
    {{
      "name_original": "texte EXACT tel qu'il apparaît sur le ticket",
      "name_fr": "nom en français (traduit si ticket japonais, identique si déjà français)",
      "name_jp": "nom en japonais (traduit si ticket français, identique si déjà japonais)",
      "price": prix_total_payé_en_nombre,
      "quantity": quantité_numérique_ou_null,
      "unit": "kg|g|L|ml|pièce|unité ou null"
    }}
  ]
}}

EXEMPLES:
- Si ticket français: "Carottes 1.5kg 2.85€" → {{
    "name_original": "carottes",
    "name_fr": "carotte",
    "name_jp": "にんじん",
    "price": 2.85,
    "quantity": 1.5,
    "unit": "kg"
  }}

- Si ticket japonais: "玉ねぎ 198円" → {{
    "name_original": "玉ねぎ",
    "name_fr": "oignon",
    "name_jp": "玉ねぎ",
    "price": 198,
    "quantity": null,
    "unit": null
  }}
"""

            # Générer la réponse
            response = self.gemini_model.generate_content([uploaded_file, prompt])

            # Nettoyer la réponse (enlever les éventuels markdown)
            content = response.text.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            logger.info(f"Réponse Gemini reçue ({len(content)} caractères)")

            # Parser le JSON
            receipt_data = json.loads(content)

            # Validation basique
            if not isinstance(receipt_data.get('items'), list):
                logger.error("Format invalide: 'items' doit être une liste")
                return None

            # Nettoyer les items
            valid_items = []
            for item in receipt_data.get('items', []):
                # Vérifier les champs requis (au moins name_original et price)
                if not item.get('name_original') or not item.get('price'):
                    continue

                valid_items.append({
                    'name_original': item['name_original'].strip(),
                    'name_fr': item.get('name_fr', '').strip() if item.get('name_fr') else item['name_original'].strip(),
                    'name_jp': item.get('name_jp', '').strip() if item.get('name_jp') else item['name_original'].strip(),
                    'price': float(item['price']),
                    'quantity': float(item['quantity']) if item.get('quantity') else None,
                    'unit': item.get('unit', '').strip() if item.get('unit') else None
                })

            receipt_data['items'] = valid_items

            logger.info(f"✓ Ticket analysé: {len(valid_items)} articles extraits")
            if receipt_data.get('store_name'):
                logger.info(f"  Commerce: {receipt_data['store_name']}")
            if receipt_data.get('date'):
                logger.info(f"  Date: {receipt_data['date']}")

            return receipt_data

        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON: {e}")
            logger.error(f"Contenu reçu: {content[:500] if 'content' in locals() else 'N/A'}")
            return None
        except Exception as e:
            logger.error(f"Erreur Gemini Vision: {e}", exc_info=True)
            return None


# Instance singleton
_extractor = None


def get_receipt_extractor() -> ReceiptExtractor:
    """Retourne l'instance singleton du receipt extractor"""
    global _extractor
    if _extractor is None:
        _extractor = ReceiptExtractor()
    return _extractor
