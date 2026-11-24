# Serifa Music — Installation Guide

This guide explains how to install, launch, and uninstall Serifa Music on Linux.

## 1. Requirements

Before installing, make sure your system has:

- A Linux distribution with Flatpak support.
- Flatpak installed and working.
- An internet connection for downloading the required runtimes.
- The Flathub remote configured.

Serifa Music is currently distributed for Linux on x86_64 systems.

## 2. Configure Flathub

If Flathub is not already configured on your system, open a terminal and run:

```bash
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

This adds Flathub as a Flatpak software source.

## 3. Download the application

Download the latest `SerifaMusic.flatpak` package from the project's GitHub Releases page:

https://github.com/Preitous/serifa-music/releases

Save the downloaded file to a location you can easily access, such as your Downloads folder.

## 4. Install Serifa Music

Open a terminal in the directory where the downloaded package is located.

Run:

```bash
flatpak install --user ./SerifaMusic.flatpak
```

Flatpak will automatically locate the required runtimes through the configured Flathub remote.

Review the installation details and confirm when prompted.

The application and its required components will then be installed.

## 5. Launch the application

You can launch Serifa Music from your desktop application menu or through the terminal:

```bash
flatpak run com.serifa.SerifaMusic
```

## 6. Uninstall

To remove Serifa Music, run:

```bash
flatpak uninstall --user com.serifa.SerifaMusic
```

Flatpak will show which components can also be removed.

Shared runtimes may remain installed if other applications depend on them.

## 7. Troubleshooting

### Flatpak command not found

Flatpak may not be installed on your Linux distribution.

Install Flatpak using your distribution's package manager and consult its official documentation.

### Flathub remote not found

Make sure Flathub is configured:

```bash
flatpak remotes
```

If it does not appear in the list, repeat the configuration step in section 2.

### Required runtime cannot be found

Check your internet connection and confirm that Flathub is available.

You can verify the configured remotes with:

```bash
flatpak remotes --show-details
```

### Application does not launch

Try launching the application from the terminal:

```bash
flatpak run com.serifa.SerifaMusic
```

This may display diagnostic messages that help identify the problem.

---

# Serifa Music — Guia de Instalação

Este guia explica como instalar, iniciar e desinstalar o Serifa Music no Linux.

## 1. Requisitos

Antes de instalar, verifique se o sistema possui:

- Uma distribuição Linux com suporte ao Flatpak.
- Flatpak instalado e funcionando.
- Conexão com a internet para baixar os runtimes necessários.
- Repositório Flathub configurado.

Atualmente, o Serifa Music é distribuído para Linux em sistemas com arquitetura x86_64.

## 2. Configurar o Flathub

Caso o Flathub ainda não esteja configurado no sistema, abra o terminal e execute:

```bash
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

Esse comando adiciona o Flathub como uma fonte de aplicativos Flatpak.

## 3. Baixar o aplicativo

Baixe a versão mais recente do pacote `SerifaMusic.flatpak` na página de Releases do projeto:

https://github.com/Preitous/serifa-music/releases

Salve o arquivo em um local de fácil acesso, como a pasta Downloads.

## 4. Instalar o Serifa Music

Abra um terminal no diretório onde o pacote foi baixado.

Execute:

```bash
flatpak install --user ./SerifaMusic.flatpak
```

O Flatpak localizará automaticamente os runtimes necessários por meio do Flathub configurado no sistema.

Confira os detalhes da instalação e confirme quando solicitado.

O aplicativo e seus componentes necessários serão instalados.

## 5. Iniciar o aplicativo

Você pode iniciar o Serifa Music pelo menu de aplicativos do ambiente gráfico ou pelo terminal:

```bash
flatpak run com.serifa.SerifaMusic
```

## 6. Desinstalar

Para remover o Serifa Music, execute:

```bash
flatpak uninstall --user com.serifa.SerifaMusic
```

O Flatpak mostrará quais componentes também podem ser removidos.

Runtimes compartilhados poderão permanecer instalados caso sejam utilizados por outros aplicativos.

## 7. Solução de problemas

### Comando Flatpak não encontrado

O Flatpak pode não estar instalado na sua distribuição Linux.

Instale-o por meio do gerenciador de pacotes da sua distribuição e consulte a documentação oficial correspondente.

### Repositório Flathub não encontrado

Verifique se o Flathub está configurado:

```bash
flatpak remotes
```

Caso ele não apareça na lista, repita a configuração apresentada na seção 2.

### Runtime necessário não encontrado

Verifique sua conexão com a internet e confirme se o Flathub está disponível.

Você pode conferir os repositórios configurados com:

```bash
flatpak remotes --show-details
```

### O aplicativo não inicia

Tente iniciar o aplicativo pelo terminal:

```bash
flatpak run com.serifa.SerifaMusic
```

O terminal poderá apresentar mensagens de diagnóstico que ajudam a identificar o problema.

---

**Serifa Music — Free Forever.**
