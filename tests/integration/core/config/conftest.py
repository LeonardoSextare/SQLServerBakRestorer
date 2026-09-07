from pathlib import Path

import pytest

from bakrestorer.core.config import ConfigService


@pytest.fixture
def caminho_da_config(tmp_path: Path) -> Path:
    """Caminho de um arquivo de configuração ainda inexistente, numa pasta que já existe."""
    return tmp_path / "config.json"


@pytest.fixture
def config_service(caminho_da_config: Path) -> ConfigService:
    """Serviço sob teste, apontado para um arquivo que ainda não foi gravado."""
    return ConfigService(caminho_da_config)
