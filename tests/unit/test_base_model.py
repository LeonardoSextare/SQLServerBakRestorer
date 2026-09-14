from typing import Self

import pytest
from bakrestorer.base_model import BakRestorerModel
from bakrestorer.exceptions import ModelInvalidoError
from pydantic import Field, model_validator


class PedidoInvalidoError(ModelInvalidoError):
    """A recusa do model usado nestes testes."""


class Pedido(BakRestorerModel):
    """Model de mentira, só para exercitar a base."""

    ERRO_DE_VALIDACAO = PedidoInvalidoError

    codigo: str = Field(min_length=1)
    quantidade: int = 1
    escolhido: str | None = None
    opcoes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _conferir_escolhido(self) -> Self:
        if self.escolhido and self.escolhido not in self.opcoes:
            raise PedidoInvalidoError({"escolhido": f"'{self.escolhido}' não está nas opções"})

        return self


@pytest.fixture
def pedido() -> Pedido:
    """O objeto sob teste, válido e com uma opção escolhida."""
    return Pedido(codigo="ABC", escolhido="a", opcoes=("a", "b"))


class TestDeclaracaoDoErro:
    """Cobre a exigência de cada model dizer qual exceção ele levanta."""

    def test_dado_um_model_sem_erro_declarado_quando_definir_a_classe_entao_ela_e_recusada(self) -> None:
        with pytest.raises(TypeError, match="ERRO_DE_VALIDACAO"):

            class Esquecido(BakRestorerModel):
                codigo: str = "ABC"

    def test_dado_um_model_com_erro_declarado_quando_construir_invalido_entao_a_recusa_e_a_dele(self) -> None:
        with pytest.raises(PedidoInvalidoError):
            Pedido(codigo="")

    def test_dado_um_model_que_herda_de_outro_ja_declarado_entao_ele_reaproveita_a_recusa(self) -> None:
        class PedidoEspecial(Pedido):
            observacao: str = ""

        assert PedidoEspecial.ERRO_DE_VALIDACAO is PedidoInvalidoError


class TestTraducaoDaFalha:
    """Cobre a troca da falha do Pydantic pela nossa."""

    def test_dado_um_campo_fora_do_formato_quando_construir_entao_a_falha_diz_qual_campo_foi(self) -> None:
        with pytest.raises(PedidoInvalidoError) as recusa:
            Pedido(codigo="ABC", quantidade="muitas")

        assert recusa.value.campos == {
            "quantidade": "Input should be a valid integer, unable to parse string as an integer"
        }

    def test_dados_dois_campos_errados_quando_construir_entao_os_dois_aparecem_na_recusa(self) -> None:
        with pytest.raises(PedidoInvalidoError) as recusa:
            Pedido(codigo="", quantidade="muitas")

        assert sorted(recusa.value.campos) == ["codigo", "quantidade"]

    def test_dado_um_valor_que_nem_e_objeto_quando_validar_entao_a_recusa_fala_do_model(self) -> None:
        with pytest.raises(PedidoInvalidoError) as recusa:
            Pedido.model_validate(42)

        assert "model" in recusa.value.campos


class TestAtribuicao:
    """Cobre a atribuição de campo."""

    def test_dado_um_valor_valido_quando_atribuir_entao_ele_e_guardado(self, pedido: Pedido) -> None:
        pedido.codigo = "XYZ"

        assert pedido.codigo == "XYZ"

    def test_dado_um_valor_que_quebra_o_campo_quando_atribuir_entao_o_valor_anterior_fica(
        self,
        pedido: Pedido,
    ) -> None:
        with pytest.raises(PedidoInvalidoError):
            pedido.codigo = ""

        assert pedido.codigo == "ABC"

    def test_dado_um_valor_que_quebra_a_regra_do_conjunto_quando_atribuir_entao_o_objeto_nao_muda(
        self,
        pedido: Pedido,
    ) -> None:
        with pytest.raises(PedidoInvalidoError):
            pedido.opcoes = ()

        assert pedido.opcoes == ("a", "b")

    def test_dado_um_valor_convertivel_quando_atribuir_entao_ele_e_guardado_convertido(
        self,
        pedido: Pedido,
    ) -> None:
        pedido.quantidade = "7"  # ty: ignore[invalid-assignment]

        assert pedido.quantidade == 7

    def test_dado_um_campo_que_nao_existe_quando_atribuir_entao_a_atribuicao_e_recusada(
        self,
        pedido: Pedido,
    ) -> None:
        with pytest.raises(PedidoInvalidoError):
            pedido.fantasma = 1

    def test_dado_um_atributo_privado_quando_atribuir_entao_ele_passa_sem_validacao(self, pedido: Pedido) -> None:
        pedido._anotacao = "qualquer coisa"

        assert pedido.model_dump() == {"codigo": "ABC", "quantidade": 1, "escolhido": "a", "opcoes": ("a", "b")}


class TestAlterando:
    """Cobre a transação."""

    def test_dadas_duas_mudancas_que_so_valem_juntas_quando_alterar_entao_as_duas_sao_aplicadas(
        self,
        pedido: Pedido,
    ) -> None:
        with pedido.alterando() as rascunho:
            rascunho.opcoes = ()
            rascunho.escolhido = None

        assert (pedido.opcoes, pedido.escolhido) == ((), None)

    def test_dado_um_rascunho_que_nao_passa_na_validacao_quando_alterar_entao_o_original_fica_intacto(
        self,
        pedido: Pedido,
    ) -> None:
        with pytest.raises(PedidoInvalidoError), pedido.alterando() as rascunho:
            rascunho.opcoes = ()

        assert pedido.opcoes == ("a", "b")

    def test_dada_uma_falha_no_meio_do_bloco_quando_alterar_entao_o_original_fica_intacto(
        self,
        pedido: Pedido,
    ) -> None:
        with pytest.raises(RuntimeError), pedido.alterando() as rascunho:
            rascunho.escolhido = None
            mensagem = "algo deu errado no meio"
            raise RuntimeError(mensagem)

        assert pedido.escolhido == "a"

    def test_dado_um_rascunho_alterado_quando_ler_o_original_dentro_do_bloco_entao_ele_ainda_e_o_antigo(
        self,
        pedido: Pedido,
    ) -> None:
        with pedido.alterando() as rascunho:
            rascunho.escolhido = None

            assert pedido.escolhido == "a"

        assert pedido.escolhido is None

    def test_dado_um_valor_convertivel_no_rascunho_quando_alterar_entao_ele_e_guardado_convertido(
        self,
        pedido: Pedido,
    ) -> None:
        with pedido.alterando() as rascunho:
            rascunho.quantidade = "7"  # ty: ignore[invalid-assignment]

        assert pedido.quantidade == 7

    def test_dada_uma_atribuicao_no_original_dentro_do_bloco_entao_ela_vale_na_hora(self, pedido: Pedido) -> None:
        with pedido.alterando() as rascunho:
            rascunho.escolhido = None
            pedido.codigo = "XYZ"

            assert pedido.codigo == "XYZ"

        assert pedido.escolhido is None
