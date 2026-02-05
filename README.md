# MYP Cards - API de Automação de Estoque

API para gerenciamento automatizado de cartas no MYP Cards com processamento em massa via CSV.

## 🚀 Funcionalidades

### 1. Recadastrar Cartas
Exclui e recadastra cartas com os mesmos dados (útil para atualizar informações do sistema).

### 2. Atualizar Cartas
Atualiza preços e quantidades de cartas específicas.

### 3. Upload CSV em Massa
- Upload de arquivo CSV para S3
- Processamento automático em chunks de 50 linhas
- Até 50 lambdas processando simultaneamente
- Apenas 1 arquivo por vez

### 4. Consultar Status
Acompanha progresso do processamento com:
- Status (PENDING, PROCESSING, COMPLETED, FAILED)
- Progresso percentual
- Linhas com erro

### 5. Inventário
- Sincronização automática do inventário completo
- Consulta com filtros (coleção, tipo, idioma, preço, quantidade)
- Exportação em CSV

### 6. Precificação Dinâmica Automatizada ⭐ NOVO
- Execução diária às 18h
- Sincroniza inventário antes de precificar
- Aplica regras de precificação por faixa de preço
- Detecta vendas e adições de estoque
- Protege estoque com disponibilização controlada
- Rastreamento completo de estado

## 🏗️ Arquitetura

```
API Gateway → Lambda Proxy (FastAPI)
                ↓
            Endpoints

S3 Upload → Lambda Producer → SQS → 50x Lambda Consumer
                ↓                           ↓
            DynamoDB ← ← ← ← ← ← ← ← ← ← ← ←

Inventory Sync → 5x Lambda Scraper (paralelo por faixa de preço)
                        ↓
                    DynamoDB + S3
```

## 📋 Formato CSV

```csv
numero,colecao,tipo,idioma,preco,quantidade
161/131,PRE,normal,portugues,2500.00,5
077/131,SVI,foil,ingles,150.00,2
248/182,PAL,reverse-foil,portugues,399.00,1
```

**Campos:**
- `numero`: Número da carta (ex: 161/131)
- `colecao`: Sigla da coleção (ex: PRE, SVI, PAL)
- `tipo`: normal, foil, reverse-foil, etc
- `idioma`: portugues, ingles, espanhol, etc
- `preco`: Será **substituído**
- `quantidade`: Será **incrementada**

## 🛠️ Tecnologias

- **Backend**: FastAPI + Python 3.11
- **Scraping**: Cloudscraper + BeautifulSoup4
- **AWS**: Lambda, API Gateway, S3, SQS, DynamoDB
- **IaC**: AWS SAM
- **CI/CD**: GitHub Actions

## 🌍 Ambientes

- `develop` → myp-cards-dev
- `staging` → myp-cards-staging
- `main` → myp-cards-prod

## 🚀 Deploy

Deploy automático via GitHub Actions ao fazer push nas branches.

### Configuração Inicial

1. Configure secrets no GitHub:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

2. Push para a branch desejada:
```bash
git push origin develop
```

### Deploy Manual (opcional)

```bash
sam build
sam deploy --config-env develop
```

## 💻 Desenvolvimento Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Edite o .env com suas credenciais

# Rodar API local
python3 main.py
```

API disponível em: http://localhost:8000

Swagger: http://localhost:8000/docs

## 📡 Endpoints

### Operações de Cartas

#### POST /api/v1/recadastrar
Recadastra cartas (exclui e cria novamente).

```bash
curl -X POST http://localhost:8000/api/v1/recadastrar \
  -H "Content-Type: application/json" \
  -d '{
    "cartas": [
      {
        "numero": "077/131",
        "colecao": "SVI",
        "tipo": "normal",
        "idioma": "ingles"
      }
    ]
  }'
```

#### POST /api/v1/atualizar
Atualiza preços e quantidades.

```bash
curl -X POST http://localhost:8000/api/v1/atualizar \
  -H "Content-Type: application/json" \
  -d '{
    "cartas": [
      {
        "numero": "077/131",
        "colecao": "SVI",
        "tipo": "normal",
        "idioma": "ingles",
        "preco": "150.00",
        "quantidade": "5"
      }
    ]
  }'
