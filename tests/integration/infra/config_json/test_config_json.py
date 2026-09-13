import json
from pathlib import Path

import pytest
from bakrestorer.infra.config_json import (
    ArquivoCorrompidoError,
    ArquivoNaoEncontradoError,
    ArquivoNaoGravavelError,
    ConfigJson,
    ConfigJsonError,
)


class TestCaminho:
    """Cobre `caminho`."""

    def test_dado_um_arquivo_inexistente_quando_perguntar_o_caminho_entao_ele_e_devolvido(
        self,
        config_de_instancias: ConfigJson,
        caminho_do_arquivo: Path,
    ) -> None:
        assert config_de_instancias.caminho == caminho_do_arquivo


class TestLer:
    """Cobre `ler`."""

    @pytest.mark.parametrize(
        ("gravado", "esperado"),
        [
            ('{"instancias": {"alias": "PROD"}}', {"alias": "PROD"}),
            ('{"instancias": [1, 2, 3]}', [1, 2, 3]),
            ('{"instancias": 42}', 42),
            ('{"instancias": "texto"}', "texto"),
            ('{"instancias": true}', True),
        ],
    )
    def test_dado_qualquer_tipo_de_json_na_secao_quando_ler_entao_o_valor_volta_igual(
        self,
        config_de_instancias: ConfigJson,
        caminho_do_arquivo: Path,
        gravado: str,
        esperado: object,
    ) -> None:
        caminho_do_arquivo.write_text(gravado, encoding="utf-8")

        assert config_de_instancias.ler() == esperado

    def test_dado_arquivo_gravado_em_utf8_quando_ler_entao_o_acento_volta_intacto(
        self,
        config_de_instancias: ConfigJson,
        caminho_do_arquivo: Path,
    ) -> None:
        caminho_do_arquivo.write_text('{"instancias": {"alias": "Produção"}}', encoding="utf-8")

        assert config_de_instancias.ler() == {"alias": "Produção"}

    def test_dada_uma_secao_ausente_no_arquivo_quando_ler_entao_a_resposta_e_nada(
        self,
        caminho_do_arquivo: Path,
    ) -> None:
        caminho_do_arquivo.write_text('{"instancias": {"alias": "PROD"}}', encoding="utf-8")

        assert ConfigJson(caminho_do_arquivo, "automacao").ler() is None

    def test_dada_uma_secao_gravada_como_nulo_quando_ler_entao_a_resposta_e_nada(
        self,
        config_de_instancias: ConfigJson,
        caminho_do_arquivo: Path,
    ) -> None:
        caminho_do_arquivo.write_text('{"instancias": null}', encoding="utf-8")

        assert config_de_instancias.ler() is None

    def test_dado_arquivo_ausente_quando_ler_entao_a_leitura_e_recusada(
        self,
        config_de_instancias: ConfigJson,
        caminho_do_arquivo: Path,
    ) -> None:
        with pytest.raises(ArquivoNaoEncontradoError) as falha:
            config_de_instancias.ler()

        assert falha.value.caminho == caminho_do_arquivo

    def test_dado_que_uma_pasta_ocupa_o_lugar_do_arquivo_quando_ler_entao_conta_como_ausencia(
        self,
        tmp_path: Path,
    ) -> None:
        pasta = tmp_path / "config.json"
        pasta.mkdir()

        with pytest.raises(ArquivoNaoEncontradoError):
            ConfigJson(pasta, "instancias").ler()

    def test_dado_json_malformado_quando_ler_entao_a_falha_e_de_corrupcao(
        self,
        config_de_instancias: ConfigJson,
        caminho_do_arquivo: Path,
    ) -> None:
        caminho_do_arquivo.write_text('{"instancias": ', encoding="utf-8")

        with pytest.raises(ArquivoCorrompidoError) as falha:
            config_de_instancias.ler()

        assert falha.value.caminho == caminho_do_arquivo

    def test_dado_conteudo_fora_de_utf8_quando_ler_entao_a_falha_e_de_corrupcao(
        self,
        config_de_instancias: ConfigJson,
        caminho_do_arquivo: Path,
    ) -> None:
        caminho_do_arquivo.write_bytes(b"\xff\xfe\x00")

        with pytest.raises(ArquivoCorrompidoError):
            config_de_instancias.ler()

    @pytest.mark.parametrize("gravado", ["[1, 2, 3]", "42", '"texto"', "null"])
    def test_dado_json_valido_que_nao_e_mapa_de_secoes_quando_ler_entao_a_falha_e_de_corrupcao(
        self,
        config_de_instancias: ConfigJson,
        caminho_do_arquivo: Path,
        gravado: str,
    ) -> None:
        caminho_do_arquivo.write_text(gravado, encoding="utf-8")

        with pytest.raises(ArquivoCorrompidoError):
            config_de_instancias.ler()


