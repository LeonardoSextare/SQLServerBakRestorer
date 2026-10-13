from collections.abc import Callable

import pytest
from bakrestorer.features.instancias import ConfigInstancias, Instancia


@pytest.fixture
def criar_cadastro(criar_instancia: Callable[..., Instancia]) -> Callable[..., ConfigInstancias]:
    """Monta cadastros válidos, com uma instância `PROD` que também é a padrão."""

    def montar(**campos: object) -> ConfigInstancias:
        prod = criar_instancia("PROD")
        padroes: dict[str, object] = {"itens": (prod,), "padrao": prod.id}

        return ConfigInstancias.model_validate({**padroes, **campos})

    return montar
