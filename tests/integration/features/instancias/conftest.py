from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from bakrestorer.features.instancias import DiagnosticoService, Instancia, InstanciasService, criar_service

if TYPE_CHECKING:
    from bakrestorer.infra.sqlserver import ClienteSqlServer, Conexao


@pytest.fixture
def instancia_no_conteiner(criar_instancia: Callable[..., Instancia], instancia_sql_server: Conexao) -> Instancia:
    """A instância do contêiner como o usuário a cadastraria: pela porta, que é como se chega nela."""
    return criar_instancia(
        host=instancia_sql_server.host,
        nome=None,
        porta=instancia_sql_server.porta,
        usuario=instancia_sql_server.usuario,
        senha=instancia_sql_server.senha,
    )


@pytest.fixture
def servico_de_diagnostico(cliente_sql_server: ClienteSqlServer) -> DiagnosticoService:
    """Serviço sob teste, falando com o contêiner."""
    return DiagnosticoService(cliente_sql_server)


@pytest.fixture
def caminho_da_config(tmp_path: Path) -> Path:
    """Caminho de um arquivo de configuração ainda inexistente, numa pasta que já existe."""
    return tmp_path / "config.json"


@pytest.fixture
def servico_de_instancias(caminho_da_config: Path) -> InstanciasService:
    """Serviço sob teste, apontado para um arquivo que ainda não foi gravado."""
    return criar_service(caminho_da_config)
