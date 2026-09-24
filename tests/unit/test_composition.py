from bakrestorer.composition import instancias_service
from bakrestorer.features.instancias import InstanciasService


class TestInstanciasService:
    """Cobre `instancias_service`."""

    def test_dado_o_aplicativo_montado_quando_pedir_o_servico_entao_ele_vem_pronto(self) -> None:
        assert isinstance(instancias_service(), InstanciasService)

    def test_dado_que_o_servico_ja_foi_pedido_quando_pedir_de_novo_entao_e_o_mesmo_objeto(self) -> None:
        assert instancias_service() is instancias_service()
