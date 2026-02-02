"""
Rotas da API - Endpoints e lógica de negócio
"""
import boto3
import csv
import io
import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from dtos.card_dtos import RecadastrarRequestDTO, AtualizarRequestDTO, ResponseDTO, CsvUploadResponseDTO, FileStatusDTO
from use_cases.recadastrar_use_case import RecadastrarUseCase
from use_cases.atualizar_use_case import AtualizarUseCase
from use_cases.excluir_massa_use_case import ExcluirMassaUseCase
from use_cases.recadastrar_massa_use_case import RecadastrarMassaUseCase

router = APIRouter(prefix="/api/v1", tags=["Cards"])

@router.post(
    "/recadastrar",
    response_model=ResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Recadastrar cartas",
    description="""
    Exclui e recadastra cartas com os mesmos dados.
    
    **Útil para:** Atualizar informações que o sistema MYP Cards alterou automaticamente.
    
    **Processo:**
    1. Busca a carta por número + coleção + tipo + idioma
    2. Salva os dados atuais
    3. Exclui a carta
    4. Recadastra com os mesmos dados
    
    **Delay:** 2 segundos entre cada operação para evitar bloqueio.
    """,
    responses={
        200: {
            "description": "Cartas processadas com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "resultados": [
                            {
                                "numero": "077/131",
                                "colecao": "SVI",
                                "tipo": "normal",
                                "idioma": "ingles",
                                "status": "ok",
                                "erro": None
                            }
                        ]
                    }
                }
            }
        },
        500: {"description": "Erro no processamento"}
    }
)
async def recadastrar_cartas(request: RecadastrarRequestDTO) -> ResponseDTO:
    try:
        use_case = RecadastrarUseCase()
        cartas_dict = [carta.dict() for carta in request.cartas]
        resultados = use_case.execute(cartas_dict)
        return ResponseDTO(resultados=resultados)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no recadastro: {str(e)}")

