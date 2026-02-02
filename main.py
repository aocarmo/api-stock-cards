"""
FastAPI app - apenas configuração
"""
from fastapi import FastAPI
from routes.routes import router

app = FastAPI(
    title="MYP Cards API",
    description="""
    API para gerenciamento automatizado de cartas do MYP Cards.
    
    ## Funcionalidades
    
    ### 1. Recadastrar Cartas
    Exclui e recadastra cartas com os mesmos dados (útil para atualizar informações do sistema).
    
    ### 2. Atualizar Cartas
    Atualiza preços e quantidades de cartas específicas.
    
    ### 3. Upload CSV em Massa
    Faz upload de arquivo CSV para processamento em massa:
    - Arquivo é salvo no S3
    - Sistema quebra em chunks de 50 linhas
    - Processa até 50 chunks simultaneamente
    - Apenas 1 arquivo pode ser processado por vez
    
    ### 4. Consultar Status
    Verifica progresso do processamento do arquivo CSV:
    - Status (PENDING, PROCESSING, COMPLETED, FAILED)
    - Progresso percentual
    
    ### 5. Inventário
    Gerenciamento de inventário com contagem assíncrona:
    - Sincronização paralela por faixa de preço
    - Consulta com filtros (coleção, tipo, idioma, preço, quantidade)
    - Agregados em tempo real
    - Linhas com erro
    
    ## Formato CSV
    
    ```csv
    numero,colecao,tipo,idioma,preco,quantidade
    161/131,PRE,normal,portugues,2500.00,5
    077/131,SVI,foil,ingles,150.00,2
    ```
    
    **Campos:**
    - `numero`: Número da carta (ex: 161/131)
    - `colecao`: Sigla da coleção (ex: PRE, SVI, PAL)
    - `tipo`: Tipo da carta (normal, foil, reverse-foil, etc)
    - `idioma`: Idioma (portugues, ingles, espanhol, etc)
    - `preco`: Preço - será **substituído**
    - `quantidade`: Quantidade - será **incrementada**
    
    ## Comportamento
    
    - **Carta existe**: Atualiza preço (substitui) e quantidade (incrementa)
    - **Carta não existe**: Retorna erro (TODO: criar carta automaticamente)
    
    ## Limites
    
    - Chunk size: 50 linhas
    - Concorrência: 50 lambdas simultâneas
    - Timeout por chunk: 15 minutos
    - Delay entre operações: 2 segundos (evitar bloqueio)
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "MYP Cards Automation",
        "email": "alex.carmo91@gmail.com"
    },
    license_info={
        "name": "Private"
    }
)

# Registrar rotas
app.include_router(router)

@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz - informações da API"""
    return {
        "message": "MYP Cards API",
        "version": "2.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "recadastrar": "/api/v1/recadastrar",
            "atualizar": "/api/v1/atualizar",
            "upload_csv": "/api/v1/upload-csv",
            "status": "/api/v1/status/{file_id}",
            "health": "/api/v1/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
