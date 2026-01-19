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
        
        # Pegar CSRF uma vez no início
        csrf = self.service.get_csrf()
        if not csrf:
            raise Exception("Erro ao obter CSRF token")
        
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
                else:
                    resultados.append({'numero': numero, 'colecao': colecao, 'tipo': tipo, 'idioma': idioma, 'status': 'erro_deletar'})
                    cartas_pendentes.pop()
                    continue
                    
            except Exception as e:
                resultados.append({'numero': numero, 'colecao': colecao, 'tipo': tipo, 'idioma': idioma, 'status': 'erro', 'erro': str(e)})
        
        # Fase 2: Recadastrar
        print(f"DEBUG - Iniciando recadastro de {len(cartas_pendentes)} cartas")
        
        for carta_pendente in cartas_pendentes:
            try:
                print(f"DEBUG - Recadastrando: {carta_pendente['numero']} ({carta_pendente['colecao']}) ({carta_pendente['tipo']}) ({carta_pendente.get('idioma_nome', '')})")
                
                if self.service.create_card(carta_pendente):
                    print(f"Carta {carta_pendente['numero']} ({carta_pendente['colecao']}) ({carta_pendente['tipo']}) ({carta_pendente.get('idioma_nome', '')}) recadastrada com sucesso")
                    resultados.append({
                        'numero': carta_pendente['numero'],
                        'colecao': carta_pendente['colecao'],
                        'tipo': carta_pendente['tipo'],
                        'idioma': carta_pendente.get('idioma_nome', ''),
                        'status': 'ok'
                    })
                else:
                    print(f"ERRO - Falha ao recadastrar: {carta_pendente['numero']}")
                    resultados.append({
                        'numero': carta_pendente['numero'],
                        'colecao': carta_pendente['colecao'],
                        'tipo': carta_pendente['tipo'],
                        'idioma': carta_pendente.get('idioma_nome', ''),
                        'status': 'erro_cadastrar'
                    })
            except Exception as e:
                print(f"ERRO - Exception ao recadastrar {carta_pendente['numero']}: {str(e)}")
                resultados.append({
                    'numero': carta_pendente['numero'],
                    'colecao': carta_pendente['colecao'],
                    'tipo': carta_pendente['tipo'],
                    'idioma': carta_pendente.get('idioma_nome', ''),
                    'status': 'erro_cadastrar', 
                    'erro': str(e)
                })
        
        return resultados
