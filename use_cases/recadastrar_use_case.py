"""
Use case para recadastrar cartas
"""
import time
from services.myp_service import MypService

class RecadastrarUseCase:
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
        
        # Fase 1: Salvar e excluir
        cartas_pendentes = []
        resultados = []
        
        for carta in cartas:
            numero = carta['numero']
            colecao = carta['colecao']
            tipo = carta.get('tipo', '')
            idioma = carta.get('idioma', '')
            
            try:
                # Buscar carta com filtros de coleção, tipo e idioma
                card_data = self.service.search_card(numero, colecao, tipo, idioma)
                
                if not card_data:
                    resultados.append({'numero': numero, 'colecao': colecao, 'tipo': tipo, 'idioma': idioma, 'status': 'nao_encontrada'})
                    continue
                
                # Salvar dados para recadastro
                cartas_pendentes.append(card_data)
                
                # Excluir carta
                if self.service.delete_card(card_data['id_estoque']):
                    print(f"Carta {numero} ({colecao}) ({tipo}) ({idioma}) excluída")
                    time.sleep(2)  # Delay após exclusão
                else:
                    resultados.append({'numero': numero, 'colecao': colecao, 'tipo': tipo, 'idioma': idioma, 'status': 'erro_deletar'})
                    cartas_pendentes.pop()
                    continue
                    
            except Exception as e:
                resultados.append({'numero': numero, 'colecao': colecao, 'tipo': tipo, 'idioma': idioma, 'status': 'erro', 'erro': str(e)})
        
        # Fase 2: Recadastrar
        for carta_pendente in cartas_pendentes:
            try:
                if self.service.create_card(carta_pendente):
                    resultados.append({
                        'numero': carta_pendente['numero'],
                        'colecao': carta_pendente['colecao'],
                        'tipo': carta_pendente['tipo'],
                        'idioma': carta_pendente.get('idioma_nome', ''),
                        'status': 'ok'
                    })
                    time.sleep(2)  # Delay após cadastro
                else:
                    resultados.append({
                        'numero': carta_pendente['numero'],
                        'colecao': carta_pendente['colecao'],
                        'tipo': carta_pendente['tipo'],
                        'idioma': carta_pendente.get('idioma_nome', ''),
                        'status': 'erro_cadastrar'
                    })
            except Exception as e:
                resultados.append({
                    'numero': carta_pendente['numero'],
                    'colecao': carta_pendente['colecao'],
                    'tipo': carta_pendente['tipo'],
                    'idioma': carta_pendente.get('idioma_nome', ''),
                    'status': 'erro_cadastrar', 
                    'erro': str(e)
                })
        
        return resultados
