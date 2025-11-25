"""
Service d'extraction et d'analyse de recettes depuis des fichiers PDF
Utilise PyPDF2 pour l'extraction de texte et Groq pour l'analyse IA
"""

import PyPDF2
import json
import logging
from typing import Dict, Optional
from groq import Groq
import os

logger = logging.getLogger(__name__)


class PDFRecipeExtractor:
    """Extracteur de recettes depuis des fichiers PDF"""

    def __init__(self):
        """Initialise l'extracteur avec le client Groq"""
        api_key = os.getenv("GROQ_API_KEY")
        self.groq_client = Groq(api_key=api_key) if api_key else None

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extrait le texte brut d'un fichier PDF

        Args:
            pdf_path: Chemin vers le fichier PDF

        Returns:
            Texte extrait du PDF
        """
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"

            logger.info(f"Texte extrait du PDF ({len(text)} caractères)")
            return text.strip()

        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du PDF: {e}")
            raise

    def analyze_recipe_with_ai(self, text: str, target_lang: str = "fr") -> Optional[Dict]:
        """
        Analyse le texte de la recette avec l'IA Groq pour extraire les informations structurées

        Args:
            text: Texte brut de la recette
            target_lang: Langue cible ('fr' ou 'jp')

        Returns:
            Dictionnaire avec les données structurées de la recette
        """
        if not self.groq_client:
            logger.error("Client Groq non initialisé")
            return None

        prompt = f"""Tu es un expert en extraction de recettes de cuisine. Analyse le texte suivant et extrait les informations de manière structurée.

IMPORTANT:
- Détecte automatiquement la langue du texte (français ou japonais)
- Si la langue détectée est différente de '{target_lang}', garde la langue d'origine
- Extrait UNIQUEMENT les informations présentes dans le texte
- Ne crée PAS d'informations fictives
- Si une information n'est pas trouvée, utilise null

Texte de la recette:
{text}

Retourne UNIQUEMENT un objet JSON valide avec cette structure exacte (sans texte avant ou après):
{{
  "name": "nom de la recette",
  "detected_language": "fr ou jp",
  "servings": nombre de personnes ou null,
  "recipe_type": "PRO, PERSO, MASTER ou null",
  "ingredients": [
    {{
      "name": "nom de l'ingrédient",
      "quantity": quantité numérique ou null,
      "unit": "unité (g, kg, ml, L, cs, cc, pièce, etc.) ou null",
      "notes": "commentaire optionnel ou null"
    }}
  ],
  "steps": [
    "étape 1 de préparation",
    "étape 2 de préparation"
  ],
  "country": "pays d'origine de la recette ou null"
}}"""

        try:
            logger.info("Envoi de la requête à Groq pour analyse...")

            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "Tu es un assistant spécialisé dans l'extraction de recettes de cuisine. Tu retournes UNIQUEMENT du JSON valide, sans aucun texte supplémentaire."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=4000
            )

            # Extraire le contenu de la réponse
            content = response.choices[0].message.content.strip()

            # Nettoyer la réponse (enlever les éventuels markdown)
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            # Parser le JSON
            recipe_data = json.loads(content)

            logger.info(f"Recette analysée avec succès: {recipe_data.get('name', 'Sans nom')}")
            return recipe_data

        except json.JSONDecodeError as e:
            logger.error(f"Erreur de parsing JSON: {e}")
            logger.error(f"Contenu reçu: {content}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse IA: {e}")
            return None

    def extract_recipe_from_pdf(self, pdf_path: str, target_lang: str = "fr") -> Optional[Dict]:
        """
        Extrait et analyse une recette complète depuis un PDF

        Args:
            pdf_path: Chemin vers le fichier PDF
            target_lang: Langue cible ('fr' ou 'jp')

        Returns:
            Dictionnaire avec les données structurées de la recette
        """
        # 1. Extraire le texte du PDF
        text = self.extract_text_from_pdf(pdf_path)

        if not text:
            logger.error("Aucun texte extrait du PDF")
            return None

        # 2. Analyser avec l'IA
        recipe_data = self.analyze_recipe_with_ai(text, target_lang)

        return recipe_data


# Instance singleton
_extractor = None


def get_pdf_extractor() -> PDFRecipeExtractor:
    """Retourne l'instance singleton du PDF extractor"""
    global _extractor
    if _extractor is None:
        _extractor = PDFRecipeExtractor()
    return _extractor
