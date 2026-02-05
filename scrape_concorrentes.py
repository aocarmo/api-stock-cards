#!/usr/bin/env python3
"""
Scraping de concorrentes para precificação dinâmica
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.myp_service import MypService
from bs4 import BeautifulSoup

class ScrapeConcorrentes:
    def __init__(self):
        self.service = MypService()
        self.service.login()
        self.service.init_scraper(self.service.get_session())
        self.meu_usuario = os.getenv('MYP_USERNAME_URL', 'aocarmo')
    
    def buscar_idproduto(self, numero, colecao):
        """Busca o ID do produto no site"""
        resp = self.service.scraper.get('https://mypcards.com/produto/search', params={
            'marca': 'pokemon',
            'term': numero
        })
        
        try:
            produtos = resp.json()
            for produto in produtos:
                nome = produto.get('nomeenproduto', '')
                if f" {colecao.upper()} " in nome.upper():
                    return {'idproduto': produto['idproduto']}
            return None
        except:
            return None
    
    def buscar_vendedores(self, idproduto, page=1, per_page=40):
        """
        Busca lista de vendedores de uma carta
        
        Args:
            idproduto: ID do produto no site
            page: Página (padrão: 1)
            per_page: Itens por página (padrão: 40)
        
        Returns:
            list: Lista de dicts com dados dos vendedores
        """
        # Acessar página do produto (vai redirecionar para URL completa)
        resp = self.service.scraper.get(f'https://mypcards.com/pokemon/produto/{idproduto}')
        
        if resp.status_code != 200:
            return []
        
        # Usar URL final após redirect
        url = resp.url
        
        # Buscar CSRF token
        soup = BeautifulSoup(resp.text, 'html.parser')
        csrf = soup.find('meta', {'name': 'csrf-token'})
        csrf_token = csrf['content'] if csrf else None
        
        # Requisição PJAX (usar URL final do redirect)
        headers = {
            'x-pjax': 'true',
            'x-pjax-container': '#p0',
            'x-requested-with': 'XMLHttpRequest',
            'x-csrf-token': csrf_token
        }
        
        params = {
            'estoque-page': page,
            'dp-1-per-page': per_page,
            '_pjax': '#p0'
        }
        
        resp = self.service.scraper.get(url, params=params, headers=headers)
        
        if resp.status_code != 200:
            return []
        
        # Parse tabela
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table', class_='table')
        
        if not table:
            return []
        
        vendedores = []
        rows = table.find_all('tr', {'data-key': True})
        
        for row in rows:
            try:
                # Vendedor
                vendedor_elem = row.find('td', class_='estoque-lista-nomevendedor')
                vendedor = vendedor_elem.find('a').text.strip() if vendedor_elem else 'Desconhecido'
                
                # Filtrar você mesmo
                if vendedor.lower() == self.meu_usuario.lower():
                    continue
                
                # Tipo/Foil
                tipo_elem = row.find('td', class_='estoque-lista-nomeenfoil')
                tipo = tipo_elem.text.strip() if tipo_elem and tipo_elem.text.strip() else 'normal'
                
                # Idioma
                idioma_elem = row.find('span', class_='flag-icon')
                idioma = idioma_elem.get('title', 'Desconhecido') if idioma_elem else 'Desconhecido'
                
                # Qualidade
                qualidade_elem = row.find('td', class_='estoque-lista-qualidadenome')
                qualidade = ''
                if qualidade_elem:
                    qualidade_text = qualidade_elem.get_text(strip=True)
                    # Extrair sigla da qualidade (NM, LP, MP, HP, DMG)
                    if 'NM' in qualidade_text:
                        qualidade = 'NM'
                    elif 'LP' in qualidade_text:
                        qualidade = 'LP'
                    elif 'MP' in qualidade_text:
                        qualidade = 'MP'
                    elif 'HP' in qualidade_text:
                        qualidade = 'HP'
                    elif 'DMG' in qualidade_text or 'Damaged' in qualidade_text:
                        qualidade = 'DMG'
                
                # Quantidade
                qtd_elem = row.find('td', class_='estoque-lista-quantidadeestoque')
                qtd_text = qtd_elem.text.strip().replace('un.', '').strip() if qtd_elem else '0'
                quantidade = int(qtd_text)
                
                # Preço
                preco_elem = row.find('span', class_='moeda')
                if not preco_elem:
                    continue
                preco_text = preco_elem.text.strip().replace('R$', '').replace('.', '').replace(',', '.').strip()
                preco = float(preco_text)
                
                vendedores.append({
                    'vendedor': vendedor,
                    'tipo': tipo,
                    'idioma': idioma,
                    'qualidade': qualidade,
                    'quantidade': quantidade,
                    'preco': preco
                })
                
            except Exception as e:
                continue
        
        return vendedores
    
    def buscar_carta_completa(self, numero, colecao, tipo, idioma):
        """
        Busca dados completos de concorrentes para uma carta
        
        Args:
            numero: Número da carta (ex: 077/131)
            colecao: Sigla da coleção (ex: SVI)
            tipo: Tipo da carta (normal, foil, reverse-foil, pokeball-foil, etc)
            idioma: Idioma (Português, Inglês)
        
        Returns:
            dict: {
                'menor_preco': float,
                'maior_preco': float,
                'preco_medio': float,
                'estoque_total': int,
                'vendedores': list
            }
        """
        # Buscar ID do produto
        produto = self.buscar_idproduto(numero, colecao)
        if not produto:
            return None
        
        idproduto = produto['idproduto']
        
        # Normalizar tipo e idioma para comparação
        tipo_busca = tipo.lower().strip()
        idioma_busca = idioma.lower().strip()
        
        # Mapear tipos para como aparecem no HTML (case-insensitive)
        tipo_map = {
            'normal': '',
            'foil': 'foil',
            'reverse-foil': 'reverse foil',
            'pokeball-foil': 'pokeball foil',
            'masterball-foil': 'masterball foil',
            'full-art': 'full-art',
            'altered-art': 'altered art',
            'promo': 'promo'
        }
        
        tipo_esperado = tipo_map.get(tipo_busca, tipo_busca)
        
        # Buscar em múltiplas páginas até encontrar ou acabar
        vendedores_filtrados = []
        page = 1
        max_pages = 20  # Aumentar limite
        
        while page <= max_pages:
            vendedores = self.buscar_vendedores(idproduto, page=page)
            
            if not vendedores:
                break  # Não há mais páginas
            
            # Filtrar por tipo, idioma E qualidade
            for v in vendedores:
                tipo_vendedor = v['tipo'].lower().strip()
                idioma_vendedor = v['idioma'].lower().strip()
                qualidade_vendedor = v.get('qualidade', '')
                
                # Normalizar idiomas
                idioma_norm = idioma_vendedor
                if 'portugu' in idioma_norm:
                    idioma_norm = 'português'
                elif 'ingl' in idioma_norm:
                    idioma_norm = 'inglês'
                elif 'espan' in idioma_norm:
                    idioma_norm = 'espanhol'
                
                # Filtrar: tipo + idioma + qualidade NM
                if tipo_vendedor == tipo_esperado and idioma_norm == idioma_busca and qualidade_vendedor == 'NM':
                    vendedores_filtrados.append(v)
            
            # Se encontrou, continua na página atual para pegar todos
            # Para quando a página tem menos de 40 itens (última página)
            if vendedores_filtrados and len(vendedores) < 40:
                break
            
            page += 1
        
        if not vendedores_filtrados:
            return None
        
        precos = [v['preco'] for v in vendedores_filtrados]
        
        return {
            'menor_preco': min(precos),
            'maior_preco': max(precos),
            'preco_medio': sum(precos) / len(precos),
            'estoque_total': sum(v['quantidade'] for v in vendedores_filtrados),
            'total_vendedores': len(vendedores_filtrados),
            'vendedores': vendedores_filtrados
        }

if __name__ == '__main__':
    import time
    
    # Teste com carta pokeball-foil que existe no inventário
    print("\n" + "="*60)
    print("Teste: 037/131 PRE pokeball-foil português")
    print("Meu preço atual: R$ 10,00")
    print("="*60)
    
    scraper = ScrapeConcorrentes()
    resultado = scraper.buscar_carta_completa('037/131', 'PRE', 'pokeball-foil', 'português')
    
    if resultado:
        print(f"💰 Menor preço: R$ {resultado['menor_preco']:.2f}")
        print(f"💰 Maior preço: R$ {resultado['maior_preco']:.2f}")
        print(f"💰 Preço médio: R$ {resultado['preco_medio']:.2f}")
        print(f"📦 Estoque total: {resultado['estoque_total']} unidades")
        print(f"👥 Total vendedores: {resultado['total_vendedores']}")
    else:
        print("❌ Nenhum resultado encontrado")
    
    print("\n" + "="*60 + "\n")
