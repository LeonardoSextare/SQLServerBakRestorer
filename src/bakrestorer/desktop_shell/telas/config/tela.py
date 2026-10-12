from collections.abc import Callable

import flet as ft

from bakrestorer.desktop_shell.telas.config.componentes.barra_lateral import barra_lateral
from bakrestorer.desktop_shell.telas.config.secoes.geral import secao_geral
from bakrestorer.desktop_shell.telas.config.secoes.sobre import secao_sobre
from bakrestorer.desktop_shell.telas.config.view_model import CONTEXTO_DA_CONFIG, ConfigViewModel, Secao
from bakrestorer.features.automacao.gui import secao_automacao
from bakrestorer.features.instancias.gui import secao_instancias

SECOES: dict[Secao, Callable[[], ft.Control]] = {
    Secao.GERAL: secao_geral,
    Secao.INSTANCIAS: secao_instancias,
    Secao.AUTOMACAO: secao_automacao,
    Secao.SOBRE: secao_sobre,
}


@ft.component
def tela_config() -> ft.Control:
    """Deixa o usuário ajustar o aplicativo e cadastrar suas instâncias.

    A tela é dona do view model que as partes leem; cada parte cuida do que só ela
    precisa saber.

    Returns:
        A linha com a barra lateral e a seção escolhida.

    Note:
        O view model nasce aqui, no `use_state`, para sobreviver aos redesenhos --
        e, por ser observável, mudar um campo dele já redesenha esta tela.

        O view model é construído a cada desenho, mas só o primeiro é guardado: o
        `use_state` ignora os seguintes. Construir um dataclass à toa custa
        quase nada, e passar a classe no lugar da instância deixa o tipo
        ambíguo.

    """
    view_model, _ = ft.use_state(ConfigViewModel())

    def quadro() -> ft.Control:
        return ft.Row(
            controls=[
                barra_lateral(view_model),
                ft.Container(
                    content=SECOES[view_model.secao](),
                    expand=True,
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            expand=True,
        )

    return CONTEXTO_DA_CONFIG(view_model, quadro)
