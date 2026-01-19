"""
Enums para tipos de cartas e idiomas
"""
from enum import Enum

class TipoCarta(Enum):
    NORMAL = ("1", "normal", "")
    FOIL = ("2", "foil", "Foil")
    REVERSE_FOIL = ("3", "reverse-foil", "Reverse Foil")
    ALTERED_ART = ("4", "altered-art", "Altered Art")
    FULL_ART = ("5", "full-art", "Full-Art")
    PROMO = ("6", "promo", "Promo")
    UNLIMITED_FOIL = ("7", "unlimited-foil", "Unlimited Foil")
    UNLIMITED = ("8", "unlimited", "Unlimited")
    STAFF = ("19", "staff", "Staff")
    POKEBALL_FOIL = ("49", "pokeball-foil", "Pokeball Foil")
    MASTERBALL_FOIL = ("50", "masterball-foil", "Masterball Foil")
    OVERSIZE = ("52", "oversize", "Oversize")
    
    def __init__(self, id_valor, nome_api, nome_dom):
        self.id_valor = id_valor
        self.nome_api = nome_api
        self.nome_dom = nome_dom
    
    @classmethod
    def get_id_by_name(cls, nome):
        """Retorna ID do tipo pelo nome da API"""
        nome_normalizado = nome.lower().replace(" ", "-")
        for tipo in cls:
            if tipo.nome_api == nome_normalizado:
                return tipo.id_valor
        return cls.NORMAL.id_valor  # Default
    
    @classmethod
    def get_dom_name_by_api_name(cls, nome_api):
        """Retorna nome do DOM pelo nome da API"""
        for tipo in cls:
            if tipo.nome_api == nome_api:
                return tipo.nome_dom
        return ""
    
    @classmethod
    def get_all_names(cls):
        """Retorna todos os nomes válidos para API"""
        return [tipo.nome_api for tipo in cls]

class IdiomaCarta(Enum):
    PORTUGUES = ("1", "portugues", "Português")
    INGLES = ("2", "ingles", "Inglês")
    ESPANHOL = ("3", "espanhol", "Espanhol")
    FRANCES = ("4", "frances", "Francês")
    ALEMAO = ("5", "alemao", "Alemão")
    ITALIANO = ("6", "italiano", "Italiano")
    JAPONES = ("7", "japones", "Japonês")
    COREANO = ("8", "coreano", "Coreano")
    RUSSO = ("9", "russo", "Russo")
    CHINES = ("10", "chines", "Chinês")
    TAILANDES = ("12", "tailandes", "Tailandês")
    
    def __init__(self, id_valor, nome_api, nome_dom):
        self.id_valor = id_valor
        self.nome_api = nome_api
        self.nome_dom = nome_dom
    
    @classmethod
    def get_id_by_name(cls, nome):
        """Retorna ID do idioma pelo nome da API"""
        nome_normalizado = nome.lower().replace("ê", "e").replace("ã", "a")
        for idioma in cls:
            if idioma.nome_api == nome_normalizado:
                return idioma.id_valor
        return cls.PORTUGUES.id_valor  # Default
    
    @classmethod
    def get_dom_name_by_api_name(cls, nome_api):
        """Retorna nome do DOM pelo nome da API"""
        for idioma in cls:
            if idioma.nome_api == nome_api:
                return idioma.nome_dom
        return ""
    
    @classmethod
    def get_all_names(cls):
        """Retorna todos os nomes válidos para API"""
        return [idioma.nome_api for idioma in cls]
