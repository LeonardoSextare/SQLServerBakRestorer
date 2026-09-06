from dataclasses import dataclass


@dataclass(frozen=True)
class Conexao:
    """Onde alcançar uma instância do SQL Server e com quais credenciais.

    Attributes:
        host: Máquina que hospeda a instância.
        instancia: Nome da instância nomeada, ou None para a padrão.
        porta: Porta a usar, ou None para deixar o SQL Browser resolver.
        usuario: Login do SQL Server, ou None para autenticar pelo Windows.
        senha: Senha do login, ignorada quando o usuário é None.

    """

    host: str
    instancia: str | None = None
    porta: int | None = None
    usuario: str | None = None
    senha: str | None = None

    @property
    def servidor(self) -> str:
        """Identifica a instância sem revelar credencial.

        Returns:
            str: O host, seguido da instância nomeada quando houver.

        """
        return f"{self.host}\\{self.instancia}" if self.instancia else self.host
