from collections.abc import Callable
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

    def test_dada_uma_instancia_que_responde_ao_ping_quando_conferir_o_acesso_entao_a_resposta_e_o_login_passam(
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

    def test_dada_uma_instancia_que_responde_ao_ping_quando_conferir_o_acesso_entao_a_latencia_e_medida(
        self,
        servico_de_diagnostico: DiagnosticoService,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        assert servico_de_diagnostico.conferir_acesso(criar_instancia()).latencia is not None

    def test_dada_uma_instancia_que_nao_responde_quando_conferir_o_acesso_entao_ela_falha_e_o_login_nao_e_verificado(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: MagicMock,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        cliente_sql_server.executar.side_effect = InstanciaInacessivelError("localhost\\SQLEXPRESS", "sem resposta")

        diagnostico = servico_de_diagnostico.conferir_acesso(criar_instancia())

        assert (diagnostico.conexao, diagnostico.login.situacao, diagnostico.latencia) == (
            Verificacao(situacao="erro", detalhe="sem resposta"),
            "nao_verificado",
            None,
        )

    def test_dada_uma_credencial_recusada_quando_conferir_o_acesso_entao_a_resposta_passa_e_o_login_falha(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: MagicMock,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        cliente_sql_server.executar.side_effect = CredenciaisInvalidasError("localhost\\SQLEXPRESS", "login falhou")

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
        cliente_sql_server.executar.side_effect = ComandoRecusadoError("localhost\\SQLEXPRESS", "recusado")

        with pytest.raises(ComandoRecusadoError):
            servico_de_diagnostico.conferir_acesso(criar_instancia())

    def test_dada_uma_instancia_quando_conferir_o_acesso_entao_a_sessao_guardada_e_descartada_antes_dos_pings(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: MagicMock,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        servico_de_diagnostico.conferir_acesso(criar_instancia())

        assert [chamada[0] for chamada in cliente_sql_server.mock_calls] == ["descartar", "executar", "executar"]

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

        assert cliente_sql_server.executar.call_args.args[0] == conexao_esperada


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
        prod = criar_instancia("PROD")
        homolog = criar_instancia("HOMOLOG")
        cliente_sql_server.executar.side_effect = [[{"": 1}], [{"": 1}], InstanciaInacessivelError("localhost", "")]

        diagnosticos = servico_de_diagnostico.diagnosticar_todas([prod, homolog])

        assert [(diagnostico.id_da_instancia, diagnostico.situacao) for diagnostico in diagnosticos] == [
            (prod.id, "ok"),
            (homolog.id, "erro"),
        ]
