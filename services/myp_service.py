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
        self.session_file = '/tmp/session.json'
        self._csrf_token = None
        self._csrf_timestamp = 0
        self.username_url = None
    
    # Auth methods
    def get_session(self):
        """Recupera cookies e username salvos"""
        with open(self.session_file, 'r') as f:
            data = json.load(f)
            # Compatibilidade com formato antigo (só cookies)
            if isinstance(data, dict) and 'cookies' in data:
                self.username_url = data.get('username')
                return data['cookies']
            return data
    
    def get_user_id(self):
        """Extrai ID do usuário do cookie _identity"""
        try:
            cookies = self.get_session()
            identity_cookie = cookies.get('_identity', '')
            
            # Cookie _identity é um formato serializado do PHP
            # Formato: hash:2:{i:0;s:9:"_identity";i:1;s:51:"[109299,\"token\",expire]";}
            import urllib.parse
            import re
            
            # Decodificar URL
            decoded = urllib.parse.unquote(identity_cookie)
            
            # Extrair o JSON array usando regex
            match = re.search(r'\[(\d+),', decoded)
            if match:
                user_id = match.group(1)
                print(f"DEBUG - User ID extraído: {user_id}")
                return user_id
            
            print("DEBUG - Não foi possível extrair user_id do cookie")
            return None
            
        except Exception as e:
            print(f"DEBUG - Erro ao extrair user_id: {e}")
            return None
    
    def save_session(self, cookies):
        """Salva cookies e username"""
        with open(self.session_file, 'w') as f:
            json.dump({
                'cookies': dict(cookies),
                'username': self.username_url
            }, f)
    
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
        
        print(f"DEBUG - Status code: {resp.status_code}")
        print(f"DEBUG - URL após login: {resp.url}")
        
        # Parse HTML para extrair username
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Tentar pegar do link "Minha Pasta" ou similar
        # Formato: <a href="/Mavipoke">Minha Pasta</a>
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Procurar por links que levam à pasta do usuário
            if 'Minha Pasta' in text or 'pasta' in text.lower():
                username = href.strip('/')
                if username and '/' not in username:
                    self.username_url = username
                    print(f"DEBUG - Username extraído do link '{text}': {self.username_url}")
                    self.save_session(scraper.cookies)
                    return True
        
        # Se não encontrou pelo link, tentar pelo canonical
        canonical = soup.find('link', {'rel': 'canonical'})
        if canonical and canonical.get('href'):
            # Formato: <link href="/Mavipoke" rel="canonical">
            username = canonical['href'].strip('/').split('/')[0]
            if username and username != 'pokemon':
                self.username_url = username
                print(f"DEBUG - Username extraído do canonical: {self.username_url}")
                self.save_session(scraper.cookies)
                return True
        
        print("❌ Não foi possível extrair username")
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
        username = self.username_url
        if not username:
            print("❌ Username não disponível para buscar CSRF")
            return None
            
        resp = self.scraper.get(f'https://mypcards.com/{username}')
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
        """Busca carta na pasta do usuário usando API"""
        user_id = self.get_user_id()
        if not user_id:
            print("❌ Não foi possível obter ID do usuário")
            return None
        
        # Buscar usando a API de produtos
        resp = self.scraper.get('https://mypcards.com/produto/search', params={
            'marca': 'pokemon',
            'idusuario': user_id,
            'term': numero
        })
        
        try:
            produtos = resp.json()
            print(f"DEBUG - Buscando: {numero} | Coleção: {colecao} | Tipo: {tipo} | Idioma: {idioma}")
            print(f"DEBUG - Produtos encontrados na API: {len(produtos)}")
            
            for produto in produtos:
                # Ignorar se não for um dicionário
                if not isinstance(produto, dict):
                    continue
                    
                nome = produto.get('nomeenproduto', '')
                print(f"DEBUG - Produto: {nome}")
                
                # Verificar se bate número e coleção
                if numero in nome and colecao.upper() in nome.upper():
                    # Agora precisa buscar o ID do estoque na página do produto
                    idproduto = produto.get('idproduto')
                    print(f"DEBUG - Produto encontrado: {nome} (idproduto: {idproduto})")
                    
                    # Acessar página do produto para pegar ID do estoque
                    prod_resp = self.scraper.get(f'https://mypcards.com/pokemon/produto/{idproduto}')
                    soup = BeautifulSoup(prod_resp.text, 'html.parser')
                    
                    # Procurar todas as linhas da tabela de estoque
                    estoque_rows = soup.find_all('tr', {'data-key': True})
                    
                    for row in estoque_rows:
                        # Verificar tipo (foil)
                        tipo_td = row.find('td', class_='estoque-lista-nomeenfoil')
                        tipo_text = tipo_td.get_text(strip=True).lower() if tipo_td else ''
                        
                        # Verificar idioma (está no title do span.flag-icon)
                        idioma_td = row.find('td', class_='estoque-lista-qualidadenome')
                        idioma_span = idioma_td.find('span', class_='flag-icon') if idioma_td else None
                        idioma_text = idioma_span.get('title', '').lower() if idioma_span else ''
                        
                        print(f"DEBUG - Row: tipo_text='{tipo_text}' | idioma_text='{idioma_text}'")
                        
                        # Mapear tipos
                        tipo_match = False
                        if tipo == 'normal' and not tipo_text:
                            tipo_match = True
                        elif tipo == 'foil' and 'foil' in tipo_text and 'reverse' not in tipo_text:
                            tipo_match = True
                        elif tipo == 'reverse-foil' and 'reverse' in tipo_text:
                            tipo_match = True
                        elif tipo.lower() in tipo_text:
                            tipo_match = True
                        
                        # Mapear idiomas
                        idioma_map = {
                            'português': 'portugues',
                            'portugues': 'portugues',
                            'inglês': 'ingles',
                            'ingles': 'ingles',
                            'espanhol': 'espanhol',
                            'francês': 'frances',
                            'frances': 'frances',
                            'alemão': 'alemao',
                            'alemao': 'alemao',
                            'italiano': 'italiano',
                            'japonês': 'japones',
                            'japones': 'japones',
                            'coreano': 'coreano',
                            'russo': 'russo',
                            'chinês': 'chines',
                            'chines': 'chines',
                            'tailandês': 'tailandes',
                            'tailandes': 'tailandes'
                        }
                        
                        idioma_normalizado = idioma_map.get(idioma_text, idioma_text)
                        idioma_csv_normalizado = idioma_map.get(idioma.lower(), idioma.lower())
                        
                        idioma_match = (idioma_normalizado == idioma_csv_normalizado)
                        
                        # Se bater tipo e idioma, pegar esse estoque
                        if tipo_match and idioma_match:
                            # Pegar link de edição
                            edit_link = row.find('a', href=lambda x: x and '/estoque/update/' in x)
                            if edit_link:
                                href = edit_link['href']
                                id_estoque = href.split('/estoque/update/')[1].split('?')[0]
                                
                                # Extrair quantidade
                                qtd_td = row.find('td', class_='estoque-lista-quantidadeestoque')
                                quantidade_atual = '1'
                                if qtd_td:
                                    qtd_text = qtd_td.get_text(strip=True)
                                    quantidade_atual = qtd_text.split()[0]
                                
                                # Extrair preço
                                preco_td = row.find('td', class_='estoque-lista-precoestoque')
                                preco_atual = '0.00'
                                if preco_td:
                                    preco_span = preco_td.find('span', class_='moeda')
                                    if preco_span:
                                        preco_text = preco_span.get_text(strip=True)
                                        preco_atual = preco_text.replace('R$', '').replace(' ', '').replace(',', '.')
                                
                                print(f"DEBUG - Estoque encontrado: {id_estoque} | Tipo: {tipo_text or 'normal'} | Idioma: {idioma_text} | Qtd: {quantidade_atual} | Preço: {preco_atual}")
                                
                                return {
                                    'id_estoque': id_estoque,
                                    'numero': numero,
                                    'colecao': colecao,
                                    'preco': preco_atual,
                                    'quantidade': quantidade_atual
                                }
                    
                    print(f"DEBUG - Nenhum estoque encontrado com tipo '{tipo}' e idioma '{idioma}'")
            
            print(f"DEBUG - Carta não encontrada na pasta")
            return None
            
        except Exception as e:
            print(f"❌ Erro ao buscar carta: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
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
        url = f'https://mypcards.com/estoque/update/{id_estoque}'
        print(f"DEBUG - URL de atualização: {url}")
        
        resp = self.scraper.get(url)
        print(f"DEBUG - Status: {resp.status_code}, URL final: {resp.url}")
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        form = soup.find('form', {'id': 'estoque-form'})
        if not form:
            print(f"❌ Formulário não encontrado para id_estoque: {id_estoque}")
            return False
            
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
        
        resp = self.scraper.post(url, data=data)
        return resp.status_code == 200 or 'estoque/update' in resp.url
    
    def scrape_inventory(self, price_ranges=None):
        """Scraping completo do inventário usando endpoint load-more"""
        username = os.getenv('MYP_USERNAME_URL', 'aocarmo')
        
        # Ranges padrão se não especificado
        if not price_ranges:
            price_ranges = [
                (0, 9.99),
                (10, 49.99), 
                (50, 99.99),
                (100, 499.99),
                (500, 9999)
            ]
        
        all_cards = []
        
        for min_price, max_price in price_ranges:
            print(f"Scraping faixa R${min_price} - R${max_price}...")
            page = 1
            
            while True:
                params = {
                    'nick': username,
                    'page': page,
                    'PastaSearch[precoMinimo]': f'{min_price:.2f}',
                    'PastaSearch[precoMaximo]': f'{max_price}'
                }
                
                resp = self.scraper.get('https://mypcards.com/usuario/load-more', params=params)
                
                if resp.status_code != 200:
                    break
                
                try:
                    data = resp.json()
                except:
                    break
                
                # Parsear HTML retornado
                soup = BeautifulSoup(data['html'], 'html.parser')
                cards = soup.find_all('li', class_='stream-item')
                
                if not cards:
                    break
                
                for card in cards:
                    try:
                        # Nome da carta (h3)
                        nome_elem = card.find('h3')
                        nome = nome_elem.text.strip() if nome_elem else ''
                        
                        # Extrair número do nome
                        numero = ''
                        if nome:
                            parts = nome.split()
                            for part in parts:
                                if '/' in part and any(c.isdigit() for c in part):
                                    numero = part.replace('(', '').replace(')', '')
                                    break
                        
                        # Coleção (span.card-edicao)
                        colecao_elem = card.find('span', class_='card-edicao')
                        colecao = colecao_elem.text.strip() if colecao_elem else ''
                        
                        # Tipo (buscar em todos os spans da div card-qualidade)
                        tipo = 'normal'
                        qualidade_div = card.find('div', class_='card-qualidade')
                        if qualidade_div:
                            all_text = qualidade_div.get_text(strip=True).lower()
                            if 'reverse' in all_text:
                                tipo = 'reverse-foil'
                            elif 'foil' in all_text or 'full-art' in all_text:
                                tipo = 'foil'
                        
                        # Idioma (flag)
                        idioma = 'portugues'
                        flag_elem = card.find('span', class_='flag-icon')
                        if flag_elem and flag_elem.get('title'):
                            idioma_map = {
                                'português': 'portugues',
                                'inglês': 'ingles',
                                'espanhol': 'espanhol',
                                'francês': 'frances',
                                'alemão': 'alemao',
                                'italiano': 'italiano',
                                'japonês': 'japones',
                                'coreano': 'coreano'
                            }
                            idioma = idioma_map.get(flag_elem['title'].lower(), 'portugues')
                        
                        # Preço
                        preco_elem = card.find('span', class_='moeda')
                        preco = '0.00'
                        if preco_elem:
                            preco = preco_elem.text.replace('R$', '').replace(' ', '').replace(',', '.').strip()
                        
                        # Quantidade
                        qtd_elem = card.find('span', class_='quantidade-num')
                        quantidade = '1'
                        if qtd_elem:
                            quantidade = qtd_elem.text.strip()
                        
                        if numero and colecao:
                            all_cards.append({
                                'numero': numero,
                                'colecao': colecao,
                                'tipo': tipo,
                                'idioma': idioma,
                                'preco': preco,
                                'quantidade': quantidade
                            })
                    
                    except Exception as e:
                        print(f"Erro ao processar carta: {e}")
                        continue
                
                # Verificar se tem mais páginas (usar metadado do JSON)
                if not data.get('hasMorePages', False):
                    break
                
                page += 1
                import time
                time.sleep(0.5)
        
        return all_cards
        
        return all_cards

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
