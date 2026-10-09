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

function Get-VersaoDoProjeto {
    return uv run python -c 'from bakrestorer._versao import VERSAO; print(VERSAO)'
}

function Assert-VersaoDeRelease {
    param([string] $Versao)

    $versaoTemSufixo = $Versao -match '[^\d.]'

    if ($versaoTemSufixo) {
        throw "Release exige uma versão limpa: um commit com tag e sem mudanças pendentes. A versão atual é $Versao."
    }
}

function ConvertTo-VersaoSemVer {
    param([string] $Versao)

    $formatoPep440 = '^(?<major>\d+)\.(?<minor>\d+)(\.(?<patch>\d+))?(\.dev(?<dev>\d+)(\+(?<local>.+))?)?$'

    if ($Versao -notmatch $formatoPep440) {
        throw "A versão $Versao está fora do formato que o script sabe converter."
    }

    $patch = $Matches['patch'] ?? '0'
    $versaoSemVer = "$($Matches['major']).$($Matches['minor']).$patch"

    if ($Matches['dev']) {
        $versaoSemVer += "-dev.$($Matches['dev'])"
    }

    if ($Matches['local']) {
        $versaoSemVer += ".$($Matches['local'])"
    }

    return $versaoSemVer
}

function Get-Versao {
    $versaoDoProjeto = Get-VersaoDoProjeto

    if ($Release) {
        Assert-VersaoDeRelease -Versao $versaoDoProjeto
    }

    return ConvertTo-VersaoSemVer -Versao $versaoDoProjeto
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
