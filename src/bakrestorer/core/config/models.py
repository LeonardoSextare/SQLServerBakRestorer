from __future__ import annotations

from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

VERSAO_DA_CONFIG = 1


class Instancia(BaseModel):
    """Uma instância local do SQL Server e as credenciais escolhidas para ela.

    Attributes:
        alias: Nome escolhido pelo usuário, que identifica esta entrada.
        nome: Nome real da instância local, como SQLEXPRESS.
        usuario: Login do SQL Server.
        senha: Senha do login, em texto puro.
        pasta_dados: Onde os arquivos `.mdf` restaurados são criados. None usa a
            pasta padrão da instância.
        pasta_log: Onde os arquivos `.ldf` restaurados são criados. None usa a
            pasta padrão da instância.

    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    # TODO: Corrigir senha em texto puro antes do lançamento.
    alias: str = Field(min_length=1)
    nome: str = Field(min_length=1)
    usuario: str = Field(min_length=1)
    senha: str = Field(min_length=1)
    pasta_dados: Path | None = None
    pasta_log: Path | None = None


class Configuracao(BaseModel):
    """A configuração inteira do aplicativo.

    Imutável: toda alteração produz uma cópia revalidada por `com_alteracoes`.
    Todos os campos têm padrão, então arquivo ausente equivale a `Configuracao()`.

    Attributes:
        versao_do_formato: Versão do formato do arquivo gravado.
        instancia_padrao: Alias da instância que o aplicativo usa para ler os
            arquivos `.bak`.
        instancias: Instâncias do SQL Server configuradas.

    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    versao_da_config: int = VERSAO_DA_CONFIG
    instancia_padrao: str | None = None
    instancias: tuple[Instancia, ...] = ()

    @model_validator(mode="after")
    def _conferir_instancias(self) -> Self:
        """Confere o que só faz sentido olhando a lista de instâncias inteira.

        Returns:
            Self: A configuração validada, inalterada.

        Raises:
            ValueError: Se um alias se repete, ou se `instancia_padrao` aponta
                para um alias que não está na lista.

        """
        aliases = [instancia.alias for instancia in self.instancias]
        repetidos = sorted({alias for alias in aliases if aliases.count(alias) > 1})

        if repetidos:
            mensagem = f"alias repetido em instâncias: {repetidos}"
            raise ValueError(mensagem)

        if self.instancia_padrao and self.instancia_padrao not in aliases:
            mensagem = f"instancia_padrao '{self.instancia_padrao}' não está em instâncias"
            raise ValueError(mensagem)

        return self

    def obter_instancia(self, alias: str) -> Instancia | None:
        """Procura uma instância configurada pelo alias.

        Args:
            alias: Nome escolhido pelo usuário.

        Returns:
            Instancia: A instância cujo alias corresponde.
            None: Quando o alias é desconhecido.

        """
        return next((instancia for instancia in self.instancias if instancia.alias == alias), None)

    def alterada(self, **alteracoes: object) -> Configuracao:
        """Monta uma cópia revalidada com os campos informados substituídos.

        Args:
            **alteracoes: Nomes de campo e seus novos valores.

        Returns:
            Configuracao: Uma nova configuração já validada.

        Raises:
            ValidationError: Se a configuração resultante for inválida, ou se um
                nome de campo não for reconhecido.

        """
        return Configuracao.model_validate({**self.model_dump(), **alteracoes})
