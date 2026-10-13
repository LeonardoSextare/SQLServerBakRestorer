import math
from collections.abc import Callable

import flet as ft

from bakrestorer.features.instancias import Instancia
from bakrestorer.features.instancias.gui.formulario.view_model import FormularioViewModel, NomeDoCampo


@ft.component
def formulario(
    instancia_em_edicao: Instancia | None,
    ao_salvar: Callable[[Instancia], None],
    ao_cancelar: Callable[[], None],
) -> ft.Control:
    """Os campos de uma instância e, embaixo, o rodapé com os botões.

    No rodapé, Testar conexão fica sozinho à esquerda, longe de Cancelar e
    Salvar: ele confere a instância, e não fecha o formulário. Por enquanto ele
    só existe desabilitado -- o diagnóstico ainda não foi escrito.

    Não conhece quem o usa: recebe a instância em edição, ou None para uma
    nova, e as funções que gravam e que fecham. Assim serve em qualquer tela
    que saiba gravar uma instância.

    Não sabe onde está: onde ele aparece é decisão de quem o usa. Ele ocupa a altura
    que receber, com os campos no topo e o rodapé preso embaixo, para os botões
    não mudarem de lugar quando o rodapé ganhar mais um.

    O view model do formulário nasce aqui, e não no da seção, para fechar o
    formulário descartar o que foi digitado. O `use_state` recebe um `inicial`
    novo a cada desenho e só guarda o primeiro: por isso o preenchimento é feito
    no `inicial`, antes de entregar, e nunca no `view_model` que volta. Lá, ele
    copiaria a instância por cima do que foi digitado a cada redesenho.

    Os campos são desenhados um a um, na ordem da tela, para o código ter a
    forma do que aparece.
    """
    inicial = FormularioViewModel()

    if instancia_em_edicao is not None:
        inicial.preencher_com(instancia_em_edicao)

    view_model, _ = ft.use_state(inicial)

    campos = ft.Column(
        controls=[
            ft.Text("Conexão", size=12, opacity=0.7),
            _campo_de_texto(view_model, "apelido", "Apelido", ft.Icons.LABEL_OUTLINE, foco=True),
            ft.Row(
                controls=[
                    _campo_de_texto(view_model, "host", "Host", ft.Icons.DNS_OUTLINED),
                    _campo_de_texto(view_model, "nome", "Instância", ft.Icons.STORAGE),
                ],
                spacing=10,
            ),
            ft.Row(
                controls=[
                    _campo_de_texto(view_model, "usuario", "Usuário", ft.Icons.PERSON_OUTLINE),
                    _campo_de_texto(view_model, "senha", "Senha", ft.Icons.KEY_OUTLINED, secreto=True),
                ],
                spacing=10,
            ),
            ft.Container(
                content=ft.Text("Arquivos (opcional)", size=12, opacity=0.7),
                padding=ft.Padding.only(top=6),
            ),
            _par_de_pastas(view_model),
        ],
        spacing=10,
    )

    rodape = ft.Row(
        controls=[
            ft.OutlinedButton(
                content="Testar conexão",
                icon=ft.Icons.NETWORK_CHECK,
                disabled=True,
                tooltip="Em breve",
            ),
            ft.Row(
                controls=[
                    ft.TextButton(content="Cancelar", on_click=lambda _: ao_cancelar()),
                    ft.FilledButton(
                        content="Salvar",
                        icon=ft.Icons.CHECK,
                        on_click=lambda _: view_model.salvar(ao_salvar),
                    ),
                ],
                spacing=8,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    return ft.Column(controls=[campos, rodape], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)


def _campo_de_texto(
    view_model: FormularioViewModel,
    campo: NomeDoCampo,
    rotulo: str,
    icone: ft.IconData,
    *,
    secreto: bool = False,
    foco: bool = False,
) -> ft.TextField:
    """Desenha um campo de texto ligado a um campo do view model.

    Borda, fundo e raio são dados aqui porque o tema não alcança o TextField.
    """
    return ft.TextField(
        label=rotulo,
        value=view_model.digitado[campo],
        error=view_model.recusas.get(campo),
        prefix_icon=ft.Icon(icone, size=18, opacity=0.7),
        password=secreto,
        can_reveal_password=secreto,
        autofocus=foco,
        dense=True,
        filled=True,
        fill_color=ft.Colors.with_opacity(0.06, ft.Colors.ON_SURFACE),
        border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.TRANSPARENT), border_radius=8),
        text_size=14,
        expand=True,
        on_change=lambda evento: view_model.digitar(campo, evento.control.value),
    )


@ft.component
def _par_de_pastas(view_model: FormularioViewModel) -> ft.Control:
    """Desenha as duas pastas lado a lado, com a corrente que liga uma à outra.

    Vincular anima em dois tempos: as linhas saem do meio da corrente até as
    pastas e, quando chegam, o contorno das pastas acende. Desvincular faz o
    caminho inverso: o contorno apaga e, quando termina, as linhas voltam para a
    corrente.

    O segundo tempo começa no fim do primeiro, pelo `on_animation_end`, e por
    isso o componente guarda em `desenho_concluido` qual desenho já terminou.
    É estado só da animação: o vínculo de verdade é o `pastas_vinculadas` do
    view model. Toda animação que termina faz o desenho alcançar o vínculo que
    vale naquele momento.

    Nada muda de tamanho no caminho: as linhas crescem dentro de um espaço fixo,
    e o contorno só troca de cor. O contorno não recorta o campo: com raio na
    borda, o `Container` recortaria por padrão, e cortaria o rótulo que sobe
    acima do campo quando ele está preenchido. O ritmo é constante, e lento o bastante para
    o caminho curto das linhas ser visto.
    """
    vinculadas = view_model.pastas_vinculadas
    desenho_inicial = "pastas_ligadas" if vinculadas else "pastas_separadas"
    desenho_concluido, marcar_desenho_concluido = ft.use_state(desenho_inicial)

    linhas_visiveis = vinculadas or desenho_concluido == "pastas_ligadas"
    contorno_visivel = vinculadas and desenho_concluido == "pastas_ligadas"
    cor_do_vinculo = ft.Colors.with_opacity(0.45, ft.Colors.PRIMARY)
    animacao_das_linhas = ft.Animation(duration=320, curve=ft.AnimationCurve.LINEAR)
    animacao_do_contorno = ft.Animation(duration=250, curve=ft.AnimationCurve.LINEAR)

    def concluir_desenho() -> None:
        marcar_desenho_concluido("pastas_ligadas" if view_model.pastas_vinculadas else "pastas_separadas")

    def com_contorno(campo: ft.TextField) -> ft.Control:
        return ft.Container(
            content=campo,
            border=ft.Border.all(1, cor_do_vinculo if contorno_visivel else ft.Colors.TRANSPARENT),
            border_radius=9,
            clip_behavior=ft.ClipBehavior.NONE,
            animate=animacao_do_contorno,
            expand=True,
            on_animation_end=lambda _: concluir_desenho(),
        )

    linhas_com_corrente = ft.Stack(
        controls=[
            ft.Container(
                right=24,
                top=19,
                width=24 if linhas_visiveis else 0,
                height=1.5,
                bgcolor=cor_do_vinculo,
                animate=animacao_das_linhas,
                on_animation_end=lambda _: concluir_desenho(),
            ),
            ft.Container(
                left=24,
                top=19,
                width=24 if linhas_visiveis else 0,
                height=1.5,
                bgcolor=cor_do_vinculo,
                animate=animacao_das_linhas,
            ),
            ft.Container(
                content=ft.Icon(
                    ft.Icons.LINK if vinculadas else ft.Icons.LINK_OFF,
                    size=20,
                    color=ft.Colors.PRIMARY if vinculadas else None,
                    opacity=1 if vinculadas else 0.6,
                    rotate=-math.pi / 4 if vinculadas else 0,
                    animate_rotation=animacao_das_linhas,
                ),
                left=8,
                top=4,
                width=32,
                height=32,
                border_radius=16,
                alignment=ft.Alignment.CENTER,
                ink=True,
                tooltip="Separar as pastas" if vinculadas else "Usar a mesma pasta para dados e log",
                on_click=lambda _: view_model.alternar_vinculo_das_pastas(),
            ),
        ],
        width=48,
        height=40,
    )

    return ft.Row(
        controls=[
            com_contorno(_campo_de_texto(view_model, "pasta_dados", "Pasta de dados", ft.Icons.FOLDER_OUTLINED)),
            linhas_com_corrente,
            com_contorno(_campo_de_texto(view_model, "pasta_log", "Pasta de log", ft.Icons.FOLDER_OUTLINED)),
        ],
        spacing=0,
    )
