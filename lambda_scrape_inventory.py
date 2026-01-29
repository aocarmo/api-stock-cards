import json
import boto3
from use_cases.inventory_scraping import InventoryScrapingUseCase

def lambda_handler(event, context):
    """Lambda para scraping automático do inventário"""
    
    use_case = InventoryScrapingUseCase()
    s3 = boto3.client('s3')
    
    try:
        # Executar scraping
        result = use_case.execute(output_format='json')
        
        if not result['success']:
            return {'statusCode': 500, 'body': result.get('error', 'Erro desconhecido')}
        
        # Ler arquivo gerado
        with open('inventory.json', 'r') as f:
            inventory_data = f.read()
        
        # Upload para S3
        bucket = 'myp-cards-inventory'
        key = f'inventory_{context.aws_request_id}.json'
        
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=inventory_data,
            ContentType='application/json'
        )
        
        return {
            'statusCode': 200,
            'body': f'{result["count"]} cartas salvas em s3://{bucket}/{key}'
        }
        
    except Exception as e:
        return {'statusCode': 500, 'body': f'Erro: {str(e)}'}
