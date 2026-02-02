"""
Use case para recadastrar cartas em massa (excluir e cadastrar)
"""
from services.myp_service import MypService

class RecadastrarMassaUseCase:
    def __init__(self):
        self.service = MypService()
    
    def execute(self, cartas):
        # Autenticação
        try:
            cookies = self.service.get_session()
        except:
            if not self.service.login():
                raise Exception("Erro no login")
            cookies = self.service.get_session()
        
        self.service.init_scraper(cookies)
        
        # Fase 1: Buscar e excluir
        cartas_pendentes = []
        resultados = []
        
        for carta in cartas:
            numero = carta['numero']
            colecao = carta['colecao']
            tipo = carta.get('tipo', 'normal')
            idioma = carta.get('idioma', 'portugues')
            preco = carta.get('preco')
            quantidade = carta.get('quantidade')
            
            try:
                # Buscar carta na pasta
                card_data = self.service.search_card(numero, colecao, tipo, idioma)
                
                if card_data:
                    # Carta existe - excluir e recadastrar
                    if self.service.delete_card(card_data['id_estoque']):
                        print(f"✅ Carta excluída: {numero} ({colecao}) ({tipo}) ({idioma})")
                        
                        # MANTER quantidade atual (NÃO somar)
                        qtd_atual = card_data.get('quantidade')
                        
                        # Substituir preço se vier no CSV, senão manter atual
                        preco_novo = preco if preco else card_data.get('preco')
                        
                        # Preservar dados e aplicar novo preço
                        card_data['preco'] = preco_novo
                        card_data['quantidade'] = qtd_atual  # MANTER quantidade atual
                        card_data['tipo'] = tipo  # Preservar tipo do CSV
                        card_data['idioma_nome'] = idioma  # Preservar idioma do CSV
                        cartas_pendentes.append(card_data)
                    else:
                        print(f"❌ Erro ao excluir: {numero}")
                        resultados.append({
                            'numero': numero,
                            'colecao': colecao,
                            'tipo': tipo,
                            'idioma': idioma,
                            'status': 'erro_deletar'
                        })
                else:
                    # Carta não existe - buscar produto no site e criar
                    print(f"⚠️ Carta não encontrada na pasta: {numero} ({colecao}) ({tipo}) - Buscando produto no site...")
                    
                    idproduto = self.service.search_product_id(numero, colecao)
                    
                    if idproduto:
                        # Criar carta com os valores informados
                        card_data = {
                            'idproduto': idproduto,
                            'numero': numero,
                            'colecao': colecao,
                            'tipo': tipo,  # Usar tipo do CSV
                            'idioma_nome': idioma,  # Usar idioma do CSV
                            'qualidade': 'NM',
                            'preco': preco,
                            'quantidade': quantidade
                        }
                        cartas_pendentes.append(card_data)
                    else:
                        print(f"❌ Produto não encontrado no site: {numero} ({colecao})")
                        resultados.append({
                            'numero': numero,
                            'colecao': colecao,
                            'tipo': tipo,
                            'idioma': idioma,
                            'status': 'produto_nao_encontrado'
                        })
                    
            except Exception as e:
                resultados.append({
                    'numero': numero,
                    'colecao': colecao,
                    'tipo': tipo,
                    'idioma': idioma,
                    'status': 'erro',
                    'erro': str(e)
                })
        
        # Fase 2: Recadastrar
        print(f"DEBUG - Iniciando recadastro de {len(cartas_pendentes)} cartas")
        
        for carta_pendente in cartas_pendentes:
            try:
                print(f"DEBUG - Recadastrando: {carta_pendente['numero']} ({carta_pendente['colecao']}) ({carta_pendente['tipo']}) ({carta_pendente.get('idioma_nome', '')})")
                
                if self.service.create_card(carta_pendente):
                    print(f"✅ Carta recadastrada: {carta_pendente['numero']} ({carta_pendente['colecao']}) ({carta_pendente['tipo']}) | Preço: {carta_pendente['preco']} | Qtd: {carta_pendente['quantidade']}")
                    
                    # Verificar se foi criação ou recadastro
                    status = 'criada' if 'id_estoque' not in carta_pendente else 'ok'
                    
                    resultados.append({
                        'numero': carta_pendente['numero'],
                        'colecao': carta_pendente['colecao'],
                        'tipo': carta_pendente['tipo'],
                        'idioma': carta_pendente.get('idioma_nome', ''),
                        'status': status,
                        'preco_novo': carta_pendente['preco'],
                        'quantidade_nova': carta_pendente['quantidade']
                    })
                else:
                    print(f"❌ Erro ao recadastrar: {carta_pendente['numero']}")
                    resultados.append({
                        'numero': carta_pendente['numero'],
                        'colecao': carta_pendente['colecao'],
                        'tipo': carta_pendente['tipo'],
                        'idioma': carta_pendente.get('idioma_nome', ''),
                        'status': 'erro_cadastrar'
                    })
            except Exception as e:
                print(f"❌ Exception ao recadastrar {carta_pendente['numero']}: {str(e)}")
                resultados.append({
                    'numero': carta_pendente['numero'],
                    'colecao': carta_pendente['colecao'],
                    'tipo': carta_pendente['tipo'],
                    'idioma': carta_pendente.get('idioma_nome', ''),
                    'status': 'erro_cadastrar',
                    'erro': str(e)
                })
        
        return resultados
