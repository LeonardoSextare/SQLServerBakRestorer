import flet as ft

from bakrestorer.features.instancias import Instancia
from bakrestorer.features.instancias.gui.formulario import formulario
from bakrestorer.features.instancias.gui.view_model import InstanciasViewModel

ALTURA_DO_CABECALHO = 44


@ft.component
def secao_instancias() -> ft.Control:
    """Mostra as instâncias do SQL Server já cadastradas.

    O view model nasce aqui porque esta seção é o topo do que a feature desenha:
    quem a monta não precisa saber que ela lê disco.

    Sem nada cadastrado, a seção não mostra lista vazia: mostra o convite para
    cadastrar. É a primeira execução, e não uma falha.

    O convite é centralizado no espaço que sobra abaixo do cabeçalho, e esse
    espaço não é a área inteira. O recuo embaixo devolve a diferença:
    centralizar numa área encurtada por baixo sobe o conteúdo pela metade do que
    foi encurtado.

    Com o formulário aberto, ele ocupa o lugar da lista, e a seta do cabeçalho
    volta para ela sem salvar. Quem decide qual dos dois aparece é o view model.
    """
    view_model, _ = ft.use_state(InstanciasViewModel())

    ft.use_effect(view_model.carregar, [])

    if view_model.formulario_aberto:
        return _painel_do_formulario(view_model)

    return _lista_de_instancias(view_model)


def _cabecalho_da_secao(icone: ft.Control, titulo: str, *, botao: ft.Control | None = None) -> ft.Control:
    """Desenha o título da seção, com o ícone ou a seta antes dele e, se houver, o botão no canto."""
    botao_no_canto: list[ft.Control] = [ft.Container(expand=True), botao] if botao is not None else []

    return ft.Container(
        content=ft.Row(
            controls=[icone, ft.Text(titulo, size=21, weight=ft.FontWeight.W_600), *botao_no_canto],
            spacing=9,
        ),
        padding=ft.Padding.only(left=2, bottom=8),
        height=ALTURA_DO_CABECALHO,
        align=ft.Alignment.CENTER_LEFT,
    )


def _lista_de_instancias(view_model: InstanciasViewModel) -> ft.Control:
    """Desenha o cabeçalho com o botão de adicionar e, abaixo dele, os cartões ou o convite.

    O botão desce 2 pixels de propósito. O olho lê o título pelo miolo das
    minúsculas, que fica abaixo do centro da caixa do texto; centralizado pela
    caixa, o botão parece mais alto que o título.
    """
    cabecalho = _cabecalho_da_secao(
        ft.Icon(ft.Icons.COMPUTER_OUTLINED, size=24, color=ft.Colors.PRIMARY),
        "Instâncias",
        botao=ft.Container(
            content=ft.FilledTonalIconButton(
                icon=ft.Icons.ADD,
                icon_size=20,
                tooltip="Adicionar instância",
                width=48,
                height=32,
                style=ft.ButtonStyle(shape=ft.StadiumBorder(), padding=0),
                on_click=lambda _: view_model.abrir_cadastro(),
            ),
            padding=ft.Padding.only(top=2),
        ),
    )

    return ft.Column(controls=[cabecalho, _cartoes_ou_convite(view_model)], spacing=3, expand=True)


def _cartoes_ou_convite(view_model: InstanciasViewModel) -> ft.Control:
    """Desenha os cartões das instâncias, ou o convite quando ainda não há nenhuma."""
    cadastro = view_model.cadastro

    if cadastro is None or not cadastro.itens:
        return _convite_para_cadastrar()

    cartoes = [
        _cartao_da_instancia(view_model, instancia, padrao=instancia.alias == cadastro.padrao)
        for instancia in cadastro.itens
    ]
    return ft.Column(controls=cartoes, spacing=3, scroll=ft.ScrollMode.AUTO, expand=True)


def _convite_para_cadastrar() -> ft.Control:
    """Desenha o cartão que aparece quando ainda não há instância cadastrada."""
    return ft.Container(
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
        padding=ft.Padding.only(bottom=ALTURA_DO_CABECALHO),
        expand=True,
    )


def _cartao_da_instancia(view_model: InstanciasViewModel, instancia: Instancia, *, padrao: bool) -> ft.Control:
    """Desenha o cartão de uma instância. Clicar nele abre a edição.

    A padrão leva o selo "Padrão" ao lado do nome. O menu fica em todos os
    cartões, e é ali que moram as ações do cartão -- hoje só definir como
    padrão, que fica desabilitado na que já é.
    """
    selo_de_padrao = ft.Container(
        content=ft.Text("Padrão", size=10.5, weight=ft.FontWeight.W_600, color=ft.Colors.PRIMARY),
        bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.PRIMARY),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.35, ft.Colors.PRIMARY)),
        padding=ft.Padding.symmetric(horizontal=7, vertical=1),
        border_radius=20,
        tooltip="A instância que o aplicativo usa para ler os backups",
    )
    nome = ft.Text(instancia.alias, size=15, weight=ft.FontWeight.W_500)

    menu = ft.PopupMenuButton(
        icon=ft.Icons.MORE_HORIZ,
        icon_size=18,
        tooltip="Mais opções",
        menu_position=ft.PopupMenuPosition.UNDER,
        menu_padding=ft.Padding.symmetric(vertical=6),
        shape=ft.RoundedRectangleBorder(radius=10),
        items=[
            ft.PopupMenuItem(
                content=ft.Text("Definir como padrão", size=14),
                icon=ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=19),
                height=38,
                padding=ft.Padding.symmetric(horizontal=14),
                disabled=padrao,
                on_click=lambda _: view_model.definir_padrao(instancia),
            ),
        ],
    )

    return ft.Card(
        content=ft.ListTile(
            leading=ft.Icon(ft.Icons.STORAGE, size=20, color=ft.Colors.PRIMARY),
            title=ft.Row(controls=[nome, selo_de_padrao] if padrao else [nome], spacing=8, tight=True),
            subtitle=ft.Text(f"{instancia.nome} · {instancia.usuario}", size=13, opacity=0.7),
            trailing=menu,
            min_height=62,
            content_padding=ft.Padding.symmetric(horizontal=14, vertical=4),
            on_click=lambda _: view_model.abrir_edicao(instancia),
        ),
    )


def _painel_do_formulario(view_model: InstanciasViewModel) -> ft.Control:
    """Desenha o formulário no lugar da lista, com a seta para voltar no cabeçalho.

    O formulário recebe toda a altura que sobra abaixo do cabeçalho, para
    prender o rodapé dele embaixo.
    """
    titulo = "Nova instância" if view_model.instancia_em_edicao is None else "Editar instância"

    cabecalho = _cabecalho_da_secao(
        ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            tooltip="Voltar sem salvar",
            on_click=lambda _: view_model.fechar_formulario(),
        ),
        titulo,
    )

    return ft.Column(
        controls=[
            cabecalho,
            ft.Container(
                content=formulario(
                    view_model.instancia_em_edicao,
                    ao_salvar=view_model.salvar,
                    ao_cancelar=view_model.fechar_formulario,
                ),
                padding=ft.Padding.only(left=2, right=8, top=8, bottom=4),
                expand=True,
            ),
        ],
        spacing=3,
        expand=True,
    )
