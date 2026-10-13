import pytest
from bakrestorer.infra.sqlserver import Conexao
from pydantic import ValidationError


class TestConexao:
    """Cobre a validação de `Conexao`."""

    def test_dadas_a_instancia_e_a_porta_juntas_quando_construir_entao_a_conexao_e_recusada(self) -> None:
        with pytest.raises(ValidationError):
            Conexao(host="localhost", instancia="SQLEXPRESS", porta=1433)

    @pytest.mark.parametrize(
        ("instancia", "porta"),
        [("SQLEXPRESS", None), (None, 1433), (None, None)],
        ids=["so_a_instancia", "so_a_porta", "nenhuma"],
    )
    def test_dada_no_maximo_uma_entre_instancia_e_porta_quando_construir_entao_a_conexao_e_aceita(
        self,
        instancia: str | None,
        porta: int | None,
    ) -> None:
        conexao = Conexao(host="localhost", instancia=instancia, porta=porta)

        assert (conexao.instancia, conexao.porta) == (instancia, porta)
