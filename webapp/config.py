"""Configuração da webapp local.

Também adiciona a raiz do repositório ao sys.path para reutilizar os enums
(`enums/tipos_carta.py`) como fonte da verdade de tipos/idiomas válidos.
"""
import sys
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

WEBAPP_DIR = Path(__file__).resolve().parent
REPO_ROOT = WEBAPP_DIR.parent

# permite `from enums.tipos_carta import TipoCarta, IdiomaCarta`
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(WEBAPP_DIR / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    myp_base_url: str = "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1"
    dynamo_table: str = "myp-cards-files-dev"
    aws_region: str = "us-east-1"

    batch_size: int = 25
    batch_interval_seconds: int = 150
    poll_interval_seconds: int = 8
    poll_timeout_seconds: int = 600
    max_retry_rounds: int = 5
    single_threshold: int = 1
    http_timeout_seconds: int = 120

    host: str = "127.0.0.1"
    port: int = 8001
    db_path: str = "./data/jobs.db"

    @property
    def base_url(self) -> str:
        return self.myp_base_url.rstrip("/")

    @property
    def db_file(self) -> Path:
        p = Path(self.db_path)
        if not p.is_absolute():
            p = WEBAPP_DIR / p
        return p


settings = Settings()
