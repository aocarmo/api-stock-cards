"""Telas HTML (Jinja2)."""
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from enums.tipos_carta import IdiomaCarta, TipoCarta

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

TIPOS = TipoCarta.get_all_names()
IDIOMAS = IdiomaCarta.get_all_names()

# action -> (título, operação, precisa de preço/qtd, endpoints)
PAGES = {
    "cadastrar": {"title": "Cadastrar", "operation": "update", "needs_price": True,
                  "action": "cadastrar", "single": "atualizar"},
    "alterar": {"title": "Alterar", "operation": "update", "needs_price": True,
                "action": "alterar", "single": "atualizar"},
    "excluir": {"title": "Excluir", "operation": "delete", "needs_price": False,
                "action": "excluir", "single": "excluir"},
}


def _render(request: Request, name: str, **ctx):
    base = {"tipos": TIPOS, "idiomas": IDIOMAS, "pages": list(PAGES)}
    base.update(ctx)
    return templates.TemplateResponse(request, name, base)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return _render(request, "manage.html", active="cadastrar", cfg=PAGES["cadastrar"])


@router.get("/{action}", response_class=HTMLResponse)
async def page(request: Request, action: str):
    if action in PAGES:
        return _render(request, "manage.html", active=action, cfg=PAGES[action])
    if action == "inventario":
        return _render(request, "inventario.html", active="inventario")
    if action == "progresso":
        return _render(request, "progresso.html", active="progresso")
    return _render(request, "manage.html", active="cadastrar", cfg=PAGES["cadastrar"])
