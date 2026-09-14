import flet as ft


@ft.component
def secao_automacao() -> ft.Control:
    """Mostra onde o usuário vai estender o aplicativo com um script próprio.

    Ainda não faz nada: só segura o lugar. O que ela vai ser está em
    `.claude/tarefas/secao-de-automacao.md`.
    """
    cabecalho = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.TERMINAL, size=24, color=ft.Colors.PRIMARY),
                ft.Text("Automação", size=21, weight=ft.FontWeight.W_600),
            ],
            spacing=9,
        ),
        padding=ft.Padding.only(left=2, bottom=8),
        height=44,
        align=ft.Alignment.CENTER_LEFT,
    )

    return ft.Column(controls=[cabecalho], spacing=3, expand=True)
