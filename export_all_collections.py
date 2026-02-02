#!/usr/bin/env python3
"""
Exporta inventário completo em múltiplos CSVs organizados por coleção, tipo e idioma
Uso: python3 export_all_collections.py [--output-dir exports]
"""
import requests
import os
import argparse
from datetime import datetime

API_URL = "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory"

def export_all_collections(output_dir):
    """Exporta todas as combinações de coleção/tipo/idioma"""
    
    # Criar diretório se não existir
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📁 Diretório de saída: {output_dir}\n")
    
    # Obter resumo para saber quais coleções existem
    print("🔍 Consultando coleções disponíveis...")
    response = requests.get(f"{API_URL}/summary")
    summary = response.json()
    
    colecoes = list(summary['by_collection'].keys())
    tipos = ['normal', 'foil', 'reverse-foil']
    idiomas = ['portugues', 'ingles', 'espanhol']
    
    print(f"📦 Coleções: {', '.join(colecoes)}")
    print(f"🎨 Tipos: {', '.join(tipos)}")
    print(f"🌍 Idiomas: {', '.join(idiomas)}\n")
    
    total_files = 0
    total_cards = 0
    
    for colecao in colecoes:
        for tipo in tipos:
            for idioma in idiomas:
                # Consultar API
                params = {
                    'colecao': colecao,
                    'tipo': tipo,
                    'idioma': idioma,
                    'limit': 10000
                }
                
                try:
                    response = requests.get(API_URL, params=params)
                    data = response.json()
                    
                    if data.get('success') and len(data.get('cards', [])) > 0:
                        filename = f"{colecao.lower()}_{tipo}_{idioma}.csv"
                        filepath = os.path.join(output_dir, filename)
                        
                        with open(filepath, 'w') as f:
                            f.write('numero,colecao,tipo,idioma,preco,quantidade\n')
                            for card in data['cards']:
                                f.write(f"{card['numero']},{card['colecao']},{card['tipo']},{card['idioma']},{card['preco']},{card['quantidade']}\n")
                        
                        card_count = len(data['cards'])
                        total_files += 1
                        total_cards += card_count
                        print(f"✅ {filename:40} - {card_count:4} cartas")
                
                except Exception as e:
                    print(f"❌ Erro ao exportar {colecao}/{tipo}/{idioma}: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"🎉 Exportação concluída!")
    print(f"📊 Total: {total_files} arquivos | {total_cards} cartas")
    print(f"📁 Localização: {os.path.abspath(output_dir)}")
    print(f"⏰ Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Exporta todas as coleções em CSVs separados')
    parser.add_argument('--output-dir', default='exports', help='Diretório de saída (padrão: exports)')
    
    args = parser.parse_args()
    
    export_all_collections(args.output_dir)
