"""
Serviços para autenticação e manipulação de cartas
"""
import json
import os
import cloudscraper
from bs4 import BeautifulSoup
from enums.tipos_carta import TipoCarta, IdiomaCarta

# Carregar .env apenas em ambiente local
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()

class MypService:
    def __init__(self):
        self.scraper = None
        self.session_file = 'session.json'
        self._csrf_token = None
        self._csrf_timestamp = 0
    
    # Auth methods
    def get_session(self):
        """Recupera cookies salvos"""
        with open(self.session_file, 'r') as f:
            return json.load(f)
    
    def save_session(self, cookies):
        """Salva cookies"""
        with open(self.session_file, 'w') as f:
            json.dump(dict(cookies), f)
    
    def login(self):
        """Faz login e salva sessão"""
        scraper = cloudscraper.create_scraper()
        
        username = os.getenv('MYP_USERNAME')
        password = os.getenv('MYP_PASSWORD')
        
        print(f"DEBUG - Username: {username}")
        print(f"DEBUG - Password: {'*' * len(password) if password else 'None'}")
        
        if not username or not password:
            print("ERRO: Credenciais não encontradas no .env")
            return False
        
        # CSRF
        resp = scraper.get('https://mypcards.com/site/login')
        soup = BeautifulSoup(resp.text, 'html.parser')
        csrf = soup.find('meta', {'name': 'csrf-token'})['content']
        
        # Login
        data = {
            '_csrf': csrf,
            'LoginForm[username]': username,
            'LoginForm[password]': password,
            'rememberMe': '1'
        }
        
        resp = scraper.post('https://mypcards.com/site/login', data=data)
        
        print(f"DEBUG - URL após login: {resp.url}")
        
        if 'pokemon' in resp.url or 'aocarmo' in resp.url:
            self.save_session(scraper.cookies)
            return True
        return False
    
    def init_scraper(self, cookies):
        """Inicializa scraper com cookies"""
        self.scraper = cloudscraper.create_scraper()
        self.scraper.cookies.update(cookies)
    
    # Card methods
    def get_csrf(self, force_refresh=False):
        """Pega CSRF token com cache de 5 minutos"""
        import time
        
        # Se tem cache válido (menos de 5 minutos), retorna
        if not force_refresh and self._csrf_token and (time.time() - self._csrf_timestamp) < 300:
            return self._csrf_token
        
        # Busca novo token
        resp = self.scraper.get('https://mypcards.com/aocarmo')
        soup = BeautifulSoup(resp.text, 'html.parser')
        csrf_meta = soup.find('meta', {'name': 'csrf-token'})
        
        if csrf_meta:
            self._csrf_token = csrf_meta['content']
            self._csrf_timestamp = time.time()
            return self._csrf_token
        
        return None
    
    def search_product_id(self, numero, colecao):
        """Busca idproduto usando API de busca"""
        resp = self.scraper.get('https://mypcards.com/produto/search', params={
            'marca': 'pokemon',
            'term': numero
        })
        
        try:
            produtos = resp.json()
            print(f"DEBUG - Buscando produto: {numero} | Coleção: {colecao}")
            print(f"DEBUG - Produtos encontrados: {len(produtos)}")
            
            for produto in produtos:
                nome = produto.get('nomeenproduto', '')
                # Extrair coleção do nome (formato: "Nome COLECAO numero/total")
                if f" {colecao.upper()} " in nome.upper():
                    idproduto = produto['idproduto']
                    print(f"✅ Produto encontrado: {numero} ({colecao}) - idproduto: {idproduto}")
                    return idproduto
            
            print(f"❌ Produto não encontrado: {numero} ({colecao})")
            return None
            
        except Exception as e:
            print(f"❌ Erro ao buscar produto: {e}")
            return None
    
    def search_card(self, numero, colecao, tipo="", idioma=""):
        """Busca carta na pasta com filtros de coleção, tipo e idioma"""
        resp = self.scraper.get('https://mypcards.com/aocarmo/pokemon', params={
            'PastaSearch[query]': numero
        })
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        cards = soup.select('.stream-item .card')
        
        print(f"DEBUG - Buscando: {numero} | Coleção: {colecao} | Tipo: {tipo} | Idioma: {idioma}")
        print(f"DEBUG - Cartas encontradas: {len(cards)}")
        
        for card in cards:
            # Verificar coleção
            colecao_elemento = card.select_one('.card-edicao')
            colecao_atual = colecao_elemento.get_text(strip=True) if colecao_elemento else ""
            
            # Verificar tipo
            tipo_elemento = card.select_one('.estoque-lista-nomeenfoil')
            tipo_atual = tipo_elemento.get_text(strip=True) if tipo_elemento else ""
            
            # Verificar idioma pelo title da bandeira
            flag_element = card.select_one('.flag-icon')
            idioma_atual = flag_element.get('title', '') if flag_element else ""
            
            print(f"DEBUG - Carta: colecao='{colecao_atual}' | tipo_dom='{tipo_atual}' | idioma='{idioma_atual}'")
            
            # Match coleção
            colecao_match = colecao.upper() == colecao_atual.upper()
            
            # Lógica de match para tipo (mapear nome_api para nome_dom)
            if tipo == "normal" or tipo == "":
                tipo_match = not tipo_atual  # Normal = sem tipo
            else:
                tipo_dom = TipoCarta.get_dom_name_by_api_name(tipo)
                tipo_match = tipo_dom and tipo_dom.lower() in tipo_atual.lower()
            
            # Lógica de match para idioma (mapear nome_api para nome_dom)
            if idioma:
                idioma_dom = IdiomaCarta.get_dom_name_by_api_name(idioma)
                idioma_match = idioma_dom and idioma_dom.lower() in idioma_atual.lower()
            else:
                idioma_match = True
            
            print(f"DEBUG - Match: colecao={colecao_match} | tipo={tipo_match} | idioma={idioma_match}")
            
            if colecao_match and tipo_match and idioma_match:
                link = card.select_one('a.bt-offers')
                if link:
                    id_estoque = link['href'].split('/')[-1]
                    
                    # Coletar dados completos da carta
                    card_data = self._get_card_details(id_estoque)
                    card_data.update({
                        'id_estoque': id_estoque,
                        'numero': numero,
                        'colecao': colecao,
                        'tipo': tipo,
                        'idioma_nome': idioma
                    })
                    return card_data
        return None
    
    def delete_card(self, id_estoque):
        """Exclui carta usando endpoint direto"""
        csrf = self.get_csrf()
        if not csrf:
            return False
            
        data = {'_csrf': csrf}
        resp = self.scraper.post(f'https://mypcards.com/estoque/delete?id={id_estoque}', data=data)
        
        # 302 é redirect de sucesso, 200 também é ok
        return resp.status_code in [200, 302]
    
    def create_card(self, card_data):
        """Cadastra carta usando endpoint direto"""
        if not card_data.get('idproduto'):
            return False
        
        # Pegar CSRF token
        csrf = self.get_csrf()
        if not csrf:
            return False
        
        # Dados do formulário
        data = {
            '_csrf': csrf,
            'estoque-card-search': '',
            'imgbase64': '',
            'excluirImg': 'N',
            'Estoque[idproduto]': card_data['idproduto'],
            'Estoque[criarnovo]': 'false',
            'Estoque[ididioma]': IdiomaCarta.get_id_by_name(card_data.get('idioma_nome', 'portugues')),
            'Estoque[qualidadeestoque]': card_data.get('qualidade', 'NM'),
            'Estoque[idfoil]': TipoCarta.get_id_by_name(card_data.get('tipo', 'normal')),
            'Estoque[statusestoque]': 'V',
            'Estoque[quantidadeestoque]': card_data.get('quantidade', '1'),
            'Estoque[precoestoque]': card_data.get('preco', '0.99'),
            'Estoque[dataenvioestoque]': '',
            'Estoque[obsestoque]': ''
        }
        
        # POST direto
        resp = self.scraper.post(f'https://mypcards.com/estoque/create?idproduto={card_data["idproduto"]}', data=data)
        
        # Se redirecionou para produto, deu certo
        return resp.status_code == 200 and 'produto' in resp.url
    
    def update_card(self, id_estoque, preco=None, quantidade=None):
        """Atualiza carta"""
        resp = self.scraper.get(f'https://mypcards.com/estoque/update/{id_estoque}')
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        form = soup.find('form', {'id': 'estoque-form'})
        csrf = soup.find('meta', {'name': 'csrf-token'})['content']
        
        data = {
            '_csrf': csrf,
            'Estoque[idproduto]': form.find('input', {'id': 'estoque-idproduto'})['value'],
            'Estoque[criarnovo]': 'false',
            'Estoque[ididioma]': form.find('select', {'id': 'estoque-ididioma'}).find('option', selected=True)['value'],
            'Estoque[qualidadeestoque]': form.find('select', {'id': 'estoque-qualidadeestoque'}).find('option', selected=True)['value'],
            'Estoque[idfoil]': form.find('select', {'id': 'estoque-idfoil'}).find('option', selected=True)['value'],
            'Estoque[statusestoque]': 'V',
            'Estoque[quantidadeestoque]': quantidade or form.find('input', {'id': 'estoque-quantidadeestoque'})['value'],
            'Estoque[precoestoque]': preco or form.find('input', {'id': 'estoque-precoestoque'})['value']
        }
        
        resp = self.scraper.post(f'https://mypcards.com/estoque/update/{id_estoque}', data=data)
        return resp.status_code == 200 or 'estoque/update' in resp.url
    
    # Private methods
    def _get_card_details(self, id_estoque):
        """Pega dados completos da carta"""
        resp = self.scraper.get(f'https://mypcards.com/estoque/update/{id_estoque}')
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        form = soup.find('form', {'id': 'estoque-form'})
        if form:
            return {
                'idproduto': form.find('input', {'id': 'estoque-idproduto'})['value'],
                'qualidade': form.find('select', {'id': 'estoque-qualidadeestoque'}).find('option', selected=True)['value'],
                'preco': form.find('input', {'id': 'estoque-precoestoque'})['value'],
                'quantidade': form.find('input', {'id': 'estoque-quantidadeestoque'})['value']
            }
        return {}
