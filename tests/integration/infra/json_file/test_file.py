import json
from pathlib import Path

import pytest

from bakrestorer.core.exceptions import BakRestorerError
from bakrestorer.infra.json_file import (
    ArquivoCorrompidoError,
    ArquivoJsonError,
    ArquivoNaoEncontradoError,
    ArquivoNaoGravavelError,
    carregar,
    salvar,
)


class TestCarregar:
    """Cobre `carregar`."""

    @pytest.mark.parametrize(
        ("gravado", "esperado"),
        [
            ('{"alias": "PROD"}', {"alias": "PROD"}),
            ("[1, 2, 3]", [1, 2, 3]),
            ("42", 42),
            ('"texto"', "texto"),
            ("true", True),
            ("null", None),
        ],
    )
    def test_dado_qualquer_tipo_de_json_quando_carregar_entao_o_valor_e_devolvido_corretamente(
        self,
        caminho_do_arquivo: Path,
        gravado: str,
        esperado: object,
    ) -> None:
        caminho_do_arquivo.write_text(gravado, encoding="utf-8")

        assert carregar(caminho_do_arquivo) == esperado

    def test_dado_arquivo_gravado_em_utf8_quando_carregar_entao_o_acento_volta_intacto(
        self,
        arquivo_com_conteudo: Path,
    ) -> None:
        assert carregar(arquivo_com_conteudo) == {"alias": "Produção"}

    def test_dado_arquivo_ausente_quando_carregar_entao_a_leitura_e_recusada(
        self,
        caminho_do_arquivo: Path,
    ) -> None:
        with pytest.raises(ArquivoNaoEncontradoError) as falha:
            carregar(caminho_do_arquivo)

        assert falha.value.caminho == caminho_do_arquivo

    def test_dado_que_uma_pasta_ocupa_o_lugar_do_arquivo_quando_carregar_entao_conta_como_ausencia(
        self,
        tmp_path: Path,
    ) -> None:
        pasta = tmp_path / "config.json"
        pasta.mkdir()

        with pytest.raises(ArquivoNaoEncontradoError):
            carregar(pasta)

    def test_dado_json_malformado_quando_carregar_entao_a_falha_e_de_corrupcao(
        self,
        caminho_do_arquivo: Path,
    ) -> None:
        caminho_do_arquivo.write_text('{"alias": ', encoding="utf-8")

        with pytest.raises(ArquivoCorrompidoError) as falha:
            carregar(caminho_do_arquivo)

        assert falha.value.caminho == caminho_do_arquivo

    def test_dado_conteudo_fora_de_utf8_quando_carregar_entao_a_falha_e_de_corrupcao(
        self,
        caminho_do_arquivo: Path,
    ) -> None:
        caminho_do_arquivo.write_bytes(b"\xff\xfe\x00")

        with pytest.raises(ArquivoCorrompidoError):
            carregar(caminho_do_arquivo)


