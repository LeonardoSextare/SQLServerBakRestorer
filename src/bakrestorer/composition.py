from functools import cache
from pathlib import Path

from bakrestorer.features.instancias import (
    DiagnosticoService,
    InstanciasService,
    criar_diagnostico_service,
    criar_instancias_service,
)
from bakrestorer.infra.sqlserver import ClienteSqlServer

# TODO: Caminho fixo, só para desenvolver -- tarefa #002
RAIZ_DO_PROJETO = Path(__file__).resolve().parents[2]
CAMINHO_DA_CONFIGURACAO = RAIZ_DO_PROJETO / "config" / "config.json"


@cache
def instancias_service() -> InstanciasService:
    """Devolve o serviço que lê e grava o cadastro de instâncias.

    Montado uma vez e reaproveitado: quem precisa chama esta função em vez de
    receber o serviço por parâmetro.
    """
    return criar_instancias_service(CAMINHO_DA_CONFIGURACAO)


@cache
def diagnostico_service() -> DiagnosticoService:
    """Devolve o serviço que pergunta às instâncias se estão prontas para restaurar."""
    return criar_diagnostico_service(cliente_sql_server())


@cache
def cliente_sql_server() -> ClienteSqlServer:
    """Devolve o cliente do SQL Server, um só para o aplicativo inteiro.

    Um só porque é ele que guarda as sessões abertas: quem vier depois do
    diagnóstico, como a restauração, encontra pronta a sessão que ele abriu.
    """
    return ClienteSqlServer()
