from collections.abc import Callable
from unittest.mock import MagicMock

import pytest
from bakrestorer.features.instancias import DiagnosticoService, EstadoDaInstancia, Instancia
from bakrestorer.infra.sqlserver import (
    ComandoRecusadoError,
    Conexao,
    CredenciaisInvalidasError,
    InstanciaInacessivelError,
)


class TestConferirAcesso:
    """Cobre `conferir_acesso`."""

    def test_dada_uma_instancia_que_responde_ao_ping_quando_conferir_o_acesso_entao_ela_esta_acessivel(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: MagicMock,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        instancia = criar_instancia()
        cliente_sql_server.executar.return_value = [{"": 1}]

        diagnostico = servico_de_diagnostico.conferir_acesso(instancia)

        assert (diagnostico.id_da_instancia, diagnostico.estado) == (instancia.id, EstadoDaInstancia.ACESSIVEL)

    def test_dada_uma_instancia_que_nao_responde_quando_conferir_o_acesso_entao_ela_esta_inacessivel_com_o_detalhe(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: MagicMock,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        cliente_sql_server.executar.side_effect = InstanciaInacessivelError("localhost\\SQLEXPRESS", "sem resposta")

        diagnostico = servico_de_diagnostico.conferir_acesso(criar_instancia())

        assert (diagnostico.estado, diagnostico.detalhe) == (EstadoDaInstancia.INACESSIVEL, "sem resposta")

    def test_dada_uma_credencial_recusada_quando_conferir_o_acesso_entao_as_credenciais_estao_recusadas_com_o_detalhe(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: MagicMock,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        cliente_sql_server.executar.side_effect = CredenciaisInvalidasError("localhost\\SQLEXPRESS", "login falhou")

        diagnostico = servico_de_diagnostico.conferir_acesso(criar_instancia())

        assert (diagnostico.estado, diagnostico.detalhe) == (EstadoDaInstancia.CREDENCIAIS_RECUSADAS, "login falhou")

    def test_dado_um_ping_recusado_quando_conferir_o_acesso_entao_a_falha_sobe(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: MagicMock,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        cliente_sql_server.executar.side_effect = ComandoRecusadoError("localhost\\SQLEXPRESS", "recusado")

        with pytest.raises(ComandoRecusadoError):
            servico_de_diagnostico.conferir_acesso(criar_instancia())

    def test_dada_uma_instancia_quando_conferir_o_acesso_entao_a_sessao_guardada_e_descartada_antes_do_ping(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: MagicMock,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        servico_de_diagnostico.conferir_acesso(criar_instancia())

        assert [chamada[0] for chamada in cliente_sql_server.mock_calls] == ["descartar", "executar"]

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

    def test_dada_uma_instancia_que_responde_ao_ping_quando_diagnosticar_entao_ela_esta_acessivel(
        self,
        servico_de_diagnostico: DiagnosticoService,
        cliente_sql_server: MagicMock,
        criar_instancia: Callable[..., Instancia],
    ) -> None:
        instancia = criar_instancia()
        cliente_sql_server.executar.return_value = [{"": 1}]

        diagnostico = servico_de_diagnostico.diagnosticar(instancia)

        assert (diagnostico.id_da_instancia, diagnostico.estado) == (instancia.id, EstadoDaInstancia.ACESSIVEL)


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
        cliente_sql_server.executar.side_effect = [[{"": 1}], InstanciaInacessivelError("localhost", "")]

        diagnosticos = servico_de_diagnostico.diagnosticar_todas([prod, homolog])

        assert [(diagnostico.id_da_instancia, diagnostico.estado) for diagnostico in diagnosticos] == [
            (prod.id, EstadoDaInstancia.ACESSIVEL),
            (homolog.id, EstadoDaInstancia.INACESSIVEL),
        ]
