#!/usr/bin/env python3
"""Script para excluir cartas em massa via CSV"""
import argparse
import csv
import os
import sys

# Execução local: manter intervalo padrão de 2s (evita bloqueio no site),
# sem afetar Lambdas (lá definimos MYP_DELETE_DELAY_SECONDS no deploy).
os.environ.setdefault('MYP_DELETE_DELAY_SECONDS', '2')

from use_cases.excluir_massa_use_case import ExcluirMassaUseCase

def main():
    parser = argparse.ArgumentParser(description='Exclui cartas em massa a partir de um CSV')
    parser.add_argument(
        'csv_file',
        nargs='?',
        default='inventory.csv',
        help='CSV com colunas numero,colecao,tipo,idioma (padrão: inventory.csv)',
    )
    args = parser.parse_args()
    csv_file = args.csv_file
    
    # Ler CSV
    cartas = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cartas.append(row)
    
    print(f"📋 {len(cartas)} cartas para excluir\n")
    
    # Executar exclusão
    use_case = ExcluirMassaUseCase()
    resultados = use_case.execute(cartas)
    
    # Resumo
    excluidas = sum(1 for r in resultados if r['status'] == 'excluida')
    nao_encontradas = sum(1 for r in resultados if r['status'] == 'nao_encontrada')
    erros = sum(1 for r in resultados if r['status'] == 'erro')
    
    print(f"\n{'='*60}")
    print(f"✅ Excluídas: {excluidas}")
    print(f"⚠️  Não encontradas: {nao_encontradas}")
    print(f"❌ Erros: {erros}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
