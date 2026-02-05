"""
Use case para sincronização assíncrona de inventário
"""
import json
import os
import boto3
from datetime import datetime, timedelta
from services.myp_service import MypService

class SyncInventoryUseCase:
    def __init__(self):
        self.service = MypService()
        self.s3 = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.lambda_client = boto3.client('lambda')
        
        self.jobs_table = self.dynamodb.Table(os.getenv('INVENTORY_JOBS_TABLE'))
        self.data_table = self.dynamodb.Table(os.getenv('INVENTORY_DATA_TABLE'))
        self.bucket = os.getenv('INVENTORY_BUCKET')
    
    def execute(self, trigger_precificacao=False):
        """
        Inicia sincronização assíncrona do inventário
        
        Args:
            trigger_precificacao: Se True, envia mensagem para fila após completar
        """
        # Verificar se já existe job em processamento
        response = self.jobs_table.scan(
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'PROCESSING'}
        )
        
        if response.get('Items'):
            return {
                'success': False,
                'error': 'Já existe uma sincronização em andamento'
            }
        
        # Criar novo job
        job_id = f"inv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        price_ranges = [
            (0, 10),
            (10, 50),
            (50, 100),
            (100, 500),
            (500, 9999)
        ]
        
        # Criar registro no DynamoDB
        ttl = int((datetime.now() + timedelta(days=7)).timestamp())
        
        self.jobs_table.put_item(Item={
            'job_id': job_id,
            'status': 'PROCESSING',
            'total_ranges': len(price_ranges),
            'ranges_completed': 0,
            'started_at': datetime.now().isoformat(),
            'trigger_precificacao': trigger_precificacao,
            'ttl': ttl
        })
        
        # Disparar lambdas em paralelo
        for index, price_range in enumerate(price_ranges):
            payload = {
                'job_id': job_id,
                'price_range': price_range,
                'range_index': index,
                'total_ranges': len(price_ranges)
            }
            
            self.lambda_client.invoke(
                FunctionName=f"myp-cards-inventory-scraper-{os.getenv('Environment', 'dev')}",
                InvocationType='Event',
                Payload=json.dumps(payload)
            )
        
        return {
            'success': True,
            'job_id': job_id,
            'status': 'PROCESSING',
            'message': f'Sincronização iniciada. {len(price_ranges)} lambdas processando em paralelo.'
        }
