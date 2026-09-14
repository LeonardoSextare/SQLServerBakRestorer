from collections.abc import Callable
from pathlib import Path

import pytest
from bakrestorer.features.instancias import (
    CadastroInvalidoError,
    ConfigInstancias,
    Instancia,
    InstanciaJaExisteError,
    InstanciaNaoEncontradaError,
    InstanciasService,
    criar_service,
)
from bakrestorer.infra.config_json import ArquivoCorrompidoError


class TestCarregar:
    """Cobre `carregar`."""

    def test_dado_que_o_arquivo_nao_existe_quando_carregar_entao_o_cadastro_volta_vazio(
        self,
        servico_de_instancias: InstanciasService,
    ) -> None:
        assert servico_de_instancias.carregar() == ConfigInstancias()

    def test_dado_um_arquivo_so_com_a_parte_de_outra_dona_quando_carregar_entao_o_cadastro_volta_vazio(
        self,
        servico_de_instancias: InstanciasService,
        caminho_da_config: Path,
    ) -> None:
        caminho_da_config.write_text('{"gui": {"tema": "escuro"}}', encoding="utf-8")

        assert servico_de_instancias.carregar() == ConfigInstancias()

    def test_dado_um_cadastro_gravado_quando_carregar_entao_ele_volta_igual(
        self,
        servico_de_instancias: InstanciasService,
        caminho_da_config: Path,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        gravado = servico_de_instancias.adicionar(criar_instancia("PROD"))

        assert criar_service(caminho_da_config).carregar() == gravado

    def test_dado_um_cadastro_sem_nenhuma_instancia_quando_carregar_entao_a_resposta_nao_e_nula(
        self,
        servico_de_instancias: InstanciasService,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        servico_de_instancias.adicionar(criar_instancia("PROD"))
        servico_de_instancias.remover("PROD")

        assert servico_de_instancias.carregar() == ConfigInstancias()

    def test_dada_uma_instancia_com_acento_e_pastas_quando_carregar_entao_tudo_volta_como_foi_gravado(
        self,
        servico_de_instancias: InstanciasService,
        caminho_da_config: Path,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        instancia = criar_instancia("Produção", pasta_dados=r"D:\dados", pasta_log=r"E:\log")
        gravado = servico_de_instancias.adicionar(instancia)

        assert criar_service(caminho_da_config).carregar() == gravado

    @pytest.mark.parametrize(
        "gravado",
        ["", "   \n", "{quebrado", "não é json", "[1, 2]", "42", "null"],
    )
    def test_dado_um_arquivo_que_nao_guarda_um_objeto_json_quando_carregar_entao_a_falha_e_de_arquivo_corrompido(
        self,
        servico_de_instancias: InstanciasService,
        caminho_da_config: Path,
        gravado: str,
    ) -> None:
        caminho_da_config.write_text(gravado, encoding="utf-8")

        with pytest.raises(ArquivoCorrompidoError):
            servico_de_instancias.carregar()

    @pytest.mark.parametrize(
        "gravado",
        ['{"instancias": [1, 2]}', '{"instancias": 42}', '{"instancias": {"campo_que_nao_existe": 1}}'],
    )
    def test_dada_uma_parte_fora_do_formato_quando_carregar_entao_a_falha_e_de_cadastro_invalido(
        self,
        servico_de_instancias: InstanciasService,
        caminho_da_config: Path,
        gravado: str,
    ) -> None:
        caminho_da_config.write_text(gravado, encoding="utf-8")

        with pytest.raises(CadastroInvalidoError):
            servico_de_instancias.carregar()


class TestSalvar:
    """Cobre `salvar`."""

    def test_dada_uma_pasta_que_ainda_nao_existe_quando_salvar_entao_ela_e_criada(
        self,
        tmp_path: Path,
    ) -> None:
        servico = criar_service(tmp_path / "ainda" / "nao" / "existe" / "config.json")

        servico.salvar(ConfigInstancias())

        assert servico.carregar() == ConfigInstancias()

    def test_dado_um_cadastro_ja_gravado_quando_salvar_outro_entao_o_anterior_e_substituido(
        self,
        servico_de_instancias: InstanciasService,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        servico_de_instancias.adicionar(criar_instancia("PROD"))

        servico_de_instancias.salvar(ConfigInstancias())

        assert servico_de_instancias.carregar() == ConfigInstancias()

    def test_dada_a_parte_de_outra_dona_no_arquivo_quando_salvar_entao_ela_sobrevive(
        self,
        servico_de_instancias: InstanciasService,
        caminho_da_config: Path,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        caminho_da_config.write_text('{"gui": {"tema": "escuro"}}', encoding="utf-8")

        servico_de_instancias.adicionar(criar_instancia("PROD"))

        assert '"gui"' in caminho_da_config.read_text(encoding="utf-8")


class TestAdicionar:
    """Cobre `adicionar`."""

    def test_dada_a_primeira_instancia_quando_adicionar_entao_ela_vira_a_padrao(
        self,
        servico_de_instancias: InstanciasService,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        assert servico_de_instancias.adicionar(criar_instancia("PROD")).padrao == "PROD"

    def test_dada_uma_padrao_ja_escolhida_quando_adicionar_outra_entao_a_padrao_nao_muda(
        self,
        servico_de_instancias: InstanciasService,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        servico_de_instancias.adicionar(criar_instancia("PROD"))

        assert servico_de_instancias.adicionar(criar_instancia("HOMOLOG")).padrao == "PROD"

    def test_dado_um_cadastro_sem_padrao_quando_adicionar_entao_a_nova_assume(
        self,
        servico_de_instancias: InstanciasService,
        caminho_da_config: Path,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        caminho_da_config.write_text('{"instancias": {"padrao": null, "itens": []}}', encoding="utf-8")

        assert servico_de_instancias.adicionar(criar_instancia("PROD")).padrao == "PROD"

    def test_dadas_varias_instancias_quando_adicionar_entao_a_ordem_de_criacao_e_mantida(
        self,
        servico_de_instancias: InstanciasService,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        for alias in ("PROD", "HOMOLOG", "DEV"):
            cadastro = servico_de_instancias.adicionar(criar_instancia(alias))

        assert [instancia.alias for instancia in cadastro.itens] == ["PROD", "HOMOLOG", "DEV"]

    def test_dado_um_alias_ja_cadastrado_quando_adicionar_entao_a_operacao_e_recusada(
        self,
        servico_de_instancias: InstanciasService,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        servico_de_instancias.adicionar(criar_instancia("PROD", senha="original"))

        with pytest.raises(InstanciaJaExisteError) as falha:
            servico_de_instancias.adicionar(criar_instancia("PROD", senha="outra"))

        assert falha.value.alias == "PROD"

    def test_dado_um_alias_ja_cadastrado_quando_adicionar_entao_nada_do_que_estava_gravado_muda(
        self,
        servico_de_instancias: InstanciasService,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        gravado = servico_de_instancias.adicionar(criar_instancia("PROD", senha="original"))

        with pytest.raises(InstanciaJaExisteError):
            servico_de_instancias.adicionar(criar_instancia("PROD", senha="outra"))

        assert servico_de_instancias.carregar() == gravado


class TestAtualizar:
    """Cobre `atualizar`."""

    def test_dada_uma_instancia_cadastrada_quando_atualizar_entao_os_valores_novos_sao_gravados(
        self,
        servico_de_instancias: InstanciasService,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        servico_de_instancias.adicionar(criar_instancia("PROD", senha="antiga"))

        atualizada = criar_instancia("PROD", senha="nova")

        cadastro = servico_de_instancias.atualizar(atualizada)

        assert cadastro.obter("PROD") == atualizada

    def test_dada_uma_instancia_no_meio_da_lista_quando_atualizar_entao_a_posicao_dela_e_mantida(
        self,
        servico_de_instancias: InstanciasService,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        for alias in ("PROD", "HOMOLOG", "DEV"):
            servico_de_instancias.adicionar(criar_instancia(alias))

        cadastro = servico_de_instancias.atualizar(criar_instancia("HOMOLOG", senha="nova"))

        assert [instancia.alias for instancia in cadastro.itens] == ["PROD", "HOMOLOG", "DEV"]

    def test_dado_um_alias_desconhecido_quando_atualizar_entao_a_operacao_e_recusada(
        self,
        servico_de_instancias: InstanciasService,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        with pytest.raises(InstanciaNaoEncontradaError) as falha:
            servico_de_instancias.atualizar(criar_instancia("FANTASMA"))

        assert falha.value.alias == "FANTASMA"


class TestRemover:
    """Cobre `remover`."""

    def test_dada_uma_instancia_que_nao_e_a_padrao_quando_remover_entao_ela_sai_e_a_padrao_segue(
        self,
        servico_de_instancias: InstanciasService,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        servico_de_instancias.adicionar(criar_instancia("PROD"))
        servico_de_instancias.adicionar(criar_instancia("HOMOLOG"))

        cadastro = servico_de_instancias.remover("HOMOLOG")

        assert ([instancia.alias for instancia in cadastro.itens], cadastro.padrao) == (["PROD"], "PROD")

    def test_dada_a_instancia_padrao_com_outras_cadastradas_quando_remover_entao_o_cadastro_fica_sem_padrao(
        self,
        servico_de_instancias: InstanciasService,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        servico_de_instancias.adicionar(criar_instancia("PROD"))
        servico_de_instancias.adicionar(criar_instancia("HOMOLOG"))

        cadastro = servico_de_instancias.remover("PROD")

        assert ([instancia.alias for instancia in cadastro.itens], cadastro.padrao) == (["HOMOLOG"], None)

    def test_dada_a_instancia_padrao_sendo_a_ultima_quando_remover_entao_o_cadastro_fica_sem_padrao(
        self,
        servico_de_instancias: InstanciasService,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        servico_de_instancias.adicionar(criar_instancia("PROD"))

        cadastro = servico_de_instancias.remover("PROD")

        assert (cadastro.itens, cadastro.padrao) == ((), None)

    def test_dado_um_alias_desconhecido_quando_remover_entao_a_operacao_e_recusada(
        self,
        servico_de_instancias: InstanciasService,
    ) -> None:
        with pytest.raises(InstanciaNaoEncontradaError):
            servico_de_instancias.remover("FANTASMA")


class TestDefinirPadrao:
    """Cobre `definir_padrao`."""

    def test_dada_outra_instancia_cadastrada_quando_defini_la_como_padrao_entao_a_escolha_e_gravada(
        self,
        servico_de_instancias: InstanciasService,
        caminho_da_config: Path,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        servico_de_instancias.adicionar(criar_instancia("PROD"))
        servico_de_instancias.adicionar(criar_instancia("HOMOLOG"))

        gravado = servico_de_instancias.definir_padrao("HOMOLOG")

        assert criar_service(caminho_da_config).carregar() == gravado

    def test_dado_um_alias_desconhecido_quando_defini_lo_como_padrao_entao_a_operacao_e_recusada(
        self,
        servico_de_instancias: InstanciasService,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        servico_de_instancias.adicionar(criar_instancia("PROD"))

        with pytest.raises(InstanciaNaoEncontradaError):
            servico_de_instancias.definir_padrao("FANTASMA")
