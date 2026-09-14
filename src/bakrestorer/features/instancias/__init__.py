from pathlib import Path

from bakrestorer.features.instancias.domain.exceptions import (
    CadastroInvalidoError,
    InstanciaError,
    InstanciaInvalidaError,
    InstanciaJaExisteError,
    InstanciaNaoEncontradaError,
    InstanciasError,
)
from bakrestorer.features.instancias.domain.instancias_service import InstanciasService
from bakrestorer.features.instancias.domain.models import ConfigInstancias, Instancia
from bakrestorer.infra.config_json import ConfigJson

CHAVE_DA_CONFIG = "instancias"

__all__ = [
    "CadastroInvalidoError",
    "ConfigInstancias",
    "Instancia",
    "InstanciaError",
    "InstanciaInvalidaError",
    "InstanciaJaExisteError",
    "InstanciaNaoEncontradaError",
    "InstanciasError",
    "InstanciasService",
    "criar_service",
]


def criar_service(caminho_da_config: Path) -> InstanciasService:
    """Monta o serviço ligado à parte do arquivo de configuração que é desta feature."""
    return InstanciasService(ConfigJson(caminho_da_config, CHAVE_DA_CONFIG))
