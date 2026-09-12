from dataclasses import dataclass

import flet as ft

from bakrestorer.desktop.telas.config.estado import EstadoConfig, Secao


@dataclass(frozen=True)
class Destino:
    """Uma parte da configuração, do jeito que ela aparece na barra lateral.

    Attributes:
        secao: A parte que este item abre.
        icone: Ícone mostrado no item.
        rotulo: Nome que aparece abaixo do ícone.

    """

    secao: Secao
    icone: ft.IconData
    rotulo: str


DESTINOS_DO_TOPO = (
    Destino(Secao.GERAL, ft.Icons.TUNE, "Geral"),
    Destino(Secao.INSTANCIAS, ft.Icons.COMPUTER_OUTLINED, "Instâncias"),
    Destino(Secao.AUTOMACAO, ft.Icons.TERMINAL, "Automação"),
)

DESTINOS_DO_FIM = (Destino(Secao.SOBRE, ft.Icons.INFO_OUTLINE, "Sobre"),)

TAMANHO_DO_ITEM = 76


@ft.component
def barra_lateral(estado: EstadoConfig) -> ft.Control:
    """Deixa o usuário andar entre as partes da configuração.

    Usa o `NavigationRail`, o componente do Material para navegação lateral,
    que traz por conta própria o indicador de selecionado, a animação e a
    navegação por teclado.

    Args:
        estado: O que a tela de configuração sabe.

    Returns:
        A barra lateral.

    Note:
        São dois rails, e não um: o "Sobre" precisa ficar no rodapé, e um rail
        só alinha o grupo inteiro.

        O rail recusa altura ilimitada, que é o que uma coluna oferece por
        padrão. O de cima resolve isso se expandindo -- e, de quebra, é a
        expansão dele que empurra o de baixo para o rodapé. O de baixo tem
        altura fixa, calculada pelo tamanho de um item.

    """
    return ft.Container(
        content=ft.Column(
            controls=[
                _navigation_rail(estado, DESTINOS_DO_TOPO, expandir=True),
                ft.Divider(height=1),
                _navigation_rail(estado, DESTINOS_DO_FIM, expandir=False),
            ],
            spacing=0,
            expand=True,
        ),
        border=ft.Border.only(right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
        padding=ft.Padding.only(right=5),
    )


def _navigation_rail(estado: EstadoConfig, destinos: tuple[Destino, ...], *, expandir: bool) -> ft.Control:
    """Monta um grupo de destinos como um rail.

    Args:
        estado: O que a tela de configuração sabe.
        destinos: As partes deste grupo, na ordem em que aparecem.
        expandir: Se este rail ocupa a altura que sobrar. Quando não ocupa,
            recebe altura fixa: o rail não desenha com altura ilimitada.

    Returns:
        O rail do grupo.

    Note:
        O rail trabalha por posição: ele avisa qual índice foi escolhido, e a
        ordem de `destinos` é que traduz isso de volta em seção.

        O índice sai como None quando a seção mostrada pertence ao outro
        grupo, e aí este rail fica sem destaque nenhum.

    """
    selecionado = next((indice for indice, destino in enumerate(destinos) if destino.secao is estado.secao), None)

    def ao_escolher(evento: ft.Event[ft.NavigationRail]) -> None:
        estado.mostrar(destinos[evento.control.selected_index or 0].secao)

    return ft.NavigationRail(
        selected_index=selecionado,
        destinations=[ft.NavigationRailDestination(icon=d.icone, label=d.rotulo) for d in destinos],
        label_type=ft.NavigationRailLabelType.ALL,
        group_alignment=-1.0,
        min_width=TAMANHO_DO_ITEM,
        bgcolor=ft.Colors.TRANSPARENT,
        expand=expandir,
        height=None if expandir else TAMANHO_DO_ITEM * len(destinos),
        on_change=ao_escolher,
    )
