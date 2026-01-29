#!/usr/bin/env python3
"""
Script para fazer scraping do inventário completo
"""
import csv
import json
from services.myp_service import MypService

def main():
    service = MypService()
    
    # Carregar sessão
    try:
        cookies = service.get_session()
        service.init_scraper(cookies)
        print(f"✅ Sessão carregada para usuário: {service.username_url}")
    except:
        print("❌ Erro ao carregar sessão. Execute o login primeiro.")
        return
    
    # Scraping
    inventory = service.scrape_inventory()
    
    if not inventory:
        print("❌ Nenhuma carta encontrada")
        return
    
    # Salvar CSV
    with open('inventory.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['numero', 'colecao', 'tipo', 'idioma', 'preco', 'quantidade'])
        writer.writeheader()
        writer.writerows(inventory)
    
    # Salvar JSON
    with open('inventory.json', 'w', encoding='utf-8') as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)
    
    print(f"✅ {len(inventory)} cartas salvas em inventory.csv e inventory.json")

if __name__ == "__main__":
    main()
