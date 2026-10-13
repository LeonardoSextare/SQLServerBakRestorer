from uuid import UUID

from bakrestorer.features.instancias.domain.exceptions import (
    InstanciaJaExisteError,
    InstanciaNaoEncontradaError,
)
from bakrestorer.features.instancias.domain.models import ConfigInstancias, Instancia
from bakrestorer.infra.config_json import ArquivoNaoEncontradoError, ConfigJson


class InstanciasService:
    """Lê e altera o cadastro de instâncias do SQL Server.

    Não guarda estado: cada operação lê, decide e grava. Assim nada fica
    desatualizado em relação ao disco, e quem chama é dono do que carregou.

    Toda alteração devolve o cadastro inteiro já gravado, porque ele é um
    documento só -- não há gravação parcial.
    """

    def __init__(self, config: ConfigJson) -> None:
        self._config = config

    def carregar(self) -> ConfigInstancias:
        """Lê o cadastro gravado, ou um cadastro vazio quando ainda não há nada gravado.

        Raises:
            ArquivoNaoLegivelError: Se o sistema recusou a leitura.
            ArquivoCorrompidoError: Se o arquivo não é json em utf-8.
            CadastroInvalidoError: Se o gravado não corresponde ao formato.
            InstanciaInvalidaError: Se uma das instâncias gravadas não
                corresponde ao formato.

        """
        try:
            gravado = self._config.ler()
        except ArquivoNaoEncontradoError:
            return ConfigInstancias()

        if gravado is None:
            return ConfigInstancias()

        return ConfigInstancias.model_validate(gravado)

    def salvar(self, cadastro: ConfigInstancias) -> ConfigInstancias:
        """Grava o cadastro inteiro e o adota como o em vigor.

        Raises:
            ArquivoNaoLegivelError: Se o sistema recusou a leitura do que já estava lá.
            ArquivoCorrompidoError: Se o arquivo não é json em utf-8.
            ArquivoNaoGravavelError: Se o arquivo não pôde ser gravado, deixando
                o conteúdo anterior intacto.

        """
        self._config.gravar(cadastro.model_dump(mode="json"))

        return cadastro

    def adicionar(self, instancia: Instancia) -> ConfigInstancias:
        """Acrescenta uma instância ao cadastro.

        Ela vira a padrão quando ainda não há uma escolhida.

        Raises:
            InstanciaJaExisteError: Se outra instância já usa esse apelido.
            CadastroInvalidoError: Se o que estava gravado não corresponde ao formato.
            ArquivoNaoGravavelError: Se o arquivo não pôde ser gravado.

        """
        cadastro = self.carregar()

        if cadastro.obter_pelo_apelido(instancia.apelido) is not None:
            raise InstanciaJaExisteError(instancia.apelido)

        with cadastro.alterando() as rascunho:
            rascunho.itens = (*rascunho.itens, instancia)
            rascunho.padrao = rascunho.padrao or instancia.id

        return self.salvar(cadastro)

    def atualizar(self, instancia: Instancia) -> ConfigInstancias:
        """Substitui uma instância cadastrada, mantendo a posição dela na lista.

        A instância é achada pelo id, e por isso o apelido pode mudar: só não
        pode ser o de outra instância.

        Raises:
            InstanciaNaoEncontradaError: Se nenhuma instância tem esse id.
            InstanciaJaExisteError: Se o apelido novo já é de outra instância.
            CadastroInvalidoError: Se o que estava gravado não corresponde ao formato.
            ArquivoNaoGravavelError: Se o arquivo não pôde ser gravado.

        """
        cadastro = self.carregar()

        if cadastro.obter(instancia.id) is None:
            raise InstanciaNaoEncontradaError(instancia.id)

        dona_do_apelido = cadastro.obter_pelo_apelido(instancia.apelido)

        if dona_do_apelido is not None and dona_do_apelido.id != instancia.id:
            raise InstanciaJaExisteError(instancia.apelido)

        cadastro.itens = tuple(
            instancia
            if cadastrada.id == instancia.id else cadastrada
            for cadastrada in cadastro.itens
        )  # fmt: off

        return self.salvar(cadastro)

    def remover(self, id_da_instancia: UUID) -> ConfigInstancias:
        """Remove uma instância cadastrada.

        Remover a que era a padrão deixa o cadastro sem padrão: eleger uma
        sucessora é escolha do usuário, e não do serviço.

        Raises:
            InstanciaNaoEncontradaError: Se nenhuma instância tem esse id.
            CadastroInvalidoError: Se o que estava gravado não corresponde ao formato.
            ArquivoNaoGravavelError: Se o arquivo não pôde ser gravado.

        """
        cadastro = self.carregar()

        if cadastro.obter(id_da_instancia) is None:
            raise InstanciaNaoEncontradaError(id_da_instancia)

        restantes = tuple(cadastrada for cadastrada in cadastro.itens if cadastrada.id != id_da_instancia)
        padrao = None if cadastro.padrao == id_da_instancia else cadastro.padrao

        with cadastro.alterando() as rascunho:
            rascunho.itens = restantes
            rascunho.padrao = padrao

        return self.salvar(cadastro)

    def definir_padrao(self, id_da_instancia: UUID) -> ConfigInstancias:
        """Escolhe a instância padrão: a que o aplicativo usa para ler os backups.

        Raises:
            InstanciaNaoEncontradaError: Se nenhuma instância tem esse id.
            CadastroInvalidoError: Se o que estava gravado não corresponde ao formato.
            ArquivoNaoGravavelError: Se o arquivo não pôde ser gravado.

        """
        cadastro = self.carregar()

        if cadastro.obter(id_da_instancia) is None:
            raise InstanciaNaoEncontradaError(id_da_instancia)

        cadastro.padrao = id_da_instancia

        return self.salvar(cadastro)
