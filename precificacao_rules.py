"""
Regras de precificação dinâmica
"""

class PrecificacaoRules:
    
    @staticmethod
    def calcular_preco(carta_dados, concorrentes_dados):
        """
        Calcula preço e quantidade ideal baseado nas regras
        
        Args:
            carta_dados: {
                'numero': str,
                'colecao': str,
                'tipo': str,
                'idioma': str,
                'preco': float,
                'quantidade': int
            }
            concorrentes_dados: {
                'menor_preco': float,
                'estoque_total': int,
                'total_vendedores': int
            } ou None
        
        Returns:
            {
                'preco_novo': float,
                'quantidade_disponivel': int,
                'estrategia': str,
                'justificativa': str,
                'deve_atualizar': bool
            }
        """
        meu_preco = float(carta_dados['preco'])
        meu_estoque = int(carta_dados['quantidade'])
        
        # Se não há concorrentes, manter preço atual
        if not concorrentes_dados:
            return {
                'preco_novo': meu_preco,
                'quantidade_disponivel': meu_estoque,
                'estrategia': 'SEM_CONCORRENTES',
                'justificativa': 'Nenhum concorrente encontrado',
                'deve_atualizar': False
            }
        
        menor_preco = concorrentes_dados['menor_preco']
        estoque_concorrente = concorrentes_dados['estoque_total']
        diferenca_estoque = meu_estoque - estoque_concorrente
        
        # REGRA 1: Estoque menor que concorrente - ser mais competitivo
        if meu_estoque < estoque_concorrente:
            preco_novo = max(menor_preco - 0.10, 0.01)  # Mínimo R$ 0,01
            return {
                'preco_novo': round(preco_novo, 2),
                'quantidade_disponivel': meu_estoque,  # 100%
                'estrategia': 'COMPETITIVO_ESTOQUE_BAIXO',
                'justificativa': f'Estoque menor ({meu_estoque} vs {estoque_concorrente}) - R$ 0,10 mais barato',
                'deve_atualizar': True
            }
        
        # REGRA 2: Cartas baratas (< R$ 4,00) - competitivo
        if menor_preco < 4.00:
            preco_novo = menor_preco * 1.08
            return {
                'preco_novo': round(preco_novo, 2),
                'quantidade_disponivel': meu_estoque,  # 100%
                'estrategia': 'COMPETITIVO_BARATO',
                'justificativa': 'Carta barata - margem 8%, vender em massa',
                'deve_atualizar': True
            }
        
        # REGRA 3: Cartas médias (R$ 4,00 - R$ 10,00)
        if 4.00 <= menor_preco < 10.00:
            # Com estoque vantajoso
            if meu_estoque >= 4 and diferenca_estoque >= 4:
                preco_novo = menor_preco * 1.18
                qtd_disponivel = max(int(meu_estoque * 0.25), 1)
                return {
                    'preco_novo': round(preco_novo, 2),
                    'quantidade_disponivel': qtd_disponivel,
                    'estrategia': 'PREMIUM_ESTOQUE_MEDIO',
                    'justificativa': f'Estoque vantajoso ({meu_estoque} vs {estoque_concorrente}) - premium 18%',
                    'deve_atualizar': True
                }
            # Sem estoque vantajoso
            else:
                preco_novo = menor_preco * 1.10
                qtd_disponivel = max(int(meu_estoque * 0.25), 1)
                return {
                    'preco_novo': round(preco_novo, 2),
                    'quantidade_disponivel': qtd_disponivel,
                    'estrategia': 'MARGEM_NORMAL_MEDIO',
                    'justificativa': 'Margem normal 10%',
                    'deve_atualizar': True
                }
        
        # REGRA 4: Cartas caras (≥ R$ 10,00)
        if menor_preco >= 10.00:
            # Com estoque vantajoso - proteção de estoque
            if meu_estoque >= 4 and diferenca_estoque >= 4:
                # Premium baseado no estoque (máximo 50%)
                premium_percentual = min((meu_estoque / 4) * 0.10, 0.50)
                preco_novo = menor_preco * (1 + premium_percentual)
                qtd_disponivel = max(int(meu_estoque * 0.25), 1)
                return {
                    'preco_novo': round(preco_novo, 2),
                    'quantidade_disponivel': qtd_disponivel,
                    'estrategia': 'PROTECAO_ESTOQUE_ALTO',
                    'justificativa': f'Proteção de estoque - premium {int(premium_percentual*100)}%',
                    'deve_atualizar': True
                }
            # Sem estoque vantajoso
            else:
                preco_novo = menor_preco * 1.12
                qtd_disponivel = max(int(meu_estoque * 0.25), 1)
                return {
                    'preco_novo': round(preco_novo, 2),
                    'quantidade_disponivel': qtd_disponivel,
                    'estrategia': 'MARGEM_NORMAL_ALTO',
                    'justificativa': 'Margem normal 12%',
                    'deve_atualizar': True
                }
        
        # Fallback
        return {
            'preco_novo': meu_preco,
            'quantidade_disponivel': meu_estoque,
            'estrategia': 'MANTER',
            'justificativa': 'Sem regra aplicável',
            'deve_atualizar': False
        }
    
    @staticmethod
    def deve_processar(carta_dados, preco_maximo=50.00):
        """
        Verifica se a carta deve ser processada
        
        Args:
            carta_dados: dict com dados da carta
            preco_maximo: float - preço máximo para processar
        
        Returns:
            bool
        """
        preco = float(carta_dados['preco'])
        return preco <= preco_maximo
