#Requires -version 7.6.0

[CmdletBinding()]
param(
    [switch] $Release
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$PSNativeCommandUseErrorActionPreference = $true

# ============================ Configurações ============================

$NOME_DO_PRODUTO = 'SQLServerBackupRestorer'
$RAIZ_DO_PROJETO = Split-Path -Parent $PSScriptRoot
$PASTA_DO_BUILD = Join-Path -Path $RAIZ_DO_PROJETO -ChildPath 'build'
$ARQUIVO_DE_RESTRICOES = Join-Path -Path $PASTA_DO_BUILD -ChildPath 'restricoes.txt'

# ============================ Funções ============================

function Export-RestricoesDeDependencias {
    Write-Host '== Fixando as dependências nas versões do uv.lock'

    New-Item -ItemType Directory -Path $PASTA_DO_BUILD -Force | Out-Null

    $argumentosDoExport = @(
        '--locked'
        '--no-default-groups'
        '--no-emit-project'
        '--format', 'requirements-txt'
        '--output-file', $ARQUIVO_DE_RESTRICOES
        '--quiet'
    )
    uv export @argumentosDoExport
}

function Get-Versao {
    $versaoDoProjeto = uv version --short

    if ($Release) {
        return $versaoDoProjeto
    }

    $commit = git rev-parse --short HEAD
    return "$versaoDoProjeto-dev-$commit"
}

function Get-Produto {
    if ($Release) {
        return $NOME_DO_PRODUTO
    }

    return "$NOME_DO_PRODUTO (dev)"
}

function Build-Aplicativo {
    $versao = Get-Versao
    $produto = Get-Produto

    $argumentosDoBuild = @(
        'windows'
        '--build-version', $versao
        '--product', $produto
    )

    if ($VerbosePreference -eq 'Continue') {
        $argumentosDoBuild += '-v'
    }

    Write-Host "== Empacotando $produto $versao"
    Write-Host "   pip restrito por $ARQUIVO_DE_RESTRICOES"

    $env:PIP_CONSTRAINT = $ARQUIVO_DE_RESTRICOES

    try {
        uv run flet build @argumentosDoBuild
    }
    finally {
        Remove-Item -Path Env:PIP_CONSTRAINT
    }
}

# ============================ Execução ============================

Push-Location -Path $RAIZ_DO_PROJETO

try {
    Export-RestricoesDeDependencias
    Build-Aplicativo
}
finally {
    Pop-Location
}
