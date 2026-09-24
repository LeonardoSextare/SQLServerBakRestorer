from dataclasses import dataclass

import flet as ft

from bakrestorer.composition import instancias_service
from bakrestorer.features.instancias import ConfigInstancias


@ft.observable
@dataclass
class EstadoDasInstancias:
    """O que a seção de instâncias precisa saber, e as ações que mudam isso.

    `cadastro` é None enquanto a seção ainda não leu o disco. Cadastro sem
    nenhuma instância volta como uma lista vazia, e não como None.
    """

    cadastro: ConfigInstancias | None = None

    def carregar(self) -> None:
        """Lê do disco o que está cadastrado.

        Ler é do estado, e não do componente: o componente só desenha o que já
        foi lido. Quem chama isto é um efeito, porque tocar o disco durante o
        desenho faria a leitura acontecer a cada redesenho.
        """
        self.cadastro = instancias_service().carregar()


CONTEXTO_DAS_INSTANCIAS = ft.create_context(EstadoDasInstancias())
