"""Operações síncronas de 1 carta (resposta imediata, sem batch)."""
import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_client
from app.validation import validate_card

router = APIRouter(prefix="/api/single", tags=["single"])


def _one(cartas: list[dict], operation: str) -> dict:
    if not cartas:
        raise HTTPException(400, "nenhuma carta enviada")
    try:
        return validate_card(cartas[0], operation)
    except ValueError as e:
        raise HTTPException(400, str(e))


async def _proxy(coro):
    try:
        return await coro
    except httpx.HTTPStatusError as e:
        detail = e.response.text
        try:
            detail = e.response.json().get("detail", detail)
        except Exception:  # noqa: BLE001
            pass
        raise HTTPException(e.response.status_code, detail)
    except httpx.HTTPError as e:
        raise HTTPException(502, f"erro na API remota: {e}")


@router.post("/atualizar")
async def atualizar(payload: dict, client=Depends(get_client)):
    carta = _one(payload.get("cartas", []), "update")
    return await _proxy(client.atualizar([carta]))


@router.post("/excluir")
async def excluir(payload: dict, client=Depends(get_client)):
    carta = _one(payload.get("cartas", []), "delete")
    return await _proxy(client.excluir([carta]))
