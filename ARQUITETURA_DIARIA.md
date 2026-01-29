# 📅 ARQUITETURA PARA EXECUÇÃO DIÁRIA

## 🎯 OBJETIVO
Executar automaticamente a estratégia de frete único todos os dias às 6h da manhã, atualizando preços de todas as cartas ativas.

## 🏗️ COMPONENTES NECESSÁRIOS

### **1. NOVOS RECURSOS AWS**

#### **EventBridge Schedule**
```yaml
DailyPriceUpdateSchedule:
  Type: AWS::Events::Rule
  Properties:
    ScheduleExpression: "cron(0 9 * * ? *)"  # 6h BRT = 9h UTC
    State: ENABLED
    Targets:
      - Arn: !GetAtt DailyOrchestratorFunction.Arn
        Id: DailyPriceUpdate
```

#### **Lambda Orquestrador** (`daily_orchestrator.py`)
- Busca cartas ativas do estoque
- Divide em chunks de 50
- Envia para SQS de precificação
- Registra execução no DynamoDB

#### **Lambda Consumer** (`pricing_consumer.py`)
- Processa chunks de precificação
- Aplica estratégia de frete único
- Atualiza preços no MYP
- Registra mudanças no DynamoDB

#### **SQS Pricing Queue**
- Fila dedicada para precificação diária
- Separada da fila de upload CSV
- Timeout de 15 minutos

#### **DynamoDB Tables**
```yaml
# Controle de execuções diárias
DailyExecutionControl:
  - execution_date (PK)
  - total_cards
  - chunks
  - status
  - timestamp

# Log de mudanças de preço
PriceChangesLog:
  - carta_id (PK)
  - execution_date (SK)
  - preco_anterior
  - preco_novo
  - estrategia_aplicada
  - estoque
```

### **2. INTEGRAÇÕES NECESSÁRIAS**

#### **Busca de Cartas Ativas**
- API do MYP para listar cartas do estoque
- Filtrar apenas cartas ativas/disponíveis
- Incluir dados de estoque atual

#### **Estratégia de Precificação**
- Integrar `precificacao_dinamica.py` como Lambda Layer
- Aplicar lógica de frete único
- Respeitar proteções (50% estoque, máximo 25% premium)

#### **Atualização no MYP**
- API para atualizar preços
- Controle de rate limiting (2s entre operações)
- Retry logic para falhas

### **3. FLUXO DE EXECUÇÃO**

```
06:00 BRT → EventBridge → Daily Orchestrator
                              ↓
                        Busca cartas ativas
                              ↓
                        Divide em chunks (50)
                              ↓
                        SQS Pricing Queue
                              ↓
                        50x Pricing Consumer
                              ↓
                        Aplica estratégia frete
                              ↓
                        Atualiza MYP + DynamoDB
                              ↓
                        Registra mudanças
```

### **4. MONITORAMENTO**

#### **CloudWatch Alarms**
- Falhas na execução diária
- Tempo de processamento > 30min
- Taxa de erro > 5%

#### **Logs Estruturados**
- Execução iniciada/finalizada
- Cartas processadas vs com erro
- Mudanças de preço aplicadas

#### **Dashboard**
- Status da última execução
- Número de cartas processadas
- Mudanças de preço por dia

## 🚀 IMPLEMENTAÇÃO

### **Fase 1: Infraestrutura**
1. Adicionar recursos no `template.yaml`
2. Deploy da nova arquitetura
3. Configurar EventBridge

### **Fase 2: Lógica de Negócio**
1. Implementar busca de cartas ativas
2. Integrar estratégia de precificação
3. Implementar atualização no MYP

### **Fase 3: Monitoramento**
1. Configurar CloudWatch Alarms
2. Criar dashboard de acompanhamento
3. Implementar notificações

## 📊 ESTIMATIVA DE CUSTOS

**Para 1000 cartas/dia:**
- Lambda executions: ~$0.50/mês
- DynamoDB writes: ~$1.00/mês
- SQS messages: ~$0.10/mês
- **Total: ~$1.60/mês**

## 🔒 SEGURANÇA

- Credenciais via Secrets Manager
- IAM roles com least privilege
- Logs sem dados sensíveis
- Rate limiting para APIs

## ✅ PRÓXIMOS PASSOS

1. **Criar** arquivos `daily_orchestrator.py` e `pricing_consumer.py` ✅
2. **Atualizar** `template.yaml` com novos recursos
3. **Implementar** busca de cartas ativas
4. **Testar** execução manual
5. **Configurar** schedule diário
6. **Monitorar** primeiras execuções
