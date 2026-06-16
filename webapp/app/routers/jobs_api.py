"""Jobs em massa: cria, lista, detalha, retry, cancela."""
from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_manager, get_store
from app.validation import validate_batch

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# ação da UI -> operação interna
ACTION_OP = {"cadastrar": "update", "alterar": "update", "excluir": "delete"}


@router.post("/{action}")
async def create_job(action: str, payload: dict, manager=Depends(get_manager)):
    if action not in ACTION_OP:
        raise HTTPException(404, f"ação desconhecida: {action}")
    operation = ACTION_OP[action]
    result = validate_batch(payload.get("cartas", []), operation)
    if result["invalid"]:
        raise HTTPException(400, {"message": "linhas inválidas", "invalid": result["invalid"]})
    if not result["valid"]:
        raise HTTPException(400, "nenhuma carta válida")
    job_id = manager.create_and_start(operation, result["valid"])
    return {"job_id": job_id, "total": len(result["valid"])}


@router.get("")
async def list_jobs(store=Depends(get_store)):
    return {"jobs": store.list_jobs()}


@router.get("/{job_id}")
async def job_detail(job_id: str, store=Depends(get_store)):
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(404, "job não encontrado")
    erros = store.get_lines(job_id, status="erro")
    job["erros"] = [
        {"numero": e["numero"], "colecao": e["colecao"], "tipo": e["tipo"],
         "idioma": e["idioma"], "status": e["ultimo_erro_status"]}
        for e in erros
    ]
    return job


@router.post("/{job_id}/retry")
async def retry_job(job_id: str, manager=Depends(get_manager)):
    if not manager.retry(job_id):
        raise HTTPException(409, "job não pode ser reenfileirado agora")
    return {"ok": True}


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str, manager=Depends(get_manager)):
    if not manager.cancel(job_id):
        raise HTTPException(404, "job não encontrado")
    return {"ok": True}
