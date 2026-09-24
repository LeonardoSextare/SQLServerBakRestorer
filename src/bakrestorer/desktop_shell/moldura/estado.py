from dataclasses import dataclass
from enum import Enum

import flet as ft

from bakrestorer.desktop_shell.tema import Tema


class Tela(Enum):
    """As telas que a moldura sabe mostrar."""

    RESTAURACAO = "restauracao"
    CONFIGURACAO = "configuracao"


@ft.observable
@dataclass
class EstadoApp:
    """O que a janela inteira precisa saber, e as ações que mudam isso.

    Guarda só o que não pertence a nenhuma tela sozinha. O que é de uma tela
    mora no `estado.py` dela.

    Observável: mudar um campo aqui redesenha sozinho quem estiver usando este
    objeto, sem ninguém chamar `update()`.

    Attributes:
        tela: Qual tela está aparecendo dentro da moldura.
        tela_anterior: De onde a configuração foi aberta, para saber para onde
            voltar.
        tema: O visual escolhido pelo usuário.

    """

    tela: Tela = Tela.RESTAURACAO
    tela_anterior: Tela = Tela.RESTAURACAO
    tema: Tema = Tema.SISTEMA

    def alternar_tela(self) -> None:
        """Abre a configuração, ou volta para a tela de onde ela foi aberta."""
        if self.tela is Tela.CONFIGURACAO:
            self.tela = self.tela_anterior
            return

        self.tela_anterior = self.tela
        self.tela = Tela.CONFIGURACAO

    def mudar_tema(self, escolhido: Tema) -> None:
        """Troca o visual do aplicativo.

        Args:
            escolhido: O visual que passa a valer.

        """
        self.tema = escolhido


CONTEXTO_DA_JANELA = ft.create_context(EstadoApp())
