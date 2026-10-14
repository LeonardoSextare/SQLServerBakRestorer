from collections.abc import Generator, Mapping
from contextlib import contextmanager, suppress
from datetime import timedelta
from time import perf_counter

import pytds

from bakrestorer.infra.sqlserver.connection import Conexao
from bakrestorer.infra.sqlserver.exceptions import (
    ComandoRecusadoError,
    CredenciaisInvalidasError,
    InstanciaInacessivelError,
)

LOGIN_RECUSADO = frozenset(
    {
        18452,  # login de domínio não confiável
        18456,  # login ou senha inválidos
        18486,  # conta bloqueada
        18487,  # senha expirada
        18488,  # senha precisa ser trocada
    },
)


class Sessao:
    """Uma conexão aberta com a instância, para rodar vários comandos em sequência.

    Só existe dentro do `with` do `ClienteSqlServer.sessao`, que a abre e a
    fecha. Entre um comando e outro ela guarda o que o SQL Server guarda numa
    sessão: tabela temporária, opção `SET`, banco em uso.
    """

    def __init__(self, conexao: pytds.Connection, servidor: str) -> None:
        self._conexao = conexao
        self._servidor = servidor

    def executar(self, comando: str, parametros: Mapping[str, object] | None = None) -> list[dict[str, object]]:
        """Roda um comando e devolve uma linha por resultado, ou lista vazia quando não há resultado.

        Raises:
            InstanciaInacessivelError: Se a instância parou de responder.
            ComandoRecusadoError: Se a instância recusou ou falhou o comando.

        """
        try:
            with self._conexao.cursor() as cursor:
                cursor.execute(comando, dict(parametros) if parametros else None)
                linhas = [] if cursor.description is None else list(cursor.fetchall())
        except pytds.DatabaseError as falha:
            raise ComandoRecusadoError(self._servidor, falha.text) from falha
        except (pytds.Error, OSError) as falha:
            raise InstanciaInacessivelError(self._servidor, str(falha)) from falha

        return linhas


class ClienteSqlServer:
    """Fala com instâncias do SQL Server, abrindo uma conexão para cada operação.

    Nenhuma conexão sobrevive à operação que a abriu: cada uma faz login, faz o
    que precisa e fecha. Assim nenhuma conexão é dividida entre threads, o que
    o driver não permite, e nenhuma fica guardada esperando para morrer. O custo
    é um login por operação, pequeno perto de um restore.

    Comandos levam parâmetros nomeados (`%(nome)s`) e devolvem linhas como
    dicionário. Nenhum erro do driver atravessa: tudo vira exceção de
    `exceptions.py`.
    """

    def __init__(self, login_timeout: float = 5) -> None:
        self._login_timeout = login_timeout

    @contextmanager
    def sessao(self, conexao: Conexao) -> Generator[Sessao]:
        """Abre uma sessão na instância para os comandos de dentro do `with`, e a fecha no fim.

        O login e o fechamento ficam em dois `try`: um erro dentro do `with` de
        quem usa a sessão não pode ser confundido com falha de login. Falha ao
        fechar é ignorada: a sessão já cumpriu o que tinha que fazer.

        Raises:
            InstanciaInacessivelError: Se a instância não respondeu.
            CredenciaisInvalidasError: Se a instância recusou o login.

        """
        try:
            aberta = pytds.connect(
                dsn=conexao.servidor,
                port=conexao.porta,
                user=conexao.usuario,
                password=conexao.senha,
                use_sso=conexao.usuario is None,
                as_dict=True,
                autocommit=True,
                login_timeout=self._login_timeout,
            )
        except pytds.DatabaseError as falha:
            if falha.msg_no in LOGIN_RECUSADO:
                raise CredenciaisInvalidasError(conexao.servidor, falha.text) from falha

            raise InstanciaInacessivelError(conexao.servidor, falha.text) from falha
        except (pytds.Error, OSError) as falha:
            raise InstanciaInacessivelError(conexao.servidor, str(falha)) from falha

        try:
            yield Sessao(aberta, conexao.servidor)
        finally:
            with suppress(pytds.Error, OSError):
                aberta.close()

    def executar(
        self,
        conexao: Conexao,
        comando: str,
        parametros: Mapping[str, object] | None = None,
    ) -> list[dict[str, object]]:
        """Roda um comando numa sessão só para ele.

        Raises:
            InstanciaInacessivelError: Se a instância não respondeu.
            CredenciaisInvalidasError: Se a instância recusou o login.
            ComandoRecusadoError: Se a instância recusou ou falhou o comando.

        """
        with self.sessao(conexao) as sessao:
            return sessao.executar(comando, parametros)

    def ping(self, conexao: Conexao) -> timedelta:
        """Confere se a instância responde e aceita o login, e mede a ida e volta de um comando.

        A latência não conta o login: ela é medida depois dele, num comando vazio.

        Raises:
            InstanciaInacessivelError: Se a instância não respondeu.
            CredenciaisInvalidasError: Se a instância recusou o login.
            ComandoRecusadoError: Se a instância aceitou o login e recusou o
                comando.

        """
        with self.sessao(conexao) as sessao:
            inicio = perf_counter()
            sessao.executar("SELECT 1")

            return timedelta(seconds=perf_counter() - inicio)

    def executar_com_progresso(
        self,
        conexao: Conexao,
        comando: str,
        parametros: Mapping[str, object] | None,
    ) -> None:
        """Roda um comando demorado relatando o quanto dele já passou.

        Como esse relato chega a quem chamou ainda não foi decidido.

        Raises:
            NotImplementedError: Sempre, enquanto não for escrito.

        """
        raise NotImplementedError
