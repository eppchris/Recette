from fastapi import Request

STRINGS = {
    "fr": {"recipes":"Recettes","all":"Toutes les recettes","type":"Type",
           "servings":"Portions","tags":"Tags","ingredients":"Ingrédients",
           "steps":"Étapes","source":"Source","lang_fr":"Français","lang_ja":"日本語"},
    "jp": {"recipes":"レシピ","all":"すべてのレシピ","type":"種類",
           "servings":"人数","tags":"タグ","ingredients":"材料",
           "steps":"手順","source":"出典","lang_fr":"Français","lang_ja":"日本語"},
}

def get_lang(request: Request) -> str:
    return "jp" if request.query_params.get("lang") == "jp" else "fr"

def S(lang: str, key: str) -> str:
    return STRINGS.get(lang, STRINGS["fr"]).get(key, key)
cs