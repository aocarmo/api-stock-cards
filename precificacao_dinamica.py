#!/usr/bin/env python3
"""
Precificação Dinâmica - Estratégia de Frete Único
Usa infraestrutura existente para otimizar preços
"""
import requests
import csv
import sys
import os
from datetime import datetime

# Adicionar path para importar services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.myp_service import MYPService

API_URL = "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory"

class PrecificacaoDinamica:
    
    def __init__(self, scrape_concorrentes=True):
        self.frete_medio = 30.00  # Frete médio no Brasil
        self.scrape_concorrentes = scrape_concorrentes
        if scrape_concorrentes:
            self.myp_service = MYPService()
    
    def obter_concorrentes(self, carta):
        """Obtém dados de concorrentes para uma carta"""
        if not self.scrape_concorrentes:
            return []
        
        try:
            ofertas = self.myp_service.scrape_market_card(
                carta['numero'],
                carta['colecao'],
                carta['tipo'],
                carta['idioma']
            )
            
            # Filtrar para remover você mesmo
            meu_usuario = os.getenv('MYP_USERNAME_URL', 'aocarmo')
            concorrentes = [o for o in ofertas if o['vendedor'].lower() != meu_usuario.lower()]
            
            return concorrentes
        except Exception as e:
            print(f"⚠️  Erro ao buscar concorrentes para {carta['numero']}: {str(e)}")
            return []
    
    def calcular_preco_ideal(self, carta, concorrentes):
        """
        Aplica estratégia de frete único
        
        Args:
            carta: dict com dados da carta (numero, colecao, tipo, idioma, preco, quantidade)
            concorrentes: list de dicts com dados dos concorrentes
        
        Returns:
            dict com preco_ideal, estrategia_usada, justificativa
        """
        preco_atual = float(carta['preco'])
        meu_estoque = int(carta['quantidade'])
        
        # Encontrar menor preço concorrente
        if concorrentes:
            menor_preco = min(float(c['preco']) for c in concorrentes)
            estoque_concorrente = sum(int(c.get('quantidade', 0)) for c in concorrentes)
        else:
            menor_preco = preco_atual
            estoque_concorrente = 0
        
        # REGRA 1: Cartas baratas (< R$5) - margem normal
        if menor_preco < 5.00:
            preco_ideal = menor_preco * 1.08  # +8%
            return {
                'preco_ideal': round(preco_ideal, 2),
                'estrategia': 'MARGEM_NORMAL',
                'justificativa': 'Carta barata - margem padrão 8%',
                'premium': 0
            }
        
        # REGRA 2: Cartas médias (R$5-10) com estoque
        if 5.00 <= menor_preco < 10.00:
            if meu_estoque >= 5 and (meu_estoque - estoque_concorrente) >= 3:
                preco_ideal = menor_preco * 1.18  # +18%
                return {
                    'preco_ideal': round(preco_ideal, 2),
                    'estrategia': 'PREMIUM_MODERADO',
                    'justificativa': f'Estoque vantajoso ({meu_estoque} vs {estoque_concorrente})',
                    'premium': round(preco_ideal - menor_preco, 2)
                }
            else:
                preco_ideal = menor_preco * 1.10  # +10%
                return {
                    'preco_ideal': round(preco_ideal, 2),
                    'estrategia': 'MARGEM_NORMAL',
                    'justificativa': 'Estoque similar aos concorrentes',
                    'premium': 0
                }
        
        # REGRA 3: Cartas caras (≥R$10) - VANTAGEM FRETE ÚNICO
        if menor_preco >= 10.00:
            if meu_estoque >= 10 and estoque_concorrente <= 3:
                # Calcular vantagem do frete único
                economia_frete = self.frete_medio * (meu_estoque - 1)
                premium_por_carta = economia_frete / meu_estoque
                
                # Limitar premium a 25% do valor da carta
                premium_maximo = menor_preco * 0.25
                premium_aplicado = min(premium_por_carta, premium_maximo)
                
                preco_ideal = menor_preco + premium_aplicado
                
                return {
                    'preco_ideal': round(preco_ideal, 2),
                    'estrategia': 'PREMIUM_FRETE_UNICO',
                    'justificativa': f'Frete único: economia de R${economia_frete:.2f} para {meu_estoque} cartas',
                    'premium': round(premium_aplicado, 2),
                    'quantidade_disponibilizar': int(meu_estoque * 0.5)  # Disponibilizar 50%
                }
            else:
                preco_ideal = menor_preco * 1.12  # +12%
                return {
                    'preco_ideal': round(preco_ideal, 2),
                    'estrategia': 'MARGEM_NORMAL',
                    'justificativa': 'Estoque insuficiente para premium',
                    'premium': 0
                }
        
        # Fallback
        return {
            'preco_ideal': preco_atual,
            'estrategia': 'MANTER',
            'justificativa': 'Sem dados suficientes',
            'premium': 0
        }
    
    def processar_inventario(self, filtros=None):
        """
        Processa todo o inventário e gera CSV com preços otimizados
        
        Args:
            filtros: dict com filtros opcionais (colecao, tipo, idioma)
        
        Returns:
            str: caminho do arquivo CSV gerado
        """
        # 1. Obter inventário atual (USA API EXISTENTE)
        params = filtros or {}
        params['limit'] = 10000
        
        response = requests.get(API_URL, params=params)
        data = response.json()
        
        if not data.get('success'):
            raise Exception(f"Erro ao obter inventário: {data.get('error')}")
        
        cartas = data['cards']
        
        # 2. Para cada carta, calcular preço ideal
        resultados = []
        total = len(cartas)
        
        print(f"\n🔍 Analisando {total} cartas...")
        print(f"{'='*60}\n")
        
        for i, carta in enumerate(cartas, 1):
            # Obter dados de concorrentes (scraping real)
            concorrentes = self.obter_concorrentes(carta)
            
            resultado = self.calcular_preco_ideal(carta, concorrentes)
            
            resultados.append({
                **carta,
                **resultado,
                'concorrentes_encontrados': len(concorrentes)
            })
            
            # Progress
            if i % 10 == 0 or i == total:
                print(f"Processadas: {i}/{total} ({i/total*100:.1f}%)")
        
        print(f"\n{'='*60}\n")
        
        # 3. Gerar CSV para atualização (USA FORMATO EXISTENTE)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'precos_otimizados_{timestamp}.csv'
        
        with open(filename, 'w') as f:
            f.write('numero,colecao,tipo,idioma,preco,quantidade\n')
            for r in resultados:
                # Usar quantidade ajustada se houver premium de frete
                qtd = r.get('quantidade_disponibilizar', r['quantidade'])
                f.write(f"{r['numero']},{r['colecao']},{r['tipo']},{r['idioma']},{r['preco_ideal']},{qtd}\n")
        
        # 4. Gerar relatório
        print(f"\n{'='*60}")
        print(f"📊 RELATÓRIO DE PRECIFICAÇÃO")
        print(f"{'='*60}\n")
        
        estrategias = {}
        for r in resultados:
            est = r['estrategia']
            estrategias[est] = estrategias.get(est, 0) + 1
        
        for est, count in estrategias.items():
            print(f"{est:25} - {count:4} cartas")
        
        print(f"\n{'='*60}")
        print(f"✅ CSV gerado: {filename}")
        print(f"📦 Total de cartas: {len(resultados)}")
        print(f"\n💡 Para aplicar os preços:")
        print(f"curl -X POST .../upload-csv -F 'file=@{filename}' -F 'operation=atualizar'")
        print(f"{'='*60}\n")
        
        return filename

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Precificação dinâmica com estratégia de frete único')
    parser.add_argument('--colecao', help='Filtrar por coleção')
    parser.add_argument('--tipo', help='Filtrar por tipo')
    parser.add_argument('--idioma', help='Filtrar por idioma')
    
    args = parser.parse_args()
    
    filtros = {}
    if args.colecao:
        filtros['colecao'] = args.colecao
    if args.tipo:
        filtros['tipo'] = args.tipo
    if args.idioma:
        filtros['idioma'] = args.idioma
    
    precificacao = PrecificacaoDinamica()
    precificacao.processar_inventario(filtros)
