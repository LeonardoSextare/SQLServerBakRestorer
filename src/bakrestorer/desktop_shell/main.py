import flet as ft

from bakrestorer.desktop_shell.moldura.estado import EstadoApp
from bakrestorer.desktop_shell.moldura.moldura import moldura


async def main(pagina: ft.Page) -> None:
    """Prepara a janela e manda desenhar a moldura.

    Args:
        pagina: Janela entregue pelo Flet.

    Note:
        A janela nasce escondida e só aparece depois de dimensionada e
        centralizada, para o usuário não ver ela abrir no tamanho padrão e
        encolher. O tamanho é enviado antes de pedir para centralizar, porque
        centralizar usa o tamanho que o cliente conhece naquele momento.

    """
    pagina.title = "SQLServerBackupRestorer"
    pagina.padding = 3
    pagina.window.title_bar_hidden = True
    pagina.window.resizable = False
    pagina.window.width = 640
    pagina.window.height = 470
    pagina.update()

    await pagina.window.center()
    pagina.window.visible = True
    pagina.update()

    pagina.render(moldura, EstadoApp())


def run() -> None:
    """Abre o aplicativo."""
    ft.run(main, view=ft.AppView.FLET_APP_HIDDEN)


if __name__ == "__main__":
    run()
