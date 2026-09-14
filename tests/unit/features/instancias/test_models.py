from collections.abc import Callable
from pathlib import Path

import pytest
from bakrestorer.features.instancias import (
    CadastroInvalidoError,
    ConfigInstancias,
    Instancia,
    InstanciaInvalidaError,
)


class TestInstancia:
    """Cobre a validação de `Instancia`."""

    @pytest.mark.parametrize("campo", ["alias", "host", "nome", "usuario", "senha"])
    def test_dado_um_campo_obrigatorio_em_branco_quando_construir_entao_a_instancia_e_recusada(
        self,
        criar_instancia: Callable[..., Instancia],
        campo: str,
    ) -> None:
        with pytest.raises(InstanciaInvalidaError) as recusa:
            criar_instancia(**{campo: ""})

        assert campo in recusa.value.campos

    def test_dado_um_campo_desconhecido_quando_construir_entao_a_instancia_e_recusada(
        self,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        with pytest.raises(InstanciaInvalidaError):
            criar_instancia(porta=1433)

    def test_dado_que_o_host_nao_foi_informado_quando_construir_entao_ele_e_a_maquina_local(
        self,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        assert criar_instancia().host == "localhost"

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


class TestInstancias:
    """Cobre a validação de `ConfigInstancias`."""

    def test_dado_que_nada_foi_informado_quando_construir_entao_o_cadastro_nasce_vazio(self) -> None:
        cadastro = ConfigInstancias()

        assert (cadastro.padrao, cadastro.itens) == (None, ())

    def test_dado_o_mesmo_alias_em_duas_instancias_quando_construir_entao_o_cadastro_e_recusado(
        self,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        with pytest.raises(CadastroInvalidoError) as recusa:
            ConfigInstancias(itens=(criar_instancia("PROD"), criar_instancia("PROD")))

        assert "itens" in recusa.value.campos

    def test_dado_um_padrao_que_nao_esta_nas_instancias_quando_construir_entao_o_cadastro_e_recusado(
        self,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        with pytest.raises(CadastroInvalidoError) as recusa:
            ConfigInstancias(itens=(criar_instancia("PROD"),), padrao="HOMOLOG")

        assert "padrao" in recusa.value.campos

    def test_dado_um_padrao_presente_nas_instancias_quando_construir_entao_o_cadastro_e_aceito(
        self,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        cadastro = ConfigInstancias(itens=(criar_instancia("PROD"),), padrao="PROD")

        assert cadastro.padrao == "PROD"

    def test_dado_um_campo_desconhecido_quando_construir_entao_o_cadastro_e_recusado(self) -> None:
        with pytest.raises(CadastroInvalidoError):
            ConfigInstancias(pastas_de_backup=())  # ty: ignore[unknown-argument]

    def test_dada_uma_instancia_fora_do_formato_quando_construir_entao_a_falha_e_da_instancia(self) -> None:
        with pytest.raises(InstanciaInvalidaError):
            ConfigInstancias.model_validate({"itens": [{"alias": ""}]})


class TestObter:
    """Cobre `obter`."""

    def test_dado_um_alias_cadastrado_quando_obter_entao_a_instancia_correspondente_volta(
        self,
        criar_instancia: Callable[..., Instancia],
        criar_cadastro: Callable[..., ConfigInstancias],
    ) -> None:
        homolog = criar_instancia("HOMOLOG")
        cadastro = criar_cadastro(itens=(criar_instancia("PROD"), homolog))

        assert cadastro.obter("HOMOLOG") == homolog

    def test_dado_um_alias_desconhecido_quando_obter_entao_a_resposta_e_nula(
        self,
        criar_cadastro: Callable[..., ConfigInstancias],
    ) -> None:
        assert criar_cadastro().obter("HOMOLOG") is None
