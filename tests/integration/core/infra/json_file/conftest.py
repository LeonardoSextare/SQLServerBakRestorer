from pathlib import Path

import pytest


@pytest.fixture
def caminho_do_arquivo(tmp_path: Path) -> Path:
    """Caminho de um arquivo json ainda inexistente, numa pasta que já existe."""
    return tmp_path / "config.json"


@pytest.fixture
def arquivo_com_conteudo(caminho_do_arquivo: Path) -> Path:
    """Arquivo json já gravado, para os testes que precisam de um estado anterior."""
    caminho_do_arquivo.write_text('{"alias": "Produção"}', encoding="utf-8")
    return caminho_do_arquivo
