from pathlib import Path
from typing import Self

from pydantic import Field, model_validator

from bakrestorer.base_model import BakRestorerModel
from bakrestorer.features.instancias.domain.exceptions import CadastroInvalidoError, InstanciaInvalidaError


class Instancia(BakRestorerModel):
    """Uma instância do SQL Server e as credenciais escolhidas para ela."""

    ERRO_DE_VALIDACAO = InstanciaInvalidaError

    # TODO: senha em texto puro -- .claude/tarefas/senha-gravada-em-texto-puro.md
    alias: str = Field(min_length=1)
    host: str = Field(default="localhost", min_length=1)
    nome: str = Field(min_length=1)
    usuario: str = Field(min_length=1)
    senha: str = Field(min_length=1)
    pasta_dados: Path | None = None
    pasta_log: Path | None = None


class ConfigInstancias(BakRestorerModel):
    """As instâncias cadastradas e qual delas é a padrão.

    Todos os campos têm padrão, então cadastro ausente equivale a `ConfigInstancias()`.
    """

    ERRO_DE_VALIDACAO = CadastroInvalidoError

    padrao: str | None = None
    itens: tuple[Instancia, ...] = ()

    @model_validator(mode="after")
    def _conferir_itens(self) -> Self:
        """Confere o que só faz sentido olhando a lista inteira.

        Raises:
            CadastroInvalidoError: Se um alias se repete, ou se `padrao` aponta
                para um alias que não está na lista.

        """
        aliases = [item.alias for item in self.itens]
        repetidos = sorted({alias for alias in aliases if aliases.count(alias) > 1})

        if repetidos:
            raise CadastroInvalidoError({"itens": f"alias repetido: {repetidos}"})

        if self.padrao and self.padrao not in aliases:
            raise CadastroInvalidoError({"padrao": f"'{self.padrao}' não está entre as instâncias"})

        return self

    def obter(self, alias: str) -> Instancia | None:
        """Procura uma instância cadastrada pelo alias."""
        return next((item for item in self.itens if item.alias == alias), None)
