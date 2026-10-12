"""Utilidades para a UI: parse de colagem/CSV + validação prévia."""
from fastapi import APIRouter, Depends, HTTPException

from app.csv_utils import parse_text
from app.deps import get_client
from app.routers.single_api import _proxy
from app.validation import validate_batch

router = APIRouter(prefix="/api", tags=["util"])


@router.post("/parse")
async def parse(payload: dict):
    """Recebe {text, operation} -> {valid, invalid}. Usado pelo botão 'Validar'."""
    operation = payload.get("operation", "update")
    rows = parse_text(payload.get("text", ""))
    return validate_batch(rows, operation)


@router.get("/sessao")
async def sessao_get(client=Depends(get_client)):
    """Proxy de GET /sessao da API: sessão gravada + se ainda loga no site."""
    return await _proxy(client.sessao_get())


@router.post("/sessao")
async def sessao_set(payload: dict, client=Depends(get_client)):
    """Recebe {identity, phpsessid?, nick?} da tela Sessão e grava na API."""
    identity = (payload.get("identity") or "").strip()
    if not identity:
        raise HTTPException(400, "cole o valor do cookie _identity")
    cookies = {"_identity": identity}
    phpsessid = (payload.get("phpsessid") or "").strip()
    if phpsessid:
        cookies["PHPSESSID"] = phpsessid
    return await _proxy(client.sessao_set(cookies, (payload.get("nick") or "").strip() or None))
