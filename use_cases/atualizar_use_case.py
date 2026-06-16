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
            colecao = carta.get('colecao', '')
            tipo = carta.get('tipo', 'normal')
            idioma = carta.get('idioma', 'portugues')
            novo_preco = carta.get('preco')
            nova_quantidade = carta.get('quantidade')
            base = {'numero': numero, 'colecao': colecao, 'tipo': tipo, 'idioma': idioma}

            try:
                # Assinatura correta: search_card(numero, colecao, tipo, idioma)
                card_data = self.service.search_card(numero, colecao, tipo, idioma)

                if not card_data:
                    resultados.append({**base, 'status': 'nao_encontrada'})
                    continue

                if self.service.update_card(card_data['id_estoque'], novo_preco, nova_quantidade):
                    resultados.append({**base, 'status': 'ok'})
                else:
                    resultados.append({**base, 'status': 'erro_atualizar'})

            except Exception as e:
                resultados.append({**base, 'status': 'erro', 'erro': str(e)})

        return resultados
