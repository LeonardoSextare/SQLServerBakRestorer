from collections.abc import Iterable

from bakrestorer.features.instancias.domain.models import Diagnostico, EstadoDaInstancia, Instancia
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
    são a resposta dele, e voltam como `Diagnostico`.
    """

    def __init__(self, cliente: ClienteSqlServer) -> None:
        self._cliente = cliente

    def diagnosticar(self, instancia: Instancia) -> Diagnostico:
        """Pergunta à instância tudo que decide se ela está pronta para restaurar.

        Hoje é só o acesso. As outras checagens entram aqui, depois dele, porque
        precisam do login que ele faz.

        Raises:
            ComandoRecusadoError: Se a instância aceitou o login e recusou o
                ping. Ninguém espera por isso.

        """
        return self.conferir_acesso(instancia)

    def conferir_acesso(self, instancia: Instancia) -> Diagnostico:
        """Pergunta à instância se ela está no ar e se a credencial vale.

        A sessão guardada é descartada antes, para o ping fazer login de novo: ela
        só prova que a credencial valia quando abriu.

        Raises:
            ComandoRecusadoError: Se a instância aceitou o login e recusou o
                ping. Ninguém espera por isso.

        """
        conexao = _montar_conexao(instancia)
        self._cliente.descartar(conexao)

        try:
            self._cliente.executar(conexao, PING)
        except InstanciaInacessivelError as falha:
            return Diagnostico(
                id_da_instancia=instancia.id,
                estado=EstadoDaInstancia.INACESSIVEL,
                detalhe=falha.detalhe,
            )
        except CredenciaisInvalidasError as falha:
            return Diagnostico(
                id_da_instancia=instancia.id,
                estado=EstadoDaInstancia.CREDENCIAIS_RECUSADAS,
                detalhe=falha.detalhe,
            )

        return Diagnostico(id_da_instancia=instancia.id, estado=EstadoDaInstancia.ACESSIVEL)

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
