from bakrestorer.core.exceptions import BakRestorerError


class ConfiguracaoError(BakRestorerError):
    """Falha ao interpretar ou alterar a configuração."""


class ConfiguracaoInvalidaError(ConfiguracaoError):
    """O arquivo foi lido, mas o conteúdo não corresponde ao formato esperado.

    Attributes:
        motivo: O que a validação recusou, campo a campo.

    """

    def __init__(self, motivo: str) -> None:
        """Registra o que a validação recusou.

        Args:
            motivo: O que a validação recusou, campo a campo.

        """
        super().__init__(motivo)
        self.motivo = motivo


class InstanciaError(ConfiguracaoError):
    """Falha ao alterar uma instância da configuração.

    Attributes:
        alias: Nome escolhido pelo usuário para a instância em questão.

    """

    def __init__(self, alias: str) -> None:
        """Registra de qual instância se trata.

        Args:
            alias: Nome escolhido pelo usuário para a instância em questão.

        """
        super().__init__(alias)
        self.alias = alias


class InstanciaNaoEncontradaError(InstanciaError):
    """Nenhuma instância configurada usa esse alias."""


class InstanciaJaExisteError(InstanciaError):
    """Já existe uma instância configurada com esse alias."""


class InstanciaEhPadraoError(InstanciaError):
    """A instância é a padrão e há outras configuradas."""
