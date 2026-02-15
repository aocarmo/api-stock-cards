"""
Use case para consolidar inventário após scraping paralelo
"""
import json
import os
import boto3
from datetime import datetime

class ConsolidateInventoryUseCase:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        
        self.jobs_table = self.dynamodb.Table(os.getenv('INVENTORY_JOBS_TABLE'))
        self.data_table = self.dynamodb.Table(os.getenv('INVENTORY_DATA_TABLE'))
        self.bucket = os.getenv('INVENTORY_BUCKET')
    
    def execute(self, job_id, total_ranges):
        """Consolida todos os ranges em um inventário completo"""
        # Baixar o arquivo único do S3
        all_cards = []
        s3_key = f"{job_id}/ranges/range_0-99999.json"
        
        try:
            obj = self.s3.get_object(Bucket=self.bucket, Key=s3_key)
            all_cards = json.loads(obj['Body'].read())
            print(f"✅ {len(all_cards)} cartas carregadas do S3")
        except Exception as e:
            print(f"❌ Erro ao baixar {s3_key}: {str(e)}")
            return {'success': False, 'error': str(e)}
        
        # Calcular agregados
        by_collection = {}
        by_type = {}
        by_language = {}
        
        for card in all_cards:
            col = card.get('colecao', 'unknown')
            tipo = card.get('tipo', 'normal')
            idioma = card.get('idioma', 'portugues')
            
            by_collection[col] = by_collection.get(col, 0) + 1
            by_type[tipo] = by_type.get(tipo, 0) + 1
            by_language[idioma] = by_language.get(idioma, 0) + 1
        
        # Particionar por coleção no S3
        cards_by_collection = {}
        for card in all_cards:
            col = card.get('colecao', 'unknown')
            if col not in cards_by_collection:
                cards_by_collection[col] = []
            cards_by_collection[col].append(card)
        
        # Salvar partições
        for col, cards in cards_by_collection.items():
            self.s3.put_object(
                Bucket=self.bucket,
                Key=f"{job_id}/by_collection/{col}.json",
                Body=json.dumps(cards, ensure_ascii=False),
                ContentType='application/json'
            )
        
        # Salvar inventário completo
        self.s3.put_object(
            Bucket=self.bucket,
            Key=f"{job_id}/full_inventory.json",
            Body=json.dumps(all_cards, ensure_ascii=False),
            ContentType='application/json'
        )
        
        # Atualizar DynamoDB com dados consolidados
        self.data_table.put_item(Item={
            'pk': 'LATEST',
            'job_id': job_id,
            's3_key': f"{job_id}/full_inventory.json",
            'total_cards': len(all_cards),
            'by_collection': by_collection,
            'by_type': by_type,
            'by_language': by_language,
            'updated_at': datetime.now().isoformat()
        })
        
        # Marcar job como COMPLETED
        self.jobs_table.update_item(
            Key={'job_id': job_id},
            UpdateExpression='SET #status = :status, completed_at = :now, total_cards = :total',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'COMPLETED',
                ':now': datetime.now().isoformat(),
                ':total': len(all_cards)
            }
        )
        
        return {
            'success': True,
            'total_cards': len(all_cards),
            'by_collection': by_collection,
            'by_type': by_type,
            'by_language': by_language
        }
