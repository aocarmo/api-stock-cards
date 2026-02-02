"""
Use case para consultar inventário com filtros
"""
import json
import os
import boto3

class GetInventoryUseCase:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        
        self.data_table = self.dynamodb.Table(os.getenv('INVENTORY_DATA_TABLE'))
        self.bucket = os.getenv('INVENTORY_BUCKET')
    
    def execute(self, colecao=None, numero=None, tipo=None, idioma=None, 
                preco_min=None, preco_max=None, quantidade_min=None, limit=1000):
        """Consulta inventário com filtros"""
        
        # Pegar última contagem
        response = self.data_table.get_item(Key={'pk': 'LATEST'})
        
        if 'Item' not in response:
            return {
                'success': False,
                'error': 'Nenhum inventário disponível. Execute sincronização primeiro.'
            }
        
        item = response['Item']
        job_id = item['job_id']
        
        # Decidir qual arquivo baixar do S3
        if colecao:
            s3_key = f"{job_id}/by_collection/{colecao}.json"
        else:
            s3_key = f"{job_id}/full_inventory.json"
        
        # Baixar dados do S3
        try:
            obj = self.s3.get_object(Bucket=self.bucket, Key=s3_key)
            cards = json.loads(obj['Body'].read())
        except self.s3.exceptions.NoSuchKey:
            if colecao:
                return {
                    'success': False,
                    'error': f"Coleção '{colecao}' não encontrada no inventário"
                }
            raise
        
        # Aplicar filtros
        filtered = cards
        
        if numero:
            filtered = [c for c in filtered if c.get('numero') == numero]
        
        if tipo:
            filtered = [c for c in filtered if c.get('tipo') == tipo]
        
        if idioma:
            filtered = [c for c in filtered if c.get('idioma') == idioma]
        
        if preco_min is not None:
            filtered = [c for c in filtered if float(c.get('preco', 0)) >= preco_min]
        
        if preco_max is not None:
            filtered = [c for c in filtered if float(c.get('preco', 0)) <= preco_max]
        
        if quantidade_min is not None:
            filtered = [c for c in filtered if int(c.get('quantidade', 0)) >= quantidade_min]
        
        # Limitar resultados
        filtered = filtered[:limit]
        
        return {
            'success': True,
            'total': len(filtered),
            'cards': filtered,
            'summary': {
                'total_cards': item['total_cards'],
                'by_collection': item['by_collection'],
                'by_type': item['by_type'],
                'by_language': item['by_language'],
                'updated_at': item['updated_at'],
                'job_id': item['job_id']
            },
            'filters_applied': {
                k: v for k, v in {
                    'colecao': colecao,
                    'numero': numero,
                    'tipo': tipo,
                    'idioma': idioma,
                    'preco_min': preco_min,
                    'preco_max': preco_max,
                    'quantidade_min': quantidade_min
                }.items() if v is not None
            }
        }
