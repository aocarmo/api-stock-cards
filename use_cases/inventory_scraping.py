"""
Use case para scraping de inventário
"""
from services.myp_service import MypService
import json
import csv

class InventoryScrapingUseCase:
    def __init__(self):
        self.service = MypService()
    
    def execute(self, price_ranges=None, output_format='both'):
        """
        Executa scraping e análise de precificação
        
        Args:
            price_ranges: Lista de tuplas (min, max) para filtrar preços
            output_format: 'csv', 'json' ou 'both'
        
        Returns:
            dict: Resultado da operação com sugestões de preço
        """
        try:
            # Carregar sessão
            cookies = self.service.get_session()
            self.service.init_scraper(cookies)
            
            # Scraping
            inventory = self.service.scrape_inventory(price_ranges)
            
            if not inventory:
                return {'success': False, 'message': 'Nenhuma carta encontrada'}
            
            # Análise de precificação
            pricing_analysis = self._analyze_pricing(inventory)
            
            result = {
                'success': True, 
                'count': len(inventory), 
                'files': [],
                'pricing_suggestions': pricing_analysis['suggestions'],
                'underpriced_count': pricing_analysis['underpriced_count']
            }
            
            # Salvar arquivos
            if output_format in ['csv', 'both']:
                self._save_csv(inventory)
                result['files'].append('inventory.csv')
            
            if output_format in ['json', 'both']:
                self._save_json(inventory)
                result['files'].append('inventory.json')
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _analyze_pricing(self, inventory):
        """Analisa preços e sugere ajustes baseado no mercado"""
        suggestions = []
        underpriced_count = 0
        
        for card in inventory:
            current_price = float(card['preco'])
            
            # Lógica simples: cartas abaixo de R$5 podem estar subprecificadas
            if current_price < 5.0:
                market_price = self._get_market_price(card)
                if market_price and market_price > current_price * 1.5:
                    suggestions.append({
                        'carta': f"{card['numero']} {card['colecao']}",
                        'preco_atual': current_price,
                        'preco_sugerido': market_price,
                        'aumento_percentual': ((market_price - current_price) / current_price) * 100
                    })
                    underpriced_count += 1
        
        return {
            'suggestions': suggestions,
            'underpriced_count': underpriced_count
        }
    
    def _get_market_price(self, card):
        """Busca preço de mercado (implementar integração com APIs)"""
        # TODO: Integrar com TCGPlayer, CardMarket, etc
        # Por enquanto, retorna None
        return None
    
    def _save_csv(self, inventory):
        with open('inventory.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['numero', 'colecao', 'tipo', 'idioma', 'preco', 'quantidade'])
            writer.writeheader()
            writer.writerows(inventory)
    
    def _save_json(self, inventory):
        with open('inventory.json', 'w', encoding='utf-8') as f:
            json.dump(inventory, f, indent=2, ensure_ascii=False)
