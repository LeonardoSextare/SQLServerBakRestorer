import flet as ft

from bakrestorer.desktop.estado import EstadoApp, Tela

TITULO = "SQLServerBackupRestorer"


@ft.component
def barra_titulo(estado: EstadoApp) -> ft.Control:
    """Desenha a barra que substitui a do Windows.

    A barra do sistema fica escondida, então esta é a única forma de arrastar,
    minimizar e fechar a janela. Por isso ela pertence à moldura, e não a uma
    tela: precisa estar visível o tempo todo.

    Recebe o estado por parâmetro, e não por contexto, porque componente que
    mora em `desktop/componentes/` não pode exigir uma tela específica acima
    dele.

    Args:
        estado: O que a janela sabe. Mudar um campo dele redesenha esta barra.

    Returns:
        A linha da barra de título.

    """
    mostrando_configuracao = estado.tela is Tela.CONFIGURACAO

    titulo_arrastavel = ft.WindowDragArea(
        content=ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.STORAGE, size=29),
                    ft.Text(TITULO, size=19, weight=ft.FontWeight.W_500),
                ],
                spacing=10,
            ),
            padding=ft.Padding.only(left=14),
            align=ft.Alignment.CENTER_LEFT,
        ),
        maximizable=False,
        expand=True,
    )

    botao_de_configuracao = ft.IconButton(
        icon=ft.Icons.ARROW_BACK if mostrando_configuracao else ft.Icons.SETTINGS,
        tooltip="Voltar" if mostrando_configuracao else "Configurações",
        icon_size=22,
        width=48,
        on_click=estado.alternar_tela,
    )

    botao_de_minimizar = ft.IconButton(
        icon=ft.Icons.REMOVE,
        tooltip="Minimizar",
        icon_size=22,
        width=48,
        on_click=_minimizar,
    )

    botao_de_fechar = ft.IconButton(
        icon=ft.Icons.CLOSE,
        tooltip="Fechar",
        icon_size=22,
        width=48,
        on_click=_fechar,
    )

    divisor = ft.Container(
        width=1,
        height=22,
        bgcolor=ft.Colors.OUTLINE_VARIANT,
        margin=ft.Margin.symmetric(horizontal=10, vertical=0),
    )

    return ft.Row(
        controls=[titulo_arrastavel, botao_de_configuracao, divisor, botao_de_minimizar, botao_de_fechar],
        spacing=0,
    )


def _minimizar() -> None:
    """Manda a janela para a barra de tarefas."""
    janela = ft.context.page.window
    janela.minimized = True
    janela.update()


async def _fechar() -> None:
    """Fecha a janela."""
    await ft.context.page.window.close()
