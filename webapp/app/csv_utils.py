"""Geração de CSV em memória e parsing de colagem/CSV importado."""
import csv
import io

from app.validation import canon_field

UPDATE_HEADER = ["numero", "colecao", "tipo", "idioma", "preco", "quantidade"]
DELETE_HEADER = ["numero", "colecao", "tipo", "idioma"]


def build_csv(cards: list[dict], operation: str) -> bytes:
    header = DELETE_HEADER if operation == "delete" else UPDATE_HEADER
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=header, extrasaction="ignore")
    writer.writeheader()
    for c in cards:
        writer.writerow({k: c.get(k, "") for k in header})
    return buf.getvalue().encode("utf-8")


def _sniff_delimiter(text: str) -> str:
    first = next((ln for ln in text.splitlines() if ln.strip()), "")
    for d in (";", "\t", ","):
        if d in first:
            return d
    return ","


def parse_text(text: str) -> list[dict]:
    """Parse de CSV/planilha colada. Detecta delimitador (',', ';', tab).

    Aceita com OU sem cabeçalho. Sem cabeçalho assume a ordem:
    numero, colecao, tipo, idioma, preco, quantidade.
    Retorna lista de dicts com chaves canônicas.
    """
    text = (text or "").strip().replace("\r\n", "\n").replace("\r", "\n")
    if not text:
        return []
    delim = _sniff_delimiter(text)
    reader = csv.reader(io.StringIO(text), delimiter=delim)
    rows = [r for r in reader if any((c or "").strip() for c in r)]
    if not rows:
        return []

    first = rows[0]
    mapped = [canon_field(c) for c in first]
    has_header = mapped.count(None) <= len(first) // 2 and "numero" in mapped

    out = []
    if has_header:
        keys = [m or f"col{i}" for i, m in enumerate(mapped)]
        for r in rows[1:]:
            out.append({keys[i]: (r[i].strip() if i < len(r) else "") for i in range(len(keys))})
    else:
        order = UPDATE_HEADER
        for r in rows:
            out.append({order[i]: r[i].strip() for i in range(min(len(order), len(r)))})
    return out
