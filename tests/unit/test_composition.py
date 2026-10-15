from bakrestorer.composition import cliente_sql_server, diagnostico_service, instancias_service
from bakrestorer.features.instancias import DiagnosticoService, InstanciasService


class TestInstanciasService:
    """Cobre `instancias_service`."""

    def test_dado_o_aplicativo_montado_quando_pedir_o_servico_entao_ele_vem_pronto(self) -> None:
        assert isinstance(instancias_service(), InstanciasService)

    def test_dado_que_o_servico_ja_foi_pedido_quando_pedir_de_novo_entao_e_o_mesmo_objeto(self) -> None:
        assert instancias_service() is instancias_service()


class TestDiagnosticoService:
    """Cobre `diagnostico_service`."""

    def test_dado_o_aplicativo_montado_quando_pedir_o_servico_entao_ele_vem_pronto(self) -> None:
        assert isinstance(diagnostico_service(), DiagnosticoService)

    def test_dado_que_o_servico_ja_foi_pedido_quando_pedir_de_novo_entao_e_o_mesmo_objeto(self) -> None:
        assert diagnostico_service() is diagnostico_service()


class TestClienteSqlServer:
    """Cobre `cliente_sql_server`."""

    def test_dado_que_o_cliente_ja_foi_pedido_quando_pedir_de_novo_entao_e_o_mesmo_objeto(self) -> None:
        assert cliente_sql_server() is cliente_sql_server()
