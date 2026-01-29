#!/usr/bin/env python3
"""
Processador de CSV com Precificação Dinâmica Configurável
Permite definir valor mínimo para aplicar estratégia dinâmica
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from precificacao_dinamica import PrecificacaoDinamica
import csv
import argparse

def processar_csv_dinamico(arquivo_csv, valor_min=5.0, valor_max=999999.0, modo='simular'):
    """
    Processa CSV aplicando precificação dinâmica apenas no range especificado
    
    Args:
        arquivo_csv: Caminho para o arquivo CSV
        valor_min: Valor mínimo para aplicar estratégia dinâmica
        valor_max: Valor máximo para aplicar estratégia dinâmica
        modo: 'simular' ou 'atualizar'
    """
    
    precificacao = PrecificacaoDinamica()
    
    print(f"🚀 PROCESSAMENTO DINÂMICO COM RANGE")
    print(f"📁 Arquivo: {arquivo_csv}")
    print(f"💰 Range dinâmico: R$ {valor_min:.2f} - R$ {valor_max:.2f}")
    print(f"🔧 Modo: {modo}")
    print("=" * 60)
    
    resultados = {
        'dinamicas': [],  # Cartas que usaram estratégia dinâmica
        'normais': [],    # Cartas que usaram estratégia normal
        'erros': []       # Cartas com erro
    }
    
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
                    
                    print(f"\n📋 [{i}] {numero} ({colecao}) - R$ {preco_atual:.2f} - {quantidade_atual} un.")
                    
                    # Processar carta com range configurável
                    resultado = precificacao.processar_carta(
                        numero, colecao, tipo, idioma, 
                        meu_estoque=quantidade_atual,
                        valor_min_dinamico=valor_min,
                        valor_max_dinamico=valor_max
                    )
                    
                    if 'erro' in resultado:
                        print(f"❌ Erro: {resultado['erro']}")
                        resultados['erros'].append({
                            'linha': i,
                            'carta': f"{numero} ({colecao})",
                            'erro': resultado['erro']
                        })
                        continue
                    
                    estrategia = resultado['estrategia']
                    
                    # Classificar resultado
                    if estrategia.get('aplicou_dinamico', False):
                        resultados['dinamicas'].append({
                            'linha': i,
                            'carta': f"{numero} ({colecao})",
                            'preco_atual': preco_atual,
                            'preco_ideal': estrategia['preco_ideal'],
                            'diferenca': estrategia['preco_ideal'] - preco_atual,
                            'vantagem_frete': estrategia.get('vantagem_frete_unico', 0),
                            'estrategia': estrategia['estrategia']
                        })
                        print(f"🎯 DINÂMICA: R$ {preco_atual:.2f} → R$ {estrategia['preco_ideal']:.2f}")
                    else:
                        resultados['normais'].append({
                            'linha': i,
                            'carta': f"{numero} ({colecao})",
                            'preco_atual': preco_atual,
                            'preco_ideal': estrategia['preco_ideal'],
                            'diferenca': estrategia['preco_ideal'] - preco_atual,
                            'estrategia': estrategia['estrategia']
                        })
                        print(f"📊 NORMAL: R$ {preco_atual:.2f} → R$ {estrategia['preco_ideal']:.2f}")
                        
                except Exception as e:
                    print(f"❌ [{i}] Erro: {e}")
                    resultados['erros'].append({
                        'linha': i,
                        'carta': f"{row.get('numero', 'N/A')} ({row.get('colecao', 'N/A')})",
                        'erro': str(e)
                    })
    
    except Exception as e:
        print(f"❌ Erro ao ler CSV: {e}")
        return None
    
    # Relatório final
    print(f"\n" + "=" * 60)
    print(f"📊 RELATÓRIO FINAL")
    print(f"=" * 60)
    print(f"🎯 Cartas dinâmicas (R$ {valor_min:.2f} - R$ {valor_max:.2f}): {len(resultados['dinamicas'])}")
    print(f"📊 Cartas normais (fora do range): {len(resultados['normais'])}")
    print(f"❌ Erros: {len(resultados['erros'])}")
    
    if resultados['dinamicas']:
        print(f"\n💰 CARTAS COM ESTRATÉGIA DINÂMICA:")
        for item in resultados['dinamicas']:
            sinal = "+" if item['diferenca'] > 0 else ""
            print(f"  • {item['carta']}: R$ {item['preco_atual']:.2f} → R$ {item['preco_ideal']:.2f} ({sinal}{item['diferenca']:.2f})")
    
    return resultados

def main():
    parser = argparse.ArgumentParser(description='Processador CSV com Precificação Dinâmica Configurável')
    parser.add_argument('--arquivo', required=True, help='Arquivo CSV com cartas')
    parser.add_argument('--valor-min', type=float, default=5.0, help='Valor mínimo para estratégia dinâmica')
    parser.add_argument('--valor-max', type=float, default=999999.0, help='Valor máximo para estratégia dinâmica')
    parser.add_argument('--modo', choices=['simular', 'atualizar'], default='simular', help='Modo de operação')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.arquivo):
        print(f"❌ Arquivo não encontrado: {args.arquivo}")
        return
    
    processar_csv_dinamico(args.arquivo, args.valor_min, args.valor_max, args.modo)

if __name__ == "__main__":
    main()
