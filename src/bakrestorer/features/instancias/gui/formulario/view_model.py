from collections.abc import Callable, Collection
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import flet as ft

from bakrestorer.features.instancias import Instancia, InstanciaInvalidaError, InstanciaJaExisteError

type NomeDoCampo = Literal["alias", "host", "nome", "usuario", "senha", "pasta_dados", "pasta_log"]


FORMULARIO_VAZIO: dict[NomeDoCampo, str] = {
    "alias": "",
    "host": "",
    "nome": "",
    "usuario": "",
    "senha": "",
    "pasta_dados": "",
    "pasta_log": "",
}


@ft.observable
@dataclass
class FormularioViewModel:
    """O que foi digitado no formulário, e o motivo de cada campo recusado.

    Guarda texto, e não uma `Instancia`: enquanto o usuário digita, o que está
    na tela pode estar incompleto, e uma `Instancia` não existe incompleta. O
    `salvar` é que transforma o texto numa, na hora de gravar.

    `digitado` tem sempre todos os campos, mesmo os vazios: assim ler um campo
    nunca falha por falta da chave.
    """

    digitado: dict[NomeDoCampo, str] = field(default_factory=FORMULARIO_VAZIO.copy)
    recusas: dict[NomeDoCampo, str] = field(default_factory=dict)

    def preencher_com(self, instancia: Instancia) -> None:
        """Copia para o formulário os dados de uma instância já cadastrada."""
        self.digitado = {
            "alias": instancia.alias,
            "host": instancia.host,
            "nome": instancia.nome,
            "usuario": instancia.usuario,
            "senha": instancia.senha,
            "pasta_dados": str(instancia.pasta_dados or ""),
            "pasta_log": str(instancia.pasta_log or ""),
        }

    def digitar(self, campo: NomeDoCampo, texto: str) -> None:
        """Guarda o que foi digitado num campo e tira a recusa dele."""
        self.digitado = {**self.digitado, campo: texto}
        self.recusas = {recusado: motivo for recusado, motivo in self.recusas.items() if recusado != campo}

    def salvar(self, gravar: Callable[[Instancia], None]) -> None:
        """Monta a instância e a entrega a `gravar`.

        O que for recusado vira mensagem no campo que causou a recusa. Quem
        grava é de fora: o formulário não sabe onde nem como.

        São dois `try` porque `gravar` também pode levantar
        `InstanciaInvalidaError`, quando uma instância já gravada está
        corrompida. Num `try` só, isso apareceria como "Preencha este campo".

        Raises:
            Exception: O que `gravar` levantar além de `InstanciaJaExisteError`,
                como a falha ao gravar o arquivo.

        """
        try:
            instancia = self._montar()
        except InstanciaInvalidaError as erro:
            self._recusar(erro.campos, "Preencha este campo")
            return

        try:
            gravar(instancia)
        except InstanciaJaExisteError:
            self._recusar({"alias"}, "Já existe uma instância com esse apelido")

    def _recusar(self, campos: Collection[str], motivo: str) -> None:
        """Marca os campos que impediram o salvamento, todos com o mesmo motivo."""
        self.recusas = {campo: motivo for campo in self.digitado if campo in campos}

    def _montar(self) -> Instancia:
        """Transforma o que foi digitado numa instância.

        Os espaços nas pontas saem de todo campo, menos da senha, em que espaço
        pode ser de propósito.

        Raises:
            InstanciaInvalidaError: Se algum campo obrigatório ficou vazio.

        """
        pasta_dados = self.digitado["pasta_dados"].strip()
        pasta_log = self.digitado["pasta_log"].strip()

        return Instancia(
            alias=self.digitado["alias"].strip(),
            host=self.digitado["host"].strip(),
            nome=self.digitado["nome"].strip(),
            usuario=self.digitado["usuario"].strip(),
            senha=self.digitado["senha"],
            pasta_dados=Path(pasta_dados) if pasta_dados else None,
            pasta_log=Path(pasta_log) if pasta_log else None,
        )
