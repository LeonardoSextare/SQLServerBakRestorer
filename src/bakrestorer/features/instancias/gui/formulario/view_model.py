import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

import flet as ft

from bakrestorer.composition import diagnostico_service
from bakrestorer.features.instancias import Diagnostico, Instancia, InstanciaInvalidaError, InstanciaJaExisteError

type NomeDoCampo = Literal["apelido", "host", "nome", "porta", "usuario", "senha", "pasta_dados", "pasta_log"]


FORMULARIO_VAZIO: dict[NomeDoCampo, str] = {
    "apelido": "",
    "host": "",
    "nome": "",
    "porta": "",
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

    `diagnostico` é a resposta do último teste de conexão, e sai quando um campo
    da conexão muda: ela respondia pelo que estava digitado na hora do teste.
    """

    digitado: dict[NomeDoCampo, str] = field(default_factory=FORMULARIO_VAZIO.copy)
    recusas: dict[NomeDoCampo, str] = field(default_factory=dict)
    pastas_vinculadas: bool = True
    usa_porta: bool = False
    id_da_instancia: UUID = field(default_factory=uuid4)
    testando: bool = False
    diagnostico: Diagnostico | None = None

    def preencher_com(self, instancia: Instancia) -> None:
        """Copia para o formulário os dados de uma instância já cadastrada.

        As pastas ficam vinculadas só se a instância já usa a mesma para as duas.
        """
        self.digitado = {
            "apelido": instancia.apelido,
            "host": instancia.host,
            "nome": instancia.nome or "",
            "porta": str(instancia.porta or ""),
            "usuario": instancia.usuario,
            "senha": instancia.senha,
            "pasta_dados": str(instancia.pasta_dados or ""),
            "pasta_log": str(instancia.pasta_log or ""),
        }
        self.pastas_vinculadas = instancia.pasta_dados == instancia.pasta_log
        self.usa_porta = instancia.porta is not None
        self.id_da_instancia = instancia.id

    def digitar(self, campo: NomeDoCampo, texto: str) -> None:
        """Guarda o que foi digitado num campo e tira a recusa dele.

        Com as pastas vinculadas, digitar numa delas escreve igual na outra.
        Mudar um campo da conexão apaga o resultado do último teste.
        """
        alterados: dict[NomeDoCampo, str] = {campo: texto}

        if self.pastas_vinculadas and campo in ("pasta_dados", "pasta_log"):
            alterados = {"pasta_dados": texto, "pasta_log": texto}

        self.digitado = {**self.digitado, **alterados}
        self.recusas = {recusado: motivo for recusado, motivo in self.recusas.items() if recusado not in alterados}

        if campo in ("host", "nome", "porta", "usuario", "senha"):
            self.diagnostico = None

    def alternar_vinculo_das_pastas(self) -> None:
        """Liga ou desliga o vínculo entre as pastas de dados e de log.

        Ao ligar, a pasta de log passa a ser igual à de dados.
        """
        if self.pastas_vinculadas:
            self.pastas_vinculadas = False
            return

        self.pastas_vinculadas = True
        self.digitado = {**self.digitado, "pasta_log": self.digitado["pasta_dados"]}

    def alternar_nome_e_porta(self) -> None:
        """Troca entre achar a instância pelo nome e achar pela porta.

        A recusa dos dois sai junto: ela foi dada ao campo que estava na tela, e
        não vale para o que entra no lugar dele. O resultado do último teste sai
        pelo mesmo motivo.
        """
        self.usa_porta = not self.usa_porta
        self.recusas = {campo: motivo for campo, motivo in self.recusas.items() if campo not in ("nome", "porta")}
        self.diagnostico = None

    async def testar_conexao(self) -> None:
        """Pergunta à instância digitada se ela responde, sem salvar nada.

        O teste sai numa thread porque espera a rede, e esperar aqui travaria a
        janela pelo tempo do login.

        Raises:
            ComandoRecusadoError: Se a instância aceitou o login e recusou o
                ping. Ninguém espera por isso.

        """
        try:
            instancia = self._montar_instancia()
        except InstanciaInvalidaError as erro:
            self._recusar({campo: self._motivo_da_recusa(campo) for campo in erro.campos})
            return

        self.diagnostico = None
        self.testando = True

        try:
            self.diagnostico = await asyncio.to_thread(diagnostico_service().conferir_acesso_a_instancia, instancia)
        finally:
            self.testando = False

    def salvar(self, gravar: Callable[[Instancia], None]) -> None:
        """Monta a instância e a entrega a `gravar`.

        O que for recusado vira mensagem no campo que causou a recusa. Quem
        grava é de fora: o formulário não sabe onde nem como.

        São dois `try` porque `gravar` também pode levantar
        `InstanciaInvalidaError`, quando uma instância já gravada está
        corrompida. Num `try` só, isso apareceria como "Campo obrigatório".

        Raises:
            Exception: O que `gravar` levantar além de `InstanciaJaExisteError`,
                como a falha ao gravar o arquivo.

        """
        try:
            instancia = self._montar_instancia()
        except InstanciaInvalidaError as erro:
            self._recusar({campo: self._motivo_da_recusa(campo) for campo in erro.campos})
            return

        try:
            gravar(instancia)
        except InstanciaJaExisteError:
            self._recusar({"apelido": "Já existe uma instância com esse apelido"})

    def _recusar(self, motivos: dict[str, str]) -> None:
        """Marca os campos que impediram a ação, cada um com o seu motivo.

        Só entram os campos do formulário: o model pode recusar uma chave que não
        é campo da tela.
        """
        self.recusas = {campo: motivos[campo] for campo in self.digitado if campo in motivos}

    def _motivo_da_recusa(self, campo: str) -> str:
        """Diz por que o model recusou o campo, olhando o que foi digitado nele.

        A porta preenchida e recusada só pode estar fora da faixa: o filtro do
        campo não deixa entrar nada além de algarismos.
        """
        if campo == "porta" and self.digitado["porta"].strip():
            return "Porta inválida (1 a 65535)"

        return "Campo obrigatório"

    def _montar_instancia(self) -> Instancia:
        """Transforma o que foi digitado numa instância.

        Os espaços nas pontas saem de todo campo, menos da senha, em que espaço
        pode ser de propósito.

        Raises:
            InstanciaInvalidaError: Se algum campo obrigatório ficou vazio, ou se
                a porta está fora da faixa.

        """
        porta = self.digitado["porta"].strip()
        pasta_dados = self.digitado["pasta_dados"].strip()
        pasta_log = self.digitado["pasta_log"].strip()

        return Instancia(
            id=self.id_da_instancia,
            apelido=self.digitado["apelido"].strip(),
            host=self.digitado["host"].strip(),
            nome=None if self.usa_porta else self.digitado["nome"].strip(),
            porta=int(porta) if self.usa_porta and porta else None,
            usuario=self.digitado["usuario"].strip(),
            senha=self.digitado["senha"],
            pasta_dados=Path(pasta_dados) if pasta_dados else None,
            pasta_log=Path(pasta_log) if pasta_log else None,
        )
