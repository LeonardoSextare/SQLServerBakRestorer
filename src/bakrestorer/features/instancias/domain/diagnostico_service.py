from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor

from bakrestorer.features.instancias.domain.models import Diagnostico, Instancia, Verificacao
from bakrestorer.infra.sqlserver import (
    ClienteSqlServer,
    Conexao,
    CredenciaisInvalidasError,
    InstanciaInacessivelError,
)


class DiagnosticoService:
    """Pergunta às instâncias do SQL Server se elas estão prontas para restaurar.

    Não guarda estado, e o cliente também não: cada pergunta abre a própria
    conexão, e por isso as instâncias podem ser diagnosticadas ao mesmo tempo.

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

        O cliente abre uma conexão só para a pergunta, então o login é sempre de
        verdade, e não uma sessão antiga que já estava aberta.

        Raises:
            ComandoRecusadoError: Se a instância aceitou o login e recusou o
                ping. Ninguém espera por isso.

        """
        try:
            latencia = self._cliente.ping(_montar_conexao(instancia))
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
        """Diagnostica as instâncias todas ao mesmo tempo, e devolve os diagnósticos na ordem em que vieram.

        Ao mesmo tempo porque cada uma pode levar o tempo limite inteiro para não
        responder: em série, a última esperaria pelas outras.

        Raises:
            ComandoRecusadoError: Se alguma instância aceitou o login e recusou
                o ping.

        """
        with ThreadPoolExecutor() as threads:
            return tuple(threads.map(self.diagnosticar, instancias))


def _montar_conexao(instancia: Instancia) -> Conexao:
    """Traduz a instância na conexão que o cliente do SQL Server entende."""
    return Conexao(
        host=instancia.host,
        instancia=instancia.nome,
        porta=instancia.porta,
        usuario=instancia.usuario,
        senha=instancia.senha,
    )
