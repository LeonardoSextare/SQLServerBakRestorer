from dataclasses import replace

import pytest

from bakrestorer.infra.sqlserver import (
    ClienteSqlServer,
    ComandoRecusadoError,
    Conexao,
    CredenciaisInvalidasError,
    InstanciaInacessivelError,
)

HOST_INALCANCAVEL = "192.0.2.1"

CRIAR_MARCA_NA_SESSAO = "CREATE TABLE #marca (id INT)"
PROCURAR_MARCA_NA_SESSAO = "SELECT OBJECT_ID('tempdb..#marca') AS marca"


class TestExecutar:
    """Cobre `executar`."""

    def test_dado_um_comando_com_resultado_quando_executar_entao_as_linhas_vem_com_o_nome_da_coluna(
        self,
        cliente_sql_server: ClienteSqlServer,
        instancia_sql_server: Conexao,
    ) -> None:
        linhas = cliente_sql_server.executar(instancia_sql_server, "SELECT 1 AS numero, 'PROD' AS alias")

        assert linhas == [{"numero": 1, "alias": "PROD"}]

    def test_dado_um_comando_sem_resultado_quando_executar_entao_a_lista_volta_vazia(
        self,
        cliente_sql_server: ClienteSqlServer,
        instancia_sql_server: Conexao,
    ) -> None:
        assert cliente_sql_server.executar(instancia_sql_server, "DECLARE @sem_resultado INT = 1") == []

    def test_dado_parametros_nomeados_quando_executar_entao_os_valores_chegam_a_instancia(
        self,
        cliente_sql_server: ClienteSqlServer,
        instancia_sql_server: Conexao,
    ) -> None:
        linhas = cliente_sql_server.executar(
            instancia_sql_server,
            "SELECT %(alias)s AS alias, %(porta)s AS porta",
            {"alias": "Produção", "porta": 1433},
        )

        assert linhas == [{"alias": "Produção", "porta": 1433}]

    def test_dado_o_mesmo_parametro_repetido_quando_executar_entao_basta_informa_lo_uma_vez(
        self,
        cliente_sql_server: ClienteSqlServer,
        instancia_sql_server: Conexao,
    ) -> None:
        linhas = cliente_sql_server.executar(
            instancia_sql_server,
            "SELECT %(alias)s AS primeiro, %(alias)s AS segundo",
            {"alias": "PROD"},
        )

        assert linhas == [{"primeiro": "PROD", "segundo": "PROD"}]

    def test_dado_um_por_cento_literal_ao_lado_de_parametros_quando_executar_entao_ele_precisa_estar_dobrado(
        self,
        cliente_sql_server: ClienteSqlServer,
        instancia_sql_server: Conexao,
    ) -> None:
        linhas = cliente_sql_server.executar(
            instancia_sql_server,
            "SELECT CASE WHEN %(alias)s LIKE 'PR%%' THEN 1 ELSE 0 END AS comeca_com_pr",
            {"alias": "PROD"},
        )

        assert linhas == [{"comeca_com_pr": 1}]

    def test_dada_a_mesma_conexao_quando_executar_duas_vezes_entao_o_estado_da_sessao_persiste(
        self,
        cliente_sql_server: ClienteSqlServer,
        instancia_sql_server: Conexao,
    ) -> None:
        cliente_sql_server.executar(instancia_sql_server, CRIAR_MARCA_NA_SESSAO)

        assert cliente_sql_server.executar(instancia_sql_server, PROCURAR_MARCA_NA_SESSAO) != [{"marca": None}]

    def test_dada_uma_sessao_aberta_quando_executar_um_comando_proibido_em_transacao_entao_ele_passa(
        self,
        cliente_sql_server: ClienteSqlServer,
        instancia_sql_server: Conexao,
    ) -> None:
        cliente_sql_server.executar(instancia_sql_server, "DROP DATABASE IF EXISTS fora_de_transacao")

        try:
            cliente_sql_server.executar(instancia_sql_server, "CREATE DATABASE fora_de_transacao")
        finally:
            cliente_sql_server.executar(instancia_sql_server, "DROP DATABASE IF EXISTS fora_de_transacao")

    def test_dada_uma_senha_errada_quando_executar_entao_a_falha_e_de_credenciais(
        self,
        cliente_sql_server: ClienteSqlServer,
        instancia_sql_server: Conexao,
    ) -> None:
        with pytest.raises(CredenciaisInvalidasError) as falha:
            cliente_sql_server.executar(replace(instancia_sql_server, senha="errada"), "SELECT 1")

        assert falha.value.servidor == instancia_sql_server.servidor

    def test_dado_um_host_que_nao_responde_quando_executar_entao_a_falha_e_de_instancia_inacessivel(self) -> None:
        cliente = ClienteSqlServer(login_timeout=1)
        inalcancavel = Conexao(host=HOST_INALCANCAVEL, porta=1433, usuario="sa", senha="segredo")

        with pytest.raises(InstanciaInacessivelError) as falha:
            cliente.executar(inalcancavel, "SELECT 1")

        assert falha.value.servidor == HOST_INALCANCAVEL

    def test_dado_um_comando_invalido_quando_executar_entao_a_falha_e_de_comando_recusado(
        self,
        cliente_sql_server: ClienteSqlServer,
        instancia_sql_server: Conexao,
    ) -> None:
        with pytest.raises(ComandoRecusadoError):
            cliente_sql_server.executar(instancia_sql_server, "SELECT * FROM tabela_que_nao_existe")

    def test_dado_um_comando_recusado_quando_executar_de_novo_entao_a_sessao_continua_utilizavel(
        self,
        cliente_sql_server: ClienteSqlServer,
        instancia_sql_server: Conexao,
    ) -> None:
        with pytest.raises(ComandoRecusadoError):
            cliente_sql_server.executar(instancia_sql_server, "SELECT * FROM tabela_que_nao_existe")

        assert cliente_sql_server.executar(instancia_sql_server, "SELECT 1 AS numero") == [{"numero": 1}]


class TestAquecer:
    """Cobre `aquecer`."""

    def test_dadas_conexoes_alcancavel_e_inalcancavel_quando_aquecer_entao_cada_uma_e_relatada(
        self,
        instancia_sql_server: Conexao,
    ) -> None:
        cliente = ClienteSqlServer(login_timeout=1)
        inalcancavel = Conexao(host=HOST_INALCANCAVEL, porta=1433, usuario="sa", senha="segredo")

        try:
            assert cliente.aquecer([instancia_sql_server, inalcancavel]) == {
                instancia_sql_server: True,
                inalcancavel: False,
            }
        finally:
            cliente.encerrar()


class TestEncerrar:
    """Cobre `encerrar`."""

    def test_dada_uma_sessao_aberta_quando_encerrar_e_executar_de_novo_entao_o_estado_anterior_se_perdeu(
        self,
        cliente_sql_server: ClienteSqlServer,
        instancia_sql_server: Conexao,
    ) -> None:
        cliente_sql_server.executar(instancia_sql_server, CRIAR_MARCA_NA_SESSAO)

        cliente_sql_server.encerrar()

        assert cliente_sql_server.executar(instancia_sql_server, PROCURAR_MARCA_NA_SESSAO) == [{"marca": None}]
