from collections.abc import Callable
from pathlib import Path

import pytest

from bakrestorer.core.config import (
    ConfigService,
    Configuracao,
    ConfiguracaoInvalidaError,
    Instancia,
    InstanciaEhPadraoError,
    InstanciaJaExisteError,
    InstanciaNaoEncontradaError,
)
from bakrestorer.infra.json_file import ArquivoCorrompidoError


class TestCaminho:
    """Cobre `caminho`."""

    def test_dado_um_servico_quando_perguntar_o_caminho_entao_ele_e_o_do_arquivo_configurado(
        self,
        config_service: ConfigService,
        caminho_da_config: Path,
    ) -> None:
        assert config_service.caminho == caminho_da_config


class TestCarregar:
    """Cobre `carregar`."""

    def test_dado_que_o_arquivo_nao_existe_quando_carregar_entao_a_resposta_e_nula(
        self,
        config_service: ConfigService,
    ) -> None:
        assert config_service.carregar() is None

    def test_dada_uma_configuracao_gravada_quando_carregar_entao_ela_volta_igual(
        self,
        config_service: ConfigService,
        caminho_da_config: Path,
        nova_instancia: Callable[..., Instancia],
    ) -> None:
        gravada = config_service.adicionar_instancia(nova_instancia("PROD"))

        assert ConfigService(caminho_da_config).carregar() == gravada

    def test_dado_um_arquivo_sem_nenhuma_instancia_quando_carregar_entao_a_resposta_nao_e_nula(
        self,
        config_service: ConfigService,
        nova_instancia: Callable[..., Instancia],
    ) -> None:
        config_service.adicionar_instancia(nova_instancia("PROD"))
        config_service.remover_instancia("PROD")

        assert config_service.carregar() == Configuracao()

    def test_dada_uma_instancia_com_acento_e_pastas_quando_carregar_entao_tudo_volta_como_foi_gravado(
        self,
        config_service: ConfigService,
        caminho_da_config: Path,
        nova_instancia: Callable[..., Instancia],
    ) -> None:
        instancia = nova_instancia("Produção", pasta_dados=r"D:\dados", pasta_log=r"E:\log")
        gravada = config_service.adicionar_instancia(instancia)

        assert ConfigService(caminho_da_config).carregar() == gravada

    @pytest.mark.parametrize(
        "gravado",
        ["", "   \n", "{quebrado", "não é json"],
    )
    def test_dado_um_arquivo_que_nao_e_json_quando_carregar_entao_a_falha_e_de_arquivo_corrompido(
        self,
        config_service: ConfigService,
        caminho_da_config: Path,
        gravado: str,
    ) -> None:
        caminho_da_config.write_text(gravado, encoding="utf-8")

        with pytest.raises(ArquivoCorrompidoError):
            config_service.carregar()

    @pytest.mark.parametrize(
        "gravado",
        ["[1, 2]", "null", "42", '{"campo_que_nao_existe": 1}'],
    )
    def test_dado_um_json_fora_do_formato_quando_carregar_entao_a_falha_e_de_configuracao_invalida(
        self,
        config_service: ConfigService,
        caminho_da_config: Path,
        gravado: str,
    ) -> None:
        caminho_da_config.write_text(gravado, encoding="utf-8")

        with pytest.raises(ConfiguracaoInvalidaError):
            config_service.carregar()


class TestSalvar:
    """Cobre `salvar`."""

    def test_dada_uma_pasta_que_ainda_nao_existe_quando_salvar_entao_ela_e_criada(
        self,
        tmp_path: Path,
    ) -> None:
        servico = ConfigService(tmp_path / "ainda" / "nao" / "existe" / "config.json")

        servico.salvar(Configuracao())

        assert servico.carregar() == Configuracao()

    def test_dada_uma_configuracao_ja_gravada_quando_salvar_outra_entao_a_anterior_e_substituida(
        self,
        config_service: ConfigService,
        nova_instancia: Callable[..., Instancia],
    ) -> None:
        config_service.adicionar_instancia(nova_instancia("PROD"))

        config_service.salvar(Configuracao())

        assert config_service.carregar() == Configuracao()


class TestAdicionarInstancia:
    """Cobre `adicionar_instancia`."""

    def test_dada_a_primeira_instancia_quando_adicionar_entao_ela_vira_a_padrao(
        self,
        config_service: ConfigService,
        nova_instancia: Callable[..., Instancia],
    ) -> None:
        assert config_service.adicionar_instancia(nova_instancia("PROD")).instancia_padrao == "PROD"

    def test_dada_uma_padrao_ja_escolhida_quando_adicionar_outra_entao_a_padrao_nao_muda(
        self,
        config_service: ConfigService,
        nova_instancia: Callable[..., Instancia],
    ) -> None:
        config_service.adicionar_instancia(nova_instancia("PROD"))

        assert config_service.adicionar_instancia(nova_instancia("HOMOLOG")).instancia_padrao == "PROD"

    def test_dada_uma_configuracao_sem_padrao_quando_adicionar_entao_a_nova_assume(
        self,
        config_service: ConfigService,
        caminho_da_config: Path,
        nova_instancia: Callable[..., Instancia],
    ) -> None:
        caminho_da_config.write_text('{"instancia_padrao": null, "instancias": []}', encoding="utf-8")

        assert config_service.adicionar_instancia(nova_instancia("PROD")).instancia_padrao == "PROD"

    def test_dadas_varias_instancias_quando_adicionar_entao_a_ordem_de_criacao_e_mantida(
        self,
        config_service: ConfigService,
        nova_instancia: Callable[..., Instancia],
    ) -> None:
        for alias in ("PROD", "HOMOLOG", "DEV"):
            configuracao = config_service.adicionar_instancia(nova_instancia(alias))

        assert [instancia.alias for instancia in configuracao.instancias] == ["PROD", "HOMOLOG", "DEV"]

    def test_dado_um_alias_ja_configurado_quando_adicionar_entao_a_operacao_e_recusada(
        self,
        config_service: ConfigService,
        nova_instancia: Callable[..., Instancia],
    ) -> None:
        config_service.adicionar_instancia(nova_instancia("PROD", senha="original"))

        with pytest.raises(InstanciaJaExisteError) as falha:
            config_service.adicionar_instancia(nova_instancia("PROD", senha="outra"))

        assert falha.value.alias == "PROD"

    def test_dado_um_alias_ja_configurado_quando_adicionar_entao_nada_do_que_estava_gravado_muda(
        self,
        config_service: ConfigService,
        nova_instancia: Callable[..., Instancia],
    ) -> None:
        gravada = config_service.adicionar_instancia(nova_instancia("PROD", senha="original"))

        with pytest.raises(InstanciaJaExisteError):
            config_service.adicionar_instancia(nova_instancia("PROD", senha="outra"))

        assert config_service.carregar() == gravada


