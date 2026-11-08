# app/routes/mobile_routes.py
from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from app.models import db
from app.template_config import templates

router = APIRouter()


@router.get("/mobile")
async def mobile_app_default():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/mobile/fr", status_code=302)


@router.get("/mobile/{lang}", response_class=HTMLResponse)
async def mobile_app(request: Request, lang: str):
    if lang not in ("fr", "jp"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/mobile/fr", status_code=302)
    return templates.TemplateResponse("mobile/app.html", {"request": request, "lang": lang})


@router.get("/sw.js")
async def service_worker():
    response = FileResponse("static/mobile/sw.js", media_type="application/javascript")
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response


@router.get("/api/mobile/recipes")
async def mobile_recipes_list(lang: str = Query("fr")):
    rows = db.list_recipes(lang)
    return JSONResponse([dict(r) for r in rows])


@router.get("/api/mobile/recipe/{slug}")
async def mobile_recipe_detail(slug: str, lang: str = Query("fr")):
    result = db.get_recipe_by_slug(slug, lang)
    if not result:
        return JSONResponse({"error": "Not found"}, status_code=404)
    rec, ings, steps = result
    return JSONResponse({
        "recipe": rec,
        "ingredients": ings,
        "steps": steps,
    })
