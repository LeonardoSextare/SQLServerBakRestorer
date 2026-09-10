from pathlib import Path

import pytest

from bakrestorer.infra.json_file import ArquivoNaoLegivelError, carregar


class TestCarregar:
    """Cobre `carregar`."""

    def test_dado_arquivo_integro_com_acesso_negado_quando_carregar_entao_a_falha_nao_e_de_corrupcao(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        caminho = tmp_path / "config.json"
        caminho.write_text('{"alias": "PROD"}', encoding="utf-8")

        def negar_o_acesso(*_: object, **__: object) -> str:
            raise PermissionError

        monkeypatch.setattr(Path, "read_text", negar_o_acesso)

        with pytest.raises(ArquivoNaoLegivelError) as falha:
            carregar(caminho)

        assert falha.value.caminho == caminho
