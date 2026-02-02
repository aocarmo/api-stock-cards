# Exportar Inventário para CSV

Existem **duas formas** de exportar o inventário:

1. **Via API (curl)** - Download direto do CSV
2. **Via Script Python** - Mais flexível para automação

---

## 🌐 Método 1: Via API (Recomendado)

### Endpoint
```
GET /api/v1/inventory/export
```

### URL Base
```
https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export
```

### 📝 Exemplos com curl

#### Exportar tudo
```bash
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export"
# Baixa: inventario.csv
```

#### Filtrar por coleção
```bash
# Apenas coleção PRE
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?colecao=PRE"
# Baixa: pre.csv

# Apenas coleção MEG
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?colecao=MEG"
# Baixa: meg.csv

# Apenas coleção DRI
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?colecao=DRI"
# Baixa: dri.csv
```

#### Filtrar por tipo
```bash
# Apenas cartas foil
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?tipo=foil"
# Baixa: foil.csv

# Apenas cartas reverse-foil
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?tipo=reverse-foil"
# Baixa: reverse-foil.csv

# Apenas cartas normais
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?tipo=normal"
# Baixa: normal.csv
```

#### Filtrar por idioma
```bash
# Apenas cartas em português
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?idioma=portugues"
# Baixa: portugues.csv

# Apenas cartas em inglês
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?idioma=ingles"
# Baixa: ingles.csv

# Apenas cartas em espanhol
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?idioma=espanhol"
# Baixa: espanhol.csv
```

#### Filtrar por preço
```bash
# Cartas até R$5
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?preco_max=5"

# Cartas entre R$10 e R$50
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?preco_min=10&preco_max=50"

# Cartas acima de R$100
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?preco_min=100"
```

#### Filtrar por quantidade
```bash
# Apenas cartas com estoque (quantidade >= 1)
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?quantidade_min=1"

# Apenas cartas com estoque alto (quantidade >= 5)
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?quantidade_min=5"
```

#### Combinar múltiplos filtros
```bash
# Cartas foil da coleção PRE em português
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?colecao=PRE&tipo=foil&idioma=portugues"
# Baixa: pre_foil_portugues.csv

# Cartas reverse-foil baratas (até R$5) com estoque
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?tipo=reverse-foil&preco_max=5&quantidade_min=1"
# Baixa: reverse-foil.csv

# Cartas em inglês da coleção MEG acima de R$10
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?colecao=MEG&idioma=ingles&preco_min=10"
# Baixa: meg_ingles.csv

# Cartas normais em português entre R$1 e R$3
curl -O "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?tipo=normal&idioma=portugues&preco_min=1&preco_max=3"
# Baixa: normal_portugues.csv
```

#### Usar no navegador
Basta colar a URL no navegador para download automático:
```
https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/export?colecao=PRE
```

---

## 🐍 Método 2: Via Script Python

## 🚀 Uso Básico

```bash
python3 export_inventory.py [opções]
```

## 📋 Filtros Disponíveis

| Filtro | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| `--colecao` | string | Sigla da coleção | PRE, SVI, PAL, MEG, DRI, PFL |
| `--numero` | string | Número da carta | 077/131, 024/131 |
| `--tipo` | string | Tipo da carta | normal, foil, reverse-foil |
| `--idioma` | string | Idioma da carta | portugues, ingles, espanhol |
| `--preco-min` | float | Preço mínimo | 10.00, 50.50 |
| `--preco-max` | float | Preço máximo | 100.00, 500.00 |
| `--quantidade-min` | int | Quantidade mínima | 1, 5, 10 |
| `--output` | string | Arquivo de saída | inventario.csv (padrão) |

## 📝 Exemplos

### Exportar tudo
```bash
python3 export_inventory.py
# Gera: inventario.csv com todas as 1200 cartas
```

### Filtrar por coleção
```bash
# Apenas coleção PRE
python3 export_inventory.py --colecao PRE --output pre.csv

# Apenas coleção MEG
python3 export_inventory.py --colecao MEG --output meg.csv

# Apenas coleção DRI
python3 export_inventory.py --colecao DRI --output dri.csv
```

### Filtrar por tipo
```bash
# Apenas cartas foil
python3 export_inventory.py --tipo foil --output foil.csv

# Apenas cartas reverse-foil
python3 export_inventory.py --tipo reverse-foil --output reverse.csv

# Apenas cartas normais
python3 export_inventory.py --tipo normal --output normal.csv
```

