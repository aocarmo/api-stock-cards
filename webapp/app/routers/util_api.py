"""Utilidades para a UI: parse de colagem/CSV + validação prévia."""
from fastapi import APIRouter

from app.csv_utils import parse_text
from app.validation import validate_batch

router = APIRouter(prefix="/api", tags=["util"])


@router.post("/parse")
async def parse(payload: dict):
    """Recebe {text, operation} -> {valid, invalid}. Usado pelo botão 'Validar'."""
    operation = payload.get("operation", "update")
    rows = parse_text(payload.get("text", ""))
    return validate_batch(rows, operation)
