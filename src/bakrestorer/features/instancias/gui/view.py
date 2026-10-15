import flet as ft

from bakrestorer.features.instancias import Diagnostico, Instancia
from bakrestorer.features.instancias.gui.componentes.checklist_do_diagnostico import checklist_do_diagnostico
from bakrestorer.features.instancias.gui.diagnosticos.view_model import CONTEXTO_DOS_DIAGNOSTICOS, DiagnosticosViewModel
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

    A confirmação de remover e os detalhes da instância são pedidos a cada
    desenho: o `use_dialog` mantém o diálogo aberto enquanto recebe um, e fecha
    quando recebe None. Pedir a cada desenho também é o que faz os detalhes
    acompanharem um diagnóstico que chega com eles abertos.

    Os diagnósticos chegam pelo contexto que a moldura provê, porque duram o
    aplicativo inteiro e não só esta seção. Salvar uma instância a diagnostica de
    novo, e remover esquece o resultado dela. Quem junta as duas coisas é este
    componente: o view model da seção não sabe que o diagnóstico existe.
    """
    view_model, _ = ft.use_state(InstanciasViewModel())
    diagnosticos = ft.use_context(CONTEXTO_DOS_DIAGNOSTICOS)

    ft.use_effect(view_model.carregar, [])
    ft.use_dialog(_dialogo_aberto(view_model, diagnosticos))

    if view_model.formulario_aberto:
        return _painel_do_formulario(view_model, diagnosticos)

    return _lista_de_instancias(view_model, diagnosticos)


def _dialogo_aberto(view_model: InstanciasViewModel, diagnosticos: DiagnosticosViewModel) -> ft.AlertDialog | None:
    """Escolhe o diálogo que a seção mostra agora: a confirmação de remover, os detalhes, ou nenhum."""
    if view_model.instancia_a_remover is not None:
        return _confirmacao_de_remocao(view_model, diagnosticos, view_model.instancia_a_remover)

    if view_model.instancia_em_detalhe is not None:
        return _detalhes_da_instancia(view_model, diagnosticos, view_model.instancia_em_detalhe)

    return None


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


def _lista_de_instancias(view_model: InstanciasViewModel, diagnosticos: DiagnosticosViewModel) -> ft.Control:
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

    return ft.Column(controls=[cabecalho, _cartoes_ou_convite(view_model, diagnosticos)], spacing=3, expand=True)


def _cartoes_ou_convite(view_model: InstanciasViewModel, diagnosticos: DiagnosticosViewModel) -> ft.Control:
    """Desenha os cartões das instâncias, ou o convite quando ainda não há nenhuma."""
    cadastro = view_model.cadastro

    if cadastro is None or not cadastro.itens:
        return _convite_para_cadastrar()

    cartoes = [
        _cartao_da_instancia(view_model, diagnosticos, instancia, padrao=instancia.id == cadastro.padrao)
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


def _cartao_da_instancia(
    view_model: InstanciasViewModel,
    diagnosticos: DiagnosticosViewModel,
    instancia: Instancia,
    *,
    padrao: bool,
) -> ft.Control:
    """Desenha o cartão de uma instância. Clicar nele abre os detalhes dela.

    À esquerda fica o diagnóstico da instância. A padrão leva o selo "Padrão" ao
    lado do nome. Editar tem botão próprio, antes do menu, porque é a ação mais
    usada. O menu fica com o resto: testar a conexão, desabilitado enquanto ela
    já está sendo testada; definir como padrão, desabilitado na que já é; e
    remover.
    """

    async def testar_conexao() -> None:
        await diagnosticos.diagnosticar_instancias((instancia,))

    nome = ft.Text(instancia.apelido, size=15, weight=ft.FontWeight.W_500)
    nome_ou_porta = instancia.nome or f"Porta {instancia.porta}"

    menu = ft.PopupMenuButton(
        icon=ft.Icons.MORE_HORIZ,
        icon_size=18,
        tooltip="Mais opções",
        menu_position=ft.PopupMenuPosition.UNDER,
        menu_padding=ft.Padding.symmetric(vertical=6),
        shape=ft.RoundedRectangleBorder(radius=10),
        items=[
            ft.PopupMenuItem(
                content=ft.Text("Testar conexão", size=14),
                icon=ft.Icon(ft.Icons.NETWORK_CHECK, size=19),
                height=38,
                padding=ft.Padding.symmetric(horizontal=14),
                disabled=instancia.id in diagnosticos.testando,
                on_click=testar_conexao,
            ),
            ft.PopupMenuItem(
                content=ft.Text("Definir como padrão", size=14),
                icon=ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=19),
                height=38,
                padding=ft.Padding.symmetric(horizontal=14),
                disabled=padrao,
                on_click=lambda _: view_model.definir_padrao(instancia),
            ),
            ft.PopupMenuItem(
                content=ft.Text("Remover", size=14, color=ft.Colors.ERROR),
                icon=ft.Icon(ft.Icons.DELETE_OUTLINE, size=19, color=ft.Colors.ERROR),
                height=38,
                padding=ft.Padding.symmetric(horizontal=14),
                on_click=lambda _: view_model.pedir_remocao(instancia),
            ),
        ],
    )

    return ft.Card(
        content=ft.ListTile(
            leading=_situacao_da_instancia(diagnosticos, instancia),
            title=ft.Row(controls=[nome, _selo_de_padrao()] if padrao else [nome], spacing=8, tight=True),
            subtitle=ft.Text(f"{nome_ou_porta} · {instancia.usuario}", size=13, opacity=0.7),
            trailing=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.EDIT_OUTLINED,
                        icon_size=18,
                        tooltip="Editar",
                        on_click=lambda _: view_model.abrir_edicao(instancia),
                    ),
                    menu,
                ],
                spacing=0,
                tight=True,
            ),
            min_height=62,
            content_padding=ft.Padding.symmetric(horizontal=14, vertical=4),
            on_click=lambda _: view_model.abrir_detalhes(instancia),
        ),
    )


def _situacao_da_instancia(diagnosticos: DiagnosticosViewModel, instancia: Instancia) -> ft.Control:
    """Desenha o servidor na cor da situação dele, com um anel girando em volta enquanto ele é testado.

    O servidor nunca troca de forma: o teste é um anel por cima dele, e o
    resultado é a cor que ele ganha. Assim nada vira outra coisa de repente.
    Antes do primeiro resultado ele fica apagado. Num teste de novo, ele guarda
    a cor do resultado anterior até chegar o novo.
    """
    servidor = _servidor_na_cor_da_situacao(diagnosticos.diagnosticos.get(instancia.id))
    anel = ft.Container(
        content=ft.ProgressRing(width=34, height=34, stroke_width=2),
        opacity=1 if instancia.id in diagnosticos.testando else 0,
        animate_opacity=ft.Animation(duration=250, curve=ft.AnimationCurve.EASE_OUT),
    )

    return ft.Stack(
        controls=[anel, ft.Container(content=servidor, width=34, height=34, alignment=ft.Alignment.CENTER)],
        width=34,
        height=34,
    )


def _servidor_na_cor_da_situacao(diagnostico: Diagnostico | None) -> ft.Control:
    """Desenha o servidor na cor do diagnóstico, ou apagado quando ainda não há diagnóstico."""
    if diagnostico is None:
        return ft.Icon(ft.Icons.STORAGE, size=23, color=ft.Colors.ON_SURFACE_VARIANT, opacity=0.4)

    match diagnostico.situacao:
        case "erro":
            cor = ft.Colors.RED
        case "aviso":
            cor = ft.Colors.AMBER
        case "ok":
            cor = ft.Colors.GREEN

    return ft.Icon(ft.Icons.STORAGE, size=23, color=cor)


def _selo_de_padrao() -> ft.Control:
    """Desenha o selo que marca a instância padrão."""
    return ft.Container(
        content=ft.Text("Padrão", size=10.5, weight=ft.FontWeight.W_600, color=ft.Colors.PRIMARY),
        bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.PRIMARY),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.35, ft.Colors.PRIMARY)),
        padding=ft.Padding.symmetric(horizontal=7, vertical=1),
        border_radius=20,
        tooltip="A instância que o aplicativo usa para ler os backups",
    )


def _detalhes_da_instancia(
    view_model: InstanciasViewModel,
    diagnosticos: DiagnosticosViewModel,
    instancia: Instancia,
) -> ft.AlertDialog:
    """Desenha o diálogo da instância: quem ela é no cabeçalho, e o diagnóstico abaixo.

    O endereço vem escrito como no SSMS: o host com a instância nomeada, ou o
    host com a porta depois da vírgula. Um teste disparado pelo menu enquanto o
    diálogo está aberto aparece nele quando chega.
    """
    diagnostico = diagnosticos.diagnosticos.get(instancia.id)
    padrao = view_model.cadastro is not None and view_model.cadastro.padrao == instancia.id
    endereco = (
        f"{instancia.host}\\{instancia.nome}" if instancia.nome is not None else f"{instancia.host},{instancia.porta}"
    )

    if instancia.id in diagnosticos.testando:
        situacao: ft.Control = ft.Row(
            controls=[ft.ProgressRing(width=14, height=14, stroke_width=2), ft.Text("Testando…", size=14, opacity=0.7)],
            spacing=8,
        )
    elif diagnostico is not None:
        situacao = checklist_do_diagnostico(diagnostico)
    else:
        situacao = ft.Text("Ainda não testada", size=14, opacity=0.6)

    cabecalho = ft.Row(
        controls=[
            _servidor_na_cor_da_situacao(diagnostico),
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(instancia.apelido, size=18, weight=ft.FontWeight.W_600),
                            *([_selo_de_padrao()] if padrao else []),
                        ],
                        spacing=8,
                        tight=True,
                    ),
                    ft.Text(f"{endereco} · {instancia.usuario}", size=13, opacity=0.7, selectable=True),
                ],
                spacing=0,
                tight=True,
            ),
        ],
        spacing=12,
    )

    secao_do_diagnostico = ft.Column(
        controls=[ft.Text("Diagnóstico", size=12, opacity=0.7), situacao],
        spacing=10,
        tight=True,
    )

    return ft.AlertDialog(
        title=cabecalho,
        content=ft.Container(content=secao_do_diagnostico, width=420),
        actions=[ft.TextButton(content="Fechar", on_click=lambda _: view_model.fechar_detalhes())],
        shape=ft.RoundedRectangleBorder(radius=20),
        on_dismiss=lambda _: view_model.fechar_detalhes(),
    )


def _confirmacao_de_remocao(
    view_model: InstanciasViewModel,
    diagnosticos: DiagnosticosViewModel,
    instancia: Instancia,
) -> ft.AlertDialog:
    """Desenha o diálogo que pede confirmação antes de tirar a instância do cadastro.

    Além da pergunta, o texto diz o que não acontece: quem lê "remover
    instância" pode achar que a instância ou os bancos somem do SQL Server.

    Remover também esquece o diagnóstico da instância, que não tem mais cartão
    onde aparecer.
    """

    def remover() -> None:
        view_model.confirmar_remocao()
        diagnosticos.esquecer(instancia.id)

    pergunta = ft.Text(
        spans=[
            ft.TextSpan(text="Tem certeza de que deseja remover "),
            ft.TextSpan(text=f'"{instancia.apelido}"', style=ft.TextStyle(color=ft.Colors.PRIMARY)),
            ft.TextSpan(text=" da lista de instâncias?"),
        ],
        size=14,
    )

    return ft.AlertDialog(
        modal=True,
        title=ft.Text("Remover instância", size=18, weight=ft.FontWeight.W_600),
        content=ft.Column(
            controls=[
                ft.Column(
                    controls=[
                        pergunta,
                        ft.Text("Nada será alterado no SQL Server.", size=14),
                    ],
                    spacing=2,
                    tight=True,
                ),
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.ERROR_OUTLINE, size=16, color=ft.Colors.ERROR),
                        ft.Text(
                            "Esta ação não pode ser desfeita.",
                            size=14,
                            weight=ft.FontWeight.W_600,
                            color=ft.Colors.ERROR,
                        ),
                    ],
                    spacing=6,
                ),
            ],
            spacing=12,
            tight=True,
            width=420,
        ),
        actions=[
            ft.TextButton(content="Cancelar", on_click=lambda _: view_model.cancelar_remocao()),
            ft.FilledButton(
                content="Remover",
                style=ft.ButtonStyle(bgcolor=ft.Colors.ERROR, color=ft.Colors.ON_ERROR),
                on_click=lambda _: remover(),
            ),
        ],
        shape=ft.RoundedRectangleBorder(radius=20),
        on_dismiss=lambda _: view_model.cancelar_remocao(),
    )


def _painel_do_formulario(view_model: InstanciasViewModel, diagnosticos: DiagnosticosViewModel) -> ft.Control:
    """Desenha o formulário no lugar da lista, com a seta para voltar no cabeçalho.

    O formulário recebe toda a altura que sobra abaixo do cabeçalho, para
    prender o rodapé dele embaixo.

    Salvar diagnostica de novo a instância salva, porque o endereço ou a
    credencial podem ter mudado. O diagnóstico é disparado sem esperar: salvar é
    síncrono, e o cartão mostra o resultado quando ele chegar.
    """

    def salvar_e_diagnosticar(instancia: Instancia) -> None:
        view_model.salvar(instancia)
        ft.context.page.run_task(diagnosticos.diagnosticar_instancias, (instancia,))

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
                    ao_salvar=salvar_e_diagnosticar,
                    ao_cancelar=view_model.fechar_formulario,
                ),
                padding=ft.Padding.only(left=2, right=8, top=8, bottom=4),
                expand=True,
            ),
        ],
        spacing=3,
        expand=True,
    )
