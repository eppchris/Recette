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
            ingredients: Liste de dictionnaires avec 'name', 'unit' et optionnellement 'notes'
            source_lang: Langue source (fr ou jp)
            target_lang: Langue cible (fr ou jp)

        Returns:
            Liste de dictionnaires avec 'name' et 'notes' traduits, 'unit' copié, ou None en cas d'erreur
        """
        if not ingredients:
            return []

        lang_names = {"fr": "français", "jp": "japonais"}

        # Prépare les données à traduire (nom et notes si présentes)
        items_to_translate = []
        for ing in ingredients:
            item = {'name': ing['name']}
            if ing.get('notes'):
                item['notes'] = ing['notes']
            items_to_translate.append(item)

        try:
            # Format JSON pour une traduction structurée
            prompt = f"""Traduis ces ingrédients de recette du {lang_names[source_lang]} vers le {lang_names[target_lang]}.

IMPORTANT: Réponds UNIQUEMENT avec un tableau JSON valide, sans texte avant ou après.
Format EXACT requis: [{{"name": "traduction"}}, {{"name": "traduction", "notes": "notes si présentes"}}]

Règles:
1. Chaque objet doit avoir au minimum la clé "name" avec la traduction
2. Ajoute la clé "notes" SEULEMENT si l'ingrédient original a des notes
3. Assure-toi que tous les objets JSON sont complets avec guillemets et virgules
4. Ne mets AUCUN texte explicatif, juste le JSON

Ingrédients à traduire:
{json.dumps(items_to_translate, ensure_ascii=False)}"""

            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=1500
            )

            # Nettoyer la réponse et parser le JSON
            import re
            response_text = response.choices[0].message.content.strip()

            # Si la réponse contient des blocs de code markdown, extraire juste le JSON
            if '```' in response_text:
                match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_text, re.DOTALL)
                if match:
                    response_text = match.group(1)

            # Supprimer les caractères de contrôle invalides
            response_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', response_text)

            try:
                translated_items = json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"Erreur JSON initiale: {e}")
                print(f"Réponse brute: {response_text[:800]}")

                # Tentative de récupération manuelle par extraction de patterns
                # Chercher tous les objets bien formés avec name et optionnellement notes
                objects = re.findall(
                    r'\{\s*"name"\s*:\s*"([^"]+)"(?:\s*,\s*"notes"\s*:\s*"([^"]*)")?\s*\}',
                    response_text
                )

                if objects:
                    translated_items = []
                    for name, notes in objects:
                        item = {"name": name}
                        if notes:
                            item["notes"] = notes
                        translated_items.append(item)
                    print(f"✓ Récupération manuelle: {len(translated_items)} ingrédients extraits")
                else:
                    # Si aucun objet valide trouvé, essayer une extraction plus permissive
                    # Chercher des paires "name": "valeur" même si l'objet est incomplet
                    names = re.findall(r'"name"\s*:\s*"([^"]+)"', response_text)
                    if names:
                        translated_items = [{"name": name} for name in names]
                        print(f"✓ Récupération partielle: {len(translated_items)} noms extraits")
                    else:
                        # Échec total
                        raise ValueError(f"Impossible de parser la réponse JSON. Erreur: {e}")

            # Combine les traductions avec les unités originales
            result = []
            for i, ing in enumerate(ingredients):
                result.append({
                    'name': translated_items[i]['name'],
                    'unit': ing['unit'],  # Copie à l'identique
                    'notes': translated_items[i].get('notes', '')  # Notes traduites ou vide
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

            # Nettoyer la réponse et parser le JSON
            import re
            response_text = response.choices[0].message.content.strip()

            # Si la réponse contient des blocs de code markdown, extraire juste le JSON
            if '```' in response_text:
                match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_text, re.DOTALL)
                if match:
                    response_text = match.group(1)

            # Supprimer les caractères de contrôle invalides
            response_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', response_text)

            # Réparer les erreurs JSON courantes de l'API (plusieurs passes)
            for _ in range(3):  # Plusieurs passes pour traiter les cas complexes
                # 1. Ajouter virgules manquantes entre éléments
                response_text = re.sub(r'"(\s*)"', r'",\1"', response_text)
                # 2. Fixer les chaînes non terminées avant ]
                response_text = re.sub(r'([^",])\]', r'\1"]', response_text)
                # 3. Éviter de doubler les guillemets
                response_text = re.sub(r'""([,\]])', r'"\1', response_text)

            try:
                translated_steps = json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"Erreur JSON: {e}")
                print(f"Réponse brute (après nettoyage): {response_text[:800]}")
                raise

            return translated_steps

        except Exception as e:
            print(f"Erreur lors de la traduction des étapes: {e}")
            return None

    def determine_ingredient_is_liquid(self, ingredient_name_fr: str, ingredient_name_jp: str = None) -> Optional[bool]:
        """Détermine si un ingrédient est liquide ou solide via l'IA

        Args:
            ingredient_name_fr: Nom de l'ingrédient en français
            ingredient_name_jp: Nom de l'ingrédient en japonais (optionnel)

        Returns:
            True si liquide, False si solide, None en cas d'erreur
        """
        try:
            # Construire le contexte avec les deux langues si disponible
            ingredient_info = ingredient_name_fr
            if ingredient_name_jp:
                ingredient_info += f" ({ingredient_name_jp})"

            prompt = f"""Détermine si cet ingrédient est un LIQUIDE ou un SOLIDE en cuisine.

