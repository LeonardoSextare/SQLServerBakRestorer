class BakRestorerError(Exception):
    """Raiz de todas as exceções originadas pela aplicação."""


class ModelInvalidoError(BakRestorerError):
    """Os dados recusados por um model do domínio.

    Guarda o motivo campo a campo para o formulário saber onde está o problema.
    Cada model diz qual subclasse dela ele levanta, no `RECUSA`.
    """

    def __init__(self, campos: dict[str, str]) -> None:
        super().__init__("; ".join(f"{campo}: {motivo}" for campo, motivo in campos.items()))
        self.campos = campos
