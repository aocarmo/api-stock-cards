"""Validação/normalização de cartas, reusando os enums do backend."""
import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from enums.tipos_carta import TipoCarta, IdiomaCarta

VALID_TIPOS = set(TipoCarta.get_all_names())
VALID_IDIOMAS = set(IdiomaCarta.get_all_names())
NUMERO_RE = re.compile(r"^\d{1,3}/\d{1,3}$")

# colunas aceitas em importação (tolerante a variações)
FIELD_ALIASES = {
    "numero": "numero", "número": "numero", "number": "numero",
    "colecao": "colecao", "coleção": "colecao", "set": "colecao",
    "tipo": "tipo", "type": "tipo",
    "idioma": "idioma", "language": "idioma", "lang": "idioma",
    "preco": "preco", "preço": "preco", "price": "preco", "valor": "preco",
    "quantidade": "quantidade", "qtd": "quantidade", "qty": "quantidade", "quantity": "quantidade",
}


def canon_field(name: str) -> Optional[str]:
    return FIELD_ALIASES.get((name or "").strip().lower())


def norm_tipo(value: str) -> str:
    return (value or "").strip().lower().replace(" ", "-")


def norm_idioma(value: str) -> str:
    v = (value or "").strip().lower()
    return (v.replace("ê", "e").replace("ã", "a").replace("ç", "c")
             .replace("á", "a").replace("é", "e").replace("í", "i")
             .replace("ó", "o").replace("ú", "u"))


def norm_preco(value) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip().replace("R$", "").replace(" ", "")
    if not s:
        return None
    s = s.replace(",", ".")
    try:
        d = Decimal(s)
    except InvalidOperation:
        raise ValueError(f"preço inválido: {value!r}")
    if d < 0:
        raise ValueError("preço não pode ser negativo")
    return f"{d:.2f}"


def validate_card(row: dict, operation: str) -> dict:
    """Valida e normaliza uma carta. Levanta ValueError com mensagem amigável.

    operation: 'update' (precisa preco/quantidade) ou 'delete' (só os 4 campos).
    Retorna dict normalizado pronto para o CSV.
    """
    numero = str(row.get("numero", "")).strip()
    colecao = str(row.get("colecao", "")).strip().upper()
    tipo = norm_tipo(row.get("tipo", ""))
    idioma = norm_idioma(row.get("idioma", ""))

    if not NUMERO_RE.match(numero):
        raise ValueError(f"número inválido: {numero!r} (esperado NNN/NNN)")
    if not colecao:
        raise ValueError("coleção vazia")
    if tipo not in VALID_TIPOS:
        raise ValueError(f"tipo inválido: {tipo!r}")
    if idioma not in VALID_IDIOMAS:
        raise ValueError(f"idioma inválido: {idioma!r}")

    out = {"numero": numero, "colecao": colecao, "tipo": tipo, "idioma": idioma}

    if operation == "delete":
        return out

    preco = norm_preco(row.get("preco"))
    if preco is None:
        raise ValueError("preço obrigatório")
    qtd_raw = str(row.get("quantidade", "")).strip()
    if not qtd_raw:
        raise ValueError("quantidade obrigatória")
    try:
        qtd = int(float(qtd_raw))
    except ValueError:
        raise ValueError(f"quantidade inválida: {qtd_raw!r}")
    if qtd < 0:
        raise ValueError("quantidade não pode ser negativa")

    out["preco"] = preco
    out["quantidade"] = str(qtd)
    return out


def validate_batch(rows: list[dict], operation: str) -> dict:
    """Retorna {'valid': [...], 'invalid': [{'linha': i, 'erro': msg, 'dados': row}]}"""
    valid, invalid = [], []
    for i, row in enumerate(rows, 1):
        try:
            valid.append(validate_card(row, operation))
        except ValueError as e:
            invalid.append({"linha": i, "erro": str(e), "dados": row})
    return {"valid": valid, "invalid": invalid}