### Filtrar por idioma
```bash
# Apenas cartas em português
python3 export_inventory.py --idioma portugues --output pt.csv

# Apenas cartas em inglês
python3 export_inventory.py --idioma ingles --output en.csv

# Apenas cartas em espanhol
python3 export_inventory.py --idioma espanhol --output es.csv
```

### Filtrar por preço
```bash
# Cartas até R$5
python3 export_inventory.py --preco-max 5 --output baratas.csv

# Cartas entre R$10 e R$50
python3 export_inventory.py --preco-min 10 --preco-max 50 --output medias.csv

# Cartas acima de R$100
python3 export_inventory.py --preco-min 100 --output caras.csv
```

### Filtrar por quantidade
```bash
# Apenas cartas com estoque (quantidade >= 1)
python3 export_inventory.py --quantidade-min 1 --output com_estoque.csv

# Apenas cartas com estoque alto (quantidade >= 5)
python3 export_inventory.py --quantidade-min 5 --output estoque_alto.csv

# Cartas sem estoque (quantidade = 0)
# Nota: não há filtro para quantidade exata, use --quantidade-min 0 e filtre manualmente
```

### Filtrar por carta específica
```bash
# Buscar carta específica
python3 export_inventory.py --numero "077/131" --colecao SVI --output carta_especifica.csv
```

### Combinar múltiplos filtros
```bash
# Cartas foil da coleção PRE em português
python3 export_inventory.py --colecao PRE --tipo foil --idioma portugues --output pre_foil_pt.csv

# Cartas reverse-foil baratas (até R$5) com estoque
python3 export_inventory.py --tipo reverse-foil --preco-max 5 --quantidade-min 1 --output reverse_baratas_estoque.csv

# Cartas em inglês da coleção MEG acima de R$10
python3 export_inventory.py --colecao MEG --idioma ingles --preco-min 10 --output meg_ingles_caras.csv

# Cartas normais em português entre R$1 e R$3
python3 export_inventory.py --tipo normal --idioma portugues --preco-min 1 --preco-max 3 --output normal_pt_1a3.csv
```

## 📊 Formato do CSV

O arquivo gerado contém as seguintes colunas:

```csv
numero,colecao,tipo,idioma,preco,quantidade
077/131,SVI,foil,ingles,150.00,2
024/131,PRE,normal,portugues,1.99,5
```

### Colunas:
- **numero**: Número da carta (ex: 077/131)
- **colecao**: Sigla da coleção (ex: PRE, SVI, MEG)
- **tipo**: Tipo da carta (normal, foil, reverse-foil)
- **idioma**: Idioma (portugues, ingles, espanhol)
- **preco**: Preço em reais (formato: 0.00)
- **quantidade**: Quantidade em estoque

## 🎯 Casos de Uso Comuns

### 1. Inventário completo para backup
```bash
python3 export_inventory.py --output backup_$(date +%Y%m%d).csv
```

### 2. Cartas para vender (com estoque)
```bash
python3 export_inventory.py --quantidade-min 1 --output para_vender.csv
```

### 3. Cartas caras para seguro
```bash
python3 export_inventory.py --preco-min 50 --output cartas_valiosas.csv
```

### 4. Cartas em português para catálogo local
```bash
python3 export_inventory.py --idioma portugues --output catalogo_pt.csv
```

### 5. Cartas foil de todas as coleções
```bash
python3 export_inventory.py --tipo foil --output todas_foil.csv
```

### 6. Análise de preços por coleção
```bash
# Exportar cada coleção separadamente
python3 export_inventory.py --colecao PRE --output analise_pre.csv
python3 export_inventory.py --colecao MEG --output analise_meg.csv
python3 export_inventory.py --colecao DRI --output analise_dri.csv
python3 export_inventory.py --colecao PFL --output analise_pfl.csv
```

## ⚠️ Notas

- O limite máximo é de 10.000 cartas por exportação
- O inventário atual tem ~1.200 cartas
- Os filtros são aplicados no servidor (API)
- O arquivo CSV usa vírgula como separador
- Preços estão em formato decimal (ex: 10.00, não 10,00)

## 🔄 Atualizar Inventário

Para ter dados atualizados, execute a sincronização antes:

```bash
curl -X POST https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/sync
```

Aguarde ~1 minuto e depois exporte os dados.

## 📞 Suporte

Para mais informações sobre a API, consulte o README principal do projeto.
