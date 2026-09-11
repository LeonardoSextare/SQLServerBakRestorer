import flet as ft

from bakrestorer.desktop.moldura.estado import CONTEXTO_DA_JANELA
from bakrestorer.desktop.tema import Tema


@ft.component
def secao_geral() -> ft.Control:
    """Deixa o usuário ajustar como o aplicativo se comporta e se parece.

    Returns:
        A coluna da seção.

    Note:
        O estado da janela chega por contexto, e não por parâmetro: o tema é
        assunto da janela inteira, e o caminho até aqui passa por componentes
        que não têm nada a ver com ele.

    """
    estado = ft.use_context(CONTEXTO_DA_JANELA)

    def escolher_tema(evento: ft.Event[ft.Dropdown]) -> None:
        escolhido = evento.control.value

        if escolhido:
            estado.mudar_tema(Tema[escolhido])

    def avisar_que_nao_associa() -> None:
        ft.context.page.show_dialog(ft.SnackBar(content=ft.Text("Associação de arquivos ainda não implementada")))

    cabecalho = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.TUNE, size=24, color=ft.Colors.PRIMARY),
                ft.Text("Geral", size=21, weight=ft.FontWeight.W_600),
            ],
            spacing=9,
        ),
        padding=ft.Padding.only(left=2, bottom=8),
        height=44,
        align=ft.Alignment.CENTER_LEFT,
    )

    associacao = ft.Card(
        content=ft.ListTile(
            title=ft.Text("Arquivos .bak", size=15),
            trailing=ft.TextButton("Associar", icon=ft.Icons.LINK, on_click=avisar_que_nao_associa),
            min_height=54,
            content_padding=ft.Padding.symmetric(horizontal=14, vertical=4),
        ),
    )

    idioma = ft.Card(
        content=ft.ListTile(
            title=ft.Text("Idioma", size=15),
            trailing=ft.Dropdown(
                value="Português",
                options=[ft.DropdownOption(key="Português"), ft.DropdownOption(key="English")],
                width=140,
                text_size=13,
                dense=True,
                content_padding=ft.Padding.symmetric(horizontal=10, vertical=0),
                disabled=True,
            ),
            min_height=54,
            content_padding=ft.Padding.symmetric(horizontal=14, vertical=4),
        ),
    )

    visual = ft.Card(
        content=ft.ListTile(
            title=ft.Text("Tema", size=15),
            trailing=ft.Dropdown(
                value=estado.tema.name,
                options=[ft.DropdownOption(key=disponivel.name, text=disponivel.rotulo) for disponivel in Tema],
                width=140,
                text_size=13,
                dense=True,
                content_padding=ft.Padding.symmetric(horizontal=10, vertical=0),
                on_select=escolher_tema,
            ),
            min_height=54,
            content_padding=ft.Padding.symmetric(horizontal=14, vertical=4),
        ),
    )

    return ft.Column(controls=[cabecalho, associacao, idioma, visual], spacing=3)