class TestAtualizarInstancia:
    """Cobre `atualizar_instancia`."""

    def test_dada_uma_instancia_configurada_quando_atualizar_entao_os_valores_novos_sao_gravados(
        self,
        config_service: ConfigService,
        nova_instancia: Callable[..., Instancia],
    ) -> None:
        config_service.adicionar_instancia(nova_instancia("PROD", senha="antiga"))

        atualizada = nova_instancia("PROD", senha="nova")

        assert config_service.atualizar_instancia(atualizada).obter_instancia("PROD") == atualizada

    def test_dada_uma_instancia_no_meio_da_lista_quando_atualizar_entao_a_posicao_dela_e_mantida(
        self,
        config_service: ConfigService,
        nova_instancia: Callable[..., Instancia],
    ) -> None:
        for alias in ("PROD", "HOMOLOG", "DEV"):
            config_service.adicionar_instancia(nova_instancia(alias))

        configuracao = config_service.atualizar_instancia(nova_instancia("HOMOLOG", senha="nova"))

        assert [instancia.alias for instancia in configuracao.instancias] == ["PROD", "HOMOLOG", "DEV"]

    def test_dado_um_alias_desconhecido_quando_atualizar_entao_a_operacao_e_recusada(
        self,
        config_service: ConfigService,
        nova_instancia: Callable[..., Instancia],
    ) -> None:
        with pytest.raises(InstanciaNaoEncontradaError) as falha:
            config_service.atualizar_instancia(nova_instancia("FANTASMA"))

        assert falha.value.alias == "FANTASMA"


class TestRemoverInstancia:
    """Cobre `remover_instancia`."""

    def test_dada_uma_instancia_que_nao_e_a_padrao_quando_remover_entao_ela_sai_e_a_padrao_segue(
        self,
        config_service: ConfigService,
        nova_instancia: Callable[..., Instancia],
    ) -> None:
        config_service.adicionar_instancia(nova_instancia("PROD"))
        config_service.adicionar_instancia(nova_instancia("HOMOLOG"))

        configuracao = config_service.remover_instancia("HOMOLOG")

        assert ([i.alias for i in configuracao.instancias], configuracao.instancia_padrao) == (["PROD"], "PROD")

    def test_dada_a_instancia_padrao_com_outras_configuradas_quando_remover_entao_a_operacao_e_recusada(
        self,
        config_service: ConfigService,
        nova_instancia: Callable[..., Instancia],
    ) -> None:
        config_service.adicionar_instancia(nova_instancia("PROD"))
        config_service.adicionar_instancia(nova_instancia("HOMOLOG"))

        with pytest.raises(InstanciaEhPadraoError) as falha:
            config_service.remover_instancia("PROD")

        assert falha.value.alias == "PROD"

    def test_dada_a_instancia_padrao_sendo_a_ultima_quando_remover_entao_a_configuracao_fica_sem_padrao(
        self,
        config_service: ConfigService,
        nova_instancia: Callable[..., Instancia],
    ) -> None:
        config_service.adicionar_instancia(nova_instancia("PROD"))

        configuracao = config_service.remover_instancia("PROD")

        assert (configuracao.instancias, configuracao.instancia_padrao) == ((), None)

    def test_dado_um_alias_desconhecido_quando_remover_entao_a_operacao_e_recusada(
        self,
        config_service: ConfigService,
    ) -> None:
        with pytest.raises(InstanciaNaoEncontradaError):
            config_service.remover_instancia("FANTASMA")


class TestDefinirInstanciaPadrao:
    """Cobre `definir_instancia_padrao`."""

    def test_dada_outra_instancia_configurada_quando_defini_la_como_padrao_entao_a_escolha_e_gravada(
        self,
        config_service: ConfigService,
        caminho_da_config: Path,
        nova_instancia: Callable[..., Instancia],
    ) -> None:
        config_service.adicionar_instancia(nova_instancia("PROD"))
        config_service.adicionar_instancia(nova_instancia("HOMOLOG"))

        gravada = config_service.definir_instancia_padrao("HOMOLOG")

        assert ConfigService(caminho_da_config).carregar() == gravada

    def test_dado_um_alias_desconhecido_quando_defini_lo_como_padrao_entao_a_operacao_e_recusada(
        self,
        config_service: ConfigService,
        nova_instancia: Callable[..., Instancia],
    ) -> None:
        config_service.adicionar_instancia(nova_instancia("PROD"))

        with pytest.raises(InstanciaNaoEncontradaError):
            config_service.definir_instancia_padrao("FANTASMA")
