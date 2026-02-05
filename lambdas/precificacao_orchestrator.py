"""
Lambda Orchestrator - Precificação Dinâmica
Dois modos de operação:
1. EventBridge (18h): Inicia sync de inventário com trigger_precificacao=True
2. SQS Trigger: Processa precificação após sync completar
"""
import json
import os
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')
lambda_client = boto3.client('lambda')

PRECIFICACAO_JOBS_TABLE = os.environ['PRECIFICACAO_JOBS_TABLE']
INVENTORY_DATA_TABLE = os.environ['INVENTORY_DATA_TABLE']
PRECIFICACAO_PRODUCER_QUEUE = os.environ['PRECIFICACAO_PRODUCER_QUEUE']
PRECO_MAXIMO = float(os.environ.get('PRECO_MAXIMO', '50.00'))
CHUNK_SIZE = 10

def lambda_handler(event, context):
    """
    Modo 1 (EventBridge): Inicia sync de inventário
    Modo 2 (SQS): Processa precificação
    """
    
    # Verificar se é trigger do EventBridge ou SQS
    if 'Records' in event:
        # Modo 2: Triggered por SQS (sync completou)
        return processar_precificacao(event)
    else:
        # Modo 1: Triggered por EventBridge (18h)
        return iniciar_sync_inventario()


def iniciar_sync_inventario():
    """
    Modo 1: Inicia sync de inventário com flag para trigger de precificação
    """
    print("Modo 1: Iniciando sync de inventário...")
    
    try:
        # Invocar API de sync com parâmetro trigger_precificacao
        response = lambda_client.invoke(
            FunctionName=os.environ.get('API_FUNCTION', 'myp-cards-api-dev'),
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'path': '/api/v1/inventory/sync',
                'httpMethod': 'POST',
                'body': json.dumps({'trigger_precificacao': True})
            })
        )
        
        result = json.loads(response['Payload'].read())
        body = json.loads(result.get('body', '{}'))
        
        print(f"✅ Sync iniciado: {body.get('job_id')}")
        print("⏳ Aguardando sync completar para iniciar precificação...")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Sync de inventário iniciado',
                'sync_job_id': body.get('job_id')
            })
        }
        
    except Exception as e:
        print(f"❌ Erro ao iniciar sync: {str(e)}")
        raise


def processar_precificacao(event):
    """
    Modo 2: Processa precificação após sync completar
    """
    print("Modo 2: Processando precificação...")
    
    job_id = f"prec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        print(f"Buscando inventário do DynamoDB...")
        
        inventory_table_name = INVENTORY_DATA_TABLE
        inventory_table = dynamodb.Table(inventory_table_name)
        
        # Scan completo da tabela de inventário
        cartas = []
        last_evaluated_key = None
        
        while True:
            if last_evaluated_key:
                response = inventory_table.scan(ExclusiveStartKey=last_evaluated_key)
            else:
                response = inventory_table.scan()
            
            items = response.get('Items', [])
            
            # Filtrar apenas cartas (não metadados)
            for item in items:
                pk = item.get('pk', '')
                if pk.startswith('CARD#'):
                    cartas.append({
                        'numero': item.get('numero'),
                        'colecao': item.get('colecao'),
                        'tipo': item.get('tipo'),
                        'idioma': item.get('idioma'),
                        'preco': float(item.get('preco', 0)),
                        'quantidade': int(item.get('quantidade', 0))
                    })
            
            last_evaluated_key = response.get('LastEvaluatedKey')
            if not last_evaluated_key:
                break
        
        print(f"Total de cartas no inventário: {len(cartas)}")
        
        # 2. Filtrar cartas elegíveis
        cartas_elegiveis = [
            carta for carta in cartas
            if float(carta.get('preco', 0)) <= PRECO_MAXIMO
        ]
        
        print(f"Cartas elegíveis (≤ R$ {PRECO_MAXIMO}): {len(cartas_elegiveis)}")
        
        if not cartas_elegiveis:
            print("Nenhuma carta elegível para precificação")
            return {'statusCode': 200, 'body': 'Nenhuma carta elegível'}
        
        # 3. Criar job no DynamoDB
        table = dynamodb.Table(PRECIFICACAO_JOBS_TABLE)
        ttl = int(datetime.now().timestamp()) + (7 * 24 * 60 * 60)  # 7 dias
        
        # Inicializar cards_state com estado inicial
        cards_state = {}
        for carta in cartas_elegiveis:
            carta_key = f"{carta['numero']}#{carta['colecao']}#{carta['tipo']}#{carta['idioma']}"
            cards_state[carta_key] = {
                'estoque_total': carta['quantidade'],
                'quantidade_disponivel': carta['quantidade'],  # Será atualizado
                'preco': carta['preco']
            }
        
        table.put_item(Item={
            'job_id': job_id,
            'status': 'PENDING',
            'started_at': datetime.now().isoformat(),
            'total_cards': len(cartas_elegiveis),
            'processed_cards': 0,
            'success_count': 0,
            'error_count': 0,
            'errors': [],
            'cards_state': cards_state,
            'ttl': ttl
        })
        
        print(f"Job criado no DynamoDB: {job_id}")
        
        # 4. Dividir em chunks
        chunks = [
            cartas_elegiveis[i:i + CHUNK_SIZE]
            for i in range(0, len(cartas_elegiveis), CHUNK_SIZE)
        ]
        
        print(f"Total de chunks: {len(chunks)}")
        
        # 5. Enviar chunks para SQS Producer
        queue_url = PRECIFICACAO_PRODUCER_QUEUE
        
        for idx, chunk in enumerate(chunks):
            message = {
                'job_id': job_id,
                'chunk_index': idx,
                'total_chunks': len(chunks),
                'cartas': chunk
            }
            
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message)
            )
        
        print(f"✅ {len(chunks)} chunks enviados para SQS Producer")
        
        # Atualizar status do job
        table.update_item(
            Key={'job_id': job_id},
            UpdateExpression='SET #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'PROCESSING'}
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'job_id': job_id,
                'total_cards': len(cartas_elegiveis),
                'total_chunks': len(chunks)
            })
        }
        
    except Exception as e:
        print(f"❌ Erro no orchestrator: {str(e)}")
        
        # Marcar job como falho
        try:
            table = dynamodb.Table(PRECIFICACAO_JOBS_TABLE)
            table.update_item(
                Key={'job_id': job_id},
                UpdateExpression='SET #status = :status, error = :error',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'FAILED',
                    ':error': str(e)
                }
            )
        except:
            pass
        
        raise
