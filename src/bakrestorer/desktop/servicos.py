from functools import cache
from pathlib import Path

from bakrestorer.core.config import ConfigService

# TODO: Caminho fixo, só para desenvolver -- ver
# .claude/tarefas/caminho-da-configuracao-hardcoded.md
CAMINHO_DA_CONFIGURACAO = Path("config/config.json")


@cache
def config_service() -> ConfigService:
    """Devolve o serviço que lê e grava a configuração do aplicativo.

    Montado uma vez e reaproveitado: qualquer componente chama esta função em
    vez de receber o serviço por parâmetro.

    Returns:
        ConfigService: O serviço, apontando para o arquivo de configuração.

    """
    return ConfigService(CAMINHO_DA_CONFIGURACAO)
