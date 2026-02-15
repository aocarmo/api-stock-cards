"""
Use case para scraping de uma faixa de preço do inventário
"""
import json
import os
import boto3
from datetime import datetime
from services.myp_service import MypService

class ScrapePriceRangeUseCase:
    def __init__(self):
        self.service = MypService()
        self.s3 = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        
        self.jobs_table = self.dynamodb.Table(os.getenv('INVENTORY_JOBS_TABLE'))
        self.data_table = self.dynamodb.Table(os.getenv('INVENTORY_DATA_TABLE'))
        self.bucket = os.getenv('INVENTORY_BUCKET')
    
    def execute(self, job_id, price_range, range_index, total_ranges):
        """Scraping de uma faixa de preço específica"""
        min_price, max_price = price_range
        
        # Autenticação
        try:
            cookies = self.service.get_session()
        except:
            if not self.service.login():
                raise Exception("Erro no login")
            cookies = self.service.get_session()
        
        self.service.init_scraper(cookies)
        
        # Scraping completo (sem filtros de preço)
        cards = self.service.scrape_inventory()
        
        # Salvar parcial no S3
        s3_key = f"{job_id}/ranges/range_{min_price}-{max_price}.json"
        self.s3.put_object(
            Bucket=self.bucket,
            Key=s3_key,
            Body=json.dumps(cards, ensure_ascii=False),
            ContentType='application/json'
        )
        
        # Atualizar progresso
        response = self.jobs_table.update_item(
            Key={'job_id': job_id},
            UpdateExpression='SET ranges_completed = ranges_completed + :inc, updated_at = :now',
            ExpressionAttributeValues={
                ':inc': 1,
                ':now': datetime.now().isoformat()
            },
            ReturnValues='ALL_NEW'
        )
        
        item = response['Attributes']
        ranges_completed = item['ranges_completed']
        
        # Se é a última faixa, consolidar
        if ranges_completed == total_ranges:
            from use_cases.consolidate_inventory_use_case import ConsolidateInventoryUseCase
            consolidate = ConsolidateInventoryUseCase()
            consolidate.execute(job_id, total_ranges)
        
        return {
            'success': True,
            'job_id': job_id,
            'range': f'{min_price}-{max_price}',
            'cards_found': len(cards),
            'progress': f'{ranges_completed}/{total_ranges}'
        }