Ingrédient: {ingredient_info}

Règles:
- LIQUIDE: eau, huile, lait, sauce, vinaigre, jus, bouillon, crème liquide, mirin, saké, etc.
- SOLIDE: sucre, sel, farine, riz, viande, légumes, fromage, beurre, crème épaisse, etc.
- Pour les cas ambigus (beurre, crème), considère l'état à température ambiante

Réponds UNIQUEMENT avec un mot: "LIQUIDE" ou "SOLIDE"."""

            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.1,  # Très faible pour cohérence
                max_tokens=10
            )

            result = response.choices[0].message.content.strip().upper()

            if "LIQUIDE" in result:
                return True
            elif "SOLIDE" in result:
                return False
            else:
                print(f"Réponse inattendue de l'IA pour {ingredient_name_fr}: {result}")
                return None

        except Exception as e:
            print(f"Erreur lors de la détermination liquide/solide pour {ingredient_name_fr}: {e}")
            return None

    def determine_ingredient_category(self, ingredient_name_fr: str, ingredient_name_jp: str = None, unit_fr: str = None) -> Optional[str]:
        """Détermine la catégorie de conversion d'un ingrédient via l'IA

        Args:
            ingredient_name_fr: Nom de l'ingrédient en français
            ingredient_name_jp: Nom de l'ingrédient en japonais (optionnel)
            unit_fr: Unité de mesure en français (optionnel, aide à la décision)

        Returns:
            'volume', 'poids' ou 'unite', None en cas d'erreur
        """
        try:
            # Construire le contexte avec les deux langues si disponible
            ingredient_info = ingredient_name_fr
            if ingredient_name_jp:
                ingredient_info += f" ({ingredient_name_jp})"
            if unit_fr:
                ingredient_info += f" [unité: {unit_fr}]"

            prompt = f"""Détermine la catégorie de conversion pour cet ingrédient culinaire.

Ingrédient: {ingredient_info}

Catégories possibles:
1. VOLUME - Liquides et ingrédients mesurés au volume
   Exemples: eau, huile, lait, sauce, vinaigre, jus, bouillon, crème liquide, mirin, saké, sirop

2. POIDS - Solides mesurés au poids
   Exemples: sucre, sel, farine, riz, viande, légumes, fromage, beurre, pâte, poudre

3. UNITE - Ingrédients vendus/comptés à l'unité
   Exemples: oeuf/œuf, sachet, feuille, gousse, cube, bouillon cube, paquet, tranche, boîte

Règles de décision:
- Si l'unité contient "sachet", "feuille", "gousse", "cube", "paquet" → UNITE
- Si c'est "oeuf" ou "œuf" → UNITE
- Si c'est un liquide qui coule → VOLUME
- Si c'est un solide mesuré au poids (même en poudre) → POIDS
- En cas de doute entre POIDS et VOLUME pour un solide → POIDS

Réponds UNIQUEMENT avec un mot: "VOLUME", "POIDS" ou "UNITE"."""

            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.1,  # Très faible pour cohérence
                max_tokens=10
            )

            result = response.choices[0].message.content.strip().upper()

            if "VOLUME" in result:
                return 'volume'
            elif "POIDS" in result:
                return 'poids'
            elif "UNITE" in result or "UNITÉ" in result:
                return 'unite'
            else:
                print(f"Réponse inattendue de l'IA pour {ingredient_name_fr}: {result}")
                return None

        except Exception as e:
            print(f"Erreur lors de la détermination de catégorie pour {ingredient_name_fr}: {e}")
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
