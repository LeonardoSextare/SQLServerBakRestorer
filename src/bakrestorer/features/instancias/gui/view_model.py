from dataclasses import dataclass

import flet as ft

from bakrestorer.composition import instancias_service
from bakrestorer.features.instancias import ConfigInstancias, Instancia


@ft.observable
@dataclass
class InstanciasViewModel:
    """O que a seção de instâncias precisa saber, e as ações que mudam isso.

    `cadastro` é None enquanto a seção ainda não leu o disco. Cadastro sem
    nenhuma instância volta como uma lista vazia, e não como None.

    `instancia_em_edicao` só tem valor com o formulário aberto: None ali quer dizer
    instância nova. Os métodos mudam os dois campos juntos, para nunca sobrar
    uma instância em edição com o formulário fechado.

    Remover acontece em dois tempos: `pedir_remocao` só guarda em
    `instancia_a_remover` qual instância o usuário quer tirar, e a tela pede a
    confirmação enquanto ela estiver ali. Quem tira de fato é o
    `confirmar_remocao`.

    `instancia_em_detalhe` é a instância com os detalhes abertos, e a tela
    mostra o diálogo dela enquanto ela estiver ali.
    """

    cadastro: ConfigInstancias | None = None
    formulario_aberto: bool = False
    instancia_em_edicao: Instancia | None = None
    instancia_a_remover: Instancia | None = None
    instancia_em_detalhe: Instancia | None = None

    def carregar(self) -> None:
        """Lê do disco o que está cadastrado.

        Ler é do view model, e não do componente: o componente só desenha o que já
        foi lido. Quem chama isto é um efeito, porque tocar o disco durante o
        desenho faria a leitura acontecer a cada redesenho.
        """
        self.cadastro = instancias_service().carregar()

    def abrir_cadastro(self) -> None:
        """Abre o formulário vazio, para uma instância nova."""
        self.instancia_em_edicao = None
        self.formulario_aberto = True

    def abrir_edicao(self, instancia: Instancia) -> None:
        """Abre o formulário preenchido com uma instância já cadastrada."""
        self.instancia_em_edicao = instancia
        self.formulario_aberto = True

    def abrir_detalhes(self, instancia: Instancia) -> None:
        """Mostra o que está cadastrado na instância e o diagnóstico dela."""
        self.instancia_em_detalhe = instancia

    def fechar_detalhes(self) -> None:
        """Fecha os detalhes da instância."""
        self.instancia_em_detalhe = None

    def fechar_formulario(self) -> None:
        """Fecha o formulário sem guardar nada."""
        self.formulario_aberto = False
        self.instancia_em_edicao = None

    def salvar(self, instancia: Instancia) -> None:
        """Grava a instância e fecha o formulário.

        O cadastro devolvido pelo serviço já é o gravado, então ele substitui o
        da tela sem uma nova leitura do disco.

        Raises:
            InstanciaJaExisteError: Se é cadastro novo e o apelido já existe.
            InstanciaNaoEncontradaError: Se é edição e o apelido sumiu do cadastro.
            ArquivoNaoLegivelError: Se o sistema recusou a leitura do cadastro.
            ArquivoCorrompidoError: Se o arquivo não é json em utf-8.
            CadastroInvalidoError: Se o gravado não corresponde ao formato.
            InstanciaInvalidaError: Se uma das instâncias gravadas não
                corresponde ao formato.
            ArquivoNaoGravavelError: Se o arquivo não pôde ser gravado.

        """
        service = instancias_service()

        if self.instancia_em_edicao is None:
            self.cadastro = service.adicionar(instancia)
        else:
            self.cadastro = service.atualizar(instancia)

        self.fechar_formulario()

    def definir_padrao(self, instancia: Instancia) -> None:
        """Torna a instância a padrão: a que o aplicativo usa para ler os backups.

        Raises:
            InstanciaNaoEncontradaError: Se a instância sumiu do cadastro.
            ArquivoNaoLegivelError: Se o sistema recusou a leitura do cadastro.
            ArquivoCorrompidoError: Se o arquivo não é json em utf-8.
            CadastroInvalidoError: Se o gravado não corresponde ao formato.
            InstanciaInvalidaError: Se uma das instâncias gravadas não
                corresponde ao formato.
            ArquivoNaoGravavelError: Se o arquivo não pôde ser gravado.

        """
        self.cadastro = instancias_service().definir_padrao(instancia.id)

    def pedir_remocao(self, instancia: Instancia) -> None:
        """Guarda qual instância o usuário quer tirar, à espera da confirmação."""
        self.instancia_a_remover = instancia

    def cancelar_remocao(self) -> None:
        """Desiste de tirar a instância, sem mexer no cadastro."""
        self.instancia_a_remover = None

    def confirmar_remocao(self) -> None:
        """Tira do cadastro a instância que estava à espera da confirmação.

        Remover a padrão deixa o cadastro sem padrão, até o usuário escolher outra.

        Raises:
            InstanciaNaoEncontradaError: Se a instância sumiu do cadastro.
            ArquivoNaoLegivelError: Se o sistema recusou a leitura do cadastro.
            ArquivoCorrompidoError: Se o arquivo não é json em utf-8.
            CadastroInvalidoError: Se o gravado não corresponde ao formato.
            InstanciaInvalidaError: Se uma das instâncias gravadas não
                corresponde ao formato.
            ArquivoNaoGravavelError: Se o arquivo não pôde ser gravado.

        """
        if self.instancia_a_remover is None:
            return

        self.cadastro = instancias_service().remover(self.instancia_a_remover.id)
        self.instancia_a_remover = None
