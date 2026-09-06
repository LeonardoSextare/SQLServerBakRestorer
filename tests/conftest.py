from collections.abc import Callable

import pytest

from bakrestorer.core.config import Instancia

FabricaDeInstancia = Callable[..., Instancia]


@pytest.fixture
def nova_instancia() -> FabricaDeInstancia:
    """Monta instâncias válidas, e é compartilhada porque `unit` e `integration` precisam dela."""

    def montar(alias: str = "PROD", **campos: object) -> Instancia:
        padroes = {"nome": "SQLEXPRESS", "usuario": "sa", "senha": "segredo"}

        return Instancia.model_validate({"alias": alias, **padroes, **campos})

    return montar
