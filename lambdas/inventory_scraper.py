"""
Lambda para scraping paralelo de inventário por faixa de preço
"""
import json
import sys

sys.path.insert(0, '/opt/python')

def lambda_handler(event, context):
    """Processa uma faixa de preço do inventário"""
    from use_cases.scrape_price_range_use_case import ScrapePriceRangeUseCase
    
    job_id = event['job_id']
    price_range = event['price_range']
    range_index = event['range_index']
    total_ranges = event['total_ranges']
    
    min_price, max_price = price_range
    print(f"🔄 Scraping faixa R${min_price}-{max_price} (job: {job_id})")
    
    try:
        use_case = ScrapePriceRangeUseCase()
        result = use_case.execute(job_id, price_range, range_index, total_ranges)
        
        print(f"✅ {result['cards_found']} cartas encontradas")
        print(f"📊 Progresso: {result['progress']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        print(f"❌ Erro no scraping: {str(e)}")
        
        # Marcar job como FAILED
        import os
        import boto3
        dynamodb = boto3.resource('dynamodb')
        jobs_table = dynamodb.Table(os.getenv('INVENTORY_JOBS_TABLE'))
        
        jobs_table.update_item(
            Key={'job_id': job_id},
            UpdateExpression='SET #status = :status, error = :error',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'FAILED',
                ':error': str(e)
            }
        )
        
        raise
