from collections.abc import Iterable
from datetime import timedelta
from time import perf_counter

from bakrestorer.features.instancias.domain.models import Diagnostico, Instancia, Verificacao
from bakrestorer.features.instancias.domain.queries import PING
from bakrestorer.infra.sqlserver import (
    ClienteSqlServer,
    Conexao,
    CredenciaisInvalidasError,
    InstanciaInacessivelError,
)


class DiagnosticoService:
    """Pergunta às instâncias do SQL Server se elas estão prontas para restaurar.

    Não guarda estado: quem guarda as sessões abertas é o cliente.

    Instância fora do ar e credencial recusada não são falha do diagnóstico:
    são a resposta dele, e voltam como verificações do `Diagnostico`.
    """

    def __init__(self, cliente: ClienteSqlServer) -> None:
        self._cliente = cliente

    def diagnosticar(self, instancia: Instancia) -> Diagnostico:
        """Pergunta à instância tudo que decide se ela está pronta para restaurar.

        Hoje é só o acesso. As outras checagens entram aqui, depois dele, porque
        precisam do login que ele faz. Elas rodam todas, mesmo quando uma falha,
        para o checklist mostrar de uma vez tudo que está errado.

        Raises:
            ComandoRecusadoError: Se a instância aceitou o login e recusou o
                ping. Ninguém espera por isso.

        """
        return self.conferir_acesso(instancia)

    def conferir_acesso(self, instancia: Instancia) -> Diagnostico:
        """Pergunta à instância se ela responde e se o login é aceito.

        A sessão guardada é descartada antes, para o primeiro ping fazer login de
        novo: ela só prova que a credencial valia quando abriu. A latência sai do
        segundo ping, que já não carrega o tempo do login.

        Raises:
            ComandoRecusadoError: Se a instância aceitou o login e recusou o
                ping. Ninguém espera por isso.

        """
        conexao = _montar_conexao(instancia)
        self._cliente.descartar(conexao)

        try:
            self._cliente.executar(conexao, PING)
            inicio = perf_counter()
            self._cliente.executar(conexao, PING)
            latencia = timedelta(seconds=perf_counter() - inicio)
        except InstanciaInacessivelError as falha:
            return Diagnostico(
                id_da_instancia=instancia.id,
                conexao=Verificacao(situacao="erro", detalhe=falha.detalhe),
                login=Verificacao(situacao="nao_verificado"),
            )
        except CredenciaisInvalidasError as falha:
            return Diagnostico(
                id_da_instancia=instancia.id,
                conexao=Verificacao(situacao="ok"),
                login=Verificacao(situacao="erro", detalhe=falha.detalhe),
            )

        return Diagnostico(
            id_da_instancia=instancia.id,
            conexao=Verificacao(situacao="ok"),
            login=Verificacao(situacao="ok"),
            latencia=latencia,
        )

    def diagnosticar_todas(self, instancias: Iterable[Instancia]) -> tuple[Diagnostico, ...]:
        """Diagnostica cada instância, na ordem em que vieram.

        Uma depois da outra, porque o cliente não pode ser usado por duas
        threads ao mesmo tempo.

        Raises:
            ComandoRecusadoError: Se alguma instância aceitou o login e recusou
                o ping.

        """
        return tuple(self.diagnosticar(instancia) for instancia in instancias)


def _montar_conexao(instancia: Instancia) -> Conexao:
    """Traduz a instância na conexão que o cliente do SQL Server entende."""
    return Conexao(
        host=instancia.host,
        instancia=instancia.nome,
        porta=instancia.porta,
        usuario=instancia.usuario,
        senha=instancia.senha,
    )
