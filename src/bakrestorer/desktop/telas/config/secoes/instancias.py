import flet as ft

from bakrestorer.desktop.telas.config.estado import CONTEXTO_DA_CONFIG


@ft.component
def secao_instancias() -> ft.Control:
    """Mostra as instâncias do SQL Server já cadastradas.

    Returns:
        A coluna da seção.

    Note:
        A configuração chega por contexto porque as seções são escolhidas por
        uma tabela, que não tem como passar argumento para cada uma.

        Sem configuração gravada, a tela não mostra lista vazia: mostra o
        convite para cadastrar. É a primeira execução, e não uma falha.

        O convite é centralizado no espaço que sobra abaixo do cabeçalho, e
        esse espaço não é a área inteira. O recuo embaixo devolve a diferença:
        centralizar numa área encurtada por baixo sobe o conteúdo pela metade
        do que foi encurtado.

    """
    estado = ft.use_context(CONTEXTO_DA_CONFIG)
    configuracao = estado.configuracao

    cabecalho = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.COMPUTER_OUTLINED, size=24, color=ft.Colors.PRIMARY),
                ft.Text("Instâncias", size=21, weight=ft.FontWeight.W_600),
            ],
            spacing=9,
        ),
        padding=ft.Padding.only(left=2, bottom=8),
        height=44,
        align=ft.Alignment.CENTER_LEFT,
    )

    if configuracao is None or not configuracao.instancias:
        cartao_do_convite = ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.STORAGE, size=34, opacity=0.5),
                            ft.Text("Nenhuma instância cadastrada", size=15),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        tight=True,
                    ),
                    padding=ft.Padding.symmetric(horizontal=24, vertical=26),
                ),
                width=300,
            ),
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.only(bottom=44),
            expand=True,
        )

        return ft.Column(
            controls=[cabecalho, cartao_do_convite],
            spacing=3,
            expand=True,
        )

    cartoes: list[ft.Control] = [
        ft.Card(
            content=ft.ListTile(
                leading=ft.Icon(ft.Icons.STORAGE, size=20, color=ft.Colors.PRIMARY),
                title=ft.Text(instancia.alias, size=15, weight=ft.FontWeight.W_500),
                subtitle=ft.Text(f"{instancia.nome} · {instancia.usuario}", size=13, opacity=0.7),
                trailing=(
                    ft.Icon(ft.Icons.STAR, size=18, color=ft.Colors.PRIMARY)
                    if instancia.alias == configuracao.instancia_padrao
                    else None
                ),
                min_height=62,
                content_padding=ft.Padding.symmetric(horizontal=14, vertical=4),
            ),
        )
        for instancia in configuracao.instancias
    ]

    lista = ft.Column(controls=cartoes, spacing=3, scroll=ft.ScrollMode.AUTO, expand=True)

    return ft.Column(controls=[cabecalho, lista], spacing=3, expand=True)
