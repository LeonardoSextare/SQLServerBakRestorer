from pathlib import Path

import pytest

from bakrestorer.core.config import ServicoDeConfiguracao


@pytest.fixture
def caminho_da_config(tmp_path: Path) -> Path:
    """Caminho de um arquivo de configuração ainda inexistente, numa pasta que já existe."""
    return tmp_path / "config.json"


@pytest.fixture
def servico_de_configuracao(caminho_da_config: Path) -> ServicoDeConfiguracao:
    """Serviço sob teste, apontado para um arquivo que ainda não foi gravado."""
    return ServicoDeConfiguracao(caminho_da_config)
