"""
Service de matching intelligent entre les articles de tickets de caisse
et les ingrédients du catalogue
"""

import logging
from typing import Dict, List, Optional, Tuple
from app.models.db_core import get_db, normalize_ingredient_name
from groq import Groq
import os
import json

logger = logging.getLogger(__name__)


class IngredientMatcher:
    """Matcher intelligent pour associer les articles du ticket aux ingrédients du catalogue"""

    def __init__(self):
        """Initialise le matcher avec le client Groq pour l'IA"""
        api_key = os.getenv("GROQ_API_KEY")
        self.groq_client = Groq(api_key=api_key) if api_key else None

    def get_all_catalog_ingredients(self) -> List[Dict]:
        """
        Récupère tous les ingrédients du catalogue pour le matching

        Returns:
            Liste des ingrédients avec id, nom_fr, nom_jp
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ingredient_name_fr, ingredient_name_jp
                FROM ingredient_price_catalog
                ORDER BY ingredient_name_fr
            """)
            return [dict(row) for row in cursor.fetchall()]

    def fuzzy_match_exact(self, receipt_item_name: str, catalog_ingredients: List[Dict]) -> Optional[Tuple[int, float]]:
        """
        Matching strict basé sur la normalisation des noms
        1. Match exact complet (100%)
        2. Match sur le premier mot (100%)

        Exemples:
        - "Poireau" = "Poireau" → 100%
        - "Poireau (ou Ail)" → premier mot "poireau" = "Poireau" → 100%
        - "Carotte bio" → premier mot "carotte" = "Carotte" → 100%
        - "Tomate ronde" → premier mot "tomate" = "Tomate" → 100%

        Args:
            receipt_item_name: Nom de l'article sur le ticket
            catalog_ingredients: Liste des ingrédients du catalogue

        Returns:
            Tuple (ingredient_id, score) ou None si pas de match
        """
        normalized_receipt = normalize_ingredient_name(receipt_item_name)

        # Extraire le premier mot (séparé par espace, parenthèse, virgule, etc.)
        first_word_receipt = normalized_receipt.split()[0] if normalized_receipt.split() else ""

        for ing in catalog_ingredients:
            normalized_fr = normalize_ingredient_name(ing['ingredient_name_fr'])
            normalized_jp = normalize_ingredient_name(ing['ingredient_name_jp']) if ing['ingredient_name_jp'] else ""

            # Match exact complet
            if normalized_receipt == normalized_fr or normalized_receipt == normalized_jp:
                return (ing['id'], 1.0)

            # Match sur le premier mot
            # Ex: "carotte bio" → "carotte" = "carotte" du catalogue
            if first_word_receipt and (first_word_receipt == normalized_fr or first_word_receipt == normalized_jp):
                return (ing['id'], 1.0)

        return None

    def ai_match(self, receipt_item_name: str, catalog_ingredients: List[Dict], lang: str = "fr") -> Optional[Tuple[int, float]]:
        """
        Matching assisté par IA pour les cas complexes

        Args:
            receipt_item_name: Nom de l'article sur le ticket
            catalog_ingredients: Liste des ingrédients du catalogue
            lang: Langue de travail (fr ou jp)

        Returns:
            Tuple (ingredient_id, score) ou None si pas de match
        """
        if not self.groq_client:
            logger.warning("Client Groq non disponible pour le matching IA")
            return None

        # Limiter à 50 ingrédients les plus probables pour ne pas surcharger le prompt
        catalog_sample = catalog_ingredients[:50]

        # Créer une liste des ingrédients pour le prompt
        if lang == "jp":
            catalog_list = "\n".join([f"- {ing['id']}: {ing['ingredient_name_jp']}" for ing in catalog_sample])
        else:
            catalog_list = "\n".join([f"- {ing['id']}: {ing['ingredient_name_fr']}" for ing in catalog_sample])

        prompt = f"""Tu es un expert en identification d'ingrédients alimentaires.

Article sur le ticket de caisse: "{receipt_item_name}"

Voici les ingrédients disponibles dans le catalogue:
{catalog_list}

TÂCHE:
1. Trouve l'ingrédient du catalogue qui correspond le mieux à l'article du ticket
2. Évalue la confiance de ton match sur une échelle de 0.0 à 1.0:
   - 1.0 = match parfait, certain
   - 0.8-0.9 = très probable
   - 0.6-0.7 = probable
   - 0.4-0.5 = possible mais incertain
   - < 0.4 = pas de match fiable

3. Si aucun ingrédient ne correspond de manière fiable (score < 0.4), retourne null

Retourne UNIQUEMENT un objet JSON valide (sans texte avant ou après):
{{
  "ingredient_id": ID de l'ingrédient ou null,
  "confidence": score entre 0.0 et 1.0,
  "reason": "courte explication du match"
}}

EXEMPLES:
- "Carottes bio" → {{"ingredient_id": 12, "confidence": 0.95, "reason": "match direct avec carotte"}}
- "Lait demi-écrémé" → {{"ingredient_id": 45, "confidence": 0.90, "reason": "correspond à lait"}}
- "Coca-Cola" → {{"ingredient_id": null, "confidence": 0.0, "reason": "pas un ingrédient alimentaire"}}
"""

        try:
            logger.info(f"Requête IA pour matcher: {receipt_item_name}")

            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "Tu es un assistant spécialisé dans l'identification d'ingrédients. Tu retournes UNIQUEMENT du JSON valide."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=500
            )

            content = response.choices[0].message.content.strip()

            # Nettoyer la réponse
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            # Parser le JSON
            result = json.loads(content)

            ingredient_id = result.get('ingredient_id')
            confidence = result.get('confidence', 0.0)

            if ingredient_id and confidence >= 0.4:
                logger.info(f"Match IA trouvé: ID={ingredient_id}, confiance={confidence:.2f}")
                return (ingredient_id, confidence)
            else:
                logger.info(f"Pas de match IA fiable: confiance={confidence:.2f}")
                return None

        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON du matching IA: {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors du matching IA: {e}")
            return None

    def match_receipt_item(self, receipt_item_name: str, lang: str = "fr") -> Dict:
        """
        Trouve le meilleur match pour un article de ticket
        Utilise uniquement un matching exact - si pas de match, retourne None
        L'utilisateur fera le lien manuellement

        Args:
            receipt_item_name: Nom de l'article sur le ticket
            lang: Langue de travail (fr ou jp)

        Returns:
            Dict avec:
            - matched_ingredient_id: ID de l'ingrédient ou None
            - confidence_score: Score de confiance (1.0 si match exact, 0.0 sinon)
            - method: 'exact' ou 'none'
        """
        catalog_ingredients = self.get_all_catalog_ingredients()

        # Match exact uniquement
        exact_match = self.fuzzy_match_exact(receipt_item_name, catalog_ingredients)
        if exact_match:
            ingredient_id, score = exact_match
            return {
                'matched_ingredient_id': ingredient_id,
                'confidence_score': score,
                'method': 'exact'
            }

        # Pas de match trouvé - l'utilisateur fera le lien manuellement
        return {
            'matched_ingredient_id': None,
            'confidence_score': 0.0,
            'method': 'none'
        }

    def match_all_items(self, receipt_items: List[Dict], lang: str = "fr") -> List[Dict]:
        """
        Matche tous les articles d'un ticket avec le catalogue

        Args:
            receipt_items: Liste des items du ticket avec name_original, name_fr, name_jp, price, quantity, unit
            lang: Langue de travail

        Returns:
            Liste des items enrichis avec matched_ingredient_id et confidence_score
        """
        results = []

        for item in receipt_items:
            # Choisir le nom à utiliser pour le matching selon la langue
            match_name = item.get('name_fr', item['name_original']) if lang == 'fr' else item.get('name_jp', item['name_original'])

            match_result = self.match_receipt_item(match_name, lang)

            results.append({
                'receipt_item_text_original': item['name_original'],
                'receipt_item_text_fr': item.get('name_fr', item['name_original']),
                'receipt_price': item['price'],
                'receipt_quantity': item.get('quantity'),
                'receipt_unit': item.get('unit'),
                'matched_ingredient_id': match_result['matched_ingredient_id'],
                'confidence_score': match_result['confidence_score'],
                'match_method': match_result['method']
            })

            logger.info(
                f"Item '{item['name_original']}' → "
                f"{'ID ' + str(match_result['matched_ingredient_id']) if match_result['matched_ingredient_id'] else 'AUCUN MATCH'} "
                f"(confiance: {match_result['confidence_score']:.2f}, méthode: {match_result['method']})"
            )

        return results


# Instance singleton
_matcher = None


def get_ingredient_matcher() -> IngredientMatcher:
    """Retourne l'instance singleton du ingredient matcher"""
    global _matcher
    if _matcher is None:
        _matcher = IngredientMatcher()
    return _matcher
