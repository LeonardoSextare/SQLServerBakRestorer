from collections.abc import Callable
from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from bakrestorer.features.instancias import DiagnosticoService, Instancia, Verificacao
from bakrestorer.infra.sqlserver import (
    ComandoRecusadoError,
    Conexao,
    CredenciaisInvalidasError,
    InstanciaInacessivelError,
)


class TestConferirAcessoAInstancia:
    """Cobre `conferir_acesso_a_instancia`."""

    def test_dada_uma_instancia_que_responde_ao_ping_quando_conferir_o_acesso_entao_a_conexao_e_o_login_passam(
        self,
        servico_de_diagnostico: DiagnosticoService,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        instancia = criar_instancia()

        diagnostico = servico_de_diagnostico.conferir_acesso_a_instancia(instancia)

        assert (diagnostico.id_da_instancia, diagnostico.conexao.situacao, diagnostico.login.situacao) == (
            instancia.id,
            "ok",
            "ok",
        )

    def test_dada_uma_instancia_que_responde_ao_ping_quando_conferir_o_acesso_entao_a_latencia_e_a_do_ping(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: MagicMock,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        cliente_sql_server.ping.return_value = timedelta(milliseconds=7)

        diagnostico = servico_de_diagnostico.conferir_acesso_a_instancia(criar_instancia())

        assert diagnostico.latencia == timedelta(milliseconds=7)

    def test_dada_uma_instancia_sem_resposta_quando_conferir_o_acesso_entao_a_conexao_falha_e_o_login_nao_e_verificado(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: MagicMock,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        cliente_sql_server.ping.side_effect = InstanciaInacessivelError("localhost\\SQLEXPRESS", "sem resposta")

        diagnostico = servico_de_diagnostico.conferir_acesso_a_instancia(criar_instancia())

        assert (diagnostico.conexao, diagnostico.login.situacao, diagnostico.latencia) == (
            Verificacao(situacao="erro", detalhe="sem resposta"),
            "nao_verificado",
            None,
        )

    def test_dada_uma_credencial_recusada_quando_conferir_o_acesso_entao_a_conexao_passa_e_o_login_falha(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: MagicMock,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        cliente_sql_server.ping.side_effect = CredenciaisInvalidasError("localhost\\SQLEXPRESS", "login falhou")

        diagnostico = servico_de_diagnostico.conferir_acesso_a_instancia(criar_instancia())

        assert (diagnostico.conexao.situacao, diagnostico.login, diagnostico.latencia) == (
            "ok",
            Verificacao(situacao="erro", detalhe="login falhou"),
            None,
        )

    def test_dado_um_ping_recusado_quando_conferir_o_acesso_entao_a_falha_sobe(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: MagicMock,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        cliente_sql_server.ping.side_effect = ComandoRecusadoError("localhost\\SQLEXPRESS", "recusado")

        with pytest.raises(ComandoRecusadoError):
            servico_de_diagnostico.conferir_acesso_a_instancia(criar_instancia())

    @pytest.mark.parametrize(
        ("campos", "conexao_esperada"),
        [
            (
                {"host": "servidor", "nome": "SQLEXPRESS", "porta": None},
                Conexao(host="servidor", instancia="SQLEXPRESS", usuario="sa", senha="segredo"),
            ),
            (
                {"host": "servidor", "nome": None, "porta": 1435},
                Conexao(host="servidor", porta=1435, usuario="sa", senha="segredo"),
            ),
        ],
        ids=["pelo_nome", "pela_porta"],
    )
    def test_dada_uma_instancia_quando_conferir_o_acesso_entao_o_ping_vai_para_a_conexao_correspondente(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: MagicMock,
        criar_instancia: Callable[..., Instancia],
        campos: dict[str, object],
        conexao_esperada: Conexao,
    ) -> None:
        servico_de_diagnostico.conferir_acesso_a_instancia(criar_instancia(**campos))

        cliente_sql_server.ping.assert_called_once_with(conexao_esperada)


class TestDiagnosticar:
    """Cobre `diagnosticar`."""

    def test_dada_uma_instancia_que_responde_ao_ping_quando_diagnosticar_entao_o_checklist_passa(
        self,
        servico_de_diagnostico: DiagnosticoService,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        instancia = criar_instancia()

        diagnostico = servico_de_diagnostico.diagnosticar(instancia)

        assert (diagnostico.id_da_instancia, diagnostico.situacao) == (instancia.id, "ok")

    def test_dada_uma_credencial_recusada_quando_diagnosticar_entao_as_permissoes_nao_sao_conferidas(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: MagicMock,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        cliente_sql_server.ping.side_effect = CredenciaisInvalidasError("localhost\\SQLEXPRESS", "login falhou")

        diagnostico = servico_de_diagnostico.diagnosticar(criar_instancia())

        assert (diagnostico.criacao_de_banco.situacao, diagnostico.sobrescrita_de_banco.situacao) == (
            "nao_verificado",
            "nao_verificado",
        )
        cliente_sql_server.executar.assert_not_called()


class TestConferirPermissoesDaInstancia:
    """Cobre `conferir_permissoes_da_instancia`."""

    @pytest.mark.parametrize(
        ("permissoes", "criacao_e_sobrescrita"),
        [
            ({"sysadmin": 1, "dbcreator": 0, "cria_banco": 1}, ("ok", "ok")),
            ({"sysadmin": 0, "dbcreator": 1, "cria_banco": 1}, ("ok", "ok")),
            ({"sysadmin": 0, "dbcreator": 0, "cria_banco": 1}, ("ok", "aviso")),
            ({"sysadmin": 0, "dbcreator": 0, "cria_banco": 0}, ("erro", "aviso")),
        ],
        ids=["sysadmin", "dbcreator", "so_cria_banco", "sem_permissao"],
    )
    def test_dadas_as_permissoes_do_login_quando_conferir_entao_criar_e_sobrescrever_banco_seguem_elas(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: MagicMock,
        criar_instancia: Callable[..., Instancia],
        permissoes: dict[str, int],
        criacao_e_sobrescrita: tuple[str, str],
    ) -> None:
        cliente_sql_server.executar.return_value = [permissoes]

        criacao, sobrescrita = servico_de_diagnostico.conferir_permissoes_da_instancia(criar_instancia())

        assert (criacao.situacao, sobrescrita.situacao) == criacao_e_sobrescrita

    def test_dada_uma_instancia_que_nao_responde_quando_conferir_entao_as_permissoes_nao_sao_verificadas(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: MagicMock,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        cliente_sql_server.executar.side_effect = InstanciaInacessivelError("localhost\\SQLEXPRESS", "caiu")

        criacao, sobrescrita = servico_de_diagnostico.conferir_permissoes_da_instancia(criar_instancia())

        assert (criacao.situacao, sobrescrita.situacao) == ("nao_verificado", "nao_verificado")

    def test_dada_a_consulta_recusada_quando_conferir_entao_a_falha_sobe(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: MagicMock,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        cliente_sql_server.executar.side_effect = ComandoRecusadoError("localhost\\SQLEXPRESS", "recusado")

        with pytest.raises(ComandoRecusadoError):
            servico_de_diagnostico.conferir_permissoes_da_instancia(criar_instancia())
