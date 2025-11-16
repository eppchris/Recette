# app/template_config.py
"""Configuration partagée des templates pour éviter les imports circulaires"""

from fastapi.templating import Jinja2Templates
from jinja2 import pass_context
from pathlib import Path

# Configuration des templates
TEMPLATES_DIR = str((Path(__file__).resolve().parent / "templates"))
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Dictionnaire de traductions complet
TRANSLATIONS = {
    "fr": {
        "recipes": "Recettes",
        "all": "Toutes les recettes",
        "import": "Importer",
        "back": "Retour",
        "type": "Type",
        "servings": "Convives",
        "tags": "Tags",
        "ingredients": "Ingrédients",
        "steps": "Étapes",
        "source": "Source",
        "lang_fr": "Français",
        "lang_jp": "日本語",
        "menu_recipes": "Recettes",
        "menu_events": "Événements",
        "menu_settings": "Gestion",
        "all_recipes": "Toutes les recettes",
        "import_recipe": "Importer",
        "coming_soon": "Bientôt",
        "dark_mode": "Mode nuit",
        "light_mode": "Mode jour",
        "login_title": "Connexion",
        "login_subtitle": "Veuillez vous connecter pour accéder à l'application",
        "password_label": "Mot de passe",
        "password_placeholder": "Entrez le mot de passe",
        "login_button": "Se connecter",
        "login_error": "Mot de passe incorrect",
        "events": "Événements",
        "events_list": "Liste des événements",
        "new_event": "Nouvel événement",
        "event_name": "Nom de l'événement",
        "event_date": "Date",
        "event_location": "Lieu",
        "event_attendees": "Convives",
        "event_notes": "Notes",
        "event_type": "Type d'événement",
        "save": "Enregistrer",
        "cancel": "Annuler",
        "edit": "Modifier",
        "delete": "Supprimer",
        "add_recipe": "Ajouter une recette",
        "remove": "Retirer",
        "shopping_list": "Liste de courses",
        "generate_shopping_list": "Générer la liste",
        "total_quantity": "Quantité totale",
        "used_in": "Utilisé dans",
    },
    "jp": {
        "recipes": "レシピ一覧",
        "all": "全てのレシピ",
        "import": "インポート",
        "back": "戻る",
        "type": "タイプ",
        "servings": "人数",
        "tags": "タグ",
        "ingredients": "材料",
        "steps": "手順",
        "source": "ソース",
        "lang_fr": "Français",
        "lang_jp": "日本語",
        "menu_recipes": "レシピ",
        "menu_events": "イベント",
        "menu_settings": "設定",
        "all_recipes": "全てのレシピ",
        "import_recipe": "インポート",
        "coming_soon": "近日公開",
        "dark_mode": "ダークモード",
        "light_mode": "ライトモード",
        "login_title": "ログイン",
        "login_subtitle": "アプリケーションにアクセスするにはログインしてください",
        "password_label": "パスワード",
        "password_placeholder": "パスワードを入力してください",
        "login_button": "ログイン",
        "login_error": "パスワードが正しくありません",
        "events": "イベント",
        "events_list": "イベント一覧",
        "new_event": "新しいイベント",
        "event_name": "イベント名",
        "event_date": "日付",
        "event_location": "場所",
        "event_attendees": "人数",
        "event_notes": "メモ",
        "event_type": "イベントタイプ",
        "save": "保存",
        "cancel": "キャンセル",
        "edit": "編集",
        "delete": "削除",
        "add_recipe": "レシピを追加",
        "remove": "削除",
        "shopping_list": "買い物リスト",
        "generate_shopping_list": "リストを生成",
        "total_quantity": "合計量",
        "used_in": "使用されています",
    },
}

@pass_context
def S(ctx, key: str):
    """Fonction de traduction pour les templates"""
    lang = ctx.get("lang", "fr")
    return TRANSLATIONS.get(lang, {}).get(key, key)

templates.env.globals["S"] = S
