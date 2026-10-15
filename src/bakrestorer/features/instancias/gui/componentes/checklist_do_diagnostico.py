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
            _linha_da_verificacao(
                "Conexão",
                diagnostico.conexao,
                complemento=latencia,
                explicacao="Tempo limite de conexão esgotado.",
            ),
            _linha_da_verificacao("Autenticação", diagnostico.login),
            _linha_da_verificacao(
                "Criar banco",
                diagnostico.criacao_de_banco,
                explicacao="O login precisa do papel dbcreator ou da permissão CREATE ANY DATABASE.",
            ),
            _linha_da_verificacao(
                "Sobrescrever banco",
                diagnostico.sobrescrita_de_banco,
                explicacao="Só bancos de que o login é dono.",
            ),
        ],
        spacing=12,
        tight=True,
    )


def _linha_da_verificacao(
    nome: str,
    verificacao: Verificacao,
    *,
    complemento: str = "",
    explicacao: str = "",
) -> ft.Control:
    """Desenha uma verificação: o ícone e o nome à esquerda, a situação à direita e, embaixo, o que houve.

    A situação usa sempre as mesmas palavras, qualquer que seja a verificação,
    para o checklist ler igual quando ganhar itens novos. Embaixo vai o que o
    servidor disse e, quando ele não disse nada, a `explicacao` de quem desenha
    a linha, só em aviso e falha. O texto é selecionável para dar para copiar.
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

    if verificacao.situacao in ("erro", "aviso") and not detalhe:
        detalhe = explicacao

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
