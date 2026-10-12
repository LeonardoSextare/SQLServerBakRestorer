from collections.abc import Callable
from typing import NamedTuple

import flet as ft

from bakrestorer.features.instancias import Instancia
from bakrestorer.features.instancias.gui.formulario.view_model import FormularioViewModel, NomeDoCampo


class Campo(NamedTuple):
    """Um campo de texto do formulário: o que ele guarda e como aparece."""

    nome: NomeDoCampo
    rotulo: str
    icone: ft.IconData
    secreto: bool = False


GRUPOS_DE_CAMPOS: dict[str, tuple[tuple[Campo, ...], ...]] = {
    "Conexão": (
        (Campo("alias", "Apelido", ft.Icons.LABEL_OUTLINE),),
        (
            Campo("host", "Host", ft.Icons.DNS_OUTLINED),
            Campo("nome", "Instância", ft.Icons.STORAGE),
        ),
        (
            Campo("usuario", "Usuário", ft.Icons.PERSON_OUTLINE),
            Campo("senha", "Senha", ft.Icons.KEY_OUTLINED, secreto=True),
        ),
    ),
    "Arquivos (opcional)": (
        (
            Campo("pasta_dados", "Pasta de dados", ft.Icons.FOLDER_OUTLINED),
            Campo("pasta_log", "Pasta de log", ft.Icons.FOLDER_OUTLINED),
        ),
    ),
}


@ft.component
def formulario(
    instancia_em_edicao: Instancia | None,
    ao_salvar: Callable[[Instancia], None],
    ao_cancelar: Callable[[], None],
) -> ft.Control:
    """Os campos de uma instância e, embaixo, o rodapé com Cancelar e Salvar.

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

    Os campos vêm da tabela `GRUPOS_DE_CAMPOS`, na ordem da tela: cada grupo tem
    um título e linhas de campos lado a lado.
    """
    editando = instancia_em_edicao is not None
    inicial = FormularioViewModel()

    if instancia_em_edicao is not None:
        inicial.preencher_com(instancia_em_edicao)

    view_model, _ = ft.use_state(inicial)

    campos = ft.Column(
        controls=[
            _grupo_de_campos(view_model, titulo, linhas, editando=editando)
            for titulo, linhas in GRUPOS_DE_CAMPOS.items()
        ],
        spacing=16,
    )

    rodape = ft.Row(
        controls=[
            ft.TextButton(content="Cancelar", on_click=lambda _: ao_cancelar()),
            ft.FilledButton(content="Salvar", icon=ft.Icons.CHECK, on_click=lambda _: view_model.salvar(ao_salvar)),
        ],
        alignment=ft.MainAxisAlignment.END,
        spacing=8,
    )

    return ft.Column(controls=[campos, rodape], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)


def _grupo_de_campos(
    view_model: FormularioViewModel,
    titulo: str,
    linhas: tuple[tuple[Campo, ...], ...],
    *,
    editando: bool,
) -> ft.Control:
    """Desenha o título de um grupo e, abaixo dele, cada linha de campos lado a lado."""
    return ft.Column(
        controls=[
            ft.Text(titulo, size=12, opacity=0.7),
            *(
                ft.Row(controls=[_campo_de_texto(view_model, campo, editando=editando) for campo in linha], spacing=10)
                for linha in linhas
            ),
        ],
        spacing=10,
    )


def _campo_de_texto(view_model: FormularioViewModel, campo: Campo, *, editando: bool) -> ft.TextField:
    """Desenha um campo de texto ligado ao view model.

    O foco começa sempre no apelido, o primeiro campo. Borda, fundo e raio são
    dados aqui porque o tema não alcança o TextField.
    """
    # TODO: o apelido trava na edição porque ele é a identidade -- tarefa #019
    return ft.TextField(
        label=campo.rotulo,
        value=view_model.digitado[campo.nome],
        error=view_model.recusas.get(campo.nome),
        prefix_icon=ft.Icon(campo.icone, size=18, opacity=0.7),
        password=campo.secreto,
        can_reveal_password=campo.secreto,
        read_only=editando and campo.nome == "alias",
        autofocus=campo.nome == "alias",
        dense=True,
        filled=True,
        fill_color=ft.Colors.with_opacity(0.06, ft.Colors.ON_SURFACE),
        border_color=ft.Colors.TRANSPARENT,
        border_radius=8,
        text_size=14,
        expand=True,
        on_change=lambda evento: view_model.digitar(campo.nome, evento.control.value),
    )
