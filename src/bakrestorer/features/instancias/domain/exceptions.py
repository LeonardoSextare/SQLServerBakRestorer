from uuid import UUID

from bakrestorer.exceptions import BakRestorerError, ModelInvalidoError


class InstanciasError(BakRestorerError):
    """Falha ao interpretar ou alterar o cadastro de instâncias."""


class InstanciaInvalidaError(ModelInvalidoError, InstanciasError):
    """Os dados informados não formam uma instância válida."""


class CadastroInvalidoError(ModelInvalidoError, InstanciasError):
    """O cadastro não corresponde ao formato esperado."""


class DiagnosticoInvalidoError(ModelInvalidoError, InstanciasError):
    """Os dados informados não formam um diagnóstico válido."""


class InstanciaError(InstanciasError):
    """Falha ao alterar uma instância do cadastro."""


class InstanciaNaoEncontradaError(InstanciaError):
    """Nenhuma instância cadastrada tem esse id."""

    def __init__(self, id_da_instancia: UUID) -> None:
        super().__init__(str(id_da_instancia))
        self.id_da_instancia = id_da_instancia


class InstanciaJaExisteError(InstanciaError):
    """Já existe outra instância cadastrada com esse apelido."""

    def __init__(self, apelido: str) -> None:
        super().__init__(apelido)
        self.apelido = apelido
