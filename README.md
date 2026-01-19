# MYP Cards - Automação Lambda

## Arquitetura

3 Lambdas independentes para automatizar cadastro/atualização de cartas no MYP Cards.

### Lambda 1: Login
- **Função**: Autentica e salva sessão no Parameter Store
- **Trigger**: Manual ou EventBridge (renovar sessão a cada X horas)
- **Timeout**: 30s
- **Memory**: 256MB

### Lambda 2: Recadastrar Cartas
- **Função**: Descadastra e recadastra cartas com mesmos dados
- **Input**: Lista de cartas com ID
- **Timeout**: 5min (300s)
- **Memory**: 512MB

### Lambda 3: Atualizar CSV
- **Função**: Lê CSV do S3 e atualiza estoque/preços
- **Input**: Bucket e key do CSV
- **Timeout**: 15min (900s)
- **Memory**: 512MB

## Deploy

```bash
# Criar layer com dependências
pip install -r requirements.txt -t python/
zip -r layer.zip python/

# Upload layer
aws lambda publish-layer-version \
  --layer-name myp-cards-deps \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.11

# Criar Lambdas
aws lambda create-function \
  --function-name myp-login \
  --runtime python3.11 \
  --handler lambda_login.lambda_handler \
  --zip-file fileb://lambda_login.zip \
  --role arn:aws:iam::ACCOUNT:role/lambda-role \
  --layers arn:aws:lambda:REGION:ACCOUNT:layer:myp-cards-deps:1 \
  --timeout 30 \
  --memory-size 256
```

## Permissões IAM

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:PutParameter"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/myp/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::SEU-BUCKET/*"
    }
  ]
}
```

## Configuração

Criar parâmetros no Parameter Store:
```bash
aws ssm put-parameter --name /myp/username --value "seu-email" --type SecureString
aws ssm put-parameter --name /myp/password --value "sua-senha" --type SecureString
```

## Uso

### 1. Login
```bash
aws lambda invoke --function-name myp-login output.json
```

### 2. Recadastrar
```bash
aws lambda invoke --function-name myp-recadastrar \
  --payload '{"cartas":[{"id":123,"nome":"Pikachu","preco":10.50,"quantidade":2}]}' \
  output.json
```

### 3. Atualizar CSV
```bash
# Upload CSV para S3
aws s3 cp cartas.csv s3://seu-bucket/cartas.csv

# Invocar Lambda
aws lambda invoke --function-name myp-atualizar-csv \
  --payload '{"bucket":"seu-bucket","key":"cartas.csv"}' \
  output.json
```

## Formato CSV

```csv
numero,preco,quantidade
153/131,599.00,1
248/182,399.00,1
013/094,24.90,2
```

**Campos:**
- `numero`: Número da carta (ex: 153/131)
- `preco`: Novo preço (use 0 para manter o atual)
- `quantidade`: Quantidade a ADICIONAR (não substituir)

## Próximos Passos

1. **Testar URLs reais**: Preciso que você me passe as URLs corretas de:
   - Busca de cartas
   - Cadastro de carta
   - Atualização de carta
   - Exclusão de carta

2. **Ajustar seletores HTML**: Preciso ver o HTML real para ajustar os seletores BeautifulSoup

3. **Adicionar retry logic**: Para lidar com timeouts/erros temporários

4. **Logs estruturados**: CloudWatch Logs com métricas


# Formato CSV para Cadastro/Atualização em Massa

## Colunas obrigatórias:
- numero: Número da carta (ex: 161/131)
- colecao: Sigla da coleção (ex: PRE, SVI, PAL)
- tipo: Tipo da carta (normal, foil, reverse-foil, etc)
- idioma: Idioma (portugues, ingles, espanhol, etc)
- preco: Preço (ex: 2500.00) - será substituído
- quantidade: Quantidade (ex: 5) - será incrementada

## Exemplo:
```csv
numero,colecao,tipo,idioma,preco,quantidade
161/131,PRE,normal,portugues,2500.00,5
077/131,SVI,foil,ingles,150.00,2
248/182,PAL,reverse-foil,portugues,399.00,1
```

## Comportamento:
- Se a carta existir: atualiza preço (substitui) e quantidade (incrementa)
- Se não existir: cria nova carta com os dados fornecidos
