"""
Lambda para processar CSV do S3 e atualizar cartas em massa
"""
import json
import csv
import boto3
import os
from io import StringIO
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE', 'myp-cards-jobs'))

def lambda_handler(event, context):
    """
    Triggered por S3 quando CSV é uploaded
    """
    try:
        # Pegar info do S3
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        print(f"Processando CSV: s3://{bucket}/{key}")
        
        # Baixar CSV
        response = s3.get_object(Bucket=bucket, Key=key)
        csv_content = response['Body'].read().decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(StringIO(csv_content))
        cartas = list(csv_reader)
        
        # Criar job no DynamoDB
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        table.put_item(Item={
            'job_id': job_id,
            'status': 'PENDING',
            's3_bucket': bucket,
            's3_key': key,
            'total_cartas': len(cartas),
            'processadas': 0,
            'created_at': datetime.now().isoformat(),
            'cartas': json.dumps(cartas)
        })
        
        # Invocar Lambda de processamento
        lambda_client = boto3.client('lambda')
        lambda_client.invoke(
            FunctionName=os.environ.get('PROCESSOR_LAMBDA', 'myp-processar-massa'),
            InvocationType='Event',  # Async
            Payload=json.dumps({'job_id': job_id})
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Job criado com sucesso',
                'job_id': job_id,
                'total_cartas': len(cartas)
            })
        }
        
    except Exception as e:
        print(f"Erro: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
