"""Consulta de status do processamento no DynamoDB, por s3_key.

Necessário porque o producer gera seu próprio file_id ao ser disparado pelo S3
(independente do file_id devolvido pelo upload), então a única correlação
confiável é o s3_key. Usa a cadeia padrão de credenciais da AWS (env/~/.aws) —
nenhum segredo é guardado pelo app.
"""
from __future__ import annotations

from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr


def _to_plain(obj):
    if isinstance(obj, list):
        return [_to_plain(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _to_plain(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return int(obj) if obj == obj.to_integral_value() else float(obj)
    return obj


class StatusTracker:
    def __init__(self, table_name: str, region: str):
        self._table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    def get_by_s3_key(self, s3_key: str) -> dict | None:
        """Retorna o registro (status, linhas_erro, total_*) ou None. Síncrono/bloqueante.

        Chamar via asyncio.to_thread a partir do runner.
        """
        resp = self._table.scan(FilterExpression=Attr("s3_key").eq(s3_key))
        items = resp.get("Items", [])
        return _to_plain(items[0]) if items else None
