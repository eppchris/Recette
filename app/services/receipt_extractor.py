"""
Service d'extraction et d'analyse de tickets de caisse depuis des fichiers PDF
Utilise l'API REST de Google Gemini Vision (pas de dépendance google-generativeai)
"""

import json
import logging
import base64
import mimetypes
from typing import Dict, Optional, Tuple
from pathlib import Path
import requests
import time
from config import Config

logger = logging.getLogger(__name__)


class ReceiptExtractor:
    """Extracteur de tickets de caisse depuis des fichiers PDF"""

    def __init__(self):
        """Initialise l'extracteur avec Gemini Vision API REST"""
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY non configurée - impossible d'analyser les tickets")

        self.api_key = Config.GEMINI_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        # Utiliser gemini-1.5-flash (quota gratuit: 15 requêtes/minute, 1500/jour)
        self.model = "gemini-1.5-flash"
        logger.info(f"✅ Gemini Vision API REST configurée (modèle: {self.model})")

    def _encode_file_to_base64(self, file_path: str) -> Tuple[str, str]:
        """
        Encode un fichier en base64 pour l'API Gemini

        Returns:
            Tuple (mime_type, base64_data)
        """
        path = Path(file_path)
        mime_type = mimetypes.guess_type(file_path)[0] or 'application/pdf'

        with open(file_path, 'rb') as f:
            file_data = f.read()
            base64_data = base64.b64encode(file_data).decode('utf-8')

        return mime_type, base64_data

    def extract_receipt_from_pdf(self, pdf_path: str, currency_hint: str = "EUR") -> Optional[Dict]:
        """
        Extrait et analyse un ticket de caisse depuis un PDF avec Gemini Vision API REST

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
            logger.info(f"Analyse du ticket PDF avec Gemini Vision API REST (devise: {currency_hint})...")

            # Encoder le PDF en base64
            mime_type, base64_data = self._encode_file_to_base64(pdf_path)
            logger.info(f"PDF encodé ({mime_type}, {len(base64_data)} caractères base64)")

            # Prompt pour Gemini
            prompt_text = f"""Analyse ce ticket de caisse et extrait les informations en JSON.

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

            # Construire la requête pour l'API REST
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt_text},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64_data
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.1,  # Faible température pour plus de précision
                    "topK": 32,
                    "topP": 1,
                    "maxOutputTokens": 2048,
                }
            }

            # Appel API REST
            logger.info("Envoi de la requête à Gemini API REST...")
            response = requests.post(url, json=payload, timeout=60)

            # Gestion du quota dépassé (429)
            if response.status_code == 429:
                logger.warning("Quota dépassé (429), retry dans 60 secondes...")
                time.sleep(60)
                response = requests.post(url, json=payload, timeout=60)

            response.raise_for_status()

            result = response.json()

            # Extraire le texte de la réponse
            if 'candidates' not in result or not result['candidates']:
                logger.error("Aucun candidat dans la réponse Gemini")
                return None

            content = result['candidates'][0]['content']['parts'][0]['text']

            # Nettoyer la réponse (enlever les éventuels markdown)
            content = content.strip()
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
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur requête API Gemini: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Réponse API: {e.response.text[:500]}")
            return None
        except Exception as e:
            logger.error(f"Erreur Gemini Vision API REST: {e}", exc_info=True)
            return None


# Instance singleton
_extractor = None


def get_receipt_extractor() -> ReceiptExtractor:
    """Retourne l'instance singleton du receipt extractor"""
    global _extractor
    if _extractor is None:
        _extractor = ReceiptExtractor()
    return _extractor
