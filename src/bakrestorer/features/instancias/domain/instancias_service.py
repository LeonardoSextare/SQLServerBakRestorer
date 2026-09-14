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
            InstanciaJaExisteError: Se o alias já está cadastrado.
            CadastroInvalidoError: Se o que estava gravado não corresponde ao formato.
            ArquivoNaoGravavelError: Se o arquivo não pôde ser gravado.

        """
        cadastro = self.carregar()

        if cadastro.obter(instancia.alias) is not None:
            raise InstanciaJaExisteError(instancia.alias)

        with cadastro.alterando() as rascunho:
            rascunho.itens = (*rascunho.itens, instancia)
            rascunho.padrao = rascunho.padrao or instancia.alias

        return self.salvar(cadastro)

    def atualizar(self, instancia: Instancia) -> ConfigInstancias:
        """Substitui uma instância cadastrada, mantendo a posição dela na lista.

        Raises:
            InstanciaNaoEncontradaError: Se o alias não está cadastrado.
            CadastroInvalidoError: Se o que estava gravado não corresponde ao formato.
            ArquivoNaoGravavelError: Se o arquivo não pôde ser gravado.

        """
        cadastro = self.carregar()

        if cadastro.obter(instancia.alias) is None:
            raise InstanciaNaoEncontradaError(instancia.alias)

        cadastro.itens = tuple(
            instancia
            if cadastrada.alias == instancia.alias else cadastrada
            for cadastrada in cadastro.itens
        )  # fmt: off

        return self.salvar(cadastro)

    def remover(self, alias: str) -> ConfigInstancias:
        """Remove uma instância cadastrada.

        Remover a que era a padrão deixa o cadastro sem padrão: eleger uma
        sucessora é escolha do usuário, e não do serviço.

        Raises:
            InstanciaNaoEncontradaError: Se nenhuma instância usa esse alias.
            CadastroInvalidoError: Se o que estava gravado não corresponde ao formato.
            ArquivoNaoGravavelError: Se o arquivo não pôde ser gravado.

        """
        cadastro = self.carregar()

        if cadastro.obter(alias) is None:
            raise InstanciaNaoEncontradaError(alias)

        restantes = tuple(cadastrada for cadastrada in cadastro.itens if cadastrada.alias != alias)
        padrao = None if cadastro.padrao == alias else cadastro.padrao

        with cadastro.alterando() as rascunho:
            rascunho.itens = restantes
            rascunho.padrao = padrao

        return self.salvar(cadastro)

    def definir_padrao(self, alias: str) -> ConfigInstancias:
        """Escolhe qual instância é usada quando nenhuma é informada.

        Raises:
            InstanciaNaoEncontradaError: Se nenhuma instância usa esse alias.
            CadastroInvalidoError: Se o que estava gravado não corresponde ao formato.
            ArquivoNaoGravavelError: Se o arquivo não pôde ser gravado.

        """
        cadastro = self.carregar()

        if cadastro.obter(alias) is None:
            raise InstanciaNaoEncontradaError(alias)

        cadastro.padrao = alias

        return self.salvar(cadastro)
