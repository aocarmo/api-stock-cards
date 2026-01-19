"""
Lambda para processar cartas em massa
"""
import json
import os
import sys
import boto3
from datetime import datetime

# Adicionar layer ao path
sys.path.insert(0, '/opt/python')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE', 'myp-cards-jobs'))

def lambda_handler(event, context):
    """
    Processa job de atualização em massa
    """
    from use_cases.atualizar_massa_use_case import AtualizarMassaUseCase
    
    try:
        job_id = event['job_id']
        
        # Buscar job no DynamoDB
        response = table.get_item(Key={'job_id': job_id})
        job = response['Item']
        
        # Atualizar status
        table.update_item(
            Key={'job_id': job_id},
            UpdateExpression='SET #status = :status, started_at = :started',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'PROCESSING',
                ':started': datetime.now().isoformat()
            }
        )
        
        # Processar cartas
        cartas = json.loads(job['cartas'])
        use_case = AtualizarMassaUseCase()
        resultados = use_case.execute(cartas)
        
        # Contar sucessos e erros
        sucessos = sum(1 for r in resultados if r['status'] in ['atualizada', 'criada'])
        erros = len(resultados) - sucessos
        
        # Atualizar job com resultados
        table.update_item(
            Key={'job_id': job_id},
            UpdateExpression='SET #status = :status, finished_at = :finished, processadas = :proc, sucessos = :suc, erros = :err, resultados = :res',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'COMPLETED',
                ':finished': datetime.now().isoformat(),
                ':proc': len(resultados),
                ':suc': sucessos,
                ':err': erros,
                ':res': json.dumps(resultados)
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'job_id': job_id,
                'total': len(resultados),
                'sucessos': sucessos,
                'erros': erros
            })
        }
        
    except Exception as e:
        print(f"Erro: {str(e)}")
        
        # Marcar job como falho
        if 'job_id' in locals():
            table.update_item(
                Key={'job_id': job_id},
                UpdateExpression='SET #status = :status, error = :error',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'FAILED',
                    ':error': str(e)
                }
            )
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
