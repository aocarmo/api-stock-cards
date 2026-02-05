"""
Helper para buscar quantidade atual de uma carta no site
"""
from scrape_concorrentes import ScrapeConcorrentes

def buscar_minha_quantidade(numero, colecao, tipo, idioma, meu_usuario="aocarmo"):
    """
    Busca quantidade atual da minha carta no site
    
    Returns:
        int ou None: Quantidade atual ou None se não encontrada
    """
    try:
        scraper = ScrapeConcorrentes()
        
        # Buscar produto
        produto = scraper.buscar_idproduto(numero, colecao)
        if not produto:
            return None
        
        idproduto = produto['idproduto']
        
        # Buscar vendedores
        vendedores = scraper.buscar_vendedores(idproduto, page=1)
        
        # Normalizar tipo e idioma
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
        tipo_esperado = tipo_map.get(tipo.lower(), tipo.lower())
        
        idioma_map = {
            'portugues': 'português',
            'ingles': 'inglês',
            'espanhol': 'espanhol'
        }
        idioma_esperado = idioma_map.get(idioma.lower(), idioma.lower())
        
        # Buscar minha carta
        for v in vendedores:
            if v['vendedor'].lower() == meu_usuario.lower():
                tipo_v = v['tipo'].lower().strip()
                idioma_v = v['idioma'].lower().strip()
                qualidade_v = v.get('qualidade', '')
                
                # Normalizar idioma do vendedor
                if 'portugu' in idioma_v:
                    idioma_v = 'português'
                elif 'ingl' in idioma_v:
                    idioma_v = 'inglês'
                elif 'espan' in idioma_v:
                    idioma_v = 'espanhol'
                
                # Verificar match
                if tipo_v == tipo_esperado and idioma_v == idioma_esperado and qualidade_v == 'NM':
                    return v['quantidade']
        
        # Não encontrada = estoque zerado
        return 0
        
    except Exception as e:
        print(f"Erro ao buscar quantidade: {str(e)}")
        return None  # Erro = não atualizar
