import asyncio
from dataclasses import dataclass, field
from uuid import UUID

import flet as ft

from bakrestorer.composition import diagnostico_service, instancias_service
from bakrestorer.features.instancias import Diagnostico, Instancia


@ft.observable
@dataclass
class DiagnosticosViewModel:
    """Os diagnósticos das instâncias cadastradas, para o aplicativo inteiro.

    Mora acima das telas porque precisa durar o aplicativo inteiro e ser lido
    por mais de uma tela: a seção de instâncias hoje, a restauração depois. Quem
    sabe o que ele guarda é esta feature; quem o cria e o transmite é a moldura,
    que é a única parte da tela que vive o tempo todo.

    `testando` diz quais instâncias estão sendo diagnosticadas agora. Enquanto
    isso, `diagnosticos` ainda guarda o resultado anterior delas, se houver.

    O diagnóstico sai numa thread porque espera a rede, e esperar aqui travaria a
    janela pelo tempo do login de cada instância.
    """

    diagnosticos: dict[UUID, Diagnostico] = field(default_factory=dict)
    testando: frozenset[UUID] = frozenset()

    async def diagnosticar_instancias_cadastradas(self) -> None:
        """Lê o cadastro e diagnostica todas as instâncias.

        Dá nome à regra de abrir o aplicativo: quem chama não precisa saber de
        onde vêm as instâncias.

        Raises:
            ArquivoNaoLegivelError: Se o sistema recusou a leitura do cadastro.
            ArquivoCorrompidoError: Se o arquivo não é json em utf-8.
            CadastroInvalidoError: Se o gravado não corresponde ao formato.
            InstanciaInvalidaError: Se uma das instâncias gravadas não
                corresponde ao formato.
            ComandoRecusadoError: Se alguma instância aceitou o login e recusou
                o ping.

        """
        await self.diagnosticar_instancias(instancias_service().carregar().itens)

    async def diagnosticar_instancias(self, instancias: tuple[Instancia, ...]) -> None:
        """Diagnostica as instâncias ao mesmo tempo, e mostra cada resultado assim que ele chega.

        Ao mesmo tempo porque cada uma pode levar o tempo limite inteiro para não
        responder: em série, a última esperaria pelas outras. Os resultados são
        guardados na ordem em que chegam, para a mais lenta não segurar as
        rápidas na tela.

        As threads só diagnosticam: quem mexe no view model é sempre este laço,
        porque a tela só pode ser alterada pela thread dela.

        Raises:
            ComandoRecusadoError: Se alguma instância aceitou o login e recusou
                o ping.

        """
        em_teste = frozenset(instancia.id for instancia in instancias)
        self.testando = self.testando | em_teste

        try:
            pedidos = [asyncio.to_thread(diagnostico_service().diagnosticar, instancia) for instancia in instancias]

            async for tarefa in asyncio.as_completed(pedidos):
                diagnostico = tarefa.result()
                self.diagnosticos = {**self.diagnosticos, diagnostico.id_da_instancia: diagnostico}
                self.testando = self.testando - {diagnostico.id_da_instancia}
        finally:
            self.testando = self.testando - em_teste

    def esquecer(self, id_da_instancia: UUID) -> None:
        """Tira o resultado de uma instância que saiu do cadastro."""
        self.diagnosticos = {
            id_diagnosticado: diagnostico
            for id_diagnosticado, diagnostico in self.diagnosticos.items()
            if id_diagnosticado != id_da_instancia
        }


CONTEXTO_DOS_DIAGNOSTICOS = ft.create_context(DiagnosticosViewModel())
