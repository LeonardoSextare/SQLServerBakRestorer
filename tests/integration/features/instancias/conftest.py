from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from bakrestorer.features.instancias import (
    DiagnosticoService,
    Instancia,
    InstanciasService,
    criar_diagnostico_service,
    criar_instancias_service,
)

if TYPE_CHECKING:
    from bakrestorer.infra.sqlserver import ClienteSqlServer, Conexao


@pytest.fixture
def instancia_no_conteiner(criar_instancia: Callable[..., Instancia], instancia_sql_server: Conexao) -> Instancia:
    """A instância do contêiner como o usuário a cadastraria: pela porta, que é como se chega nela."""
    return criar_instancia(
        host=instancia_sql_server.host,
        nome=None,
        porta=instancia_sql_server.porta,
        usuario=instancia_sql_server.usuario,
        senha=instancia_sql_server.senha,
    )


@pytest.fixture
def criar_instancia_com_login_proprio(
    criar_instancia: Callable[..., Instancia],
    instancia_sql_server: Conexao,
    cliente_sql_server: ClienteSqlServer,
) -> Iterator[Callable[..., Instancia]]:
    """Cria no contêiner um login só do teste, sem papel nenhum, e devolve a instância que entra com ele.

    `pode_criar_banco` dá ao login a permissão CREATE ANY DATABASE. Os logins
    criados são apagados no fim, porque o contêiner é o mesmo para a suíte
    inteira. O nome é gerado aqui, e por isso pode ir direto no comando.
    """
    senha = "Senha-do-teste-1234"
    criados: list[str] = []

    def criar(*, pode_criar_banco: bool = False) -> Instancia:
        login = f"teste_{uuid4().hex[:12]}"
        cliente_sql_server.executar(
            instancia_sql_server,
            f"CREATE LOGIN [{login}] WITH PASSWORD = '{senha}', CHECK_POLICY = OFF",
        )
        criados.append(login)

        if pode_criar_banco:
            cliente_sql_server.executar(instancia_sql_server, f"GRANT CREATE ANY DATABASE TO [{login}]")

        return criar_instancia(
            host=instancia_sql_server.host,
            nome=None,
            porta=instancia_sql_server.porta,
            usuario=login,
            senha=senha,
        )

    try:
        yield criar
    finally:
        for login in criados:
            cliente_sql_server.executar(instancia_sql_server, f"DROP LOGIN [{login}]")


@pytest.fixture
def servico_de_diagnostico(cliente_sql_server: ClienteSqlServer) -> DiagnosticoService:
    """Serviço sob teste, falando com o contêiner."""
    return criar_diagnostico_service(cliente_sql_server)


@pytest.fixture
def caminho_da_config(tmp_path: Path) -> Path:
    """Caminho de um arquivo de configuração ainda inexistente, numa pasta que já existe."""
    return tmp_path / "config.json"


@pytest.fixture
def servico_de_instancias(caminho_da_config: Path) -> InstanciasService:
    """Serviço sob teste, apontado para um arquivo que ainda não foi gravado."""
    return criar_instancias_service(caminho_da_config)
