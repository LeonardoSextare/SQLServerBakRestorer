from collections.abc import Callable

import flet as ft

from bakrestorer.desktop.componentes.barra_titulo import barra_titulo
from bakrestorer.desktop.estado import EstadoApp, Tela

TELAS: dict[Tela, Callable[[], ft.Control]] = {
    Tela.RESTAURACAO: lambda: ft.Text("Tela de restauração"),
    Tela.CONFIGURACAO: lambda: ft.Text("Tela de configuração"),
}


@ft.component
def moldura(estado: EstadoApp) -> ft.Control:
    """Desenha o quadro fixo da janela e põe dentro dele a tela escolhida.

    A barra de título mora aqui porque precisa aparecer em qualquer tela, e é
    ela que troca de tela.

    Args:
        estado: O que a janela sabe.

    Returns:
        A coluna que ocupa a janela inteira.

    Note:
        A coluna se expande de propósito: sem isso o quadro fica só do tamanho
        do que tem dentro, e nenhuma tela consegue ter altura definida.

    """
    return ft.Column(
        controls=[
            barra_titulo(estado),
            ft.Container(
                content=TELAS[estado.tela](),
                padding=11,
                expand=True,
            ),
        ],
        spacing=0,
        expand=True,
    )
