#!/usr/bin/env python3
"""
Exporta inventário para CSV com filtros opcionais
Uso: python3 export_inventory.py [--colecao PRE] [--tipo foil] [--idioma ingles] [--preco-min 10] [--preco-max 100] [--quantidade-min 1] [--output inventario.csv]
"""
import requests
import sys
import argparse

API_URL = "https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory"

def export_inventory(filters, output_file):
    """Exporta inventário para CSV"""
    
    # Adicionar limit alto para pegar todas as cartas
    params = {**filters, 'limit': 10000}
    
    print(f"🔄 Consultando inventário com filtros: {params}")
    
    response = requests.get(API_URL, params=params)
    data = response.json()
    
    if not data.get('success'):
        print(f"❌ Erro: {data.get('error', 'Erro desconhecido')}")
        sys.exit(1)
    
    cards = data.get('cards', [])
    total = data.get('total', 0)
    
    print(f"✅ {len(cards)} cartas encontradas (total: {total})")
    
    # Escrever CSV
    with open(output_file, 'w') as f:
        f.write('numero,colecao,tipo,idioma,preco,quantidade\n')
        for card in cards:
            f.write(f"{card['numero']},{card['colecao']},{card['tipo']},{card['idioma']},{card['preco']},{card['quantidade']}\n")
    
    print(f"💾 Arquivo salvo: {output_file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Exporta inventário para CSV')
    parser.add_argument('--colecao', help='Filtrar por coleção (ex: PRE, SVI)')
    parser.add_argument('--numero', help='Filtrar por número (ex: 077/131)')
    parser.add_argument('--tipo', help='Filtrar por tipo (normal, foil, reverse-foil)')
    parser.add_argument('--idioma', help='Filtrar por idioma (portugues, ingles)')
    parser.add_argument('--preco-min', type=float, help='Preço mínimo')
    parser.add_argument('--preco-max', type=float, help='Preço máximo')
    parser.add_argument('--quantidade-min', type=int, help='Quantidade mínima')
    parser.add_argument('--output', default='inventario.csv', help='Arquivo de saída (padrão: inventario.csv)')
    
    args = parser.parse_args()
    
    # Montar filtros
    filters = {}
    if args.colecao:
        filters['colecao'] = args.colecao
    if args.numero:
        filters['numero'] = args.numero
    if args.tipo:
        filters['tipo'] = args.tipo
    if args.idioma:
        filters['idioma'] = args.idioma
    if args.preco_min:
        filters['preco_min'] = args.preco_min
    if args.preco_max:
        filters['preco_max'] = args.preco_max
    if args.quantidade_min:
        filters['quantidade_min'] = args.quantidade_min
    
    export_inventory(filters, args.output)