class TestSalvar:
    """Cobre `salvar`."""

    def test_dado_um_valor_qualquer_quando_salvar_entao_a_leitura_devolve_o_mesmo(
        self,
        caminho_do_arquivo: Path,
    ) -> None:
        salvar(caminho_do_arquivo, {"alias": "Produção", "instancias": [1, 2]})

        assert carregar(caminho_do_arquivo) == {"alias": "Produção", "instancias": [1, 2]}

    def test_dado_um_texto_com_acento_quando_salvar_entao_o_arquivo_sai_em_utf8_sem_escape(
        self,
        caminho_do_arquivo: Path,
    ) -> None:
        salvar(caminho_do_arquivo, {"alias": "Produção"})

        assert caminho_do_arquivo.read_bytes() == '{\n  "alias": "Produção"\n}'.encode()

    def test_dado_um_caminho_com_pastas_inexistentes_quando_salvar_entao_elas_sao_criadas(
        self,
        tmp_path: Path,
    ) -> None:
        caminho = tmp_path / "ainda" / "nao" / "existe" / "config.json"

        salvar(caminho, {"alias": "PROD"})

        assert carregar(caminho) == {"alias": "PROD"}

    def test_dado_arquivo_ja_gravado_quando_salvar_entao_o_conteudo_anterior_e_substituido(
        self,
        arquivo_com_conteudo: Path,
    ) -> None:
        salvar(arquivo_com_conteudo, {"outro": "valor"})

        assert carregar(arquivo_com_conteudo) == {"outro": "valor"}

    def test_dado_um_caminho_livre_quando_salvar_entao_nenhum_temporario_sobra(
        self,
        caminho_do_arquivo: Path,
    ) -> None:
        salvar(caminho_do_arquivo, {"alias": "PROD"})

        assert [arquivo.name for arquivo in caminho_do_arquivo.parent.iterdir()] == ["config.json"]

    def test_dado_um_valor_sem_representacao_json_quando_salvar_entao_a_gravacao_e_recusada(
        self,
        caminho_do_arquivo: Path,
    ) -> None:
        with pytest.raises(ArquivoNaoGravavelError) as falha:
            salvar(caminho_do_arquivo, {"alias": object()})

        assert falha.value.caminho == caminho_do_arquivo

    def test_dado_que_a_estrutura_referencia_a_si_mesma_quando_salvar_entao_a_gravacao_e_recusada(
        self,
        caminho_do_arquivo: Path,
    ) -> None:
        circular: dict[str, object] = {}
        circular["ele_mesmo"] = circular

        with pytest.raises(ArquivoNaoGravavelError):
            salvar(caminho_do_arquivo, circular)

    def test_dado_arquivo_ja_gravado_quando_salvar_valor_invalido_entao_o_conteudo_anterior_sobrevive(
        self,
        arquivo_com_conteudo: Path,
    ) -> None:
        with pytest.raises(ArquivoNaoGravavelError):
            salvar(arquivo_com_conteudo, {"alias": object()})

        assert carregar(arquivo_com_conteudo) == {"alias": "Produção"}

    def test_dado_um_arquivo_ocupando_o_lugar_de_uma_pasta_quando_salvar_entao_a_gravacao_e_recusada(
        self,
        tmp_path: Path,
    ) -> None:
        ocupado = tmp_path / "ocupado"
        ocupado.write_text("nao sou pasta", encoding="utf-8")

        with pytest.raises(ArquivoNaoGravavelError):
            salvar(ocupado / "config.json", {"alias": "PROD"})

    def test_dado_que_o_destino_e_uma_pasta_quando_salvar_entao_nenhum_temporario_sobra(
        self,
        tmp_path: Path,
    ) -> None:
        destino_ocupado_por_pasta = tmp_path / "config.json"
        destino_ocupado_por_pasta.mkdir()

        with pytest.raises(ArquivoNaoGravavelError):
            salvar(destino_ocupado_por_pasta, {"alias": "PROD"})

        assert [arquivo.name for arquivo in tmp_path.iterdir()] == ["config.json"]


class TestHierarquiaDeExcecoes:
    """Cobre a hierarquia que o pacote expõe a quem trata as falhas."""

    @pytest.mark.parametrize(
        "excecao",
        [ArquivoNaoEncontradoError, ArquivoCorrompidoError, ArquivoNaoGravavelError],
    )
    def test_dado_qualquer_erro_do_pacote_entao_ele_pode_ser_tratado_como_arquivo_json_error(
        self,
        excecao: type[ArquivoJsonError],
    ) -> None:
        assert issubclass(excecao, ArquivoJsonError)

    def test_dado_o_erro_raiz_do_pacote_entao_ele_pertence_a_raiz_da_aplicacao(self) -> None:
        assert issubclass(ArquivoJsonError, BakRestorerError)

    def test_dado_um_erro_do_pacote_quando_convertido_em_texto_entao_ele_carrega_o_caminho(
        self,
        caminho_do_arquivo: Path,
    ) -> None:
        with pytest.raises(ArquivoJsonError) as falha:
            carregar(caminho_do_arquivo)

        assert str(caminho_do_arquivo) in str(falha.value)


class TestFormatoGravado:
    """Cobre o formato do arquivo, que é editado à mão durante o desenvolvimento."""

    def test_dado_um_conteudo_qualquer_quando_salvar_entao_o_arquivo_sai_indentado(
        self,
        caminho_do_arquivo: Path,
    ) -> None:
        salvar(caminho_do_arquivo, {"alias": "PROD", "porta": 1433})

        assert caminho_do_arquivo.read_text(encoding="utf-8") == json.dumps(
            {"alias": "PROD", "porta": 1433},
            indent=2,
            ensure_ascii=False,
        )
