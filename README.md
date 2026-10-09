# SQLServerBackupRestorer



[![CI](https://github.com/LeonardoSextare/SQLServerBakRestorer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/LeonardoSextare/SQLServerBakRestorer/actions/workflows/ci.yml)
![Status: alpha](https://img.shields.io/badge/status-alpha-orange)
[![Versão](https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fraw.githubusercontent.com%2FLeonardoSextare%2FSQLServerBakRestorer%2Fmaster%2Fpyproject.toml&query=%24.project.version&label=vers%C3%A3o&color=blue)](https://github.com/LeonardoSextare/SQLServerBakRestorer/releases)
[![Python 3.14+](https://img.shields.io/badge/python-3.14%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Plataforma: Windows](https://img.shields.io/badge/plataforma-Windows-0078D6)](#requisitos)
[![Licença: GPL-3.0](https://img.shields.io/badge/licen%C3%A7a-GPL--3.0-blue)](LICENSE)

Restaure arquivos `.bak` no SQL Server local sem repetir os mesmos passos no SSMS
toda vez.

> [!WARNING]
> O aplicativo está em versão alpha e ainda não pode ser usado.

## Por que existe

Restaurar um `.bak` no SQL Server não é difícil, mas é repetitivo. Toda vez são
os mesmos passos no SSMS: escolher o arquivo, conferir o que tem dentro, ajustar
o nome do banco e o lugar dos arquivos, e esperar. Quem faz isso várias vezes ao
dia, em instâncias diferentes, perde tempo com o volume, e não com a dificuldade.

O SQLServerBackupRestorer troca essa rotina por duas ações: cadastrar a instância
uma vez e, daí em diante, escolher o arquivo e mandar restaurar.

## Como funciona

1. **Cadastre suas instâncias uma vez.** Para cada uma: um apelido, o nome da
   instância, o usuário, a senha e, se quiser, a pasta onde os arquivos `.mdf` e
   `.ldf` devem ficar.
2. **Escolha o backup.** Abra o aplicativo e escolha o `.bak`, ou dê um duplo
   clique no arquivo e o aplicativo já abre com ele carregado.
3. **Veja o que tem dentro.** O aplicativo lê o backup antes de agir e mostra o
   que encontrou.
4. **Escolha o destino.** Selecione a instância e o nome do banco. Dá para
   restaurar com um nome novo ou sobrescrever um banco que já existe.
5. **Acompanhe o progresso.** A restauração mostra quanto já foi e quanto falta.

O aplicativo também confere se cada instância está acessível, ao abrir e ao
cadastrar. Se uma instância não responde, você fica sabendo antes de começar, e
não no meio da restauração.

Quem só quer restaurar vê uma tela simples. Quem quer saber o que há dentro do
backup encontra os detalhes ali mesmo.

## Requisitos

- Windows.
- Um SQL Server instalado na mesma máquina.

## Instalação

Baixe a versão mais recente na página de
[Releases](https://github.com/LeonardoSextare/SQLServerBakRestorer/releases).

## Licença

Copyright (C) 2026 Leonardo Sextare. Distribuído sob a [GPL-3.0](LICENSE).
