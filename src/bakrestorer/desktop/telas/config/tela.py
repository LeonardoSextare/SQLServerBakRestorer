from collections.abc import Callable

import flet as ft

from bakrestorer.desktop.telas.config.componentes.barra_lateral import barra_lateral
from bakrestorer.desktop.telas.config.estado import EstadoConfig, Secao
from bakrestorer.desktop.telas.config.secoes.geral import secao_geral
from bakrestorer.desktop.telas.config.secoes.sobre import secao_sobre

SECOES: dict[Secao, Callable[[], ft.Control]] = {
    Secao.GERAL: secao_geral,
    Secao.INSTANCIAS: lambda: ft.Text("Instâncias cadastradas"),
    Secao.SOBRE: secao_sobre,
}


@ft.component
def tela_config() -> ft.Control:
    """Deixa o usuário ajustar o aplicativo e cadastrar suas instâncias.

    A tela é dona do estado que as partes leem; cada parte cuida do que só ela
    precisa saber.

    Returns:
        A linha com a barra lateral e a seção escolhida.

    Note:
        O estado nasce aqui, no `use_state`, para sobreviver aos redesenhos --
        e, por ser observável, mudar um campo dele já redesenha esta tela.

        O estado é construído a cada desenho, mas só o primeiro é guardado: o
        `use_state` ignora os seguintes. Construir um dataclass à toa custa
        quase nada, e passar a classe no lugar da instância deixa o tipo
        ambíguo.

    """
    estado, _ = ft.use_state(EstadoConfig())

    return ft.Row(
        controls=[
            barra_lateral(estado),
            ft.Column(
                controls=[SECOES[estado.secao]()],
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
        ],
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        expand=True,
    )
