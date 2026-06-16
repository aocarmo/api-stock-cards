"""Wrapper httpx sobre a API remota (api-stock-cards). Único ponto de saída HTTP."""
import httpx


class MypClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str):
        self.client = client
        self.base = base_url.rstrip("/")

    # ---- massa (assíncrono) ----
    async def upload_mass(self, csv_bytes: bytes, filename: str, operation: str) -> dict:
        """Sobe um lote. Retorna {file_id, s3_key, total_linhas}."""
        files = {"file": (filename, csv_bytes, "text/csv")}
        if operation == "delete":
            url = f"{self.base}/upload-csv-excluir"
            data = None
        else:
            url = f"{self.base}/upload-csv"
            data = {"operation": operation}
        r = await self.client.post(url, files=files, data=data)
        r.raise_for_status()
        return r.json()

    # ---- síncrono (1 carta) ----
    async def atualizar(self, cartas: list[dict]) -> dict:
        r = await self.client.post(f"{self.base}/atualizar", json={"cartas": cartas})
        r.raise_for_status()
        return r.json()

    async def excluir(self, cartas: list[dict]) -> dict:
        r = await self.client.post(f"{self.base}/excluir", json={"cartas": cartas})
        r.raise_for_status()
        return r.json()

    # ---- inventário (proxies) ----
    async def get_inventory(self, params: dict) -> dict:
        r = await self.client.get(f"{self.base}/inventory", params=params)
        r.raise_for_status()
        return r.json()

    async def inventory_summary(self) -> dict:
        r = await self.client.get(f"{self.base}/inventory/summary")
        r.raise_for_status()
        return r.json()

    async def inventory_sync(self) -> dict:
        r = await self.client.post(f"{self.base}/inventory/sync")
        r.raise_for_status()
        return r.json()

    async def inventory_sync_status(self, job_id: str) -> dict:
        r = await self.client.get(f"{self.base}/inventory/status/{job_id}")
        r.raise_for_status()
        return r.json()

    async def inventory_export(self, params: dict) -> httpx.Response:
        r = await self.client.get(f"{self.base}/inventory/export", params=params)
        r.raise_for_status()
        return r

    async def health(self) -> dict:
        r = await self.client.get(f"{self.base}/health")
        r.raise_for_status()
        return r.json()
