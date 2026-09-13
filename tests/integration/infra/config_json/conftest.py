from pathlib import Path

import pytest
from bakrestorer.infra.config_json import ConfigJson


@pytest.fixture
def caminho_do_arquivo(tmp_path: Path) -> Path:
    """Caminho de um arquivo json ainda inexistente, numa pasta que já existe."""
    return tmp_path / "config.json"


@pytest.fixture
def config_de_instancias(caminho_do_arquivo: Path) -> ConfigJson:
    """A seção sob teste, num arquivo que ainda não existe."""
    return ConfigJson(caminho_do_arquivo, "instancias")


@pytest.fixture
def config_de_gui(caminho_do_arquivo: Path) -> ConfigJson:
    """A seção vizinha, para provar que uma não apaga a outra."""
    return ConfigJson(caminho_do_arquivo, "gui")
