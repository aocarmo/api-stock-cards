"""
Lambda Producer - Precificação Dinâmica
Processa chunks de cartas: scrape concorrentes + aplica regras
"""
import json
import os
import sys
import boto3
import time

# Adicionar path para imports
sys.path.append('/opt/python')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrape_concorrentes import ScrapeConcorrentes
from precificacao_rules import PrecificacaoRules

dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

PRECIFICACAO_JOBS_TABLE = os.environ['PRECIFICACAO_JOBS_TABLE']
PRECIFICACAO_CONSUMER_QUEUE = os.environ['PRECIFICACAO_CONSUMER_QUEUE']
DELAY_ENTRE_SCRAPES = 2  # segundos

def lambda_handler(event, context):
    """
    1. Recebe chunk de cartas do SQS
    2. Para cada carta: scrape concorrentes
    3. Aplica regras de precificação
    4. Envia para SQS Consumer
    """
    for record in event['Records']:
        try:
            message = json.loads(record['body'])
            job_id = message['job_id']
            chunk_index = message['chunk_index']
            cartas = message['cartas']
            
            print(f"Processando chunk {chunk_index} do job {job_id} ({len(cartas)} cartas)")
            
            # Inicializar scraper
            scraper = ScrapeConcorrentes()
            
            cartas_processadas = []
            
            for idx, carta in enumerate(cartas):
                try:
                    numero = carta['numero']
                    colecao = carta['colecao']
                    tipo = carta['tipo']
                    idioma = carta['idioma']
                    
                    print(f"  [{idx+1}/{len(cartas)}] Processando {numero} {colecao} {tipo} {idioma}")
                    
                    # Scrape concorrentes
                    concorrentes = scraper.buscar_carta_completa(numero, colecao, tipo, idioma)
                    
                    # Aplicar regras de precificação
                    resultado = PrecificacaoRules.calcular_preco(carta, concorrentes)
                    
                    if resultado['deve_atualizar']:
                        carta_processada = {
                            'job_id': job_id,
                            'carta': carta,
                            'quantidade_original': carta['quantidade'],  # Guardar quantidade original
                            'preco_novo': resultado['preco_novo'],
                            'quantidade_nova': resultado['quantidade_disponivel'],
                            'estrategia': resultado['estrategia'],
                            'justificativa': resultado['justificativa']
                        }
                        
                        cartas_processadas.append(carta_processada)
                        
                        print(f"    ✅ {numero}: R$ {carta['preco']} → R$ {resultado['preco_novo']} | Qtd: {carta['quantidade']} → {resultado['quantidade_disponivel']} (original: {carta['quantidade']})")
                    else:
                        print(f"    ⏭️  {numero}: Manter preço atual ({resultado['estrategia']})")
                    
                    # Delay entre scrapes
                    if idx < len(cartas) - 1:
                        time.sleep(DELAY_ENTRE_SCRAPES)
                    
                except Exception as e:
                    print(f"    ❌ Erro ao processar {carta.get('numero', '?')}: {str(e)}")
                    
                    # Registrar erro no job
                    try:
                        table = dynamodb.Table(PRECIFICACAO_JOBS_TABLE)
                        table.update_item(
                            Key={'job_id': job_id},
                            UpdateExpression='SET error_count = error_count + :inc, errors = list_append(if_not_exists(errors, :empty_list), :error)',
                            ExpressionAttributeValues={
                                ':inc': 1,
                                ':empty_list': [],
                                ':error': [{
                                    'carta': f"{carta.get('numero', '?')} {carta.get('colecao', '?')}",
                                    'erro': str(e)
                                }]
                            }
                        )
                    except:
                        pass
                    
                    continue
            
            # Enviar cartas processadas para Consumer
            if cartas_processadas:
                queue_url = PRECIFICACAO_CONSUMER_QUEUE
                
                for carta_proc in cartas_processadas:
                    sqs.send_message(
                        QueueUrl=queue_url,
                        MessageBody=json.dumps(carta_proc)
                    )
                
                print(f"✅ {len(cartas_processadas)} cartas enviadas para Consumer")
            
            # Atualizar progresso do job
            table = dynamodb.Table(PRECIFICACAO_JOBS_TABLE)
            table.update_item(
                Key={'job_id': job_id},
                UpdateExpression='SET processed_cards = processed_cards + :count',
                ExpressionAttributeValues={':count': len(cartas)}
            )
            
        except Exception as e:
            print(f"❌ Erro ao processar chunk: {str(e)}")
            raise
    
    return {'statusCode': 200, 'body': 'Chunk processado'}
