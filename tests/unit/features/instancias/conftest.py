from collections.abc import Callable
from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from bakrestorer.features.instancias import ConfigInstancias, DiagnosticoService, Instancia, criar_diagnostico_service
from bakrestorer.infra.sqlserver import ClienteSqlServer


@pytest.fixture
def cliente_sql_server() -> MagicMock:
    """Dublê do cliente: o ping responde em 1 ms e o login pode tudo, a não ser que o teste diga outra coisa."""
    cliente = MagicMock(spec=ClienteSqlServer)
    cliente.ping.return_value = timedelta(milliseconds=1)
    cliente.executar.return_value = [{"sysadmin": 1, "dbcreator": 1, "cria_banco": 1}]

    return cliente


@pytest.fixture
def servico_de_diagnostico(cliente_sql_server: MagicMock) -> DiagnosticoService:
    """Serviço sob teste, falando com o dublê do cliente."""
    return criar_diagnostico_service(cliente_sql_server)


@pytest.fixture
def criar_cadastro(criar_instancia: Callable[..., Instancia]) -> Callable[..., ConfigInstancias]:
    """Monta cadastros válidos, com uma instância `PROD` que também é a padrão."""

    def montar(**campos: object) -> ConfigInstancias:
        prod = criar_instancia("PROD")
        padroes: dict[str, object] = {"itens": (prod,), "padrao": prod.id}

        return ConfigInstancias.model_validate({**padroes, **campos})

    return montar
