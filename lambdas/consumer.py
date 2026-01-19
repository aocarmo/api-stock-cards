"""
Lambda Consumer - Processa chunks do SQS
"""
import json
import os
import sys
import boto3
from datetime import datetime
from decimal import Decimal

# Adicionar layer ao path
sys.path.insert(0, '/opt/python')

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ['DYNAMODB_TABLE']
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """Processa mensagens do SQS"""
    from use_cases.atualizar_massa_use_case import AtualizarMassaUseCase
    
    total_processadas = 0
    
    for record in event['Records']:
        try:
            body = json.loads(record['body'])
            file_id = body['file_id']
            chunk_id = body['chunk_id']
            lines = body['lines']
            
            print(f"🔄 Processando chunk {chunk_id} do arquivo {file_id}")
            
            # Processar cartas
            use_case = AtualizarMassaUseCase()
            resultados = use_case.execute(lines)
            
            # Separar erros
            erros = [r for r in resultados if r['status'] not in ['atualizada', 'criada']]
            
            # Atualizar DynamoDB
            update_file_progress(file_id, chunk_id, erros)
            
            total_processadas += len(lines)
            print(f"✅ Chunk {chunk_id} processado: {len(lines)} linhas")
            
        except Exception as e:
            print(f"❌ Erro ao processar chunk: {str(e)}")
            # Registrar erro no DynamoDB
            if 'file_id' in locals() and 'chunk_id' in locals():
                register_chunk_error(file_id, chunk_id, str(e), lines)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'processadas': total_processadas})
    }

def update_file_progress(file_id, chunk_id, erros):
    """Atualiza progresso do arquivo no DynamoDB"""
    # Incrementar chunks processados
    response = table.update_item(
        Key={'file_id': file_id},
        UpdateExpression='SET chunks_processados = chunks_processados + :inc, updated_at = :now',
        ExpressionAttributeValues={
            ':inc': 1,
            ':now': datetime.now().isoformat()
        },
        ReturnValues='ALL_NEW'
    )
    
    item = response['Attributes']
    
    # Adicionar erros se houver
    if erros:
        current_errors = item.get('linhas_erro', [])
        current_errors.extend(erros)
        table.update_item(
            Key={'file_id': file_id},
            UpdateExpression='SET linhas_erro = :erros',
            ExpressionAttributeValues={':erros': current_errors}
        )
    
    # Verificar se finalizou
    if item['chunks_processados'] >= item['total_chunks']:
        table.update_item(
            Key={'file_id': file_id},
            UpdateExpression='SET #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'COMPLETED'}
        )
        print(f"🎉 Arquivo {file_id} finalizado!")

def register_chunk_error(file_id, chunk_id, error_msg, lines):
    """Registra erro de chunk no DynamoDB"""
    erro = {
        'chunk_id': chunk_id,
        'error': error_msg,
        'lines': lines
    }
    
    table.update_item(
        Key={'file_id': file_id},
        UpdateExpression='SET linhas_erro = list_append(if_not_exists(linhas_erro, :empty), :erro)',
        ExpressionAttributeValues={
            ':erro': [erro],
            ':empty': []
        }
    )
