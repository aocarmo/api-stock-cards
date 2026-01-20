from services.myp_service import MypService

class ExcluirMassaUseCase:
    def __init__(self):
        self.service = MypService()
    
    def execute(self, cartas):
        """Exclui cartas em massa"""
        resultados = []
        
        for carta in cartas:
            numero = carta.get('numero')
            colecao = carta.get('colecao')
            tipo = carta.get('tipo', 'normal')
            idioma = carta.get('idioma', 'portugues')
            
            try:
                # Buscar carta na pasta
                card_data = self.service.search_card(numero, colecao, tipo, idioma)
                
                if card_data:
                    # Carta existe - excluir
                    print(f"DEBUG - Carta encontrada: {numero} ({colecao}) - Excluindo...")
                    
                    if self.service.delete_card(card_data['id_estoque']):
                        print(f"✅ Carta excluída: {numero} ({colecao})")
                        resultados.append({
                            'numero': numero,
                            'colecao': colecao,
                            'tipo': tipo,
                            'idioma': idioma,
                            'status': 'excluida'
                        })
                    else:
                        print(f"❌ Erro ao excluir: {numero}")
                        resultados.append({
                            'numero': numero,
                            'colecao': colecao,
                            'tipo': tipo,
                            'idioma': idioma,
                            'status': 'erro',
                            'mensagem': 'Falha ao excluir'
                        })
                else:
                    # Carta não existe
                    print(f"⚠️ Carta não encontrada: {numero} ({colecao})")
                    resultados.append({
                        'numero': numero,
                        'colecao': colecao,
                        'tipo': tipo,
                        'idioma': idioma,
                        'status': 'nao_encontrada'
                    })
                    
            except Exception as e:
                print(f"❌ Erro ao processar {numero}: {str(e)}")
                resultados.append({
                    'numero': numero,
                    'colecao': colecao,
                    'tipo': tipo,
                    'idioma': idioma,
                    'status': 'erro',
                    'mensagem': str(e)
                })
        
        return resultados
