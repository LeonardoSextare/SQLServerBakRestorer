from collections.abc import Iterable, Mapping
from contextlib import suppress

import pytds

from bakrestorer.infra.sqlserver.connection import Conexao
from bakrestorer.infra.sqlserver.exceptions import (
    ComandoRecusadoError,
    CredenciaisInvalidasError,
    InstanciaInacessivelError,
    SqlServerError,
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


class ClienteSqlServer:
    """Executa comandos em instâncias do SQL Server, mantendo uma sessão por instância.

    A sessão abre no primeiro comando dirigido à instância e é reaproveitada até
    `encerrar`. A chave é a própria `Conexao`: valores iguais compartilham sessão.

    Comandos levam parâmetros nomeados (`%(nome)s`) e devolvem linhas como
    dicionário. Nenhum erro do driver atravessa: tudo vira exceção de
    `exceptions.py`.

    """

    def __init__(self, login_timeout: float = 5) -> None:
        """Cria o cliente, ainda sem nenhuma sessão aberta.

        Args:
            login_timeout: Segundos a esperar pelo login antes de
                desistir. Sem limite, um host inalcançável só falha no tempo do
                sistema, que pode ser indefinido quando os pacotes são
                descartados em silêncio.

        """
        self._login_timeout = login_timeout
        self._sessoes: dict[Conexao, pytds.Connection] = {}

    def aquecer(self, conexoes: Iterable[Conexao]) -> dict[Conexao, bool]:
        """Abre as sessões das conexões informadas, seguindo adiante quando alguma falha.

        Antecipa o custo do login. A conexão que falhar aqui não fica registrada
        e volta a ser tentada no primeiro comando dirigido a ela.

        Args:
            conexoes: Instâncias a alcançar.

        Returns:
            dict[Conexao, bool]: Cada conexão informada e se a sessão dela ficou aberta.

        """
        aberta: dict[Conexao, bool] = {}

        for conexao in conexoes:
            try:
                self._sessao(conexao)
            except SqlServerError:
                aberta[conexao] = False
            else:
                aberta[conexao] = True

        return aberta

    def executar(
        self,
        conexao: Conexao,
        comando: str,
        parametros: Mapping[str, object] | None = None,
    ) -> list[dict[str, object]]:
        """Roda um comando na instância.

        Comando que não produz conjunto de resultados devolve lista vazia.

        Args:
            conexao: Instância alvo.
            comando: Comando a executar, com parâmetros nomeados.
            parametros: Valores dos parâmetros nomeados.

        Returns:
            list[dict[str, object]]: Uma linha por resultado, mapeando coluna a valor.

        Raises:
            InstanciaInacessivelError: Se a instância não respondeu.
            CredenciaisInvalidasError: Se a instância recusou o login.
            ComandoRecusadoError: Se a instância recusou ou falhou o comando.

        """
        sessao = self._sessao(conexao)

        try:
            with sessao.cursor() as cursor:
                cursor.execute(comando, dict(parametros) if parametros else None)
                linhas = [] if cursor.description is None else list(cursor.fetchall())
        except pytds.DatabaseError as falha:
            raise ComandoRecusadoError(conexao.servidor, str(falha)) from falha
        except (pytds.Error, OSError) as falha:
            self.descartar(conexao)
            raise InstanciaInacessivelError(conexao.servidor, str(falha)) from falha

        return linhas

    def executar_com_progresso(
        self,
        conexao: Conexao,
        comando: str,
        parametros: Mapping[str, object] | None,
    ) -> None:
        """Roda um comando demorado relatando o quanto dele já passou.

        Como esse relato chega a quem chamou ainda não foi decidido.

        Args:
            conexao: Instância a alcançar.
            comando: Comando a executar, com parâmetros nomeados na forma
                `%(nome)s`.
            parametros: Valores dos parâmetros nomeados.

        Raises:
            NotImplementedError: Sempre, enquanto não for escrito.

        """
        raise NotImplementedError

    def descartar(self, conexao: Conexao) -> None:
        """Fecha a sessão da instância e a esquece, quando houver uma.

        O próximo comando dirigido a ela faz login de novo. É o jeito de saber
        se a credencial ainda vale: a sessão guardada só prova que valia quando
        abriu.

        Falha ao fechar é ignorada: a sessão já não serve, e não há estado a
        preservar.
        """
        sessao = self._sessoes.pop(conexao, None)

        if sessao is None:
            return

        with suppress(pytds.Error):
            sessao.close()

    def encerrar(self) -> None:
        """Fecha todas as sessões abertas e esvazia o cache."""
        for conexao in list(self._sessoes):
            self.descartar(conexao)

    def _sessao(self, conexao: Conexao) -> pytds.Connection:
        """Devolve a sessão da instância, abrindo-a quando ainda não houver.

        Args:
            conexao: Instância a alcançar.

        Returns:
            pytds.Connection: A sessão aberta.

        Raises:
            InstanciaInacessivelError: Se a instância não respondeu.
            CredenciaisInvalidasError: Se a instância recusou o login.

        """
        if conexao not in self._sessoes:
            self._sessoes[conexao] = self._abrir_sessao(conexao)

        return self._sessoes[conexao]

    def _abrir_sessao(self, conexao: Conexao) -> pytds.Connection:
        """Faz o login na instância.

        Args:
            conexao: Instância a alcançar.

        Returns:
            pytds.Connection: A sessão recém-aberta.

        Raises:
            InstanciaInacessivelError: Se a instância não respondeu.
            CredenciaisInvalidasError: Se a instância recusou o login.

        """
        try:
            return pytds.connect(
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
                raise CredenciaisInvalidasError(conexao.servidor, str(falha)) from falha

            raise InstanciaInacessivelError(conexao.servidor, str(falha)) from falha
        except (pytds.Error, OSError) as falha:
            raise InstanciaInacessivelError(conexao.servidor, str(falha)) from falha
