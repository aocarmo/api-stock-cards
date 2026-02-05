"""
Lambda Consumer - Precificação Dinâmica
Recebe cartas processadas e recadastra com novos preços/quantidades
Detecta vendas/adições comparando quantidade disponível anterior vs atual
"""
import json
import os
import sys
import boto3
from datetime import datetime

# Adicionar path para imports
sys.path.append('/opt/python')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from use_cases.recadastrar_massa_use_case import RecadastrarMassaUseCase
from helpers.buscar_quantidade import buscar_minha_quantidade

dynamodb = boto3.resource('dynamodb')

PRECIFICACAO_JOBS_TABLE = os.environ['PRECIFICACAO_JOBS_TABLE']

def lambda_handler(event, context):
    """
    1. Recebe carta processada do SQS
    2. Busca quantidade atual no site
    3. Calcula vendas/adições
    4. Ajusta estoque total
    5. Recadastra com nova quantidade disponível
    6. Atualiza job no DynamoDB
    """
    for record in event['Records']:
        try:
            message = json.loads(record['body'])
            job_id = message['job_id']
            carta = message['carta']
            quantidade_original = message['quantidade_original']
            preco_novo = message['preco_novo']
            quantidade_nova = message['quantidade_nova']
            estrategia = message['estrategia']
            justificativa = message['justificativa']
            
            numero = carta['numero']
            colecao = carta['colecao']
            tipo = carta['tipo']
            idioma = carta['idioma']
            
            # Criar chave única para a carta
            carta_key = f"{numero}#{colecao}#{tipo}#{idioma}"
            
            print(f"Processando {numero} {colecao} {tipo} {idioma}")
            print(f"  Estoque total original: {quantidade_original}")
            print(f"  Quantidade nova calculada: {quantidade_nova}")
            
            # Buscar estado anterior no job (se existir)
            table = dynamodb.Table(PRECIFICACAO_JOBS_TABLE)
            job_response = table.get_item(Key={'job_id': job_id})
            job_data = job_response.get('Item', {})
            cards_state = job_data.get('cards_state', {})
            
            estado_anterior = cards_state.get(carta_key, {})
            quantidade_disponivel_anterior = estado_anterior.get('quantidade_disponivel', quantidade_nova)
            estoque_total_anterior = estado_anterior.get('estoque_total', quantidade_original)
            
            # Buscar quantidade atual no site
            print(f"  Buscando quantidade atual no site...")
            quantidade_disponivel_atual = buscar_minha_quantidade(numero, colecao, tipo, idioma)
            
            if quantidade_disponivel_atual is None:
                # Erro ao buscar - manter estado anterior
                print(f"  ⚠️  Erro ao buscar quantidade. Mantendo estado anterior.")
                estoque_total_final = estoque_total_anterior
                quantidade_final = quantidade_nova
                
            elif quantidade_disponivel_atual == 0:
                # Carta não encontrada = vendeu tudo que estava disponível
                vendas = quantidade_disponivel_anterior
                estoque_total_final = max(estoque_total_anterior - vendas, 0)
                
                print(f"  📉 Carta não encontrada no site (vendeu {vendas} disponíveis)")
                print(f"  Estoque total: {estoque_total_anterior} → {estoque_total_final}")
                
                if estoque_total_final == 0:
                    # Estoque total zerado - não recadastrar
                    print(f"  ⚠️  Estoque total zerado. Não recadastrar.")
                    
                    table.update_item(
                        Key={'job_id': job_id},
                        UpdateExpression='SET cards_state.#carta_key = :state',
                        ExpressionAttributeNames={'#carta_key': carta_key},
                        ExpressionAttributeValues={
                            ':state': {
                                'estoque_total': 0,
                                'quantidade_disponivel': 0,
                                'preco': preco_novo,
                                'status': 'SOLD_OUT',
                                'updated_at': datetime.now().isoformat()
                            }
                        }
                    )
                    continue
                
                # Ainda tem estoque - recalcular quantidade disponível
                proporcao = quantidade_nova / quantidade_original if quantidade_original > 0 else 0.25
                quantidade_final = max(int(estoque_total_final * proporcao), 1)
                print(f"  ✅ Ainda tem estoque. Recadastrar com {quantidade_final} unidades")
                
            else:
                # Calcular vendas/adições
                diferenca = quantidade_disponivel_atual - quantidade_disponivel_anterior
                
                if diferenca < 0:
                    # Vendeu
                    vendas = abs(diferenca)
                    estoque_total_final = max(estoque_total_anterior - vendas, 0)
                    print(f"  📉 Vendas detectadas: {vendas} unidades")
                    print(f"  Estoque total: {estoque_total_anterior} → {estoque_total_final}")
                    
                elif diferenca > 0:
                    # Adicionou
                    adicoes = diferenca
                    estoque_total_final = estoque_total_anterior + adicoes
                    print(f"  📈 Adições detectadas: {adicoes} unidades")
                    print(f"  Estoque total: {estoque_total_anterior} → {estoque_total_final}")
                    
                else:
                    # Sem mudança
                    estoque_total_final = estoque_total_anterior
                    print(f"  ✅ Sem movimentação de estoque")
                
                # Recalcular quantidade disponível baseada no estoque total final
                if estoque_total_final == 0:
                    quantidade_final = 0
                    print(f"  ⚠️  Estoque total zerado. Não recadastrar.")
                    continue
                else:
                    # Aplicar mesma proporção
                    proporcao = quantidade_nova / quantidade_original if quantidade_original > 0 else 0.25
                    quantidade_final = max(int(estoque_total_final * proporcao), 1)
                    print(f"  Quantidade final: {quantidade_final} ({proporcao*100:.0f}% de {estoque_total_final})")
            
            # Recadastrar carta
            print(f"  Recadastrando com preço R$ {preco_novo} e quantidade {quantidade_final}")
            
            carta_recadastrar = {
                'numero': numero,
                'colecao': colecao,
                'tipo': tipo,
                'idioma': idioma,
                'preco': preco_novo,
                'quantidade': quantidade_final
            }
            
            use_case = RecadastrarMassaUseCase()
            resultados = use_case.execute([carta_recadastrar])
            
            # Verificar resultado
            if resultados and len(resultados) > 0:
                resultado = resultados[0]
                status = resultado.get('status', 'erro')
                
                if status in ['ok', 'criada']:
                    print(f"✅ Carta recadastrada com sucesso")
                    
                    # Salvar estado no job
                    table.update_item(
                        Key={'job_id': job_id},
                        UpdateExpression='SET success_count = success_count + :inc, cards_state.#carta_key = :state',
                        ExpressionAttributeNames={'#carta_key': carta_key},
                        ExpressionAttributeValues={
                            ':inc': 1,
                            ':state': {
                                'estoque_total': estoque_total_final,
                                'quantidade_disponivel': quantidade_final,
                                'preco': preco_novo,
                                'estrategia': estrategia,
                                'updated_at': datetime.now().isoformat()
                            }
                        }
                    )
                else:
                    erro = resultado.get('erro', 'Erro desconhecido')
                    print(f"❌ Erro ao recadastrar: {erro}")
                    
                    # Registrar erro
                    table.update_item(
                        Key={'job_id': job_id},
                        UpdateExpression='SET error_count = error_count + :inc, errors = list_append(if_not_exists(errors, :empty_list), :error)',
                        ExpressionAttributeValues={
                            ':inc': 1,
                            ':empty_list': [],
                            ':error': [{
                                'carta': f"{numero} {colecao} {tipo} {idioma}",
                                'erro': erro
                            }]
                        }
                    )
            else:
                print(f"❌ Nenhum resultado retornado")
                
                # Registrar erro
                table.update_item(
                    Key={'job_id': job_id},
                    UpdateExpression='SET error_count = error_count + :inc',
                    ExpressionAttributeValues={':inc': 1}
                )
            
        except Exception as e:
            print(f"❌ Erro ao processar mensagem: {str(e)}")
            
            # Registrar erro genérico
            try:
                job_id = json.loads(record['body']).get('job_id')
                if job_id:
                    table = dynamodb.Table(PRECIFICACAO_JOBS_TABLE)
                    table.update_item(
                        Key={'job_id': job_id},
                        UpdateExpression='SET error_count = error_count + :inc, errors = list_append(if_not_exists(errors, :empty_list), :error)',
                        ExpressionAttributeValues={
                            ':inc': 1,
                            ':empty_list': [],
                            ':error': [{'carta': 'desconhecida', 'erro': str(e)}]
                        }
                    )
            except:
                pass
            
            raise
    
    return {'statusCode': 200, 'body': 'Carta processada'}
