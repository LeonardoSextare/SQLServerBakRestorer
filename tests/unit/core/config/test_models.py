from collections.abc import Callable
from pathlib import Path

import pytest
from bakrestorer.core.config import VERSAO_DA_CONFIG, Configuracao, Instancia
from pydantic import ValidationError


class TestInstancia:
    """Cobre a validação de `Instancia`."""

    @pytest.mark.parametrize(
        "campo",
        ["alias", "nome", "usuario", "senha"],
    )
    def test_dado_um_campo_obrigatorio_em_branco_quando_construir_entao_a_instancia_e_recusada(
        self,
        criar_instancia: Callable[..., Instancia],
        campo: str,
    ) -> None:
        with pytest.raises(ValidationError):
            criar_instancia(**{campo: ""})

    def test_dado_um_campo_desconhecido_quando_construir_entao_a_instancia_e_recusada(
        self,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        with pytest.raises(ValidationError):
            criar_instancia(porta=1433)

    def test_dada_uma_instancia_construida_quando_tentar_alterar_um_campo_entao_a_alteracao_e_recusada(
        self,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        instancia = criar_instancia()

        with pytest.raises(ValidationError):
            instancia.senha = "outra"  # ty: ignore[invalid-assignment]

    def test_dado_que_as_pastas_nao_foram_informadas_quando_construir_entao_elas_ficam_nulas(
        self,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        instancia = criar_instancia()

        assert (instancia.pasta_dados, instancia.pasta_log) == (None, None)

    def test_dada_uma_pasta_como_texto_quando_construir_entao_ela_vira_caminho(
        self,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        instancia = criar_instancia(pasta_dados=r"D:\dados")

        assert instancia.pasta_dados == Path(r"D:\dados")


class TestConfiguracao:
    """Cobre a validação de `Configuracao`."""

    def test_dado_que_nada_foi_informado_quando_construir_entao_a_configuracao_nasce_vazia(self) -> None:
        configuracao = Configuracao()

        assert configuracao.versao_da_config == VERSAO_DA_CONFIG
        assert configuracao.instancia_padrao is None
        assert configuracao.instancias == ()

    def test_dado_o_mesmo_alias_em_duas_instancias_quando_construir_entao_a_configuracao_e_recusada(
        self,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        with pytest.raises(ValidationError):
            Configuracao(instancias=(criar_instancia("PROD"), criar_instancia("PROD")))

    def test_dado_um_padrao_que_nao_esta_nas_instancias_quando_construir_entao_a_configuracao_e_recusada(
        self,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        with pytest.raises(ValidationError):
            Configuracao(instancias=(criar_instancia("PROD"),), instancia_padrao="HOMOLOG")

    def test_dado_um_padrao_presente_nas_instancias_quando_construir_entao_a_configuracao_e_aceita(
        self,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        configuracao = Configuracao(instancias=(criar_instancia("PROD"),), instancia_padrao="PROD")

        assert configuracao.instancia_padrao == "PROD"

    def test_dado_um_campo_desconhecido_quando_construir_entao_a_configuracao_e_recusada(self) -> None:
        with pytest.raises(ValidationError):
            Configuracao(pastas_de_backup=())  # ty: ignore[unknown-argument]


class TestObterInstancia:
    """Cobre `obter_instancia`."""

    def test_dado_um_alias_configurado_quando_obter_entao_a_instancia_correspondente_volta(
        self,
        criar_instancia: Callable[..., Instancia],
        criar_configuracao: Callable[..., Configuracao],
    ) -> None:
        homolog = criar_instancia("HOMOLOG")
        configuracao = criar_configuracao(instancias=(criar_instancia("PROD"), homolog))

        assert configuracao.obter_instancia("HOMOLOG") == homolog

    def test_dado_um_alias_desconhecido_quando_obter_entao_a_resposta_e_nula(
        self,
        criar_configuracao: Callable[..., Configuracao],
    ) -> None:
        configuracao = criar_configuracao()

        assert configuracao.obter_instancia("HOMOLOG") is None


class TestAlterada:
    """Cobre `alterada`."""

    def test_dado_um_campo_substituido_quando_alterar_entao_os_demais_permanecem(
        self,
        criar_configuracao: Callable[..., Configuracao],
    ) -> None:
        configuracao = criar_configuracao()

        alterada = configuracao.alterada(instancia_padrao=None)

        assert (alterada.instancia_padrao, alterada.instancias) == (None, configuracao.instancias)

    def test_dada_uma_configuracao_alterada_quando_ler_a_original_entao_ela_continua_intacta(
        self,
        criar_configuracao: Callable[..., Configuracao],
    ) -> None:
        configuracao = criar_configuracao()

        configuracao.alterada(instancia_padrao=None)

        assert configuracao.instancia_padrao == "PROD"

    def test_dada_uma_alteracao_que_quebra_uma_regra_quando_alterar_entao_a_copia_e_recusada(
        self,
        criar_configuracao: Callable[..., Configuracao],
    ) -> None:
        configuracao = criar_configuracao()

        with pytest.raises(ValidationError):
            configuracao.alterada(instancias=())

    def test_dado_um_campo_desconhecido_quando_alterar_entao_a_copia_e_recusada(self) -> None:
        with pytest.raises(ValidationError):
            Configuracao().alterada(campo_que_nao_existe=1)
