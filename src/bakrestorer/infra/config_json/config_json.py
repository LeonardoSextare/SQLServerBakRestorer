import json
from pathlib import Path

from bakrestorer.infra.config_json.exceptions import (
    ArquivoCorrompidoError,
    ArquivoNaoEncontradoError,
    ArquivoNaoGravavelError,
    ArquivoNaoLegivelError,
)

CODIFICACAO = "utf-8"


class ConfigJson:
    """Lê e grava um pedaço de um arquivo json.

    O arquivo é dividido em chaves de topo, uma por dono. Cada dono recebe um
    ConfigJson já apontado para a chave dele, então lê e grava sem informar a
    chave e sem enxergar o que é dos outros.

    Gravar nunca apaga o que está sob as outras chaves.
    """

    def __init__(self, caminho: Path, chave: str) -> None:
        self._caminho = caminho
        self._chave = chave

    @property
    def caminho(self) -> Path:
        """Diz em que arquivo esta configuração é guardada, existindo ele ou não."""
        return self._caminho

    def ler(self) -> object | None:
        """Lê o que está gravado, ou None quando ainda não há nada gravado.

        Raises:
            ArquivoNaoEncontradoError: Se ainda não há arquivo no caminho.
            ArquivoNaoLegivelError: Se o sistema recusou a leitura.
            ArquivoCorrompidoError: Se o arquivo não é json em utf-8, ou não é um objeto.

        """
        return self._ler_o_arquivo().get(self._chave)

    def gravar(self, conteudo: object) -> None:
        """Grava o conteúdo da chave, de forma atômica.

        Raises:
            ArquivoNaoLegivelError: Se o sistema recusou a leitura do que já estava lá.
            ArquivoCorrompidoError: Se o que já estava lá não é json em utf-8.
                Nada é gravado, para o que é das outras donas não ser perdido.
            ArquivoNaoGravavelError: Se a pasta ou o arquivo não aceitaram a
                escrita, ou se o conteúdo não pode ser representado em json.

        """
        try:
            gravado = self._ler_o_arquivo()
        except ArquivoNaoEncontradoError:
            gravado = {}

        arquivo_temp = self._caminho.with_name(self._caminho.name + ".tmp")

        try:
            self._caminho.parent.mkdir(parents=True, exist_ok=True)
            arquivo_temp.write_text(
                json.dumps({**gravado, self._chave: conteudo}, indent=2, ensure_ascii=False),
                encoding=CODIFICACAO,
                newline="\n",
            )
            arquivo_temp.replace(self._caminho)
        except (OSError, TypeError, ValueError) as falha:
            arquivo_temp.unlink(missing_ok=True)
            raise ArquivoNaoGravavelError(self._caminho) from falha

    def _ler_o_arquivo(self) -> dict[str, object]:
        """Lê o arquivo inteiro e confere que ele é mesmo um mapa de chaves de topo.

        Raises:
            ArquivoNaoEncontradoError: Se ainda não há arquivo no caminho.
            ArquivoNaoLegivelError: Se o sistema recusou a leitura.
            ArquivoCorrompidoError: Se o gravado não é json em utf-8, ou não é um objeto.

        """
        if not self._caminho.is_file():
            raise ArquivoNaoEncontradoError(self._caminho)

        try:
            gravado = json.loads(self._caminho.read_text(encoding=CODIFICACAO))
        except OSError as falha:
            raise ArquivoNaoLegivelError(self._caminho) from falha
        except ValueError as falha:
            raise ArquivoCorrompidoError(self._caminho) from falha

        if not isinstance(gravado, dict):
            raise ArquivoCorrompidoError(self._caminho)

        return {str(chave): valor for chave, valor in gravado.items()}
