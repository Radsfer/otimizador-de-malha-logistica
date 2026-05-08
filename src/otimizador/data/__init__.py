"""Camada de dados: geração sintética e carregamento de instâncias."""

from .generator import gerar_dados_sinteticos
from .loader import DataLoader

__all__ = ["gerar_dados_sinteticos", "DataLoader"]
