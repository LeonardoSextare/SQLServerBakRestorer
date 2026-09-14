from dataclasses import dataclass
from enum import Enum

import flet as ft

from bakrestorer.desktop.servicos import instancias_service
from bakrestorer.features.instancias import ConfigInstancias


class Secao(Enum):
    """As partes da configuração, na ordem em que aparecem na barra lateral."""

    GERAL = "geral"
    INSTANCIAS = "instancias"
    AUTOMACAO = "automacao"
    SOBRE = "sobre"


@ft.observable
@dataclass
class EstadoConfig:
    """O que a tela de configuração precisa saber, e as ações que mudam isso.

    Attributes:
        secao: Qual parte da configuração está aparecendo.
        cadastro: O que está gravado em disco, ou None enquanto a tela ainda
            não leu. Cadastro sem nenhuma instância volta como uma lista vazia,
            e não como None.

    """

    secao: Secao = Secao.GERAL
    cadastro: ConfigInstancias | None = None

    def mostrar(self, secao: Secao) -> None:
        """Passa a mostrar outra parte da configuração.

        Args:
            secao: A parte escolhida na barra lateral.

        """
        self.secao = secao

    def carregar(self) -> None:
        """Lê do disco o que está gravado.

        Note:
            Ler é do estado, e não do componente: o componente só desenha o
            que já foi lido. Quem chama isto é um efeito, porque tocar o disco
            durante o desenho faria a leitura acontecer a cada redesenho.

        """
        self.cadastro = instancias_service().carregar()


CONTEXTO_DA_CONFIG = ft.create_context(EstadoConfig())
