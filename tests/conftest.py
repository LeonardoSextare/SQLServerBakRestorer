from collections.abc import Callable

import pytest

from bakrestorer.core.config import Instancia


@pytest.fixture
def criar_instancia() -> Callable[..., Instancia]:
    """Monta instâncias válidas, e é compartilhada porque `unit` e `integration` precisam dela."""

    def montar(alias: str = "PROD", **campos: object) -> Instancia:
        padroes = {"nome": "SQLEXPRESS", "usuario": "sa", "senha": "segredo"}

        return Instancia.model_validate({"alias": alias, **padroes, **campos})

    return montar