@router.post(
    "/atualizar",
    response_model=ResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Atualizar cartas",
    description="""
    Atualiza preços e/ou quantidades de cartas específicas.
    
    **Comportamento:**
    - **Preço:** Substitui o valor atual
    - **Quantidade:** Incrementa (soma com a quantidade atual)
    
    **Delay:** 2 segundos entre cada operação.
    """,
    responses={
        200: {
            "description": "Cartas atualizadas",
            "content": {
                "application/json": {
                    "example": {
                        "resultados": [
                            {
                                "numero": "077/131",
                                "colecao": "SVI",
                                "tipo": "normal",
                                "idioma": "ingles",
                                "status": "atualizada",
                                "erro": None
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def atualizar_cartas(request: AtualizarRequestDTO) -> ResponseDTO:
    try:
        use_case = AtualizarUseCase()
        cartas_dict = [carta.dict() for carta in request.cartas]
        resultados = use_case.execute(cartas_dict)
        return ResponseDTO(resultados=resultados)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na atualização: {str(e)}")

@router.post(
    "/recadastrar-massa",
    response_model=ResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Recadastrar cartas em massa",
    description="""
    Exclui e recadastra cartas (mesmo comportamento do atualizar, mas com exclusão antes).
    
    **Processo:**
    1. Busca a carta por número + coleção + tipo + idioma
    2. Exclui a carta encontrada
    3. Recadastra com os valores atualizados
    
    **Comportamento:**
    - **Preço:** Substitui o valor atual
    - **Quantidade:** Incrementa (soma com a quantidade atual)
    
    **Delay:** 2 segundos entre cada operação.
    """,
    responses={
        200: {
            "description": "Cartas processadas",
            "content": {
                "application/json": {
                    "example": {
                        "resultados": [
                            {
                                "numero": "077/131",
                                "colecao": "SVI",
                                "tipo": "normal",
                                "idioma": "ingles",
                                "status": "ok",
                                "preco": "150.00",
                                "quantidade": "5"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def recadastrar_massa_cartas(request: AtualizarRequestDTO) -> ResponseDTO:
    try:
        use_case = RecadastrarMassaUseCase()
        cartas_dict = [carta.dict() for carta in request.cartas]
        resultados = use_case.execute(cartas_dict)
        return ResponseDTO(resultados=resultados)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no recadastro em massa: {str(e)}")

@router.post(
    "/excluir",
    response_model=ResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Excluir cartas",
    description="""
    Exclui cartas da pasta do usuário.
    
    **Processo:**
    1. Busca a carta por número + coleção + tipo + idioma
    2. Exclui a carta encontrada
    
    **Formato:** Mesmo formato do CSV (numero, colecao, tipo, idioma)
    """,
    responses={
        200: {
            "description": "Cartas processadas com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "resultados": [
                            {
                                "numero": "077/131",
                                "colecao": "SVI",
                                "tipo": "normal",
                                "idioma": "ingles",
                                "status": "excluida"
                            }
                        ]
                    }
                }
            }
        },
        500: {"description": "Erro no processamento"}
    }
)
async def excluir_cartas(request: RecadastrarRequestDTO) -> ResponseDTO:
    try:
        use_case = ExcluirMassaUseCase()
        cartas_dict = [carta.dict() for carta in request.cartas]
        resultados = use_case.execute(cartas_dict)
        return ResponseDTO(resultados=resultados)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na exclusão: {str(e)}")

@router.post(
    "/upload-csv",
    response_model=CsvUploadResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Upload CSV para atualização em massa",
    description="""
    Faz upload de arquivo CSV para processamento em massa.
    
    **Fluxo:**
    1. Valida formato do CSV
    2. Salva no S3
    3. Dispara Lambda Producer
    4. Producer quebra em chunks de 50 linhas
    5. Envia chunks para SQS
    6. 50 Lambdas Consumer processam simultaneamente
    
    **Restrições:**
    - Apenas 1 arquivo pode ser processado por vez
    - Se houver arquivo em processamento, retorna erro 429
    
    **Formato CSV obrigatório:**
    ```
    numero,colecao,tipo,idioma,preco,quantidade
    161/131,PRE,normal,portugues,2500.00,5
    ```
    """,
    responses={
        200: {
            "description": "CSV enviado com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "message": "CSV enviado com sucesso. Processamento iniciado.",
                        "file_id": "file_20260118_200500",
                        "s3_key": "csv-uploads/20260118_200500_exemplo.csv",
                        "total_linhas": 100
                    }
                }
            }
        },
        400: {"description": "CSV inválido ou campos faltando"},
        429: {"description": "Já existe um arquivo sendo processado"}
    }
)
async def upload_csv(
    file: UploadFile = File(..., description="Arquivo CSV com as cartas"),
    operation: str = Form("update", description="Operação: update, delete ou recadastrar")
) -> CsvUploadResponseDTO:
    try:
        # Validar operação
        if operation not in ['update', 'delete', 'recadastrar']:
            raise HTTPException(status_code=400, detail="Operação inválida. Use: update, delete ou recadastrar")
        
        # Validar extensão
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Arquivo deve ser CSV")
        
        # Ler conteúdo
        content = await file.read()
        
        # Validar CSV
        csv_reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
        
        # Campos obrigatórios variam por operação
        if operation == "delete":
            required_fields = ['numero', 'colecao', 'tipo', 'idioma']
        else:  # update ou recadastrar
            required_fields = ['numero', 'colecao', 'tipo', 'idioma', 'preco', 'quantidade']
        
        if not all(field in csv_reader.fieldnames for field in required_fields):
            raise HTTPException(
                status_code=400, 
                detail=f"CSV deve conter os campos: {', '.join(required_fields)}"
            )
        
        # Contar linhas
        rows = list(csv_reader)
        total_linhas = len(rows)
        
        # Gerar nome com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_id = f"file_{timestamp}"
        
        # Definir prefixo baseado na operação
        if operation == "delete":
            prefix = "csv-excluir"
        elif operation == "recadastrar":
            prefix = "csv-recadastrar"
        else:
            prefix = "csv-uploads"
            
        s3_key = f"{prefix}/{timestamp}_{file.filename}"
        
        # Upload para S3
        s3 = boto3.client('s3')
        bucket_name = os.getenv('S3_BUCKET', 'myp-cards-csv')
        
        s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=content,
            ContentType='text/csv'
        )
        
        return CsvUploadResponseDTO(
            message="CSV enviado com sucesso. Processamento iniciado.",
            file_id=file_id,
            s3_key=s3_key,
            total_linhas=total_linhas
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")

@router.post(
    "/upload-csv-excluir",
    response_model=CsvUploadResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Upload CSV para exclusão em massa",
    description="""
    Faz upload de arquivo CSV para exclusão em massa.
    
    **Fluxo:**
    1. Valida formato do CSV
    2. Salva no S3 (pasta csv-excluir/)
    3. Dispara Lambda Producer
    4. Producer quebra em chunks de 50 linhas
    5. Envia chunks para SQS
    6. 50 Lambdas Consumer processam simultaneamente
    
    **Formato CSV obrigatório:**
    ```
    numero,colecao,tipo,idioma
    161/131,PRE,normal,portugues
    077/131,SVI,foil,ingles
    ```
    
    **Nota:** Não precisa de preço e quantidade para exclusão.
    """,
    responses={
        200: {
            "description": "CSV enviado com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "message": "CSV enviado com sucesso. Exclusão iniciada.",
                        "file_id": "file_20260118_200500",
                        "s3_key": "csv-excluir/20260118_200500_exemplo.csv",
                        "total_linhas": 100
                    }
                }
            }
        },
        400: {"description": "CSV inválido ou campos faltando"}
    }
)
async def upload_csv_excluir(file: UploadFile = File(..., description="Arquivo CSV com as cartas para excluir")) -> CsvUploadResponseDTO:
    try:
        # Validar extensão
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Arquivo deve ser CSV")
        
        # Ler conteúdo
        content = await file.read()
        
        # Validar CSV
        csv_reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
        required_fields = ['numero', 'colecao', 'tipo', 'idioma']
        
        if not all(field in csv_reader.fieldnames for field in required_fields):
            raise HTTPException(
                status_code=400, 
                detail=f"CSV deve conter os campos: {', '.join(required_fields)}"
            )
        
        # Contar linhas
        rows = list(csv_reader)
        total_linhas = len(rows)
        
        # Gerar nome com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_id = f"file_{timestamp}"
        s3_key = f"csv-excluir/{timestamp}_{file.filename}"
        
        # Upload para S3
        s3 = boto3.client('s3')
        bucket_name = os.getenv('S3_BUCKET', 'myp-cards-csv')
        
        s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=content,
            ContentType='text/csv',
            Metadata={'operation': 'delete'}
        )
        
        return CsvUploadResponseDTO(
            message="CSV enviado com sucesso. Exclusão iniciada.",
            file_id=file_id,
            s3_key=s3_key,
            total_linhas=total_linhas
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")

@router.post(
    "/upload-csv-recadastrar",
    response_model=CsvUploadResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Upload CSV para recadastrar em massa",
    description="""
    Faz upload de arquivo CSV para recadastro em massa (exclui e cria).
    
    **Fluxo:**
    1. Valida formato do CSV
    2. Salva no S3 (pasta csv-recadastrar/)
    3. Dispara Lambda Producer
    4. Producer quebra em chunks de 50 linhas
    5. Envia chunks para SQS
    6. 50 Lambdas Consumer processam simultaneamente
    
    **Comportamento:**
    - **Preço:** Substitui o valor atual
    - **Quantidade:** Incrementa (soma com a quantidade atual)
    - Se não existir, busca produto e cria
    
    **Formato CSV obrigatório:**
    ```
    numero,colecao,tipo,idioma,preco,quantidade
    161/131,PRE,normal,portugues,2500.00,5
    077/131,SVI,foil,ingles,150.00,2
    ```
    """,
    responses={
        200: {
            "description": "CSV enviado com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "message": "CSV enviado com sucesso. Recadastro iniciado.",
                        "file_id": "file_20260118_200500",
                        "s3_key": "csv-recadastrar/20260118_200500_exemplo.csv",
                        "total_linhas": 100
                    }
                }
            }
        },
        400: {"description": "CSV inválido ou campos faltando"}
    }
)
async def upload_csv_recadastrar(file: UploadFile = File(..., description="Arquivo CSV com as cartas para recadastrar")) -> CsvUploadResponseDTO:
    try:
        # Validar extensão
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Arquivo deve ser CSV")
        
        # Ler conteúdo
        content = await file.read()
        
        # Validar CSV
        csv_reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
        required_fields = ['numero', 'colecao', 'tipo', 'idioma', 'preco', 'quantidade']
        
        if not all(field in csv_reader.fieldnames for field in required_fields):
            raise HTTPException(
                status_code=400, 
                detail=f"CSV deve conter os campos: {', '.join(required_fields)}"
            )
        
        # Contar linhas
        rows = list(csv_reader)
        total_linhas = len(rows)
        
        # Gerar nome com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_id = f"file_{timestamp}"
        s3_key = f"csv-recadastrar/{timestamp}_{file.filename}"
        
        # Upload para S3
        s3 = boto3.client('s3')
        bucket_name = os.getenv('S3_BUCKET', 'myp-cards-csv')
        
        s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=content,
            ContentType='text/csv',
            Metadata={'operation': 'recadastrar'}
        )
        
        return CsvUploadResponseDTO(
            message="CSV enviado com sucesso. Recadastro iniciado.",
            file_id=file_id,
            s3_key=s3_key,
            total_linhas=total_linhas
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")

@router.get(
    "/status/{file_id}",
    response_model=FileStatusDTO,
    status_code=status.HTTP_200_OK,
    summary="Consultar status de processamento",
    description="""
    Retorna status e progresso do processamento do arquivo CSV.
    
    **Status possíveis:**
    - `PENDING`: Aguardando processamento
    - `PROCESSING`: Em processamento
    - `COMPLETED`: Finalizado com sucesso
    - `FAILED`: Falhou
    
    **Informações retornadas:**
    - Progresso percentual
    - Total de chunks processados
    - Linhas com erro (se houver)
    """,
    responses={
        200: {
            "description": "Status do arquivo",
            "content": {
                "application/json": {
                    "example": {
                        "file_id": "file_20260118_200500",
                        "status": "PROCESSING",
                        "total_linhas": 100,
                        "total_chunks": 2,
                        "chunks_processados": 1,
                        "progresso_percentual": 50.0,
                        "linhas_erro": [],
                        "created_at": "2026-01-18T20:05:00",
                        "updated_at": "2026-01-18T20:06:30"
                    }
                }
            }
        },
        404: {"description": "Arquivo não encontrado"}
    }
)
async def get_file_status(file_id: str) -> FileStatusDTO:
    try:
        dynamodb = boto3.resource('dynamodb')
        table_name = os.getenv('DYNAMODB_TABLE', 'myp-cards-files')
        table = dynamodb.Table(table_name)
        
        response = table.get_item(Key={'file_id': file_id})
        
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
        item = response['Item']
        
        # Calcular progresso
        total_chunks = item.get('total_chunks', 0)
        chunks_processados = item.get('chunks_processados', 0)
        progresso = (chunks_processados / total_chunks * 100) if total_chunks > 0 else 0
        
        return FileStatusDTO(
            file_id=item['file_id'],
            status=item['status'],
            total_linhas=item['total_linhas'],
            total_chunks=total_chunks,
            chunks_processados=chunks_processados,
            progresso_percentual=round(progresso, 2),
            linhas_erro=item.get('linhas_erro', []),
            created_at=item['created_at'],
            updated_at=item['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar status: {str(e)}")

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Verifica se a API está funcionando",
    responses={
        200: {
            "description": "API funcionando",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "message": "MYP Cards API está funcionando"
                    }
                }
            }
        }
    }
)
async def health_check():
    return {"status": "ok", "message": "MYP Cards API está funcionando"}

# ==================== INVENTORY ENDPOINTS ====================

@router.post(
    "/inventory/sync",
    status_code=status.HTTP_200_OK,
    summary="Sincronizar inventário",
    description="Inicia scraping assíncrono do inventário completo em paralelo"
)
async def sync_inventory():
    """Inicia sincronização assíncrona do inventário"""
    from use_cases.sync_inventory_use_case import SyncInventoryUseCase
    
    try:
        use_case = SyncInventoryUseCase()
        result = use_case.execute()
        
        if not result['success']:
            raise HTTPException(status_code=429, detail=result['error'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar sincronização: {str(e)}")

@router.get(
    "/inventory/status/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Status de sincronização",
    description="Retorna progresso da sincronização em andamento"
)
async def get_inventory_status(job_id: str):
    """Consulta status de um job de sincronização"""
    try:
        dynamodb = boto3.resource('dynamodb')
        jobs_table = dynamodb.Table(os.getenv('INVENTORY_JOBS_TABLE'))
        
        response = jobs_table.get_item(Key={'job_id': job_id})
        
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Job não encontrado")
        
        item = response['Item']
        
        total_ranges = item.get('total_ranges', 0)
        ranges_completed = item.get('ranges_completed', 0)
        progress = (ranges_completed / total_ranges * 100) if total_ranges > 0 else 0
        
        return {
            'job_id': item['job_id'],
            'status': item['status'],
            'total_ranges': total_ranges,
            'ranges_completed': ranges_completed,
            'progress_percent': round(progress, 2),
            'total_cards': item.get('total_cards'),
            'started_at': item['started_at'],
            'completed_at': item.get('completed_at'),
            'error': item.get('error')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar status: {str(e)}")

@router.get(
    "/inventory/summary",
    status_code=status.HTTP_200_OK,
    summary="Resumo do inventário",
    description="Retorna agregados da última contagem (rápido)"
)
async def get_inventory_summary():
    """Retorna apenas agregados do inventário"""
    try:
        dynamodb = boto3.resource('dynamodb')
        data_table = dynamodb.Table(os.getenv('INVENTORY_DATA_TABLE'))
        
        response = data_table.get_item(Key={'pk': 'LATEST'})
        
        if 'Item' not in response:
            raise HTTPException(
                status_code=404,
                detail="Nenhum inventário disponível. Execute /sync primeiro."
            )
        
        item = response['Item']
        
        return {
            'total_cards': item['total_cards'],
            'by_collection': item['by_collection'],
            'by_type': item['by_type'],
            'by_language': item['by_language'],
            'updated_at': item['updated_at'],
            'job_id': item['job_id']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar resumo: {str(e)}")

@router.get(
    "/inventory",
    status_code=status.HTTP_200_OK,
    summary="Consultar inventário",
    description="Retorna cartas do inventário com filtros opcionais"
)
async def get_inventory(
    colecao: Optional[str] = None,
    numero: Optional[str] = None,
    tipo: Optional[str] = None,
    idioma: Optional[str] = None,
    preco_min: Optional[float] = None,
    preco_max: Optional[float] = None,
    quantidade_min: Optional[int] = None,
    limit: Optional[int] = 1000
):
    """Consulta inventário com filtros"""
    from use_cases.get_inventory_use_case import GetInventoryUseCase
    
    try:
        use_case = GetInventoryUseCase()
        result = use_case.execute(
            colecao=colecao,
            numero=numero,
            tipo=tipo,
            idioma=idioma,
            preco_min=preco_min,
            preco_max=preco_max,
            quantidade_min=quantidade_min,
            limit=limit
        )
        
        if not result['success']:
            raise HTTPException(status_code=404, detail=result['error'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar inventário: {str(e)}")

