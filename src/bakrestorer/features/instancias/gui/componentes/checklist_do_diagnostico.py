import flet as ft

from bakrestorer.features.instancias import Diagnostico, Verificacao


def checklist_do_diagnostico(diagnostico: Diagnostico) -> ft.Control:
    """Desenha cada verificação do diagnóstico, uma por linha, na ordem em que rodam."""
    latencia = ""

    if diagnostico.latencia is not None:
        milissegundos = diagnostico.latencia.total_seconds() * 1000
        latencia = "< 1 ms" if milissegundos < 1 else f"{milissegundos:.0f} ms"

    return ft.Column(
        controls=[
            _linha_da_verificacao("Conexão", diagnostico.conexao, complemento=latencia),
            _linha_da_verificacao("Autenticação", diagnostico.login),
        ],
        spacing=12,
        tight=True,
    )


def _linha_da_verificacao(nome: str, verificacao: Verificacao, *, complemento: str = "") -> ft.Control:
    """Desenha uma verificação: o ícone e o nome à esquerda, a situação à direita e, embaixo, o que o servidor disse.

    A situação usa sempre as mesmas palavras, qualquer que seja a verificação,
    para o checklist ler igual quando ganhar itens novos. O detalhe é
    selecionável para dar para copiar a mensagem do servidor. O erro sem
    detalhe é o tempo de espera que acabou sem resposta nenhuma.
    """
    match verificacao.situacao:
        case "ok":
            icone, cor, situacao = ft.Icons.CHECK_CIRCLE, ft.Colors.GREEN, "OK"
        case "aviso":
            icone, cor, situacao = ft.Icons.ERROR, ft.Colors.AMBER, "Aviso"
        case "erro":
            icone, cor, situacao = ft.Icons.CANCEL, ft.Colors.RED, "Falha"
        case "nao_verificado":
            icone, cor, situacao = ft.Icons.REMOVE_CIRCLE_OUTLINE, ft.Colors.ON_SURFACE_VARIANT, "Não verificado"

    detalhe = verificacao.detalhe

    if verificacao.situacao == "erro" and not detalhe:
        detalhe = "Tempo limite de conexão esgotado."

    linha = ft.Row(
        controls=[
            ft.Icon(icone, size=18, color=cor),
            ft.Text(nome, size=14, expand=True),
            ft.Text(f"{situacao} · {complemento}" if complemento else situacao, size=12, opacity=0.6),
        ],
        spacing=10,
    )

    if not detalhe:
        return linha

    return ft.Column(
        controls=[
            linha,
            ft.Container(
                content=ft.Text(detalhe, size=12, opacity=0.75, selectable=True),
                padding=ft.Padding.only(left=28),
            ),
        ],
        spacing=2,
        tight=True,
    )
