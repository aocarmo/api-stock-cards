#!/usr/bin/env python3
"""
Algoritmo de Precificação Dinâmica MYP Cards
Baseado na análise de concorrência real
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.myp_service import MypService
from bs4 import BeautifulSoup
import re
import json

class PrecificacaoDinamica:
    def __init__(self):
        self.myp = MypService()
        self._init_session()
    
    def _init_session(self):
        """Inicializa sessão MYP"""
        try:
            cookies = self.myp.get_session()
            self.myp.init_scraper(cookies)
            print("✅ Sessão carregada")
        except:
            print("🔄 Fazendo login...")
            if not self.myp.login():
                raise Exception("❌ Erro no login")
            cookies = self.myp.get_session()
            self.myp.init_scraper(cookies)
    
    def analisar_concorrencia(self, idproduto):
        """Analisa concorrência de um produto específico"""
        url = f'https://mypcards.com/pokemon/produto/{idproduto}'
        
        try:
            resp = self.myp.scraper.get(url)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Extrair nome do produto
            nome_produto = soup.find('h1')
            nome = nome_produto.get_text(strip=True) if nome_produto else f'Produto {idproduto}'
            
            # Extrair dados dos vendedores
            vendedores = []
            rows = soup.find_all('tr', {'data-key': True})
            
            for row in rows:
                try:
                    # Nome do vendedor
                    vendedor_td = row.find('td', class_='estoque-lista-nomevendedor')
                    vendedor = vendedor_td.find('a').get_text(strip=True) if vendedor_td and vendedor_td.find('a') else 'N/A'
                    
                    # Tipo (foil)
                    tipo_td = row.find('td', class_='estoque-lista-nomeenfoil')
                    tipo = tipo_td.get_text(strip=True) if tipo_td else 'Normal'
                    if not tipo:
                        tipo = 'Normal'
                    
                    # Idioma
                    qualidade_td = row.find('td', class_='estoque-lista-qualidadenome')
                    idioma = 'N/A'
                    if qualidade_td:
                        flag = qualidade_td.find('span', class_='flag-icon')
                        if flag:
                            idioma = flag.get('title', 'N/A')
                    
                    # Quantidade
                    qtd_td = row.find('td', class_='estoque-lista-quantidadeestoque')
                    quantidade_text = qtd_td.get_text(strip=True) if qtd_td else '1 un.'
                    quantidade = int(quantidade_text.split()[0]) if quantidade_text.split() else 1
                    
                    # Preço
                    preco_td = row.find('td', class_='estoque-lista-precoestoque')
                    preco_valor = 0.0
                    
                    if preco_td:
                        preco_span = preco_td.find('span', class_='moeda')
                        if preco_span:
                            preco_text = preco_span.get_text(strip=True)
                            match = re.search(r'R\$\s*([\d,]+\.?\d*)', preco_text)
                            if match:
                                valor_str = match.group(1)
                                if ',' in valor_str and '.' not in valor_str:
                                    preco_valor = float(valor_str.replace(',', '.'))
                                elif '.' in valor_str and ',' in valor_str:
                                    preco_valor = float(valor_str.replace('.', '').replace(',', '.'))
                                else:
                                    preco_valor = float(valor_str)
                    
                    if preco_valor > 0:
                        vendedores.append({
                            'vendedor': vendedor,
                            'tipo': tipo,
                            'idioma': idioma,
                            'quantidade': quantidade,
                            'preco': preco_valor
                        })
                        
                except Exception as e:
                    continue
            
            return {
                'nome': nome,
                'idproduto': idproduto,
                'vendedores': vendedores,
                'total_ofertas': len(vendedores)
            }
            
        except Exception as e:
            print(f"❌ Erro ao analisar produto {idproduto}: {e}")
            return None
    
    def calcular_preco_ideal(self, analise, tipo_desejado='Normal', idioma_desejado='Português', meu_estoque=1, valor_min_dinamico=5.0, valor_max_dinamico=999999.0):
        """Calcula preço ideal baseado na concorrência E no meu estoque"""
        if not analise or not analise['vendedores']:
            return None
        
        # Filtrar por tipo e idioma
        concorrentes = [
            v for v in analise['vendedores'] 
            if v['tipo'] == tipo_desejado and v['idioma'] == idioma_desejado
        ]
        
        if not concorrentes:
            concorrentes = analise['vendedores']
        
        if not concorrentes:
            return None
        
        # Ordenar por preço
        concorrentes.sort(key=lambda x: x['preco'])
        
        precos = [c['preco'] for c in concorrentes]
        menor = min(precos)
        
        # NOVA LÓGICA: Considerar vantagem do frete único APENAS no range configurado
        menor_concorrente = concorrentes[0]
        estoque_menor_preco = menor_concorrente['quantidade']
        
        # Verificar se está no range para aplicar estratégia dinâmica
        no_range_dinamico = valor_min_dinamico <= menor <= valor_max_dinamico
        
        # Calcular "valor do frete único" baseado no range configurável
        if no_range_dinamico:
            frete_medio = 30.0  # Custo médio do frete
            # Vantagem = economia de fretes que o cliente teria
            if meu_estoque > estoque_menor_preco:
                fretes_economizados = min(meu_estoque - estoque_menor_preco, 10)  # Máximo 10 fretes
                vantagem_frete = (fretes_economizados * frete_medio) / meu_estoque  # Distribuir entre as cartas
                vantagem_frete = min(vantagem_frete, menor * 0.25)  # Máximo 25% do valor da carta
            else:
                vantagem_frete = 0
        else:
            vantagem_frete = 0  # Fora do range = estratégia normal
        
        # Estratégia baseada na diferença de estoque
        diferenca_estoque = meu_estoque - estoque_menor_preco
        
        if meu_estoque >= 10 and no_range_dinamico and estoque_menor_preco <= 3:
            # GRANDE VANTAGEM: Posso cobrar premium pelo frete único
            preco_ideal = menor + vantagem_frete
            quantidade_rec = min(meu_estoque // 2, 10)  # Até 50% do estoque ou 10 unidades
            estrategia = f"Premium por frete único - concorrente tem só {estoque_menor_preco} un."
            
        elif meu_estoque >= 5 and no_range_dinamico and diferenca_estoque >= 3:  # Vantagem moderada
            preco_ideal = menor + (vantagem_frete * 0.6)
            quantidade_rec = min(meu_estoque // 3, 8)
            estrategia = f"Vantagem moderada - {diferenca_estoque} unidades a mais"
            
        else:  # Estratégia normal
            num_concorrentes = len(concorrentes)
            vantagem_frete = 0  # Não aplicar vantagem frete em estratégia normal
            
            if num_concorrentes <= 3:
                preco_ideal = menor * 1.10
                quantidade_rec = min(meu_estoque, 5)
                estrategia = "Baixa concorrência - estratégia normal"
            elif num_concorrentes <= 8:
                preco_ideal = menor * 1.08
                quantidade_rec = min(meu_estoque, 3)
                estrategia = "Média concorrência - estratégia normal"
            else:
                preco_ideal = menor * 1.05
                quantidade_rec = min(meu_estoque, 2)
                estrategia = "Alta concorrência - estratégia normal"
        
        # Garantir margem mínima
        preco_ideal = max(preco_ideal, menor * 1.05)
        
        return {
            'preco_ideal': round(preco_ideal, 2),
            'quantidade_recomendada': quantidade_rec,
            'posicao_estimada': '2ª-3ª mais barata' if vantagem_frete == 0 else 'Premium justificado',
            'margem_sobre_menor': round(((preco_ideal/menor-1)*100), 1),
            'estrategia': estrategia,
            'vantagem_frete_unico': round(vantagem_frete, 2),
            'valor_min_dinamico': valor_min_dinamico,
            'valor_max_dinamico': valor_max_dinamico,
            'no_range_dinamico': no_range_dinamico,
            'aplicou_dinamico': no_range_dinamico and vantagem_frete > 0,
            'meu_estoque': meu_estoque,
            'estoque_menor_preco': estoque_menor_preco,
            'diferenca_estoque': diferenca_estoque,
            'concorrentes_diretos': len(concorrentes),
            'menor_preco_concorrencia': menor,
            'alertas': self._gerar_alertas_v2(concorrentes, preco_ideal, meu_estoque, menor)
        }
    
    def _gerar_alertas_v2(self, concorrentes, preco_ideal, meu_estoque, menor_preco):
        """Gera alertas considerando vantagem do frete único"""
        alertas = []
        
        menor_concorrente = concorrentes[0]
        estoque_menor_preco = menor_concorrente['quantidade']
        
        # Alerta de oportunidade de frete único
        if meu_estoque >= 10 and menor_preco >= 5.0 and estoque_menor_preco <= 2:
            alertas.append(f"🎯 GRANDE OPORTUNIDADE: Você tem {meu_estoque} un. vs {estoque_menor_preco} un. do mais barato")
            alertas.append("💰 Pode cobrar premium pelo frete único!")
        
        # Alerta de vantagem moderada
        elif meu_estoque >= 5 and (meu_estoque - estoque_menor_preco) >= 3:
            alertas.append(f"📦 Vantagem de estoque: +{meu_estoque - estoque_menor_preco} unidades vs concorrente")
        
        # Alerta de desvantagem
        elif estoque_menor_preco >= meu_estoque * 2:
            alertas.append(f"⚠️ Concorrente tem muito mais estoque ({estoque_menor_preco} vs {meu_estoque})")
        
        # Alerta de guerra de preços
        precos_similares = [c['preco'] for c in concorrentes if c['preco'] < menor_preco * 1.1]
        if len(precos_similares) >= 3:
            alertas.append("⚠️ Guerra de preços ativa - muitos vendedores com preços similares")
        
        # Alerta de margem
        margem = (preco_ideal / menor_preco - 1) * 100
        if margem < 8:
            alertas.append("💰 Margem baixa - considere focar em outras cartas")
        elif margem > 25:
            alertas.append("🚀 Margem alta - ótima oportunidade!")
        
        return alertas
    
    def processar_carta(self, numero, colecao, tipo='Normal', idioma='Português', meu_estoque=1, valor_min_dinamico=5.0, valor_max_dinamico=999999.0):
        """Processa uma carta específica e retorna estratégia completa"""
        print(f"\n🔍 Analisando: {numero} ({colecao}) - {tipo} - {idioma} | Estoque: {meu_estoque}")
        print(f"🎯 Range dinâmico: R$ {valor_min_dinamico:.2f} - R$ {valor_max_dinamico:.2f}")
        print("=" * 80)
        
        # Buscar ID do produto
        idproduto = self.myp.search_product_id(numero, colecao)
        if not idproduto:
            return {"erro": f"Produto não encontrado: {numero} ({colecao})"}
        
        # Analisar concorrência
        analise = self.analisar_concorrencia(idproduto)
        if not analise:
            return {"erro": f"Erro ao analisar concorrência do produto {idproduto}"}
        
        # Calcular preço ideal COM RANGE
        estrategia = self.calcular_preco_ideal(analise, tipo, idioma, meu_estoque, valor_min_dinamico, valor_max_dinamico)
        if not estrategia:
            return {"erro": "Não foi possível calcular estratégia de preço"}
        
        # Montar resultado
        resultado = {
            "carta": f"{numero} ({colecao})",
            "tipo": tipo,
            "idioma": idioma,
            "meu_estoque": meu_estoque,
            "valor_min_dinamico": valor_min_dinamico,
            "valor_max_dinamico": valor_max_dinamico,
            "idproduto": idproduto,
            "analise_concorrencia": analise,
            "estrategia": estrategia
        }
        
        # Exibir resultado
        self._exibir_resultado_v2(resultado)
        
        return resultado
    
    def _exibir_resultado_v2(self, resultado):
        """Exibe resultado formatado com nova lógica"""
        est = resultado['estrategia']
        analise = resultado['analise_concorrencia']
        
        print(f"📊 CONCORRÊNCIA: {analise['total_ofertas']} ofertas ativas")
        print(f"🎯 PREÇO IDEAL: R$ {est['preco_ideal']:.2f}")
        print(f"📦 QUANTIDADE: {est['quantidade_recomendada']} unidades")
        print(f"📈 MARGEM: +{est['margem_sobre_menor']:.1f}% sobre menor preço")
        print(f"🏆 POSIÇÃO: {est['posicao_estimada']}")
        print(f"💡 ESTRATÉGIA: {est['estrategia']}")
        
        # Mostrar se aplicou estratégia dinâmica
        if est.get('no_range_dinamico', False):
            if est.get('aplicou_dinamico', False):
                print(f"🎯 ESTRATÉGIA DINÂMICA APLICADA (R$ {est['valor_min_dinamico']:.2f} - R$ {est['valor_max_dinamico']:.2f})")
            else:
                print(f"📊 NO RANGE MAS SEM VANTAGEM (R$ {est['valor_min_dinamico']:.2f} - R$ {est['valor_max_dinamico']:.2f})")
        else:
            print(f"📊 FORA DO RANGE DINÂMICO (R$ {est['valor_min_dinamico']:.2f} - R$ {est['valor_max_dinamico']:.2f})")
        
        # Mostrar vantagem do frete único
        if est.get('vantagem_frete_unico', 0) > 0:
            print(f"🚚 VANTAGEM FRETE ÚNICO: +R$ {est['vantagem_frete_unico']:.2f}")
        
        # Comparação de estoque
        print(f"\n📦 COMPARAÇÃO DE ESTOQUE:")
        print(f"• Seu estoque: {est['meu_estoque']} unidades")
        print(f"• Menor preço tem: {est['estoque_menor_preco']} unidades")
        print(f"• Diferença: {est['diferenca_estoque']:+d} unidades")
        
        if est['alertas']:
            print(f"\n⚠️ ALERTAS:")
            for alerta in est['alertas']:
                print(f"  {alerta}")
        
        print(f"\n📋 RESUMO EXECUTIVO:")
        print(f"• Concorrentes diretos: {est['concorrentes_diretos']}")
        print(f"• Menor preço mercado: R$ {est['menor_preco_concorrencia']:.2f}")
        
        # Justificativa da estratégia
        if est.get('vantagem_frete_unico', 0) > 0:
            print(f"\n💰 JUSTIFICATIVA DO PREÇO PREMIUM:")
            print(f"• Cliente economiza R$ 30 de frete comprando {est['meu_estoque']} cartas")
            print(f"• Vs {est['estoque_menor_preco']} fretes de R$ 30 = R$ {est['estoque_menor_preco'] * 30:.0f}")
            print(f"• Economia real do cliente: R$ {(est['estoque_menor_preco'] - 1) * 30:.0f}")
            print(f"• Seu premium: R$ {est['vantagem_frete_unico']:.2f} (justo!)")

def main():
    """Exemplo de uso com diferentes cenários de estoque"""
    precificacao = PrecificacaoDinamica()
    
    print("🧪 TESTANDO ESTRATÉGIA COM DIFERENTES ESTOQUES")
    print("=" * 60)
    
    # Cenário 1: Pouco estoque (estratégia normal)
    print("\n🔸 CENÁRIO 1: Pouco estoque")
    resultado1 = precificacao.processar_carta("161/131", "PRE", "Normal", "Português", meu_estoque=2)
    
    # Cenário 2: Muito estoque (vantagem frete único)
    print("\n🔸 CENÁRIO 2: Muito estoque")
    resultado2 = precificacao.processar_carta("161/131", "PRE", "Normal", "Português", meu_estoque=20)
    
    # Salvar resultado em JSON para uso posterior
    with open('/tmp/estrategia_precificacao_v2.json', 'w') as f:
        json.dump({
            'pouco_estoque': resultado1,
            'muito_estoque': resultado2
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Estratégias salvas em /tmp/estrategia_precificacao_v2.json")

if __name__ == "__main__":
    main()
