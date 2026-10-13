from collections.abc import Callable, Iterator

import pytest
from bakrestorer.infra.sqlserver import ClienteSqlServer, Conexao
from docker.errors import DockerException
from testcontainers.community.mssql import SqlServerContainer

VERSOES_SUPORTADAS = ("2017", "2019", "2022", "2025")


@pytest.fixture(scope="session", params=VERSOES_SUPORTADAS, ids=VERSOES_SUPORTADAS)
def instancia_sql_server(request: pytest.FixtureRequest) -> Iterator[Conexao]:
    """Instância descartável em contêiner, uma por versão do SQL Server publicada como imagem Linux.

    A suíte inteira é percorrida em cada versão, e é essa lista que sustenta a
    afirmação de que o aplicativo foi testado em todas elas.
    """
    container = SqlServerContainer(
        image=f"mcr.microsoft.com/mssql/server:{request.param}-latest",
        password="SENHA-1234",
    )

    try:
        container.start()
    except (DockerException, OSError) as falha:
        pytest.fail(f"A instância {request.param} não pôde ser criada: {falha}")

    try:
        yield Conexao(
            host=container.get_container_host_ip(),
            porta=int(container.get_exposed_port(1433)),
            usuario="SA",
            senha="SENHA-1234",
        )
    finally:
        container.stop()


@pytest.fixture
def derrubar_sessao(instancia_sql_server: Conexao) -> Iterator[Callable[[ClienteSqlServer], None]]:
    """Derruba, a partir de outra sessão, a sessão que um cliente mantém aberta.

    É a instância caindo com a sessão aberta, sem parar o contêiner, que é o
    mesmo para a suíte inteira.
    """
    outro_cliente = ClienteSqlServer()

    def derrubar(cliente: ClienteSqlServer) -> None:
        sessao = cliente.executar(instancia_sql_server, "SELECT @@SPID AS sessao")[0]["sessao"]
        outro_cliente.executar(
            instancia_sql_server,
            "DECLARE @comando NVARCHAR(20) = CONCAT('KILL ', %(sessao)s); EXEC (@comando)",
            {"sessao": sessao},
        )

    try:
        yield derrubar
    finally:
        outro_cliente.encerrar()


@pytest.fixture
def cliente_sql_server() -> Iterator[ClienteSqlServer]:
    """Cliente sob teste, encerrado ao fim para não deixar sessão aberta no contêiner."""
    cliente = ClienteSqlServer()

    try:
        yield cliente
    finally:
        cliente.encerrar()
