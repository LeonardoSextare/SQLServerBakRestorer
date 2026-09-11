import flet as ft

from bakrestorer.desktop.moldura.estado import EstadoApp
from bakrestorer.desktop.moldura.moldura import moldura


async def main(pagina: ft.Page) -> None:
    """Prepara a janela e manda desenhar a moldura.

    Args:
        pagina: Janela entregue pelo Flet.

    Note:
        O tamanho é enviado antes de pedir para centralizar. Centralizar
        posiciona a janela pelo meio dela, usando o tamanho que o cliente
        conhece naquele momento; pedir antes deixa a janela centralizada como
        se ainda tivesse o tamanho padrão.

    """
    pagina.title = "SQLServerBackupRestorer"
    pagina.padding = 3
    pagina.window.title_bar_hidden = True
    pagina.window.resizable = False
    pagina.window.width = 640
    pagina.window.height = 470
    pagina.update()

    # await pagina.window.center() # noqa: ERA001

    pagina.render(moldura, EstadoApp())


def run() -> None:
    """Abre o aplicativo."""
    ft.run(main)


if __name__ == "__main__":
    run()
