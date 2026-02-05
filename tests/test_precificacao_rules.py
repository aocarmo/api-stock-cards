"""
Testes unitários para regras de precificação
"""
import pytest
from precificacao_rules import PrecificacaoRules

class TestPrecificacaoRules:
    
    def test_carta_barata_competitiva(self):
        """Carta < R$ 4,00 deve ter margem 8% e 100% do estoque"""
        carta = {
            'numero': '001/131',
            'colecao': 'PRE',
            'tipo': 'normal',
            'idioma': 'portugues',
            'preco': 5.00,
            'quantidade': 20
        }
        
        concorrentes = {
            'menor_preco': 1.50,
            'estoque_total': 3,
            'total_vendedores': 2
        }
        
        resultado = PrecificacaoRules.calcular_preco(carta, concorrentes)
        
        assert resultado['preco_novo'] == 1.62  # 1.50 * 1.08
        assert resultado['quantidade_disponivel'] == 20  # 100%
        assert resultado['estrategia'] == 'COMPETITIVO_BARATO'
        assert resultado['deve_atualizar'] == True
    
    def test_carta_media_sem_estoque_vantajoso(self):
        """Carta R$ 4-10 sem estoque vantajoso: margem 10%, 25% estoque"""
        carta = {
            'numero': '002/131',
            'colecao': 'PRE',
            'tipo': 'normal',
            'idioma': 'portugues',
            'preco': 10.00,
            'quantidade': 5  # Igual ao concorrente
        }
        
        concorrentes = {
            'menor_preco': 7.00,
            'estoque_total': 5,  # Igual
            'total_vendedores': 3
        }
        
        resultado = PrecificacaoRules.calcular_preco(carta, concorrentes)
        
        assert resultado['preco_novo'] == 7.70  # 7.00 * 1.10
        assert resultado['quantidade_disponivel'] == 1  # 25% de 5 = 1.25 -> 1
        assert resultado['estrategia'] == 'MARGEM_NORMAL_MEDIO'
        assert resultado['deve_atualizar'] == True
    
    def test_carta_media_com_estoque_vantajoso(self):
        """Carta R$ 4-10 com estoque >= 4 e diferença >= 4: premium 18%, 25% estoque"""
        carta = {
            'numero': '003/131',
            'colecao': 'PRE',
            'tipo': 'normal',
            'idioma': 'portugues',
            'preco': 15.00,
            'quantidade': 12
        }
        
        concorrentes = {
            'menor_preco': 8.00,
            'estoque_total': 2,
            'total_vendedores': 2
        }
        
        resultado = PrecificacaoRules.calcular_preco(carta, concorrentes)
        
        assert resultado['preco_novo'] == 9.44  # 8.00 * 1.18
        assert resultado['quantidade_disponivel'] == 3  # 25% de 12
        assert resultado['estrategia'] == 'PREMIUM_ESTOQUE_MEDIO'
        assert resultado['deve_atualizar'] == True
    
    def test_carta_cara_sem_estoque_vantajoso(self):
        """Carta >= R$ 10 sem estoque vantajoso: margem 12%, 25% estoque"""
        carta = {
            'numero': '004/131',
            'colecao': 'PRE',
            'tipo': 'normal',
            'idioma': 'portugues',
            'preco': 20.00,
            'quantidade': 8  # Igual ao concorrente
        }
        
        concorrentes = {
            'menor_preco': 15.00,
            'estoque_total': 8,  # Igual
            'total_vendedores': 5
        }
        
        resultado = PrecificacaoRules.calcular_preco(carta, concorrentes)
        
        assert resultado['preco_novo'] == 16.80  # 15.00 * 1.12
        assert resultado['quantidade_disponivel'] == 2  # 25% de 8
        assert resultado['estrategia'] == 'MARGEM_NORMAL_ALTO'
        assert resultado['deve_atualizar'] == True
    
    def test_carta_cara_com_estoque_vantajoso(self):
        """Carta >= R$ 10 com estoque >= 4 e diferença >= 4: premium baseado em estoque"""
        carta = {
            'numero': '005/131',
            'colecao': 'PRE',
            'tipo': 'normal',
            'idioma': 'portugues',
            'preco': 35.00,
            'quantidade': 16
        }
        
        concorrentes = {
            'menor_preco': 20.00,
            'estoque_total': 1,
            'total_vendedores': 1
        }
        
        resultado = PrecificacaoRules.calcular_preco(carta, concorrentes)
        
        # Premium: (16 / 4) * 10% = 40%
        assert resultado['preco_novo'] == 28.00  # 20.00 * 1.40
        assert resultado['quantidade_disponivel'] == 4  # 25% de 16
        assert resultado['estrategia'] == 'PROTECAO_ESTOQUE_ALTO'
        assert resultado['deve_atualizar'] == True
    
    def test_estoque_menor_que_concorrente(self):
        """Estoque menor: R$ 0,10 mais barato, 100% do estoque"""
        carta = {
            'numero': '006/131',
            'colecao': 'PRE',
            'tipo': 'normal',
            'idioma': 'portugues',
            'preco': 20.00,
            'quantidade': 2
        }
        
        concorrentes = {
            'menor_preco': 15.00,
            'estoque_total': 8,
            'total_vendedores': 5
        }
        
        resultado = PrecificacaoRules.calcular_preco(carta, concorrentes)
        
        assert resultado['preco_novo'] == 14.90  # 15.00 - 0.10
        assert resultado['quantidade_disponivel'] == 2  # 100%
        assert resultado['estrategia'] == 'COMPETITIVO_ESTOQUE_BAIXO'
        assert resultado['deve_atualizar'] == True
    
    def test_sem_concorrentes(self):
        """Sem concorrentes: manter preço atual"""
        carta = {
            'numero': '007/131',
            'colecao': 'PRE',
            'tipo': 'normal',
            'idioma': 'portugues',
            'preco': 10.00,
            'quantidade': 5
        }
        
        resultado = PrecificacaoRules.calcular_preco(carta, None)
        
        assert resultado['preco_novo'] == 10.00
        assert resultado['quantidade_disponivel'] == 5
        assert resultado['estrategia'] == 'SEM_CONCORRENTES'
        assert resultado['deve_atualizar'] == False
    
    def test_filtro_preco_maximo(self):
        """Cartas acima do preço máximo não devem ser processadas"""
        carta_barata = {'preco': 30.00}
        carta_cara = {'preco': 60.00}
        
        assert PrecificacaoRules.deve_processar(carta_barata, preco_maximo=50.00) == True
        assert PrecificacaoRules.deve_processar(carta_cara, preco_maximo=50.00) == False
    
    def test_quantidade_minima_sempre_1(self):
        """25% de estoque pequeno deve ser no mínimo 1"""
        carta = {
            'numero': '008/131',
            'colecao': 'PRE',
            'tipo': 'normal',
            'idioma': 'portugues',
            'preco': 10.00,
            'quantidade': 2
        }
        
        concorrentes = {
            'menor_preco': 8.00,
            'estoque_total': 1,
            'total_vendedores': 1
        }
        
        resultado = PrecificacaoRules.calcular_preco(carta, concorrentes)
        
        # 25% de 2 = 0.5, mas mínimo é 1
        assert resultado['quantidade_disponivel'] == 1
    
    def test_premium_maximo_50_por_cento(self):
        """Premium de proteção não deve ultrapassar 50%"""
        carta = {
            'numero': '009/131',
            'colecao': 'PRE',
            'tipo': 'normal',
            'idioma': 'portugues',
            'preco': 50.00,
            'quantidade': 100  # Muito estoque
        }
        
        concorrentes = {
            'menor_preco': 20.00,
            'estoque_total': 1,
            'total_vendedores': 1
        }
        
        resultado = PrecificacaoRules.calcular_preco(carta, concorrentes)
        
        # (100 / 4) * 10% = 250%, mas máximo é 50%
        assert resultado['preco_novo'] == 30.00  # 20.00 * 1.50
        assert resultado['estrategia'] == 'PROTECAO_ESTOQUE_ALTO'
    
    def test_preco_minimo_0_01(self):
        """Preço nunca deve ser menor que R$ 0,01"""
        carta = {
            'numero': '010/131',
            'colecao': 'PRE',
            'tipo': 'normal',
            'idioma': 'portugues',
            'preco': 0.50,
            'quantidade': 1
        }
        
        concorrentes = {
            'menor_preco': 0.05,
            'estoque_total': 10,
            'total_vendedores': 5
        }
        
        resultado = PrecificacaoRules.calcular_preco(carta, concorrentes)
        
        # 0.05 - 0.10 = -0.05, mas mínimo é 0.01
        assert resultado['preco_novo'] >= 0.01


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
