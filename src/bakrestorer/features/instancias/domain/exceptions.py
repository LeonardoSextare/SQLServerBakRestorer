from bakrestorer.exceptions import BakRestorerError, ModelInvalidoError


class InstanciasError(BakRestorerError):
    """Falha ao interpretar ou alterar o cadastro de instâncias."""


class InstanciaInvalidaError(ModelInvalidoError, InstanciasError):
    """Os dados informados não formam uma instância válida."""


class CadastroInvalidoError(ModelInvalidoError, InstanciasError):
    """O cadastro não corresponde ao formato esperado."""


class InstanciaError(InstanciasError):
    """Falha ao alterar uma instância do cadastro."""

    def __init__(self, alias: str) -> None:
        super().__init__(alias)
        self.alias = alias


class InstanciaNaoEncontradaError(InstanciaError):
    """Nenhuma instância cadastrada usa esse alias."""


class InstanciaJaExisteError(InstanciaError):
    """Já existe uma instância cadastrada com esse alias."""
