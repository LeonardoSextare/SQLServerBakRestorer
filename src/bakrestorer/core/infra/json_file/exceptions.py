from pathlib import Path

from bakrestorer.core.exceptions import BakRestorerError


class ArquivoJsonError(BakRestorerError):
    """Falha ao ler ou gravar um arquivo json.

    Attributes:
        caminho: Arquivo que a operação tentou alcançar.

    """

    def __init__(self, caminho: Path) -> None:
        """Registra qual arquivo falhou.

        Args:
            caminho: Arquivo que a operação tentou alcançar.

        """
        super().__init__(str(caminho))
        self.caminho = caminho


class ArquivoNaoEncontradoError(ArquivoJsonError):
    """Não há arquivo no caminho informado."""


class ArquivoNaoLegivelError(ArquivoJsonError):
    """O arquivo existe, mas o sistema recusou a leitura.

    Note:
        O conteúdo pode estar perfeito: a falha é de permissão, disco ou
        bloqueio, e some quando a causa é removida.

    """


class ArquivoCorrompidoError(ArquivoJsonError):
    """O arquivo foi lido, mas o que está gravado não é json em utf-8."""


class ArquivoNaoGravavelError(ArquivoJsonError):
    """O arquivo não pôde ser gravado.

    Note:
        O conteúdo anterior continua intacto: a gravação só substitui o arquivo
        depois de ter escrito o novo conteúdo por inteiro.

    """
