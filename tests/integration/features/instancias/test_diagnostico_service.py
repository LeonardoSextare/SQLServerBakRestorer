from collections.abc import Callable

from bakrestorer.features.instancias import DiagnosticoService, Instancia
from bakrestorer.infra.sqlserver import ClienteSqlServer


class TestConferirAcessoAInstancia:
    """Cobre `conferir_acesso_a_instancia`."""

    def test_dada_a_instancia_do_conteiner_quando_conferir_o_acesso_entao_tudo_passa_e_a_latencia_e_medida(
        self,
        servico_de_diagnostico: DiagnosticoService,
        instancia_no_conteiner: Instancia,
    ) -> None:
        diagnostico = servico_de_diagnostico.conferir_acesso_a_instancia(instancia_no_conteiner)

        assert (diagnostico.situacao, diagnostico.latencia is not None) == ("ok", True)

    def test_dada_uma_senha_errada_quando_conferir_o_acesso_entao_o_login_falha(
        self,
        servico_de_diagnostico: DiagnosticoService,
        instancia_no_conteiner: Instancia,
    ) -> None:
        instancia = instancia_no_conteiner.model_copy(update={"senha": "errada"})

        assert servico_de_diagnostico.conferir_acesso_a_instancia(instancia).login.situacao == "erro"

    def test_dado_um_host_que_nao_responde_quando_conferir_o_acesso_entao_a_conexao_falha(
        self,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        inalcancavel = criar_instancia(host="192.0.2.1", nome=None, porta=1433)

        diagnostico = DiagnosticoService(ClienteSqlServer(login_timeout=1)).conferir_acesso_a_instancia(inalcancavel)

        assert diagnostico.conexao.situacao == "erro"
