from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import ClassVar, Self, Unpack

from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    ValidatorFunctionWrapHandler,
    model_validator,
)

from bakrestorer.exceptions import ModelInvalidoError

_RASCUNHOS: ContextVar[frozenset[int]] = ContextVar("rascunhos_em_edicao", default=frozenset())


class BakRestorerModel(BaseModel):
    """Base de todo model do domínio.

    Ela dá três coisas a quem herda:

    - a falha sai como exceção nossa, e não como `ValidationError` do Pydantic;
    - atribuir um campo valida o objeto inteiro antes de escrever, então ele
      nunca fica no estado que acabou de recusar;
    - `alterando()` junta várias mudanças numa só, como uma transação.

    Cada model **precisa** declarar em `ERRO_DE_VALIDACAO` qual exceção ele
    levanta; quem esquecer não chega a existir. Regra que só faz sentido
    olhando o objeto inteiro vai num `model_validator(mode="after")` e
    levanta essa mesma exceção direto.
    """

    model_config = ConfigDict(extra="forbid")

    ERRO_DE_VALIDACAO: ClassVar[type[ModelInvalidoError]]

    def __init_subclass__(cls, **configuracao: Unpack[ConfigDict]) -> None:
        """Recusa o model que não disse qual exceção ele levanta.

        Raises:
            TypeError: Se nem a classe nem uma ancestral dela declarou
                `ERRO_DE_VALIDACAO`.

        """
        super().__init_subclass__(**configuracao)

        if not hasattr(cls, "ERRO_DE_VALIDACAO"):
            mensagem = f"{cls.__name__} não declarou ERRO_DE_VALIDACAO"
            raise TypeError(mensagem)

    @model_validator(mode="wrap")
    @classmethod
    def _traduzir_excecao(cls, dados: object, validar: ValidatorFunctionWrapHandler) -> Self:
        """Deixa o Pydantic validar e troca a falha dele pela nossa.

        Raises:
            ModelInvalidoError: A subclasse declarada em `ERRO_DE_VALIDACAO`,
                quando algum campo não foi aceito.

        """
        try:
            return validar(dados)
        except ValidationError as falha:
            raise cls.ERRO_DE_VALIDACAO(_por_campo(falha)) from falha

    def __setattr__(self, nome: str, valor: object) -> None:
        """Valida o objeto inteiro com o valor novo e só então escreve.

        Num rascunho a escrita é crua: quem confere é o `alterando()`, no fim.

        Raises:
            ModelInvalidoError: A subclasse declarada em `ERRO_DE_VALIDACAO`,
                quando o objeto com o valor novo não seria válido. Campo que não
                existe cai aqui também, recusado pelo `extra="forbid"`.

        """
        if nome.startswith("_"):
            super().__setattr__(nome, valor)
            return

        if id(self) in _RASCUNHOS.get():
            object.__setattr__(self, nome, valor)
            return

        candidato = type(self).model_validate({**self.__dict__, nome: valor})
        super().__setattr__(nome, getattr(candidato, nome))

    @contextmanager
    def alterando(self) -> Generator[Self]:
        """Acumula mudanças num rascunho e só aplica se o conjunto todo passar.

        É o jeito de trocar mais de um campo quando cada um sozinho deixaria o
        objeto inválido. A cópia é profunda, então mexer no rascunho não alcança
        o original -- e uma recusa deixa ele exatamente como estava.

        Raises:
            ModelInvalidoError: A subclasse declarada em `ERRO_DE_VALIDACAO`,
                quando o rascunho inteiro não é aceito. Nada é aplicado.

        """
        rascunho = self.model_copy(deep=True)
        em_edicao = _RASCUNHOS.set(_RASCUNHOS.get() | {id(rascunho)})

        try:
            yield rascunho
        finally:
            _RASCUNHOS.reset(em_edicao)

        validado = type(self).model_validate(dict(rascunho.__dict__))
        object.__setattr__(self, "__dict__", dict(validado.__dict__))


def _por_campo(falha: ValidationError) -> dict[str, str]:
    """Reduz a falha do Pydantic a um motivo por campo."""
    return {".".join(str(parte) for parte in recusa["loc"]) or "model": recusa["msg"] for recusa in falha.errors()}
