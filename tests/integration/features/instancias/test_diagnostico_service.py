from collections.abc import Callable

from bakrestorer.features.instancias import DiagnosticoService, EstadoDaInstancia, Instancia
from bakrestorer.infra.sqlserver import ClienteSqlServer, Conexao


class TestConferirAcesso:
    """Cobre `conferir_acesso`."""

    def test_dada_a_instancia_do_conteiner_quando_conferir_o_acesso_entao_ela_esta_acessivel(
        self,
        servico_de_diagnostico: DiagnosticoService,
        instancia_no_conteiner: Instancia,
    ) -> None:
        assert servico_de_diagnostico.conferir_acesso(instancia_no_conteiner).estado == EstadoDaInstancia.ACESSIVEL

    def test_dada_uma_senha_errada_quando_conferir_o_acesso_entao_as_credenciais_estao_recusadas(
        self,
        servico_de_diagnostico: DiagnosticoService,
        instancia_no_conteiner: Instancia,
    ) -> None:
        instancia = instancia_no_conteiner.model_copy(update={"senha": "errada"})

        assert servico_de_diagnostico.conferir_acesso(instancia).estado == EstadoDaInstancia.CREDENCIAIS_RECUSADAS

    def test_dado_um_host_que_nao_responde_quando_conferir_o_acesso_entao_a_instancia_esta_inacessivel(
        self,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        cliente = ClienteSqlServer(login_timeout=1)
        inalcancavel = criar_instancia(host="192.0.2.1", nome=None, porta=1433)

        try:
            diagnostico = DiagnosticoService(cliente).conferir_acesso(inalcancavel)
        finally:
            cliente.encerrar()

        assert diagnostico.estado == EstadoDaInstancia.INACESSIVEL

    def test_dada_uma_sessao_guardada_que_caiu_quando_conferir_o_acesso_entao_um_login_novo_responde(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: ClienteSqlServer,
        instancia_sql_server: Conexao,
        instancia_no_conteiner: Instancia,
        derrubar_sessao: Callable[[ClienteSqlServer], None],
    ) -> None:
        cliente_sql_server.executar(instancia_sql_server, "SELECT 1")
        derrubar_sessao(cliente_sql_server)

        assert servico_de_diagnostico.conferir_acesso(instancia_no_conteiner).estado == EstadoDaInstancia.ACESSIVEL