class TestGravar:
    """Cobre `gravar`."""

    def test_dado_arquivo_ainda_inexistente_quando_gravar_entao_ele_nasce_com_a_secao(
        self,
        config_de_instancias: ConfigJson,
    ) -> None:
        config_de_instancias.gravar({"alias": "PROD"})

        assert config_de_instancias.ler() == {"alias": "PROD"}

    def test_dada_a_secao_vizinha_ja_gravada_quando_gravar_entao_ela_sobrevive(
        self,
        config_de_instancias: ConfigJson,
        config_de_gui: ConfigJson,
    ) -> None:
        config_de_instancias.gravar({"alias": "PROD"})
        config_de_gui.gravar({"tema": "escuro"})

        config_de_instancias.gravar({"alias": "HOMOLOG"})

        assert config_de_gui.ler() == {"tema": "escuro"}

    def test_dada_a_secao_ja_gravada_quando_gravar_de_novo_entao_o_conteudo_anterior_e_substituido(
        self,
        config_de_instancias: ConfigJson,
    ) -> None:
        config_de_instancias.gravar({"alias": "PROD"})

        config_de_instancias.gravar({"alias": "HOMOLOG"})

        assert config_de_instancias.ler() == {"alias": "HOMOLOG"}

    def test_dado_um_texto_com_acento_quando_gravar_entao_o_arquivo_sai_em_utf8_sem_escape(
        self,
        config_de_instancias: ConfigJson,
        caminho_do_arquivo: Path,
    ) -> None:
        config_de_instancias.gravar({"alias": "Produção"})

        assert "Produção" in caminho_do_arquivo.read_text(encoding="utf-8")

    def test_dado_um_caminho_com_pastas_inexistentes_quando_gravar_entao_elas_sao_criadas(
        self,
        tmp_path: Path,
    ) -> None:
        config_em_pasta_funda = ConfigJson(tmp_path / "ainda" / "nao" / "existe" / "config.json", "instancias")

        config_em_pasta_funda.gravar({"alias": "PROD"})

        assert config_em_pasta_funda.ler() == {"alias": "PROD"}

    def test_dado_um_caminho_livre_quando_gravar_entao_nenhum_temporario_sobra(
        self,
        config_de_instancias: ConfigJson,
        caminho_do_arquivo: Path,
    ) -> None:
        config_de_instancias.gravar({"alias": "PROD"})

        assert [arquivo.name for arquivo in caminho_do_arquivo.parent.iterdir()] == ["config.json"]

    def test_dado_um_valor_sem_representacao_json_quando_gravar_entao_a_gravacao_e_recusada(
        self,
        config_de_instancias: ConfigJson,
        caminho_do_arquivo: Path,
    ) -> None:
        with pytest.raises(ArquivoNaoGravavelError) as falha:
            config_de_instancias.gravar({"alias": object()})

        assert falha.value.caminho == caminho_do_arquivo

    def test_dado_que_a_estrutura_referencia_a_si_mesma_quando_gravar_entao_a_gravacao_e_recusada(
        self,
        config_de_instancias: ConfigJson,
    ) -> None:
        circular: dict[str, object] = {}
        circular["ele_mesmo"] = circular

        with pytest.raises(ArquivoNaoGravavelError):
            config_de_instancias.gravar(circular)

    def test_dado_arquivo_ja_gravado_quando_gravar_valor_invalido_entao_o_conteudo_anterior_sobrevive(
        self,
        config_de_instancias: ConfigJson,
    ) -> None:
        config_de_instancias.gravar({"alias": "PROD"})

        with pytest.raises(ArquivoNaoGravavelError):
            config_de_instancias.gravar({"alias": object()})

        assert config_de_instancias.ler() == {"alias": "PROD"}

    def test_dado_arquivo_corrompido_quando_gravar_entao_a_gravacao_e_recusada_sem_apagar_nada(
        self,
        config_de_instancias: ConfigJson,
        caminho_do_arquivo: Path,
    ) -> None:
        caminho_do_arquivo.write_text("nao sou json", encoding="utf-8")

        with pytest.raises(ArquivoCorrompidoError):
            config_de_instancias.gravar({"alias": "PROD"})

        assert caminho_do_arquivo.read_text(encoding="utf-8") == "nao sou json"

    def test_dado_um_arquivo_ocupando_o_lugar_de_uma_pasta_quando_gravar_entao_a_gravacao_e_recusada(
        self,
        tmp_path: Path,
    ) -> None:
        ocupado = tmp_path / "ocupado"
        ocupado.write_text("nao sou pasta", encoding="utf-8")

        with pytest.raises(ArquivoNaoGravavelError):
            ConfigJson(ocupado / "config.json", "instancias").gravar({"alias": "PROD"})

    def test_dado_que_o_destino_e_uma_pasta_quando_gravar_entao_nenhum_temporario_sobra(
        self,
        tmp_path: Path,
    ) -> None:
        destino_ocupado_por_pasta = tmp_path / "config.json"
        destino_ocupado_por_pasta.mkdir()

        with pytest.raises(ArquivoNaoGravavelError):
            ConfigJson(destino_ocupado_por_pasta, "instancias").gravar({"alias": "PROD"})

        assert [arquivo.name for arquivo in tmp_path.iterdir()] == ["config.json"]


