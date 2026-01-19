"""
DTOs para requests e responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enums.tipos_carta import TipoCarta, IdiomaCarta

class CartaRecadastrarDTO(BaseModel):
    numero: str = Field(..., description="Número da carta (ex: 077/131)")
    colecao: str = Field(..., description="Sigla da coleção (ex: PRE, SVI, PAL)")
    tipo: Optional[str] = Field("normal", description=f"Tipo da carta. Valores válidos: {', '.join(TipoCarta.get_all_names())}")
    idioma: Optional[str] = Field("portugues", description=f"Idioma da carta. Valores válidos: {', '.join(IdiomaCarta.get_all_names())}")

class CartaAtualizarDTO(BaseModel):
    numero: str = Field(..., description="Número da carta (ex: 077/131)")
    colecao: str = Field(..., description="Sigla da coleção (ex: PRE, SVI, PAL)")
    tipo: Optional[str] = Field("normal", description=f"Tipo da carta. Valores válidos: {', '.join(TipoCarta.get_all_names())}")
    idioma: Optional[str] = Field("portugues", description=f"Idioma da carta. Valores válidos: {', '.join(IdiomaCarta.get_all_names())}")
    preco: Optional[str] = Field(None, description="Novo preço (ex: 1.50)")
    quantidade: Optional[str] = Field(None, description="Nova quantidade (ex: 10)")

class CartaCsvDTO(BaseModel):
    numero: str
    colecao: str
    tipo: str
    idioma: str
    preco: str
    quantidade: str

class RecadastrarRequestDTO(BaseModel):
    cartas: List[CartaRecadastrarDTO] = Field(..., description="Lista de cartas para recadastrar")

class AtualizarRequestDTO(BaseModel):
    cartas: List[CartaAtualizarDTO] = Field(..., description="Lista de cartas para atualizar")

class CsvUploadResponseDTO(BaseModel):
    message: str
    file_id: str
    s3_key: str
    total_linhas: int

class FileStatusDTO(BaseModel):
    file_id: str
    status: str  # PENDING, PROCESSING, COMPLETED, FAILED
    total_linhas: int
    total_chunks: int
    chunks_processados: int
    progresso_percentual: float
    linhas_erro: List[dict]
    created_at: str
    updated_at: str

class ResultadoDTO(BaseModel):
    numero: str
    colecao: str
    tipo: str
    idioma: Optional[str] = ""
    status: str
    erro: Optional[str] = None

class ResponseDTO(BaseModel):
    resultados: List[ResultadoDTO]
