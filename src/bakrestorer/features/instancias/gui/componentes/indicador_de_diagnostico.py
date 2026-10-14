from collections.abc import Callable

import flet as ft

from bakrestorer.features.instancias import Diagnostico, Verificacao


@ft.component
def indicador_de_diagnostico(diagnostico: Diagnostico) -> ft.Control:
    """Desenha o resumo do diagnóstico num ícone que, clicado, abre o checklist completo.

    Só o ícone, para caber onde não sobra espaço, como o rodapé do formulário e
    o cartão da lista. O componente guarda se o mouse está em cima e se o
    checklist está aberto: é estado só da tela, e por isso não vai para um view
    model.
    """
    posicao_do_mouse, marcar_posicao_do_mouse = ft.use_state("fora")
    checklist, marcar_checklist = ft.use_state("fechado")

    ft.use_dialog(
        _checklist(diagnostico, ao_fechar=lambda: marcar_checklist("fechado")) if checklist == "aberto" else None,
    )

    match diagnostico.situacao:
        case "erro":
            icone, cor = ft.Icons.CANCEL, ft.Colors.RED

        case "aviso":
            icone, cor = ft.Icons.ERROR, ft.Colors.AMBER
        case "ok":
            icone, cor = ft.Icons.CHECK_CIRCLE, ft.Colors.GREEN

    return ft.GestureDetector(
        content=ft.Icon(
            icone,
            size=20,
            color=cor,
            scale=1.2 if posicao_do_mouse == "em_cima" else 1,
            animate_scale=ft.Animation(duration=150, curve=ft.AnimationCurve.EASE_OUT),
        ),
        tooltip="Ver diagnóstico",
        mouse_cursor=ft.MouseCursor.CLICK,
        on_enter=lambda _: marcar_posicao_do_mouse("em_cima"),
        on_exit=lambda _: marcar_posicao_do_mouse("fora"),
        on_tap=lambda _: marcar_checklist("aberto"),
    )


def _checklist(diagnostico: Diagnostico, ao_fechar: Callable[[], None]) -> ft.AlertDialog:
    """Desenha o diálogo com cada verificação do diagnóstico, uma por linha, na ordem em que rodam."""
    latencia = ""

    if diagnostico.latencia is not None:
        milissegundos = diagnostico.latencia.total_seconds() * 1000
        latencia = "< 1 ms" if milissegundos < 1 else f"{milissegundos:.0f} ms"

    return ft.AlertDialog(
        title=ft.Text("Diagnóstico", size=18, weight=ft.FontWeight.W_600),
        content=ft.Column(
            controls=[
                _linha_da_verificacao("Conexão", diagnostico.conexao, complemento=latencia),
                _linha_da_verificacao("Autenticação", diagnostico.login),
            ],
            spacing=12,
            tight=True,
            width=420,
        ),
        actions=[ft.TextButton(content="Fechar", on_click=lambda _: ao_fechar())],
        shape=ft.RoundedRectangleBorder(radius=20),
        on_dismiss=lambda _: ao_fechar(),
    )


def _linha_da_verificacao(nome: str, verificacao: Verificacao, *, complemento: str = "") -> ft.Control:
    """Desenha uma verificação: o ícone e o nome à esquerda, a situação à direita e, embaixo, o que o servidor disse.

    A situação usa sempre as mesmas palavras, qualquer que seja a verificação,
    para o checklist ler igual quando ganhar itens novos. O detalhe é
    selecionável para dar para copiar a mensagem do servidor. O erro sem
    detalhe é o tempo de espera que acabou sem resposta nenhuma.
    """
    match verificacao.situacao:
        case "ok":
            icone, cor, situacao = ft.Icons.CHECK_CIRCLE, ft.Colors.GREEN, "OK"
        case "aviso":
            icone, cor, situacao = ft.Icons.ERROR, ft.Colors.AMBER, "Aviso"
        case "erro":
            icone, cor, situacao = ft.Icons.CANCEL, ft.Colors.RED, "Falha"
        case "nao_verificado":
            icone, cor, situacao = ft.Icons.REMOVE_CIRCLE_OUTLINE, ft.Colors.ON_SURFACE_VARIANT, "Não verificado"

    detalhe = verificacao.detalhe

    if verificacao.situacao == "erro" and not detalhe:
        detalhe = "Tempo limite de conexão esgotado."

    linha = ft.Row(
        controls=[
            ft.Icon(icone, size=18, color=cor),
            ft.Text(nome, size=14, expand=True),
            ft.Text(f"{situacao} · {complemento}" if complemento else situacao, size=12, opacity=0.6),
        ],
        spacing=10,
    )

    if not detalhe:
        return linha

    return ft.Column(
        controls=[
            linha,
            ft.Container(
                content=ft.Text(detalhe, size=12, opacity=0.75, selectable=True),
                padding=ft.Padding.only(left=28),
            ),
        ],
        spacing=2,
        tight=True,
    )
