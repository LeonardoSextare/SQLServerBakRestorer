from importlib.metadata import version

import flet as ft

from bakrestorer.desktop.servicos import CAMINHO_DA_CONFIGURACAO


@ft.component
def secao_sobre() -> ft.Control:
    """Mostra o que identifica esta instalação do aplicativo.

    Tudo aqui responde a uma pergunta de suporte: qual versão está rodando,
    quem escreveu, onde a configuração mora e se há algo mais novo.

    Returns:
        A coluna da seção.

    Note:
        A versão vem do próprio pacote instalado, e o caminho vem do serviço
        de configuração. Assim nenhum dos dois é escrito à mão aqui, e não há
        como esta tela discordar do que o aplicativo realmente usa.

    """
    cabecalho = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.INFO_OUTLINE, size=24, color=ft.Colors.PRIMARY),
                ft.Text("Sobre", size=21, weight=ft.FontWeight.W_600),
            ],
            spacing=9,
        ),
        padding=ft.Padding.only(left=2, bottom=8),
        height=44,
        align=ft.Alignment.CENTER_LEFT,
    )

    return ft.Column(
        controls=[cabecalho, _cartao_de_atualizacao(), _cartao_de_detalhes()],
        spacing=3,
    )


def _cartao_de_atualizacao() -> ft.Control:
    """Monta o cartão que procura por uma versão mais nova.

    Returns:
        O cartão.

    """

    def avisar_que_nao_verifica() -> None:
        ft.context.page.show_dialog(ft.SnackBar(content=ft.Text("Verificação de atualização ainda não implementada")))

    return ft.Card(
        content=ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text("Atualizações", size=14, expand=True),
                    ft.TextButton(
                        "Verificar",
                        icon=ft.Icons.SYSTEM_UPDATE_ALT,
                        on_click=avisar_que_nao_verifica,
                    ),
                ],
                spacing=8,
                height=36,
            ),
            padding=10,
        ),
    )


def _cartao_de_detalhes() -> ft.Control:
    """Monta o cartão com o que se sabe desta cópia do aplicativo.

    Returns:
        O cartão.

    Note:
        O dado de cada linha é o par valor e endereço. O endereço vazio é
        escrito em todas as linhas de propósito: com a forma igual em todas,
        o laço monta o cartão sem precisar decidir nada.

        O valor é sempre um `TextSpan`, mesmo sem endereço. `ft.Text` não tem
        clique nem endereço; o span tem, e é o próprio Flet que abre, sem
        serviço nenhum no meio.

        O caminho é comprido o bastante para esticar o cartão além da janela,
        então o valor é cortado com reticências e repetido inteiro na dica do
        mouse.

    """
    arquivo = CAMINHO_DA_CONFIGURACAO
    estilo_de_link = ft.TextStyle(color=ft.Colors.PRIMARY, decoration=ft.TextDecoration.UNDERLINE)
    tabela = {
        "Aplicativo": ("SQLServerBackupRestorer", None),
        "Versão": (version("sqlserverbakrestorer"), None),
        "Autor": ("Leonardo Sextare", None),
        "Configuração": (str(arquivo), arquivo.parent.as_uri()),
        "Repositorio": ("https://github.com/leonardosextare", "https://github.com/leonardosextare"),
    }

    linhas: list[ft.Control] = [
        ft.Row(
            controls=[
                ft.Text(rotulo, size=13, opacity=0.7, width=92, no_wrap=True),
                ft.Text(
                    spans=[ft.TextSpan(text=valor, url=endereco, style=estilo_de_link if endereco else None)],
                    size=13,
                    no_wrap=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    tooltip=valor,
                    expand=True,
                ),
            ],
            spacing=8,
            height=24,
        )
        for rotulo, (valor, endereco) in tabela.items()
    ]

    return ft.Card(
        content=ft.Container(content=ft.Column(controls=linhas, spacing=5), padding=10),
    )
