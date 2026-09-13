from pathlib import Path

import pytest
from bakrestorer.infra.config_json import ArquivoNaoLegivelError, ConfigJson


class TestLer:
    """Cobre `ler`."""

    def test_dado_arquivo_integro_com_acesso_negado_quando_ler_entao_a_falha_nao_e_de_corrupcao(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def existir(*_: object, **__: object) -> bool:
            return True

        def negar_o_acesso(*_: object, **__: object) -> str:
            raise PermissionError

        monkeypatch.setattr(Path, "is_file", existir)
        monkeypatch.setattr(Path, "read_text", negar_o_acesso)
        caminho = Path("config.json")

        with pytest.raises(ArquivoNaoLegivelError) as falha:
            ConfigJson(caminho, "instancias").ler()

        assert falha.value.caminho == caminho