```

#### POST /api/v1/upload-csv
Upload de CSV para processamento em massa.

```bash
curl -X POST http://localhost:8000/api/v1/upload-csv \
  -F "file=@exemplo.csv" \
  -F "operation=atualizar"
```

#### GET /api/v1/status/{file_id}
Consulta status do processamento.

```bash
curl http://localhost:8000/api/v1/status/file_20260118_200500
```

### Inventário

#### POST /api/v1/inventory/sync
Inicia sincronização do inventário (~1 minuto).

```bash
curl -X POST https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/sync
```

#### GET /api/v1/inventory/status/{job_id}
Consulta progresso da sincronização.

```bash
curl https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/status/inv_20260202_010624
```

#### GET /api/v1/inventory/summary
Resumo agregado (rápido).

```bash
curl https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/summary
```

**Retorna:**
```json
{
  "total_cards": 1200,
  "by_collection": {"PRE": 316, "MEG": 130},
  "by_type": {"normal": 671, "foil": 106},
  "by_language": {"portugues": 911, "ingles": 289}
}
```

#### GET /api/v1/inventory
Consulta cartas com filtros.

**Filtros disponíveis:**
- `colecao` - Sigla da coleção
- `numero` - Número da carta
- `tipo` - normal, foil, reverse-foil
- `idioma` - portugues, ingles, espanhol
- `preco_min` / `preco_max` - Faixa de preço
- `quantidade_min` - Quantidade mínima
- `limit` - Limite de resultados (padrão: 1000)

```bash
# Cartas foil da coleção PRE
curl "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory?colecao=PRE&tipo=foil"

# Cartas em inglês acima de R$10
curl "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory?idioma=ingles&preco_min=10"
```

#### GET /api/v1/inventory/export
Exporta inventário em CSV (download direto).

```bash
# Exportar tudo
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export"

# Exportar apenas PRE
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?colecao=PRE"

# Exportar cartas foil em inglês acima de R$10
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?tipo=foil&idioma=ingles&preco_min=10"
```

## 🐍 Scripts de Exportação

### Exportação Customizada
```bash
# Exportar com filtros específicos
python3 export_inventory.py --colecao PRE --tipo foil --output pre_foil.csv
```

### Exportação Completa Organizada
```bash
# Exporta todas as combinações de coleção/tipo/idioma em arquivos separados
python3 export_all_collections.py

# Resultado: 27 arquivos CSV na pasta exports/
# Exemplo: pre_normal_portugues.csv, meg_foil_ingles.csv, etc
```

## ⚙️ Configurações

- **Chunk Size**: 50 linhas por chunk
- **Concorrência**: 50 lambdas simultâneas
- **Timeout Lambda**: 15 minutos
- **Delay entre operações**: 2 segundos (evitar bloqueio)
- **Inventário**: Sincronização paralela em 5 faixas de preço

## 📊 Monitoramento

```bash
# Logs da API
aws logs tail /aws/lambda/myp-api --follow

# Logs do Producer
aws logs tail /aws/lambda/myp-producer --follow

# Logs do Consumer
aws logs tail /aws/lambda/myp-consumer --follow

# Logs do Inventory Scraper
aws logs tail /aws/lambda/myp-inventory-scraper --follow

# Status dos arquivos
aws dynamodb scan --table-name myp-cards-files
```

## 🔒 Segurança

- Credenciais hardcoded no template (projeto pessoal)
- TODO: Migrar para AWS Secrets Manager

## 📝 TODO

- [ ] Implementar criação automática de cartas não encontradas
- [ ] Adicionar retry logic com exponential backoff
- [ ] Migrar credenciais para Secrets Manager
- [ ] Adicionar testes unitários
- [ ] Implementar logs estruturados
- [ ] Dashboard de monitoramento

## 📄 Licença

Projeto pessoal - Uso privado

## 👤 Autor

Alex Carmo - alex.carmo91@gmail.com