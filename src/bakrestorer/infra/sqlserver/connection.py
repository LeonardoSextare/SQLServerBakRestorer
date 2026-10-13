from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


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

    @model_validator(mode="after")
    def _conferir_instancia_ou_porta(self) -> Self:
        """Recusa a instância nomeada e a porta juntas.

        O nome só serve para o SQL Browser descobrir a porta, e o driver recusa
        receber os dois. Sem nenhum, a conexão vai à instância padrão, na 1433.

        Raises:
            ValueError: Se a instância e a porta vieram juntas. O Pydantic
                entrega como `ValidationError`.

        """
        if self.instancia is not None and self.porta is not None:
            mensagem = "informe a instância ou a porta, não as duas"
            raise ValueError(mensagem)

        return self

    @property
    def servidor(self) -> str:
        """Identifica a instância sem revelar credencial.

        Returns:
            str: O host, seguido da instância nomeada quando houver.

        """
        return f"{self.host}\\{self.instancia}" if self.instancia else self.host
