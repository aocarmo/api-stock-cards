"""
Use case para atualizar cartas em massa (criar ou atualizar)
"""
import time
from services.myp_service import MypService

class AtualizarMassaUseCase:
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
        
        resultados = []
        
        for carta in cartas:
            numero = carta['numero']
            colecao = carta['colecao']
            tipo = carta.get('tipo', 'normal')
            idioma = carta.get('idioma', 'portugues')
            preco = carta.get('preco')
            quantidade = carta.get('quantidade')
            
            try:
                # Buscar carta
                card_data = self.service.search_card(numero, colecao, tipo, idioma)
                
                if card_data:
                    # Carta existe - atualizar
                    print(f"DEBUG - Carta encontrada: {numero} ({colecao}) - Atualizando...")
                    
                    # Incrementar quantidade
                    qtd_atual = int(card_data.get('quantidade', 0))
                    qtd_nova = qtd_atual + int(quantidade) if quantidade else qtd_atual
                    
                    # Substituir preço
                    preco_novo = preco if preco else card_data.get('preco')
                    
                    if self.service.update_card(card_data['id_estoque'], preco_novo, str(qtd_nova)):
                        print(f"✅ Carta atualizada: {numero} | Preço: {card_data.get('preco')} → {preco_novo} | Qtd: {qtd_atual} → {qtd_nova}")
                        resultados.append({
                            'numero': numero,
                            'colecao': colecao,
                            'tipo': tipo,
                            'idioma': idioma,
                            'status': 'atualizada',
                            'preco_anterior': card_data.get('preco'),
                            'preco_novo': preco_novo,
                            'quantidade_anterior': qtd_atual,
                            'quantidade_nova': qtd_nova
                        })
                    else:
                        print(f"❌ Erro ao atualizar: {numero}")
                        resultados.append({
                            'numero': numero,
                            'colecao': colecao,
                            'tipo': tipo,
                            'idioma': idioma,
                            'status': 'erro_atualizar'
                        })
                else:
                    # Carta não existe - buscar idproduto e criar
                    print(f"⚠️ Carta não encontrada na pasta: {numero} ({colecao}) - Buscando no site...")
                    
                    idproduto = self.service.search_product_id(numero, colecao)
                    
                    if idproduto:
                        # Criar carta
                        card_data = {
                            'idproduto': idproduto,
                            'numero': numero,
                            'colecao': colecao,
                            'tipo': tipo,
                            'idioma_nome': idioma,
                            'qualidade': 'NM',
                            'preco': preco,
                            'quantidade': quantidade
                        }
                        
                        if self.service.create_card(card_data):
                            print(f"✅ Carta criada: {numero} ({colecao}) | Preço: {preco} | Qtd: {quantidade}")
                            resultados.append({
                                'numero': numero,
                                'colecao': colecao,
                                'tipo': tipo,
                                'idioma': idioma,
                                'status': 'criada',
                                'preco': preco,
                                'quantidade': quantidade
                            })
                        else:
                            print(f"❌ Erro ao criar carta: {numero}")
                            resultados.append({
                                'numero': numero,
                                'colecao': colecao,
                                'tipo': tipo,
                                'idioma': idioma,
                                'status': 'erro_criar'
                            })
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
        
        return resultados
