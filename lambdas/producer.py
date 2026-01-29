"""
Lambda Producer - Quebra CSV em chunks e envia para SQS
"""
import json
import csv
import boto3
import os
from io import StringIO
from datetime import datetime

s3 = boto3.client('s3')
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

QUEUE_URL = os.environ['QUEUE_URL']
TABLE_NAME = os.environ['DYNAMODB_TABLE']
CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', '50'))  # Linhas por chunk

table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """Triggered por S3 quando CSV é uploaded"""
    print(f"🔄 Producer iniciado")
    print(f"📦 Event recebido: {json.dumps(event)}")
    
    try:
        # Verificar se há arquivo em processamento
        print("🔍 Verificando se há arquivo em processamento...")
        if has_processing_file():
            print("⚠️ Já existe um arquivo sendo processado")
            return {
                'statusCode': 429,
                'body': json.dumps({'error': 'Já existe um arquivo sendo processado'})
            }
        
        print("✅ Nenhum arquivo em processamento")
        
        # Pegar info do S3
        print("📥 Extraindo informações do evento S3...")
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        # Detectar operação (delete, recadastrar ou update)
        if key.startswith('csv-excluir/'):
            operation = 'delete'
        elif key.startswith('csv-recadastrar/'):
            operation = 'recadastrar'
        else:
            operation = 'update'
        print(f"🔧 Operação detectada: {operation}")
        
        print(f"📥 Processando CSV: s3://{bucket}/{key}")
        
        # Baixar e ler CSV
        print("⬇️ Baixando CSV do S3...")
        response = s3.get_object(Bucket=bucket, Key=key)
        csv_content = response['Body'].read().decode('utf-8')
        print(f"✅ CSV baixado: {len(csv_content)} bytes")
        
        print("📖 Lendo CSV...")
        csv_reader = csv.DictReader(StringIO(csv_content))
        rows = list(csv_reader)
        print(f"✅ CSV lido: {len(rows)} linhas")
        
        file_id = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        total_chunks = (len(rows) + CHUNK_SIZE - 1) // CHUNK_SIZE
        print(f"📦 Arquivo será dividido em {total_chunks} chunks de {CHUNK_SIZE} linhas")
        
        # Criar registro no DynamoDB
        print(f"💾 Criando registro no DynamoDB: {file_id}")
        table.put_item(Item={
            'file_id': file_id,
            'status': 'PROCESSING',
            's3_bucket': bucket,
            's3_key': key,
            'total_linhas': len(rows),
            'total_chunks': total_chunks,
            'chunks_processados': 0,
            'linhas_erro': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        })
        print("✅ Registro criado no DynamoDB")
        
        # Quebrar em chunks e enviar para SQS
        print(f"📤 Enviando {total_chunks} chunks para SQS...")
        for chunk_id in range(total_chunks):
            start = chunk_id * CHUNK_SIZE
            end = min(start + CHUNK_SIZE, len(rows))
            chunk_lines = rows[start:end]
            
            message = {
                'file_id': file_id,
                'chunk_id': chunk_id,
                'lines': chunk_lines,
                'operation': operation
            }
            print(f"  📨 Enviando chunk {chunk_id + 1}/{total_chunks} ({len(chunk_lines)} linhas)")
            
            sqs.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=json.dumps(message)
            )
        
        print(f"✅ Todos os {total_chunks} chunks enviados para SQS")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'file_id': file_id,
                'total_linhas': len(rows),
                'total_chunks': total_chunks
            })
        }
        
    except Exception as e:
        print(f"❌ ERRO NO PRODUCER: {str(e)}")
        print(f"❌ Tipo do erro: {type(e).__name__}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def has_processing_file():
    """Verifica se há arquivo em processamento"""
    response = table.scan(
        FilterExpression='#status = :status',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={':status': 'PROCESSING'}
    )
    return len(response.get('Items', [])) > 0
