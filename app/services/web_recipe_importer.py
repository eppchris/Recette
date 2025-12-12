"""
Service d'importation de recettes depuis une URL web
Utilise l'IA (Groq) pour extraire intelligemment les informations
"""

import requests
from bs4 import BeautifulSoup
import json
from typing import Optional, Dict, Any
from groq import Groq


class WebRecipeImporter:
    """Importateur de recettes depuis URL avec IA"""

    def __init__(self, groq_api_key: str):
        self.client = Groq(api_key=groq_api_key) if groq_api_key else None

    def fetch_page_content(self, url: str) -> str:
        """
        Récupère le contenu HTML d'une page web

        Args:
            url: URL de la page contenant la recette

        Returns:
            Contenu texte de la page
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parser le HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Supprimer les scripts et styles
            for script in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                script.decompose()

            # Extraire le texte
            text = soup.get_text(separator='\n', strip=True)

            # Nettoyer le texte
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n'.join(lines)

            # Limiter à ~10000 caractères pour ne pas surcharger l'IA
            if len(text) > 10000:
                text = text[:10000] + "\n...[contenu tronqué]"

            return text

        except requests.RequestException as e:
            raise Exception(f"Erreur lors de la récupération de la page: {str(e)}")

    def extract_recipe_with_ai(self, page_content: str, target_lang: str = 'fr') -> Dict[str, Any]:
        """
        Utilise l'IA pour extraire les informations de recette

        Args:
            page_content: Contenu texte de la page
            target_lang: Langue cible ('fr' ou 'jp')

        Returns:
            Dictionnaire avec les informations de la recette
        """
        if not self.client:
            raise Exception("Clé API Groq non configurée")

        lang_name = "français" if target_lang == 'fr' else "japonais"

        prompt = f"""Tu es un expert en extraction de recettes culinaires.
Analyse le contenu de page web suivant et extrais les informations de la recette.

IMPORTANT: La recette finale doit être en {lang_name}.
Si la recette source est dans une autre langue, traduis-la en {lang_name}.

Retourne un JSON avec cette structure EXACTE:
{{
  "name": "Nom de la recette",
  "description": "Description courte (1-2 phrases)",
  "servings": 4,
  "prep_time": 15,
  "cook_time": 30,
  "recipe_type": "plat",
  "country": "France",
  "ingredients": [
    {{"quantity": 200, "unit": "g", "name": "farine", "notes": ""}},
    {{"quantity": 2, "unit": "", "name": "œufs", "notes": ""}},
    {{"quantity": 250, "unit": "ml", "name": "lait", "notes": ""}}
  ],
  "steps": [
    "Préchauffer le four à 180°C.",
    "Mélanger les ingrédients secs.",
    "Incorporer les œufs et le lait."
  ]
}}

RÈGLES IMPORTANTES:
- Si une information n'est pas trouvée, utilise des valeurs par défaut raisonnables
- Les quantités doivent être des NOMBRES (utilise 0 si non spécifié)
- Les unités courantes: g, kg, ml, L, c. à soupe, c. à café, pincée, tranche, etc.
- Les étapes doivent être claires et numérotées
- Traduis TOUT en {lang_name} si nécessaire
- recipe_type doit être l'un de: apéritif, entrée, plat, dessert, autre
- country: nom du pays d'origine de la recette

CONTENU DE LA PAGE:
{page_content}

Réponds UNIQUEMENT avec le JSON, sans texte avant ou après."""

        try:
            # Appel à l'API Groq
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Tu es un assistant expert en extraction de recettes culinaires. Tu réponds toujours avec du JSON valide."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=2000
            )

            # Extraire la réponse
            response_text = chat_completion.choices[0].message.content.strip()

            # Nettoyer la réponse (enlever les markdown si présents)
            response_text = response_text.replace('```json', '').replace('```', '').strip()

            # Parser le JSON
            recipe_data = json.loads(response_text)

            return recipe_data

        except json.JSONDecodeError as e:
            raise Exception(f"Erreur de parsing JSON: {str(e)}\nRéponse: {response_text[:500]}")
        except Exception as e:
            raise Exception(f"Erreur lors de l'extraction IA: {str(e)}")

    def import_recipe(self, url: str, target_lang: str = 'fr') -> Dict[str, Any]:
        """
        Importe une recette complète depuis une URL

        Args:
            url: URL de la page contenant la recette
            target_lang: Langue cible ('fr' ou 'jp')

        Returns:
            Données de la recette extraites
        """
        # Étape 1: Récupérer le contenu de la page
        page_content = self.fetch_page_content(url)

        # Étape 2: Extraire la recette avec l'IA
        recipe_data = self.extract_recipe_with_ai(page_content, target_lang)

        # Étape 3: Ajouter l'URL source
        recipe_data['source_url'] = url

        # Étape 4: Valider et nettoyer les données
        recipe_data = self._validate_recipe_data(recipe_data)

        return recipe_data

    def _validate_recipe_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide et nettoie les données de recette

        Args:
            data: Données brutes de la recette

        Returns:
            Données validées et nettoyées
        """
        # Valeurs par défaut
        validated = {
            'name': data.get('name', 'Recette importée'),
            'description': data.get('description', ''),
            'servings': int(data.get('servings', 4)),
            'prep_time': int(data.get('prep_time', 0)),
            'cook_time': int(data.get('cook_time', 0)),
            'recipe_type': data.get('recipe_type', 'autre'),
            'country': data.get('country', 'France'),
            'source_url': data.get('source_url', ''),
            'ingredients': [],
            'steps': []
        }

        # Valider recipe_type
        valid_types = ['apéritif', 'entrée', 'plat', 'dessert', 'autre']
        if validated['recipe_type'].lower() not in valid_types:
            validated['recipe_type'] = 'autre'

        # Valider les ingrédients
        for ing in data.get('ingredients', []):
            if isinstance(ing, dict) and 'name' in ing:
                try:
                    quantity = float(ing.get('quantity', 0))
                except (ValueError, TypeError):
                    quantity = 0

                validated['ingredients'].append({
                    'quantity': quantity,
                    'unit': str(ing.get('unit', '')),
                    'name': str(ing.get('name', '')),
                    'notes': str(ing.get('notes', ''))
                })

        # Valider les étapes
        for step in data.get('steps', []):
            if isinstance(step, str) and step.strip():
                validated['steps'].append(step.strip())

        # Si pas d'ingrédients ou d'étapes, lever une erreur
        if not validated['ingredients']:
            raise Exception("Aucun ingrédient trouvé dans la recette")
        if not validated['steps']:
            raise Exception("Aucune étape de préparation trouvée")

        return validated


# Instance globale (sera initialisée avec la clé API)
_web_importer_instance: Optional[WebRecipeImporter] = None


def init_web_recipe_importer(groq_api_key: str):
    """Initialise l'importateur de recettes web"""
    global _web_importer_instance
    _web_importer_instance = WebRecipeImporter(groq_api_key)


def get_web_recipe_importer() -> WebRecipeImporter:
    """Récupère l'instance de l'importateur web"""
    if _web_importer_instance is None:
        raise Exception("L'importateur de recettes web n'est pas initialisé")
    return _web_importer_instance
