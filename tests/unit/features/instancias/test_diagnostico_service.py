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


class TestConferirAcesso:
    """Cobre `conferir_acesso`."""

    def test_dada_uma_instancia_que_responde_ao_ping_quando_conferir_o_acesso_entao_a_conexao_e_o_login_passam(
        self,
        servico_de_diagnostico: DiagnosticoService,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        instancia = criar_instancia()

        diagnostico = servico_de_diagnostico.conferir_acesso(instancia)

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

        assert servico_de_diagnostico.conferir_acesso(criar_instancia()).latencia == timedelta(milliseconds=7)

    def test_dada_uma_instancia_sem_resposta_quando_conferir_o_acesso_entao_a_conexao_falha_e_o_login_nao_e_verificado(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: MagicMock,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        cliente_sql_server.ping.side_effect = InstanciaInacessivelError("localhost\\SQLEXPRESS", "sem resposta")

        diagnostico = servico_de_diagnostico.conferir_acesso(criar_instancia())

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

        diagnostico = servico_de_diagnostico.conferir_acesso(criar_instancia())

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
            servico_de_diagnostico.conferir_acesso(criar_instancia())

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
        servico_de_diagnostico.conferir_acesso(criar_instancia(**campos))

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


class TestDiagnosticarTodas:
    """Cobre `diagnosticar_todas`."""

    def test_dadas_varias_instancias_quando_diagnosticar_todas_entao_cada_uma_tem_o_seu_diagnostico_na_mesma_ordem(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: MagicMock,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        prod = criar_instancia("PROD", host="prod")
        homolog = criar_instancia("HOMOLOG", host="homolog")

        def responder(conexao: Conexao) -> timedelta:
            if conexao.host == "homolog":
                raise InstanciaInacessivelError(conexao.servidor, "")

            return timedelta(milliseconds=1)

        cliente_sql_server.ping.side_effect = responder

        diagnosticos = servico_de_diagnostico.diagnosticar_todas([prod, homolog])

        assert [(diagnostico.id_da_instancia, diagnostico.situacao) for diagnostico in diagnosticos] == [
            (prod.id, "ok"),
            (homolog.id, "erro"),
        ]