class TestHierarquiaDeExcecoes:
    """Cobre a hierarquia que o pacote expõe a quem trata as falhas."""

    @pytest.mark.parametrize(
        "excecao",
        [ArquivoNaoEncontradoError, ArquivoCorrompidoError, ArquivoNaoGravavelError],
    )
    def test_dado_qualquer_erro_do_pacote_entao_ele_pode_ser_tratado_como_config_json_error(
        self,
        excecao: type[ConfigJsonError],
    ) -> None:
        assert issubclass(excecao, ConfigJsonError)

    def test_dado_um_erro_do_pacote_quando_convertido_em_texto_entao_ele_carrega_o_caminho(
        self,
        config_de_instancias: ConfigJson,
        caminho_do_arquivo: Path,
    ) -> None:
        with pytest.raises(ConfigJsonError) as falha:
            config_de_instancias.ler()

        assert str(caminho_do_arquivo) in str(falha.value)


class TestFormatoGravado:
    """Cobre o formato do arquivo, que é editado à mão durante o desenvolvimento."""

    def test_dadas_duas_secoes_gravadas_quando_ler_o_arquivo_entao_ele_esta_indentado(
        self,
        config_de_instancias: ConfigJson,
        config_de_gui: ConfigJson,
        caminho_do_arquivo: Path,
    ) -> None:
        config_de_instancias.gravar({"alias": "PROD"})
        config_de_gui.gravar({"tema": "escuro"})

        assert caminho_do_arquivo.read_text(encoding="utf-8") == json.dumps(
            {"instancias": {"alias": "PROD"}, "gui": {"tema": "escuro"}},
            indent=2,
            ensure_ascii=False,
        )
