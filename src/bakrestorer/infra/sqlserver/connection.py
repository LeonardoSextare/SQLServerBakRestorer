from pydantic import BaseModel, ConfigDict, Field


class Conexao(BaseModel):
    """Onde alcançar uma instância do SQL Server e com quais credenciais.

    Imutável e comparada por valor, o que a deixa servir de chave de dicionário:
    duas conexões com os mesmos campos são a mesma chave.

    Attributes:
        host: Máquina que hospeda a instância.
        instancia: Nome da instância nomeada, ou None para a padrão.
        porta: Porta a usar, ou None para deixar o SQL Browser resolver.
        usuario: Login do SQL Server, ou None para autenticar pelo Windows.
        senha: Senha do login, ignorada quando o usuário é None.

    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    host: str = Field(min_length=1)
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
