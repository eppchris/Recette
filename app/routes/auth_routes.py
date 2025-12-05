"""Routes d'authentification multi-utilisateurs"""

import os
import markdown
from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from app.models import authenticate_user, create_user, get_user_by_id, update_user_password, verify_password, get_user_by_username, list_users, activate_user, deactivate_user
from app.template_config import templates

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request, lang: str = Query("fr")):
    """Affiche le formulaire de connexion"""
    # Si déjà connecté, rediriger vers l'accueil
    if request.session.get("user_id"):
        return RedirectResponse(url=f"/recipes?lang={lang}", status_code=303)

    return templates.TemplateResponse(
        "login.html",
        {"request": request, "lang": lang, "error": None}
    )


@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    lang: str = Query("fr")
):
    """Traite la tentative de connexion"""

    # Authentifier l'utilisateur
    user = authenticate_user(username, password)

    if user:
        # Connexion réussie : créer la session
        request.session["user_id"] = user["id"]
        request.session["username"] = user["username"]
        request.session["is_admin"] = user["is_admin"]
        request.session["authenticated"] = True  # Pour compatibilité avec l'ancien système

        # Rediriger vers la page d'accueil
        return RedirectResponse(url=f"/recipes?lang={lang}", status_code=303)
    else:
        # Authentification échouée
        error = "Nom d'utilisateur ou mot de passe incorrect" if lang == "fr" else "ユーザー名またはパスワードが間違っています"
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "lang": lang, "error": error}
        )


@router.get("/register", response_class=HTMLResponse)
async def register_form(request: Request, lang: str = Query("fr")):
    """Affiche le formulaire d'inscription"""
    # Si déjà connecté, rediriger vers l'accueil
    if request.session.get("user_id"):
        return RedirectResponse(url=f"/recipes?lang={lang}", status_code=303)

    return templates.TemplateResponse(
        "register.html",
        {"request": request, "lang": lang, "error": None}
    )


@router.post("/register", response_class=HTMLResponse)
async def register_post(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    display_name: str = Form(None),
    lang: str = Query("fr")
):
    """Traite l'inscription d'un nouvel utilisateur"""

    # Vérifier que les mots de passe correspondent
    if password != password_confirm:
        error = "Les mots de passe ne correspondent pas" if lang == "fr" else "パスワードが一致しません"
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "lang": lang, "error": error}
        )

    # Vérifier la longueur du mot de passe
    if len(password) < 6:
        error = "Le mot de passe doit contenir au moins 6 caractères" if lang == "fr" else "パスワードは6文字以上である必要があります"
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "lang": lang, "error": error}
        )

    try:
        # Créer l'utilisateur
        user_id = create_user(
            username=username,
            email=email,
            password=password,
            display_name=display_name or username,
            is_admin=False
        )

        # Connecter automatiquement le nouvel utilisateur
        request.session["user_id"] = user_id
        request.session["username"] = username
        request.session["is_admin"] = False
        request.session["authenticated"] = True

        # Rediriger vers l'accueil
        return RedirectResponse(url=f"/recipes?lang={lang}", status_code=303)

    except ValueError as e:
        # Erreur (username ou email déjà pris)
        error = str(e)
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "lang": lang, "error": error}
        )


@router.get("/logout")
async def logout(request: Request, lang: str = Query("fr")):
    """Déconnexion de l'utilisateur"""
    request.session.clear()
    return RedirectResponse(url=f"/login?lang={lang}", status_code=303)


@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, lang: str = Query("fr"), success: str = Query(None)):
    """Affiche le profil de l'utilisateur connecté"""
    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse(url=f"/login?lang={lang}", status_code=303)

    user = get_user_by_id(user_id)

    if not user:
        request.session.clear()
        return RedirectResponse(url=f"/login?lang={lang}", status_code=303)

    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "lang": lang, "user": user, "success": success, "error": None}
    )


