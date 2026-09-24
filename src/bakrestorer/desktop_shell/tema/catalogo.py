from enum import Enum

import flet as ft

from bakrestorer.desktop_shell.tema import aparencias


class Tema(Enum):
    """Os visuais que o aplicativo oferece.

    Cada membro junta as duas coisas que o Flet guarda separadas: o modo, que
    é da página, e a aparência, que é um `ft.Theme`.

    Sem aparência própria, o visual é o padrão do Flet, e o modo escolhe qual:
    o claro, o escuro, ou o que o sistema estiver usando.

    Este arquivo é a tabela: uma linha por visual. As cores de cada um ficam
    no `aparencias.py`, para esta lista continuar legível por mais visuais que
    apareçam.

    Attributes:
        rotulo: Como o visual aparece no seletor.
        modo: O modo em que a página fica.
        aparencia: Os padrões que o Flet usa para desenhar.

    """

    SISTEMA = ("Sistema", ft.ThemeMode.SYSTEM)
    CLARO = ("Claro", ft.ThemeMode.LIGHT)
    ESCURO = ("Escuro", ft.ThemeMode.DARK)
    SAKURA = ("Sakura", ft.ThemeMode.LIGHT, aparencias.SAKURA)
    OCEANO = ("Oceano", ft.ThemeMode.DARK, aparencias.OCEANO)
    FLORESTA = ("Floresta", ft.ThemeMode.DARK, aparencias.FLORESTA)
    INDUSTRIAL = ("Industrial", ft.ThemeMode.DARK, aparencias.INDUSTRIAL)

    def __init__(self, rotulo: str, modo: ft.ThemeMode, aparencia: ft.Theme | None = None) -> None:
        """Guarda as partes do visual em campos com nome.

        Args:
            rotulo: Como o visual aparece no seletor.
            modo: O modo em que a página fica.
            aparencia: A aparência própria, ou None para a do Flet.

        """
        self.rotulo = rotulo
        self.modo = modo
        self.aparencia = aparencia or ft.Theme()

    def aplicar(self, pagina: ft.Page) -> None:
        """Põe este visual na página.

        A mesma aparência vai nos dois campos: ela diz a intenção, e o campo em
        que cai é que decide se a paleta sai clara ou escura.

        Args:
            pagina: A janela.

        """
        pagina.theme_mode = self.modo
        pagina.theme = self.aparencia
        pagina.dark_theme = self.aparencia
        pagina.update()
