from bakrestorer.core.exceptions import BakRestorerError


class SqlServerError(BakRestorerError):
    """Falha ao alcançar uma instância do SQL Server ou ao executar um comando nela.

    Attributes:
        servidor: Instância que a operação tentou alcançar.
        detalhe: O que a instância ou a rede responderam.

    """

    def __init__(self, servidor: str, detalhe: str) -> None:
        super().__init__(f"{servidor}: {detalhe}")
        self.servidor = servidor
        self.detalhe = detalhe


class InstanciaInacessivelError(SqlServerError):
    """A instância não respondeu."""


class CredenciaisInvalidasError(SqlServerError):
    """A instância respondeu e recusou o login."""


class ComandoRecusadoError(SqlServerError):
    """A instância aceitou o login e recusou ou falhou o comando."""
