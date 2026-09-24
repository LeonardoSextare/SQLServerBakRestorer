from functools import cache
from pathlib import Path

from bakrestorer.features.instancias import InstanciasService, criar_service

# TODO: Caminho fixo, só para desenvolver -- ver
# .claude/tarefas/caminho-da-configuracao-hardcoded.md
RAIZ_DO_PROJETO = Path(__file__).resolve().parents[2]
CAMINHO_DA_CONFIGURACAO = RAIZ_DO_PROJETO / "config" / "config.json"


@cache
def instancias_service() -> InstanciasService:
    """Devolve o serviço que lê e grava o cadastro de instâncias.

    Montado uma vez e reaproveitado: quem precisa chama esta função em vez de
    receber o serviço por parâmetro.
    """
    return criar_service(CAMINHO_DA_CONFIGURACAO)