@router.post("/change-password", response_class=HTMLResponse)
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    new_password_confirm: str = Form(...),
    lang: str = Query("fr")
):
    """Change le mot de passe de l'utilisateur connecté"""
    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse(url=f"/login?lang={lang}", status_code=303)

    user = get_user_by_username(request.session.get("username"))

    if not user:
        return RedirectResponse(url=f"/login?lang={lang}", status_code=303)

    # Vérifier que les nouveaux mots de passe correspondent
    if new_password != new_password_confirm:
        error = "Les nouveaux mots de passe ne correspondent pas" if lang == "fr" else "新しいパスワードが一致しません"
        user_display = get_user_by_id(user_id)
        return templates.TemplateResponse(
            "profile.html",
            {"request": request, "lang": lang, "user": user_display, "error": error, "success": None}
        )

    # Vérifier la longueur du nouveau mot de passe
    if len(new_password) < 6:
        error = "Le mot de passe doit contenir au moins 6 caractères" if lang == "fr" else "パスワードは6文字以上である必要があります"
        user_display = get_user_by_id(user_id)
        return templates.TemplateResponse(
            "profile.html",
            {"request": request, "lang": lang, "user": user_display, "error": error, "success": None}
        )

    # Vérifier le mot de passe actuel
    if not verify_password(current_password, user['password_hash']):
        error = "Mot de passe actuel incorrect" if lang == "fr" else "現在のパスワードが間違っています"
        user_display = get_user_by_id(user_id)
        return templates.TemplateResponse(
            "profile.html",
            {"request": request, "lang": lang, "user": user_display, "error": error, "success": None}
        )

    # Mettre à jour le mot de passe
    update_user_password(user_id, new_password)

    # Rediriger avec message de succès
    success = "Mot de passe modifié avec succès" if lang == "fr" else "パスワードが正常に変更されました"
    return RedirectResponse(url=f"/profile?lang={lang}&success={success}", status_code=303)


@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users(request: Request, lang: str = Query("fr"), success: str = Query(None)):
    """Page d'administration des utilisateurs (admins uniquement)"""
    user_id = request.session.get("user_id")
    is_admin = request.session.get("is_admin")

    # Vérifier que l'utilisateur est connecté et admin
    if not user_id or not is_admin:
        return RedirectResponse(url=f"/recipes?lang={lang}", status_code=303)

    # Récupérer la liste de tous les utilisateurs
    users = list_users()

    return templates.TemplateResponse(
        "admin_users.html",
        {"request": request, "lang": lang, "users": users, "success": success, "error": None}
    )


@router.post("/admin/users/{user_id}/toggle-active")
async def toggle_user_active(request: Request, user_id: int, lang: str = Query("fr")):
    """Active ou désactive un utilisateur (admins uniquement)"""
    admin_user_id = request.session.get("user_id")
    is_admin = request.session.get("is_admin")

    # Vérifier que l'utilisateur est connecté et admin
    if not admin_user_id or not is_admin:
        return RedirectResponse(url=f"/recipes?lang={lang}", status_code=303)

    # Récupérer l'utilisateur cible
    user = get_user_by_id(user_id)

    if not user:
        return RedirectResponse(url=f"/admin/users?lang={lang}", status_code=303)

    # Empêcher de se désactiver soi-même
    if user_id == admin_user_id:
        error = "Vous ne pouvez pas vous désactiver vous-même" if lang == "fr" else "自分自身を無効化できません"
        return RedirectResponse(url=f"/admin/users?lang={lang}&error={error}", status_code=303)

    # Activer ou désactiver
    if user['is_active']:
        deactivate_user(user_id)
        success = f"Utilisateur {user['username']} désactivé" if lang == "fr" else f"ユーザー {user['username']} を無効化しました"
    else:
        activate_user(user_id)
        success = f"Utilisateur {user['username']} activé" if lang == "fr" else f"ユーザー {user['username']} を有効化しました"

    return RedirectResponse(url=f"/admin/users?lang={lang}&success={success}", status_code=303)


@router.get("/admin/users/new", response_class=HTMLResponse)
async def admin_new_user_form(request: Request, lang: str = Query("fr")):
    """Affiche le formulaire de création d'utilisateur (admins uniquement)"""
    user_id = request.session.get("user_id")
    is_admin = request.session.get("is_admin")

    # Vérifier que l'utilisateur est connecté et admin
    if not user_id or not is_admin:
        return RedirectResponse(url=f"/recipes?lang={lang}", status_code=303)

    return templates.TemplateResponse(
        "admin_user_new.html",
        {"request": request, "lang": lang, "error": None}
    )


