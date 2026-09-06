import json
from pathlib import Path

from bakrestorer.core.infra.json_file.exceptions import (
    ArquivoCorrompidoError,
    ArquivoNaoEncontradoError,
    ArquivoNaoGravavelError,
    ArquivoNaoLegivelError,
)

CODIFICACAO = "utf-8"


def carregar(caminho: Path) -> object:
    """Lê o valor que o arquivo guarda.

    Returns:
        object: O valor gravado, do tipo que o json trouxer.

    Raises:
        ArquivoNaoEncontradoError: Se não há arquivo no caminho informado.
        ArquivoNaoLegivelError: Se o sistema recusou a leitura.
        ArquivoCorrompidoError: Se o que está gravado não está em utf-8 ou não
            é json válido.

    """
    if not caminho.is_file():
        raise ArquivoNaoEncontradoError(caminho)

    try:
        return json.loads(caminho.read_text(encoding=CODIFICACAO))
    except OSError as falha:
        raise ArquivoNaoLegivelError(caminho) from falha
    except ValueError as falha:
        raise ArquivoCorrompidoError(caminho) from falha


def salvar(caminho: Path, conteudo: object) -> None:
    """Grava o arquivo inteiro de forma atômica, criando a pasta quando ela ainda não existe.

    Args:
        caminho: Arquivo a gravar.
        conteudo: Valor a guardar, montado apenas com tipos que o json aceita.

    Raises:
        ArquivoNaoGravavelError: Se a pasta ou o arquivo não aceitaram a
            escrita, ou se o conteúdo não pode ser representado em json.

    """
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        json_str = json.dumps(conteudo, indent=2, ensure_ascii=False)
        _gravar_arquivo_atomicamente(caminho, json_str)
    except (OSError, TypeError, ValueError) as falha:
        raise ArquivoNaoGravavelError(caminho) from falha


def _gravar_arquivo_atomicamente(caminho: Path, dados: str) -> None:
    """Escreve o conteúdo em um arquivo temporário e o promove ao lugar do arquivo final.

    O temporário nasce na mesma pasta do arquivo final porque a troca só é
    atômica dentro do mesmo volume. Enquanto ele é escrito, o arquivo final
    continua intacto: uma falha no meio da escrita não deixa nada pela metade.

    Args:
        caminho: Arquivo a substituir.
        dados: Conteúdo já serializado.

    Raises:
        OSError: Se a escrita ou a troca falharem, sem deixar o temporário para trás.

    """
    arquivo_temp = caminho.with_name(caminho.name + ".tmp")

    try:
        arquivo_temp.write_text(dados, encoding=CODIFICACAO, newline="\n")
        arquivo_temp.replace(caminho)
    except OSError:
        arquivo_temp.unlink(missing_ok=True)
        raise
