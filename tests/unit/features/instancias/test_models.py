from collections.abc import Callable
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from bakrestorer.features.instancias import (
    CadastroInvalidoError,
    ConfigInstancias,
    Instancia,
    InstanciaInvalidaError,
)


class TestInstancia:
    """Cobre a validação de `Instancia`."""

    @pytest.mark.parametrize("campo", ["apelido", "host", "nome", "usuario", "senha"])
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

    def test_dado_que_o_id_nao_foi_informado_quando_construir_entao_cada_instancia_ganha_o_seu(
        self,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        assert criar_instancia("PROD").id != criar_instancia("HOMOLOG").id

    def test_dado_um_id_como_texto_quando_construir_entao_ele_vira_uuid(
        self,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        instancia = criar_instancia(id="3f2b8c1e-4a5d-4e6f-8a9b-0c1d2e3f4a5b")

        assert instancia.id == UUID("3f2b8c1e-4a5d-4e6f-8a9b-0c1d2e3f4a5b")

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

    def test_dado_o_mesmo_apelido_em_duas_instancias_quando_construir_entao_o_cadastro_e_recusado(
        self,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        with pytest.raises(CadastroInvalidoError) as recusa:
            ConfigInstancias(itens=(criar_instancia("PROD"), criar_instancia("PROD")))

        assert "itens" in recusa.value.campos

    def test_dado_o_mesmo_id_em_duas_instancias_quando_construir_entao_o_cadastro_e_recusado(
        self,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        prod = criar_instancia("PROD")

        with pytest.raises(CadastroInvalidoError) as recusa:
            ConfigInstancias(itens=(prod, criar_instancia("HOMOLOG", id=prod.id)))

        assert "itens" in recusa.value.campos

    def test_dado_um_padrao_que_nao_esta_nas_instancias_quando_construir_entao_o_cadastro_e_recusado(
        self,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        with pytest.raises(CadastroInvalidoError) as recusa:
            ConfigInstancias(itens=(criar_instancia("PROD"),), padrao=uuid4())

        assert "padrao" in recusa.value.campos

    def test_dado_um_padrao_presente_nas_instancias_quando_construir_entao_o_cadastro_e_aceito(
        self,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        prod = criar_instancia("PROD")

        cadastro = ConfigInstancias(itens=(prod,), padrao=prod.id)

        assert cadastro.padrao == prod.id

    def test_dado_um_campo_desconhecido_quando_construir_entao_o_cadastro_e_recusado(self) -> None:
        with pytest.raises(CadastroInvalidoError):
            ConfigInstancias(pastas_de_backup=())  # ty: ignore[unknown-argument]

    def test_dada_uma_instancia_fora_do_formato_quando_construir_entao_a_falha_e_da_instancia(self) -> None:
        with pytest.raises(InstanciaInvalidaError):
            ConfigInstancias.model_validate({"itens": [{"apelido": ""}]})


class TestObter:
    """Cobre `obter`."""

    def test_dado_um_id_cadastrado_quando_obter_entao_a_instancia_correspondente_volta(
        self,
        criar_instancia: Callable[..., Instancia],
        criar_cadastro: Callable[..., ConfigInstancias],
    ) -> None:
        prod = criar_instancia("PROD")
        homolog = criar_instancia("HOMOLOG")
        cadastro = criar_cadastro(itens=(prod, homolog), padrao=prod.id)

        assert cadastro.obter(homolog.id) == homolog

    def test_dado_um_id_desconhecido_quando_obter_entao_a_resposta_e_nula(
        self,
        criar_cadastro: Callable[..., ConfigInstancias],
    ) -> None:
        assert criar_cadastro().obter(uuid4()) is None


class TestObterPeloApelido:
    """Cobre `obter_pelo_apelido`."""

    def test_dado_um_apelido_cadastrado_quando_obter_pelo_apelido_entao_a_instancia_correspondente_volta(
        self,
        criar_instancia: Callable[..., Instancia],
        criar_cadastro: Callable[..., ConfigInstancias],
    ) -> None:
        prod = criar_instancia("PROD")
        homolog = criar_instancia("HOMOLOG")
        cadastro = criar_cadastro(itens=(prod, homolog), padrao=prod.id)

        assert cadastro.obter_pelo_apelido("HOMOLOG") == homolog

    def test_dado_um_apelido_desconhecido_quando_obter_pelo_apelido_entao_a_resposta_e_nula(
        self,
        criar_cadastro: Callable[..., ConfigInstancias],
    ) -> None:
        assert criar_cadastro().obter_pelo_apelido("HOMOLOG") is None
