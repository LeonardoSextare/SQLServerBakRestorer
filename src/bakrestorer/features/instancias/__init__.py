from pathlib import Path

from bakrestorer.features.instancias.domain.diagnostico_service import DiagnosticoService
from bakrestorer.features.instancias.domain.exceptions import (
    CadastroInvalidoError,
    DiagnosticoInvalidoError,
    InstanciaError,
    InstanciaInvalidaError,
    InstanciaJaExisteError,
    InstanciaNaoEncontradaError,
    InstanciasError,
)
from bakrestorer.features.instancias.domain.instancias_service import InstanciasService
from bakrestorer.features.instancias.domain.models import (
    ConfigInstancias,
    Diagnostico,
    Instancia,
    Situacao,
    Verificacao,
)
from bakrestorer.infra.config_json import ConfigJson
from bakrestorer.infra.sqlserver import ClienteSqlServer

CHAVE_DA_CONFIG = "instancias"

__all__ = [
    "CadastroInvalidoError",
    "ConfigInstancias",
    "Diagnostico",
    "DiagnosticoInvalidoError",
    "DiagnosticoService",
    "Instancia",
    "InstanciaError",
    "InstanciaInvalidaError",
    "InstanciaJaExisteError",
    "InstanciaNaoEncontradaError",
    "InstanciasError",
    "InstanciasService",
    "Situacao",
    "Verificacao",
    "criar_diagnostico_service",
    "criar_instancias_service",
]


def criar_instancias_service(caminho_da_config: Path) -> InstanciasService:
    """Monta o serviço ligado à parte do arquivo de configuração que é desta feature."""
    return InstanciasService(ConfigJson(caminho_da_config, CHAVE_DA_CONFIG))


def criar_diagnostico_service(cliente: ClienteSqlServer) -> DiagnosticoService:
    """Monta o serviço de diagnóstico sobre o cliente do SQL Server que o aplicativo divide."""
    return DiagnosticoService(cliente)
