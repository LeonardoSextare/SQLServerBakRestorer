from pathlib import Path

from pydantic import ValidationError

from bakrestorer.core.config.exceptions import (
    ConfiguracaoInvalidaError,
    InstanciaEhPadraoError,
    InstanciaJaExisteError,
    InstanciaNaoEncontradaError,
)
from bakrestorer.core.config.models import Configuracao, Instancia
from bakrestorer.core.infra import json_file


class ConfigService:
    """Lê e altera a configuração do aplicativo.

    Não guarda estado: cada operação lê o arquivo, decide e grava. Assim nada
    fica desatualizado em relação ao disco, e quem chama é dono do que carregou.

    Toda alteração devolve a configuração inteira já gravada, porque ela é um
    documento só -- não há gravação parcial.
    """

    def __init__(self, caminho: Path) -> None:
        """Cria o serviço, ainda sem ler o arquivo.

        Args:
            caminho: Arquivo onde a configuração é gravada.

        """
        self._caminho = caminho

    @property
    def caminho(self) -> Path:
        """Diz onde a configuração é gravada.

        Returns:
            Path: O arquivo, que pode ainda não existir.

        """
        return self._caminho

    def carregar(self) -> Configuracao | None:
        """Lê a configuração gravada.

        Returns:
            Configuracao: A configuração gravada.
            None: Quando o arquivo ainda não existe, o que marca a primeira execução.

        Raises:
            ArquivoNaoLegivelError: Se o sistema recusou a leitura.
            ArquivoCorrompidoError: Se o gravado não é json em utf-8, o que
                inclui o arquivo de tamanho zero.
            ConfiguracaoInvalidaError: Se o conteúdo não corresponde ao formato.

        """
        try:
            gravada = json_file.carregar(self._caminho)
        except json_file.ArquivoNaoEncontradoError:
            return None

        return self._validar(gravada)

    def salvar(self, configuracao: Configuracao) -> Configuracao:
        """Grava a configuração inteira e a adota como a em vigor.

        Args:
            configuracao: Configuração a gravar.

        Returns:
            Configuracao: A configuração gravada.

        Raises:
            ArquivoNaoGravavelError: Se o arquivo não pôde ser gravado, deixando
                o conteúdo anterior intacto.

        """
        json_file.salvar(self._caminho, configuracao.model_dump(mode="json"))

        return configuracao

    def adicionar_instancia(self, instancia: Instancia) -> Configuracao:
        """Acrescenta uma instância à configuração.

        Vira a instância padrão quando ainda não há uma configurada.

        Args:
            instancia: Instância a guardar.

        Returns:
            Configuracao: A configuração gravada.

        Raises:
            InstanciaJaExisteError: Se o alias já está configurado.
            ArquivoNaoGravavelError: Se o arquivo não pôde ser gravado.

        """
        config_atual = self.carregar() or Configuracao()

        if config_atual.obter_instancia(instancia.alias) is not None:
            raise InstanciaJaExisteError(instancia.alias)

        instancia_padrao = config_atual.instancia_padrao or instancia.alias

        return self.salvar(
            config_atual.alterada(
                instancias=(*config_atual.instancias, instancia),
                instancia_padrao=instancia_padrao,
            ),
        )

    def atualizar_instancia(self, instancia: Instancia) -> Configuracao:
        """Substitui uma instância configurada, mantendo a posição dela na lista.

        Args:
            instancia: Instância com o alias a substituir e os valores novos.

        Returns:
            Configuracao: A configuração gravada.

        Raises:
            InstanciaNaoEncontradaError: Se o alias não está configurado.
            ArquivoNaoGravavelError: Se o arquivo não pôde ser gravado.

        """
        config_atual = self.carregar() or Configuracao()

        if config_atual.obter_instancia(instancia.alias) is None:
            raise InstanciaNaoEncontradaError(instancia.alias)

        instancias_atualizadas = tuple(
            instancia if instancia_configurada.alias == instancia.alias else instancia_configurada
            for instancia_configurada in config_atual.instancias
        )

        return self.salvar(config_atual.alterada(instancias=instancias_atualizadas))

    def remover_instancia(self, alias: str) -> Configuracao:
        """Remove uma instância configurada.

        A padrão só sai quando é a última: com outras configuradas, removê-la
        exigiria eleger uma sucessora, e essa escolha é do usuário.

        Args:
            alias: Alias da instância a remover.

        Returns:
            Configuracao: A configuração gravada.

        Raises:
            InstanciaNaoEncontradaError: Se nenhuma instância usa esse alias.
            InstanciaEhPadraoError: Se é a padrão e há outras configuradas.
            ArquivoNaoGravavelError: Se o arquivo não pôde ser gravado.

        """
        config_atual = self.carregar() or Configuracao()

        if config_atual.obter_instancia(alias) is None:
            raise InstanciaNaoEncontradaError(alias)

        instancias_restantes = tuple(
            instancia_configurada
            for instancia_configurada in config_atual.instancias
            if instancia_configurada.alias != alias
        )

        if alias == config_atual.instancia_padrao and instancias_restantes:
            raise InstanciaEhPadraoError(alias)

        return self.salvar(
            config_atual.alterada(
                instancias=instancias_restantes,
                instancia_padrao=config_atual.instancia_padrao if instancias_restantes else None,
            ),
        )

    def definir_instancia_padrao(self, alias: str) -> Configuracao:
        """Escolhe qual instância é usada quando nenhuma é informada.

        Args:
            alias: Alias de uma instância já configurada.

        Returns:
            Configuracao: A configuração gravada.

        Raises:
            InstanciaNaoEncontradaError: Se nenhuma instância usa esse alias.
            ArquivoNaoGravavelError: Se o arquivo não pôde ser gravado.

        """
        config_atual = self.carregar() or Configuracao()

        if config_atual.obter_instancia(alias) is None:
            raise InstanciaNaoEncontradaError(alias)

        return self.salvar(config_atual.alterada(instancia_padrao=alias))

    def _validar(self, gravado: object) -> Configuracao:
        """Confere se o que estava gravado corresponde ao formato da configuração.

        Args:
            gravado: O valor lido do arquivo, de qualquer tipo que o json aceite.

        Returns:
            Configuracao: A configuração validada.

        Raises:
            ConfiguracaoInvalidaError: Se o valor não é um objeto, ou se algum
                campo não corresponde ao formato.

        """
        if not isinstance(gravado, dict):
            mensagem = f"o arquivo guarda {type(gravado).__name__}, e a configuração precisa ser um objeto"
            raise ConfiguracaoInvalidaError(mensagem)

        try:
            return Configuracao.model_validate(gravado)
        except ValidationError as falha:
            raise ConfiguracaoInvalidaError(str(falha)) from falha