@router.post("/admin/users/new", response_class=HTMLResponse)
async def admin_new_user_create(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    display_name: str = Form(None),
    is_admin: bool = Form(False),
    lang: str = Query("fr")
):
    """Crée un nouvel utilisateur (admins uniquement)"""
    admin_user_id = request.session.get("user_id")
    admin_is_admin = request.session.get("is_admin")

    # Vérifier que l'utilisateur est connecté et admin
    if not admin_user_id or not admin_is_admin:
        return RedirectResponse(url=f"/recipes?lang={lang}", status_code=303)

    # Vérifier que les mots de passe correspondent
    if password != password_confirm:
        error = "Les mots de passe ne correspondent pas" if lang == "fr" else "パスワードが一致しません"
        return templates.TemplateResponse(
            "admin_user_new.html",
            {"request": request, "lang": lang, "error": error}
        )

    # Vérifier la longueur du mot de passe
    if len(password) < 6:
        error = "Le mot de passe doit contenir au moins 6 caractères" if lang == "fr" else "パスワードは6文字以上である必要があります"
        return templates.TemplateResponse(
            "admin_user_new.html",
            {"request": request, "lang": lang, "error": error}
        )

    try:
        # Créer l'utilisateur
        user_id = create_user(
            username=username,
            email=email,
            password=password,
            display_name=display_name or username,
            is_admin=is_admin
        )

        # Rediriger vers la liste des utilisateurs avec message de succès
        success = f"Utilisateur {username} créé avec succès" if lang == "fr" else f"ユーザー {username} を作成しました"
        return RedirectResponse(url=f"/admin/users?lang={lang}&success={success}", status_code=303)

    except ValueError as e:
        # Erreur (username ou email déjà pris)
        error = str(e)
        return templates.TemplateResponse(
            "admin_user_new.html",
            {"request": request, "lang": lang, "error": error}
        )


@router.post("/admin/users/{user_id}/delete")
async def delete_user_endpoint(request: Request, user_id: int, lang: str = Query("fr")):
    """Supprime un utilisateur (admins uniquement)"""
    admin_user_id = request.session.get("user_id")
    is_admin = request.session.get("is_admin")

    # Vérifier que l'utilisateur est connecté et admin
    if not admin_user_id or not is_admin:
        return RedirectResponse(url=f"/recipes?lang={lang}", status_code=303)

    # Empêcher de se supprimer soi-même
    if user_id == admin_user_id:
        error = "Vous ne pouvez pas vous supprimer vous-même" if lang == "fr" else "自分自身を削除できません"
        return RedirectResponse(url=f"/admin/users?lang={lang}&error={error}", status_code=303)

    # Récupérer l'utilisateur
    user = get_user_by_id(user_id)
    if not user:
        return RedirectResponse(url=f"/admin/users?lang={lang}", status_code=303)

    username = user['username']

    # Supprimer l'utilisateur (vraie suppression)
    from app.models.db_core import get_db
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user WHERE id = ?", (user_id,))
        conn.commit()

    success = f"Utilisateur {username} supprimé" if lang == "fr" else f"ユーザー {username} を削除しました"
    return RedirectResponse(url=f"/admin/users?lang={lang}&success={success}", status_code=303)


