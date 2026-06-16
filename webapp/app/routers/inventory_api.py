"""Proxies finos para os endpoints de inventário/health da API remota."""
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from app.deps import get_client

router = APIRouter(prefix="/api", tags=["inventory"])

INV_PARAMS = ("colecao", "numero", "tipo", "idioma", "preco_min", "preco_max",
              "quantidade_min", "limit")


def _params(request: Request) -> dict:
    return {k: v for k, v in request.query_params.items() if k in INV_PARAMS and v != ""}


async def _proxy(coro):
    """Executa a chamada remota repassando status/detalhe reais ao cliente."""
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
        raise HTTPException(502, f"API remota indisponível: {e}")


@router.get("/health")
async def health(client=Depends(get_client)):
    return await _proxy(client.health())


@router.get("/inventory")
async def inventory(request: Request, client=Depends(get_client)):
    return await _proxy(client.get_inventory(_params(request)))


@router.get("/inventory/summary")
async def inventory_summary(client=Depends(get_client)):
    return await _proxy(client.inventory_summary())


@router.post("/inventory/sync")
async def inventory_sync(client=Depends(get_client)):
    return await _proxy(client.inventory_sync())


@router.get("/inventory/sync/{job_id}")
async def inventory_sync_status(job_id: str, client=Depends(get_client)):
    return await _proxy(client.inventory_sync_status(job_id))


@router.get("/inventory/export")
async def inventory_export(request: Request, client=Depends(get_client)):
    r = await _proxy(client.inventory_export(_params(request)))
    return Response(
        content=r.content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventario.csv"},
    )
