from collections.abc import Callable

import flet as ft

from bakrestorer.features.instancias import Diagnostico
from bakrestorer.features.instancias.gui.componentes.checklist_do_diagnostico import checklist_do_diagnostico


@ft.component
def indicador_de_diagnostico(diagnostico: Diagnostico) -> ft.Control:
    """Desenha o resumo do diagnóstico num ícone que, clicado, abre o checklist completo.

    Só o ícone, para caber onde não sobra espaço, como o rodapé do formulário.
    O componente guarda se o mouse está em cima e se o checklist está aberto: é
    estado só da tela, e por isso não vai para um view model.
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
    """Desenha o diálogo com o checklist do diagnóstico."""
    return ft.AlertDialog(
        title=ft.Text("Diagnóstico", size=18, weight=ft.FontWeight.W_600),
        content=ft.Container(content=checklist_do_diagnostico(diagnostico), width=420),
        actions=[ft.TextButton(content="Fechar", on_click=lambda _: ao_fechar())],
        shape=ft.RoundedRectangleBorder(radius=20),
        on_dismiss=lambda _: ao_fechar(),
    )
