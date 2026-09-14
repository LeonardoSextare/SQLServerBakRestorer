from pathlib import Path

import pytest
from bakrestorer.features.instancias import InstanciasService, criar_service


@pytest.fixture
def caminho_da_config(tmp_path: Path) -> Path:
    """Caminho de um arquivo de configuração ainda inexistente, numa pasta que já existe."""
    return tmp_path / "config.json"


@pytest.fixture
def servico_de_instancias(caminho_da_config: Path) -> InstanciasService:
    """Serviço sob teste, apontado para um arquivo que ainda não foi gravado."""
    return criar_service(caminho_da_config)
