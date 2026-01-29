#!/usr/bin/env python3
"""
Integração da Precificação Dinâmica com o Sistema MYP
Atualiza preços automaticamente baseado na concorrência
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from precificacao_dinamica import PrecificacaoDinamica
import csv
import json
from datetime import datetime

class AtualizadorPrecos:
    def __init__(self):
        self.precificacao = PrecificacaDinamica()
        self.log_file = f'/tmp/atualizacao_precos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    def log(self, mensagem):
        """Log com timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {mensagem}"
        print(log_msg)
        
        with open(self.log_file, 'a') as f:
            f.write(log_msg + '\n')
    
    def processar_csv(self, arquivo_csv, modo='atualizar'):
        """
        Processa CSV e aplica estratégia de precificação dinâmica
        
        Modos:
        - 'atualizar': Atualiza preços existentes
        - 'simular': Apenas simula, não atualiza
        - 'relatorio': Gera relatório de recomendações
        """
        
        self.log(f"🚀 Iniciando processamento: {arquivo_csv} (modo: {modo})")
        
        resultados = []
        
        try:
            with open(arquivo_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for i, row in enumerate(reader, 1):
                    try:
                        numero = row['numero']
                        colecao = row['colecao']
                        tipo = row.get('tipo', 'normal')
                        idioma = row.get('idioma', 'portugues')
                        preco_atual = float(row.get('preco', 0))
                        quantidade_atual = int(row.get('quantidade', 1))
                        
                        self.log(f"📋 [{i}] Processando: {numero} ({colecao})")
                        
                        # Analisar concorrência e calcular preço ideal
                        resultado = self.precificacao.processar_carta(numero, colecao, tipo, idioma)
                        
                        if 'erro' in resultado:
                            self.log(f"❌ [{i}] Erro: {resultado['erro']}")
                            resultados.append({
                                'linha': i,
                                'carta': f"{numero} ({colecao})",
                                'status': 'erro',
                                'erro': resultado['erro']
                            })
                            continue
                        
                        estrategia = resultado['estrategia']
                        preco_ideal = estrategia['preco_ideal']
                        quantidade_ideal = estrategia['quantidade_recomendada']
                        
                        # Decidir se deve atualizar
                        diferenca_preco = abs(preco_atual - preco_ideal)
                        diferenca_percentual = (diferenca_preco / preco_atual * 100) if preco_atual > 0 else 100
                        
                        deve_atualizar_preco = diferenca_percentual > 5  # Atualizar se diferença > 5%
                        deve_atualizar_quantidade = quantidade_atual != quantidade_ideal
                        
                        resultado_item = {
                            'linha': i,
                            'carta': f"{numero} ({colecao})",
                            'preco_atual': preco_atual,
                            'preco_ideal': preco_ideal,
                            'quantidade_atual': quantidade_atual,
                            'quantidade_ideal': quantidade_ideal,
                            'diferenca_preco': diferenca_preco,
                            'diferenca_percentual': diferenca_percentual,
                            'deve_atualizar_preco': deve_atualizar_preco,
                            'deve_atualizar_quantidade': deve_atualizar_quantidade,
                            'estrategia': estrategia,
                            'status': 'pendente'
                        }
                        
                        # Executar atualização se necessário
                        if modo == 'atualizar' and (deve_atualizar_preco or deve_atualizar_quantidade):
                            sucesso = self._atualizar_carta(resultado, preco_ideal, quantidade_ideal)
                            resultado_item['status'] = 'atualizado' if sucesso else 'erro_atualizacao'
                            
                            if sucesso:
                                self.log(f"✅ [{i}] Atualizado: R$ {preco_atual:.2f} → R$ {preco_ideal:.2f} | {quantidade_atual} → {quantidade_ideal} un.")
                            else:
                                self.log(f"❌ [{i}] Erro na atualização")
                        
                        elif modo == 'simular':
                            resultado_item['status'] = 'simulado'
                            if deve_atualizar_preco or deve_atualizar_quantidade:
                                self.log(f"💡 [{i}] Recomendação: R$ {preco_atual:.2f} → R$ {preco_ideal:.2f} | {quantidade_atual} → {quantidade_ideal} un.")
                            else:
                                self.log(f"✅ [{i}] Preço atual já está otimizado")
                        
                        resultados.append(resultado_item)
                        
                    except Exception as e:
                        self.log(f"❌ [{i}] Erro ao processar linha: {e}")
                        resultados.append({
                            'linha': i,
                            'carta': f"{row.get('numero', 'N/A')} ({row.get('colecao', 'N/A')})",
                            'status': 'erro',
                            'erro': str(e)
                        })
        
        except Exception as e:
            self.log(f"❌ Erro ao ler arquivo CSV: {e}")
            return None
        
        # Gerar relatório
        self._gerar_relatorio(resultados, modo)
        
        return resultados
    
    def _atualizar_carta(self, resultado_analise, novo_preco, nova_quantidade):
        """Atualiza carta no sistema MYP"""
        try:
            # Buscar carta existente
            numero = resultado_analise['carta'].split(' (')[0]
            colecao = resultado_analise['carta'].split('(')[1].split(')')[0]
            tipo = resultado_analise['tipo']
            idioma = resultado_analise['idioma']
            
            carta_existente = self.precificacao.myp.search_card(numero, colecao, tipo, idioma)
            
            if not carta_existente:
                self.log(f"❌ Carta não encontrada no seu estoque: {numero} ({colecao})")
                return False
            
            # Atualizar preço e quantidade
            sucesso = self.precificacao.myp.update_card(
                carta_existente['id_estoque'],
                preco=str(novo_preco),
                quantidade=str(nova_quantidade)
            )
            
            return sucesso
            
        except Exception as e:
            self.log(f"❌ Erro ao atualizar carta: {e}")
            return False
    
    def _gerar_relatorio(self, resultados, modo):
        """Gera relatório detalhado"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo_relatorio = f'/tmp/relatorio_precificacao_{timestamp}.json'
        
        # Estatísticas
        total = len(resultados)
        atualizados = len([r for r in resultados if r.get('status') == 'atualizado'])
        erros = len([r for r in resultados if r.get('status') in ['erro', 'erro_atualizacao']])
        simulados = len([r for r in resultados if r.get('status') == 'simulado'])
        
        relatorio = {
            'timestamp': datetime.now().isoformat(),
            'modo': modo,
            'estatisticas': {
                'total_processados': total,
                'atualizados': atualizados,
                'erros': erros,
                'simulados': simulados
            },
            'resultados': resultados
        }
        
        # Salvar relatório
        with open(arquivo_relatorio, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False)
        
        self.log(f"📊 RELATÓRIO FINAL:")
        self.log(f"   Total processados: {total}")
        self.log(f"   Atualizados: {atualizados}")
        self.log(f"   Erros: {erros}")
        self.log(f"   Simulados: {simulados}")
        self.log(f"   Relatório salvo: {arquivo_relatorio}")

def main():
    """Exemplo de uso"""
    atualizador = AtualizadorPrecos()
    
    # Exemplo com arquivo CSV
    arquivo_exemplo = '/Users/alex/Documents/projetos/pessoais/update-myp/exemplo.csv'
    
    if os.path.exists(arquivo_exemplo):
        print("🔍 Simulando atualização de preços...")
        resultados = atualizador.processar_csv(arquivo_exemplo, modo='simular')
        
        print(f"\n💡 Para aplicar as mudanças, execute:")
        print(f"python3 atualizador_precos.py --arquivo {arquivo_exemplo} --modo atualizar")
    else:
        print(f"❌ Arquivo não encontrado: {arquivo_exemplo}")
        print(f"💡 Crie um CSV com as colunas: numero,colecao,tipo,idioma,preco,quantidade")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Atualizador de Preços Dinâmico')
    parser.add_argument('--arquivo', required=True, help='Arquivo CSV com cartas')
    parser.add_argument('--modo', choices=['simular', 'atualizar', 'relatorio'], default='simular', help='Modo de operação')
    
    args = parser.parse_args()
    
    atualizador = AtualizadorPrecos()
    atualizador.processar_csv(args.arquivo, args.modo)
