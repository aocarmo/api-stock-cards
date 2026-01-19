"""
Enums para tipos de cartas
"""
from enum import Enum

class TipoCarta(Enum):
    NORMAL = ("1", "normal")
    FOIL = ("2", "foil")
    REVERSE_FOIL = ("3", "reverse-foil")
    ALTERED_ART = ("4", "altered-art")
    FULL_ART = ("5", "full-art")
    PROMO = ("6", "promo")
    UNLIMITED_FOIL = ("7", "unlimited-foil")
    UNLIMITED = ("8", "unlimited")
    STAFF = ("19", "staff")
    POKEBALL_FOIL = ("49", "pokeball-foil")
    MASTERBALL_FOIL = ("50", "masterball-foil")
    OVERSIZE = ("52", "oversize")
    
    def __init__(self, id_valor, nome_api):
        self.id_valor = id_valor
        self.nome_api = nome_api
    
    @classmethod
    def get_id_by_name(cls, nome):
        """Retorna ID do tipo pelo nome da API"""
        nome_normalizado = nome.lower().replace(" ", "-")
        for tipo in cls:
            if tipo.nome_api == nome_normalizado:
                return tipo.id_valor
        return cls.NORMAL.id_valor  # Default
    
    @classmethod
    def get_all_names(cls):
        """Retorna todos os nomes válidos para API"""
        return [tipo.nome_api for tipo in cls]
