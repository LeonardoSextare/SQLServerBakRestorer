from collections.abc import Callable

import flet as ft

from bakrestorer.desktop.moldura.componentes.barra_titulo import barra_titulo
from bakrestorer.desktop.moldura.estado import CONTEXTO_DA_JANELA, EstadoApp, Tela
from bakrestorer.desktop.telas.config.tela import tela_config

TELAS: dict[Tela, Callable[[], ft.Control]] = {
    Tela.RESTAURACAO: lambda: ft.Text("Tela de restauração"),
    Tela.CONFIGURACAO: tela_config,
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

        O tema é aplicado num efeito, e não no clique de quem escolheu: o
        seletor muda o estado, e a página é ajustada por consequência. Por isso
        a dependência do efeito é o tema -- ele roda no primeiro desenho e a
        cada troca, e em mais nenhuma hora.

        O `quadro` é montado dentro da chamada do contexto, e não antes dela:
        é durante essa chamada que o estado fica publicado, e é ali que os
        componentes abaixo conseguem alcançá-lo.

    """
    pagina = ft.context.page

    def aplicar_tema() -> None:
        estado.tema.aplicar(pagina)

    def quadro() -> ft.Control:
        return ft.Column(
            controls=[
                barra_titulo(estado),
                ft.Container(content=TELAS[estado.tela](), padding=11, expand=True),
            ],
            spacing=0,
            expand=True,
        )

    ft.use_effect(aplicar_tema, [estado.tema])

    return CONTEXTO_DA_JANELA(estado, quadro)
