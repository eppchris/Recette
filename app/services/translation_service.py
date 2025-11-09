# app/services/translation_service.py
"""Service de traduction utilisant l'API Groq"""

import os
from typing import Optional, List, Dict
from groq import Groq
import json

class TranslationService:
    """Service pour traduire des recettes via l'API Groq"""

    def __init__(self, api_key: str):
        """Initialise le client Groq

        Args:
            api_key: Clé API Groq
        """
        self.client = Groq(api_key=api_key)
        # Utilisation d'un modèle rapide et performant pour la traduction
        self.model = "llama-3.3-70b-versatile"

    def check_api_status(self) -> bool:
        """Vérifie si l'API Groq est opérationnelle

        Returns:
            True si l'API répond, False sinon
        """
        try:
            # Test simple avec une requête minimaliste
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": "ping"}],
                model=self.model,
                max_tokens=5
            )
            return True
        except Exception as e:
            print(f"Erreur lors de la vérification de l'API Groq: {e}")
            return False

    def translate_recipe_title(self, title: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Traduit le titre d'une recette

        Args:
            title: Titre à traduire
            source_lang: Langue source (fr ou jp)
            target_lang: Langue cible (fr ou jp)

        Returns:
            Titre traduit ou None en cas d'erreur
        """
        lang_names = {"fr": "français", "jp": "japonais"}

        try:
            prompt = f"""Traduis uniquement ce titre de recette du {lang_names[source_lang]} vers le {lang_names[target_lang]}.
Réponds UNIQUEMENT avec la traduction, sans aucune explication ou formatage.

Titre: {title}"""

            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=100
            )

            translated = response.choices[0].message.content.strip()
            return translated

        except Exception as e:
            print(f"Erreur lors de la traduction du titre: {e}")
            return None

    def translate_ingredients(
        self,
        ingredients: List[Dict[str, any]],
        source_lang: str,
        target_lang: str
    ) -> Optional[List[Dict[str, str]]]:
        """Traduit une liste d'ingrédients

        Args:
            ingredients: Liste de dictionnaires avec 'name' et 'unit'
            source_lang: Langue source (fr ou jp)
            target_lang: Langue cible (fr ou jp)

        Returns:
            Liste de dictionnaires avec 'name' traduit et 'unit' copié, ou None en cas d'erreur
        """
        if not ingredients:
            return []

        lang_names = {"fr": "français", "jp": "japonais"}

        # Prépare la liste des noms d'ingrédients
        ingredient_names = [ing['name'] for ing in ingredients]

        try:
            # Format JSON pour une traduction structurée
            prompt = f"""Traduis cette liste d'ingrédients de recette du {lang_names[source_lang]} vers le {lang_names[target_lang]}.
Réponds UNIQUEMENT avec un tableau JSON contenant les traductions dans le même ordre.
Format attendu: ["traduction1", "traduction2", ...]

Ingrédients à traduire:
{json.dumps(ingredient_names, ensure_ascii=False)}"""

            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=1000
            )

            # Parse la réponse JSON
            translated_names = json.loads(response.choices[0].message.content.strip())

            # Combine les traductions avec les unités originales
            result = []
            for i, ing in enumerate(ingredients):
                result.append({
                    'name': translated_names[i],
                    'unit': ing['unit']  # Copie à l'identique
                })

            return result

        except Exception as e:
            print(f"Erreur lors de la traduction des ingrédients: {e}")
            return None

    def translate_steps(
        self,
        steps: List[str],
        source_lang: str,
        target_lang: str
    ) -> Optional[List[str]]:
        """Traduit une liste d'étapes de recette

        Args:
            steps: Liste des textes d'étapes à traduire
            source_lang: Langue source (fr ou jp)
            target_lang: Langue cible (fr ou jp)

        Returns:
            Liste des étapes traduites ou None en cas d'erreur
        """
        if not steps:
            return []

        lang_names = {"fr": "français", "jp": "japonais"}

        try:
            # Format JSON pour une traduction structurée
            prompt = f"""Traduis ces étapes de recette du {lang_names[source_lang]} vers le {lang_names[target_lang]}.
Réponds UNIQUEMENT avec un tableau JSON contenant les traductions dans le même ordre.
Format attendu: ["traduction étape 1", "traduction étape 2", ...]

Étapes à traduire:
{json.dumps(steps, ensure_ascii=False)}"""

            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=2000
            )

            # Parse la réponse JSON
            translated_steps = json.loads(response.choices[0].message.content.strip())

            return translated_steps

        except Exception as e:
            print(f"Erreur lors de la traduction des étapes: {e}")
            return None


# Instance globale (sera initialisée dans main.py)
translation_service: Optional[TranslationService] = None


def init_translation_service(api_key: str):
    """Initialise le service de traduction global

    Args:
        api_key: Clé API Groq
    """
    global translation_service
    translation_service = TranslationService(api_key)


def get_translation_service() -> Optional[TranslationService]:
    """Retourne l'instance du service de traduction

    Returns:
        TranslationService ou None si non initialisé
    """
    return translation_service
