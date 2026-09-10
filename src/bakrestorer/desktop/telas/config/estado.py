from dataclasses import dataclass
from enum import Enum

import flet as ft


class Secao(Enum):
    """As partes da configuração, na ordem em que aparecem na barra lateral."""

    GERAL = "geral"
    INSTANCIAS = "instancias"
    SOBRE = "sobre"


@ft.observable
@dataclass
class EstadoConfig:
    """O que a tela de configuração precisa saber, e as ações que mudam isso.

    Attributes:
        secao: Qual parte da configuração está aparecendo.

    """

    secao: Secao = Secao.GERAL

    def mostrar(self, secao: Secao) -> None:
        """Passa a mostrar outra parte da configuração.

        Args:
            secao: A parte escolhida na barra lateral.

        """
        self.secao = secao
