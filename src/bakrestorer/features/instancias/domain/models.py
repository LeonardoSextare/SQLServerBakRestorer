from pathlib import Path
from typing import Self
from uuid import UUID, uuid4

from pydantic import Field, model_validator

from bakrestorer.base_model import BakRestorerModel
from bakrestorer.features.instancias.domain.exceptions import CadastroInvalidoError, InstanciaInvalidaError


class Instancia(BakRestorerModel):
    """Uma instância do SQL Server e as credenciais escolhidas para ela."""

    ERRO_DE_VALIDACAO = InstanciaInvalidaError

    id: UUID = Field(default_factory=uuid4)
    apelido: str = Field(min_length=1)
    host: str = Field(default="localhost", min_length=1)
    nome: str | None = Field(default=None, min_length=1)
    porta: int | None = Field(default=None, ge=1, le=65535)
    usuario: str = Field(min_length=1)
    # TODO: senha em texto puro -- tarefa #014
    senha: str = Field(min_length=1)
    pasta_dados: Path | None = None
    pasta_log: Path | None = None

    @model_validator(mode="after")
    def _conferir_nome_ou_porta(self) -> Self:
        """Exige exatamente um entre o nome e a porta.

        Raises:
            InstanciaInvalidaError: Se os dois vieram preenchidos, ou nenhum.

        """
        if self.nome is not None and self.porta is not None:
            motivo = "informe só um: o nome ou a porta"
            raise InstanciaInvalidaError({"nome": motivo, "porta": motivo})

        if self.nome is None and self.porta is None:
            motivo = "informe o nome ou a porta"
            raise InstanciaInvalidaError({"nome": motivo, "porta": motivo})

        return self


class ConfigInstancias(BakRestorerModel):
    """As instâncias cadastradas e qual delas é a padrão.

    Todos os campos têm padrão, então cadastro ausente equivale a `ConfigInstancias()`.
    """

    ERRO_DE_VALIDACAO = CadastroInvalidoError

    padrao: UUID | None = None
    itens: tuple[Instancia, ...] = ()

    @model_validator(mode="after")
    def _conferir_itens(self) -> Self:
        """Confere o que só faz sentido olhando a lista inteira.

        O apelido continua único mesmo sem ser a identidade: é o nome que o
        usuário vê, e duas instâncias com o mesmo nome confundiriam.

        Raises:
            CadastroInvalidoError: Se um apelido ou um id se repete, ou se
                `padrao` aponta para um id que não está na lista.

        """
        apelidos = [item.apelido for item in self.itens]
        apelidos_repetidos = sorted({apelido for apelido in apelidos if apelidos.count(apelido) > 1})

        if apelidos_repetidos:
            raise CadastroInvalidoError({"itens": f"apelido repetido: {apelidos_repetidos}"})

        ids = [item.id for item in self.itens]

        if len(set(ids)) < len(ids):
            raise CadastroInvalidoError({"itens": "id repetido"})

        if self.padrao is not None and self.padrao not in ids:
            raise CadastroInvalidoError({"padrao": f"'{self.padrao}' não está entre as instâncias"})

        return self

    def obter(self, id_da_instancia: UUID) -> Instancia | None:
        """Procura uma instância cadastrada pela identidade."""
        return next((item for item in self.itens if item.id == id_da_instancia), None)

    def obter_pelo_apelido(self, apelido: str) -> Instancia | None:
        """Procura uma instância cadastrada pelo nome que o usuário vê."""
        return next((item for item in self.itens if item.apelido == apelido), None)