@router.post("/admin/users/{user_id}/reset-password")
async def reset_user_password(
    request: Request,
    user_id: int,
    new_password: str = Form(...),
    new_password_confirm: str = Form(...),
    lang: str = Query("fr")
):
    """Réinitialise le mot de passe d'un utilisateur (admins uniquement, sans ancien mot de passe)"""
    admin_user_id = request.session.get("user_id")
    is_admin = request.session.get("is_admin")

    # Vérifier que l'utilisateur est connecté et admin
    if not admin_user_id or not is_admin:
        return RedirectResponse(url=f"/recipes?lang={lang}", status_code=303)

    # Vérifier que les mots de passe correspondent
    if new_password != new_password_confirm:
        error = "Les mots de passe ne correspondent pas" if lang == "fr" else "パスワードが一致しません"
        return RedirectResponse(url=f"/admin/users?lang={lang}&error={error}", status_code=303)

    # Vérifier la longueur du mot de passe
    if len(new_password) < 6:
        error = "Le mot de passe doit contenir au moins 6 caractères" if lang == "fr" else "パスワードは6文字以上である必要があります"
        return RedirectResponse(url=f"/admin/users?lang={lang}&error={error}", status_code=303)

    # Récupérer l'utilisateur
    user = get_user_by_id(user_id)
    if not user:
        return RedirectResponse(url=f"/admin/users?lang={lang}", status_code=303)

    username = user['username']

    # Changer le mot de passe
    update_user_password(user_id, new_password)

    success = f"Mot de passe de {username} modifié" if lang == "fr" else f"{username} のパスワードを変更しました"
    return RedirectResponse(url=f"/admin/users?lang={lang}&success={success}", status_code=303)


@router.get("/help", response_class=HTMLResponse)
async def help_page(request: Request, lang: str = Query("fr")):
    """Page d'aide générale par fonction"""
    # Charger le contenu markdown
    help_file = f"docs/help/content/help_{lang}.md"

    if os.path.exists(help_file):
        with open(help_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
            help_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    else:
        help_content = "Aide non disponible" if lang == "fr" else "ヘルプは利用できません"

    return templates.TemplateResponse(
        "help.html",
        {"request": request, "lang": lang, "help_content": help_content}
    )


@router.get("/admin/help/edit", response_class=HTMLResponse)
async def admin_help_edit_form(request: Request, lang: str = Query("fr")):
    """Formulaire d'édition de l'aide (admins uniquement)"""
    user_id = request.session.get("user_id")
    is_admin = request.session.get("is_admin")

    # Vérifier que l'utilisateur est connecté et admin
    if not user_id or not is_admin:
        return RedirectResponse(url=f"/recipes?lang={lang}", status_code=303)

    # Charger le contenu markdown actuel
    help_file = f"docs/help/content/help_{lang}.md"

    if os.path.exists(help_file):
        with open(help_file, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = ""

    # Générer preview
    preview_html = markdown.markdown(content, extensions=['tables', 'fenced_code']) if content else ""

    return templates.TemplateResponse(
        "admin_help_edit.html",
        {
            "request": request,
            "lang": lang,
            "content": content,
            "preview_html": preview_html,
            "error": None,
            "success": None
        }
    )


@router.post("/admin/help/edit", response_class=HTMLResponse)
async def admin_help_edit_save(
    request: Request,
    content: str = Form(...),
    lang: str = Query("fr")
):
    """Sauvegarde le contenu de l'aide (admins uniquement)"""
    user_id = request.session.get("user_id")
    is_admin = request.session.get("is_admin")

    # Vérifier que l'utilisateur est connecté et admin
    if not user_id or not is_admin:
        return RedirectResponse(url=f"/recipes?lang={lang}", status_code=303)

    try:
        # Sauvegarder le contenu
        help_file = f"docs/help/content/help_{lang}.md"

        # Créer le dossier si nécessaire
        os.makedirs(os.path.dirname(help_file), exist_ok=True)

        with open(help_file, 'w', encoding='utf-8') as f:
            f.write(content)

        # Générer preview pour affichage
        preview_html = markdown.markdown(content, extensions=['tables', 'fenced_code'])

        success = "Aide mise à jour avec succès" if lang == "fr" else "ヘルプが正常に更新されました"

        return templates.TemplateResponse(
            "admin_help_edit.html",
            {
                "request": request,
                "lang": lang,
                "content": content,
                "preview_html": preview_html,
                "success": success,
                "error": None
            }
        )

    except Exception as e:
        error = f"Erreur lors de la sauvegarde: {str(e)}" if lang == "fr" else f"保存エラー: {str(e)}"
        preview_html = markdown.markdown(content, extensions=['tables', 'fenced_code'])

        return templates.TemplateResponse(
            "admin_help_edit.html",
            {
                "request": request,
                "lang": lang,
                "content": content,
                "preview_html": preview_html,
                "error": error,
                "success": None
            }
        )
