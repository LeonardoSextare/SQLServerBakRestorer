from collections.abc import Callable

import flet as ft

from bakrestorer.desktop_shell.moldura.componentes.barra_titulo import barra_titulo
from bakrestorer.desktop_shell.moldura.view_model import CONTEXTO_DA_JANELA, JanelaViewModel, Tela
from bakrestorer.desktop_shell.telas.config.tela import tela_config
from bakrestorer.features.instancias.gui import CONTEXTO_DOS_DIAGNOSTICOS, DiagnosticosViewModel

TELAS: dict[Tela, Callable[[], ft.Control]] = {
    Tela.RESTAURACAO: lambda: ft.Text("Tela de restauração"),
    Tela.CONFIGURACAO: tela_config,
}


@ft.component
def moldura(view_model: JanelaViewModel) -> ft.Control:
    """Desenha o quadro fixo da janela e põe dentro dele a tela escolhida.

    A barra de título mora aqui porque precisa aparecer em qualquer tela, e é
    ela que troca de tela.

    Args:
        view_model: O que a janela sabe.

    Returns:
        A coluna que ocupa a janela inteira.

    Note:
        A coluna se expande de propósito: sem isso o quadro fica só do tamanho
        do que tem dentro, e nenhuma tela consegue ter altura definida.

        O tema é aplicado num efeito, e não no clique de quem escolheu: o
        seletor muda o view model, e a página é ajustada por consequência. Por isso
        a dependência do efeito é o tema -- ele roda no primeiro desenho e a
        cada troca, e em mais nenhuma hora.

        O `quadro` é montado dentro da chamada do contexto, e não antes dela:
        é durante essa chamada que o view model fica publicado, e é ali que os
        componentes abaixo conseguem alcançá-lo.

        Os diagnósticos das instâncias também nascem aqui, num contexto por
        fora do da janela: a moldura é a única parte da tela que vive o
        aplicativo inteiro, e eles precisam durar isso para mais de uma tela
        ler. Eles são da feature de instâncias; a moldura só os cria, os
        transmite e pede o primeiro diagnóstico, uma vez, ao abrir.

    """
    pagina = ft.context.page
    diagnosticos, _ = ft.use_state(DiagnosticosViewModel())

    def aplicar_tema() -> None:
        view_model.tema.aplicar(pagina)

    def quadro() -> ft.Control:
        return ft.Column(
            controls=[
                barra_titulo(view_model),
                ft.Container(content=TELAS[view_model.tela](), padding=11, expand=True),
            ],
            spacing=0,
            expand=True,
        )

    ft.use_effect(aplicar_tema, [view_model.tema])
    ft.use_effect(diagnosticos.diagnosticar_instancias_cadastradas, [])

    def quadro_com_a_janela() -> ft.Control:
        return CONTEXTO_DA_JANELA(view_model, quadro)

    return CONTEXTO_DOS_DIAGNOSTICOS(diagnosticos, quadro_com_a_janela)
