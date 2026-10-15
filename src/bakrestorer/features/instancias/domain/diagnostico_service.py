from bakrestorer.features.instancias.domain.models import Diagnostico, Instancia, Verificacao
from bakrestorer.features.instancias.domain.queries import PERMISSOES_DE_RESTAURACAO
from bakrestorer.infra.sqlserver import (
    ClienteSqlServer,
    Conexao,
    CredenciaisInvalidasError,
    InstanciaInacessivelError,
)


class DiagnosticoService:
    """Pergunta às instâncias do SQL Server se elas estão prontas para restaurar.

    Não guarda estado, e o cliente também não: cada pergunta abre a própria
    conexão, e por isso as instâncias podem ser diagnosticadas ao mesmo tempo.

    Instância fora do ar e credencial recusada não são falha do diagnóstico:
    são a resposta dele, e voltam como verificações do `Diagnostico`.
    """

    def __init__(self, cliente: ClienteSqlServer) -> None:
        self._cliente = cliente

    def diagnosticar(self, instancia: Instancia) -> Diagnostico:
        """Pergunta à instância tudo que decide se ela está pronta para restaurar.

        Reúne as conferências na ordem em que uma depende da outra: primeiro o
        acesso e, só com o login aceito, as permissões dele.

        Raises:
            ComandoRecusadoError: Se a instância aceitou o login e recusou o
                ping ou a consulta das permissões. Ninguém espera por isso.

        """
        diagnostico = self.conferir_acesso_a_instancia(instancia)

        if diagnostico.login.situacao != "ok":
            return diagnostico

        permissoes = self.conferir_permissoes_da_instancia(instancia)
        diagnostico.criacao_de_banco, diagnostico.sobrescrita_de_banco = permissoes

        return diagnostico

    def conferir_acesso_a_instancia(self, instancia: Instancia) -> Diagnostico:
        """Pergunta à instância se ela responde e se o login é aceito.

        O cliente abre uma conexão só para a pergunta, então o login é sempre de
        verdade, e não uma sessão antiga que já estava aberta.

        Raises:
            ComandoRecusadoError: Se a instância aceitou o login e recusou o
                ping. Ninguém espera por isso.

        """
        try:
            latencia = self._cliente.ping(_montar_conexao(instancia))
        except InstanciaInacessivelError as falha:
            return Diagnostico(
                id_da_instancia=instancia.id,
                conexao=Verificacao(situacao="erro", detalhe=falha.detalhe),
            )
        except CredenciaisInvalidasError as falha:
            return Diagnostico(
                id_da_instancia=instancia.id,
                conexao=Verificacao(situacao="ok"),
                login=Verificacao(situacao="erro", detalhe=falha.detalhe),
            )

        return Diagnostico(
            id_da_instancia=instancia.id,
            conexao=Verificacao(situacao="ok"),
            login=Verificacao(situacao="ok"),
            latencia=latencia,
        )

    def conferir_permissoes_da_instancia(self, instancia: Instancia) -> tuple[Verificacao, Verificacao]:
        """Pergunta se o login da instância pode criar banco e sobrescrever banco, nessa ordem.

        As duas saem de uma consulta só. Criar banco basta com `sysadmin`,
        `dbcreator` ou `CREATE ANY DATABASE`. Sobrescrever qualquer banco pede
        `sysadmin` ou `dbcreator`; sem eles o login só sobrescreve os bancos de
        que é dono, e isso é aviso, porque o banco de destino só aparece na hora
        de restaurar.

        Se a instância não responder ou recusar o login, as duas ficam não
        verificadas: quem conta essa falha é a conferência do acesso.

        Raises:
            ComandoRecusadoError: Se a instância aceitou o login e recusou a
                consulta. Ninguém espera por isso.

        """
        try:
            permissoes = self._cliente.executar(_montar_conexao(instancia), PERMISSOES_DE_RESTAURACAO)[0]
        except InstanciaInacessivelError, CredenciaisInvalidasError:
            return Verificacao(situacao="nao_verificado"), Verificacao(situacao="nao_verificado")

        papel_de_restaurar = bool(permissoes["sysadmin"]) or bool(permissoes["dbcreator"])
        pode_criar_banco = papel_de_restaurar or bool(permissoes["cria_banco"])

        return (
            Verificacao(situacao="ok" if pode_criar_banco else "erro"),
            Verificacao(situacao="ok" if papel_de_restaurar else "aviso"),
        )


def _montar_conexao(instancia: Instancia) -> Conexao:
    """Traduz a instância na conexão que o cliente do SQL Server entende."""
    return Conexao(
        host=instancia.host,
        instancia=instancia.nome,
        porta=instancia.porta,
        usuario=instancia.usuario,
        senha=instancia.senha,
    )
