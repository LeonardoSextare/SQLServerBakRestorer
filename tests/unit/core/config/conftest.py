from collections.abc import Callable

import pytest
from bakrestorer.core.config import Configuracao, Instancia


@pytest.fixture
def criar_configuracao(criar_instancia: Callable[..., Instancia]) -> Callable[..., Configuracao]:
    """Monta configurações válidas, com uma instância `PROD` que também é a padrão."""

    def montar(**campos: object) -> Configuracao:
        padroes = {"instancias": (criar_instancia("PROD"),), "instancia_padrao": "PROD"}

        return Configuracao.model_validate({**padroes, **campos})

    return montar
