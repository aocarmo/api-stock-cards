"""
Use case para atualizar cartas
"""
from services.myp_service import MypService

class AtualizarUseCase:
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
            tipo = carta.get('tipo', '')
            novo_preco = carta.get('preco')
            nova_quantidade = carta.get('quantidade')
            
            try:
                card_data = self.service.search_card(numero, tipo)
                
                if not card_data:
                    resultados.append({'numero': numero, 'tipo': tipo, 'status': 'nao_encontrada'})
                    continue
                
                if self.service.update_card(card_data['id_estoque'], novo_preco, nova_quantidade):
                    resultados.append({'numero': numero, 'tipo': tipo, 'status': 'ok'})
                else:
                    resultados.append({'numero': numero, 'tipo': tipo, 'status': 'erro_atualizar'})
                    
            except Exception as e:
                resultados.append({'numero': numero, 'tipo': tipo, 'status': 'erro', 'erro': str(e)})
        
        return resultados
