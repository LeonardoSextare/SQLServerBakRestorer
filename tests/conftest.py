from collections.abc import Callable

import pytest
from bakrestorer.features.instancias import Instancia


@pytest.fixture
def criar_instancia() -> Callable[..., Instancia]:
    """Monta instâncias válidas, e é compartilhada porque `unit` e `integration` precisam dela."""

    def montar(apelido: str = "PROD", **campos: object) -> Instancia:
        padroes = {"nome": "SQLEXPRESS", "usuario": "sa", "senha": "segredo"}

        return Instancia.model_validate({"apelido": apelido, **padroes, **campos})

    return montar
