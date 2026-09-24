from dataclasses import dataclass
from enum import Enum

import flet as ft


class Secao(Enum):
    """As partes da configuração, na ordem em que aparecem na barra lateral."""

    GERAL = "geral"
    INSTANCIAS = "instancias"
    AUTOMACAO = "automacao"
    SOBRE = "sobre"


@ft.observable
@dataclass
class EstadoConfig:
    """Qual parte da configuração está aparecendo, e como trocar de parte.

    A tela não sabe nada do conteúdo das seções: cada uma cuida do que só ela
    precisa saber.
    """

    secao: Secao = Secao.GERAL

    def mostrar(self, secao: Secao) -> None:
        """Passa a mostrar outra parte da configuração."""
        self.secao = secao


CONTEXTO_DA_CONFIG = ft.create_context(EstadoConfig())
