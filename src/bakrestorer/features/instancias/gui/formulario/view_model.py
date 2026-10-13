from collections.abc import Callable, Collection
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

import flet as ft

from bakrestorer.features.instancias import Instancia, InstanciaInvalidaError, InstanciaJaExisteError

type NomeDoCampo = Literal["apelido", "host", "nome", "usuario", "senha", "pasta_dados", "pasta_log"]


FORMULARIO_VAZIO: dict[NomeDoCampo, str] = {
    "apelido": "",
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

    Com `pastas_vinculadas`, digitar numa das pastas escreve igual na outra. O
    formulário nasce vinculado, porque as duas pastas começam vazias, e iguais.

    `id_da_instancia` é sempre o de quem será gravado: o formulário novo nasce
    com o de uma instância nova, e a edição troca pelo da instância editada.
    Assim o salvar não precisa saber se é cadastro ou edição.
    """

    digitado: dict[NomeDoCampo, str] = field(default_factory=FORMULARIO_VAZIO.copy)
    recusas: dict[NomeDoCampo, str] = field(default_factory=dict)
    pastas_vinculadas: bool = True
    id_da_instancia: UUID = field(default_factory=uuid4)

    def preencher_com(self, instancia: Instancia) -> None:
        """Copia para o formulário os dados de uma instância já cadastrada.

        As pastas ficam vinculadas só se a instância já usa a mesma para as duas.
        """
        self.digitado = {
            "apelido": instancia.apelido,
            "host": instancia.host,
            "nome": instancia.nome,
            "usuario": instancia.usuario,
            "senha": instancia.senha,
            "pasta_dados": str(instancia.pasta_dados or ""),
            "pasta_log": str(instancia.pasta_log or ""),
        }
        self.pastas_vinculadas = instancia.pasta_dados == instancia.pasta_log
        self.id_da_instancia = instancia.id

    def digitar(self, campo: NomeDoCampo, texto: str) -> None:
        """Guarda o que foi digitado num campo e tira a recusa dele.

        Com as pastas vinculadas, digitar numa delas escreve igual na outra.
        """
        alterados: dict[NomeDoCampo, str] = {campo: texto}

        if self.pastas_vinculadas and campo in ("pasta_dados", "pasta_log"):
            alterados = {"pasta_dados": texto, "pasta_log": texto}

        self.digitado = {**self.digitado, **alterados}
        self.recusas = {recusado: motivo for recusado, motivo in self.recusas.items() if recusado not in alterados}

    def alternar_vinculo_das_pastas(self) -> None:
        """Liga ou desliga o vínculo entre as pastas de dados e de log.

        Ao ligar, a pasta de log passa a ser igual à de dados.
        """
        if self.pastas_vinculadas:
            self.pastas_vinculadas = False
            return

        self.pastas_vinculadas = True
        self.digitado = {**self.digitado, "pasta_log": self.digitado["pasta_dados"]}

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
            self._recusar({"apelido"}, "Já existe uma instância com esse apelido")

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
            id=self.id_da_instancia,
            apelido=self.digitado["apelido"].strip(),
            host=self.digitado["host"].strip(),
            nome=self.digitado["nome"].strip(),
            usuario=self.digitado["usuario"].strip(),
            senha=self.digitado["senha"],
            pasta_dados=Path(pasta_dados) if pasta_dados else None,
            pasta_log=Path(pasta_log) if pasta_log else None,
        )
