# Serifa Music

**A music player for Linux, built with Python and Qt.**

Serifa Music is a desktop application designed to organize and play local music libraries, featuring a customizable interface and integration with the Linux environment.

The project focuses on user experience, visual organization, and giving users control over their own music libraries.

## Features

- Music library with local file indexing.
- Music playback.
- Playlist organization and management.
- Favorites system.
- Playback queue.
- Audio equalizer.
- Fullscreen playback.
- Access to music libraries stored on external drives, mounted in read-only mode.
- Customizable graphical interface through external configuration files.
- Multilingual interface with support for Brazilian Portuguese and English.

## Languages

- 🇧🇷 Brazilian Portuguese (pt-BR)
- 🇺🇸 English (en-US)

## Technologies

- Python 3.12.3
- PySide6 / Qt
- GStreamer
- Mutagen
- PyGObject
- D-Bus

## Distribution

The initial release of Serifa Music targets Linux, using the Flatpak format.

Installation packages will be available in the [Releases](https://github.com/Preitous/serifa-music/releases) section of this repository.

## Customization

The project includes an external interface customization system.

The `customization/` directory contains configuration files and graphical resources used by the application, including:

- Color palette.
- Typography.
- Component dimensions and spacing.
- Interface styles.
- SVG icons.
- Logos.
- Splash screen.

See the [customization guide](customization/GUIA_PERSONALIZACAO.md) for available formats, settings, and procedures.

## Source Code

The source code is organized into the following directories:

- `app/`: main application.
- `customization/`: visual settings and graphical resources.
- `flatpak/`: manifest, dependencies, and Flatpak packaging structure.

## License

Serifa Music is distributed under the **GNU General Public License v3.0 (GPL-3.0)**.

See the [LICENSE](LICENSE) file for the complete license terms.

---

**Serifa Music — Free Forever.**

---

# Serifa Music

**Um reprodutor de música para Linux, desenvolvido com Python e Qt.**

Serifa Music é um aplicativo desktop desenvolvido para organizar e reproduzir bibliotecas musicais locais, com uma interface personalizável e integração com o ambiente Linux.

O projeto tem como foco a experiência de uso, a organização visual e o controle do usuário sobre sua própria biblioteca musical.

## Recursos

- Biblioteca musical com indexação de arquivos locais.
- Reprodução de músicas.
- Organização e gerenciamento de playlists.
- Sistema de favoritos.
- Fila de reprodução.
- Equalizador de áudio.
- Reprodução em tela cheia.
- Acesso a bibliotecas musicais armazenadas em discos externos, montados em modo somente leitura.
- Interface gráfica personalizável por arquivos de configuração externos.
- Interface multilíngue com suporte a português brasileiro e inglês.

## Idiomas

- 🇧🇷 Português brasileiro (pt-BR)
- 🇺🇸 Inglês (en-US)

## Tecnologias

- Python 3.12.3
- PySide6 / Qt
- GStreamer
- Mutagen
- PyGObject
- D-Bus

## Distribuição

O lançamento inicial do Serifa Music será voltado ao Linux, utilizando o formato Flatpak.

Os pacotes de instalação serão disponibilizados na seção [Releases](https://github.com/Preitous/serifa-music/releases) deste repositório.

## Personalização

O projeto possui um sistema externo de personalização da interface.

A pasta `customization/` reúne configurações e recursos gráficos utilizados pelo aplicativo, incluindo:

- Paleta de cores.
- Tipografia.
- Dimensões e espaçamentos dos componentes.
- Estilos da interface.
- Ícones SVG.
- Logotipos.
- Tela de abertura.

Consulte o [guia de personalização](customization/GUIA_PERSONALIZACAO.md) para conhecer os formatos, configurações e procedimentos disponíveis.

## Código-fonte

O código-fonte está organizado nas seguintes pastas:

- `app/`: aplicação principal.
- `customization/`: configurações visuais e recursos gráficos.
- `flatpak/`: manifesto, dependências e estrutura de empacotamento Flatpak.

## Licença

Serifa Music é distribuído sob a licença **GNU General Public License v3.0 (GPL-3.0)**.

Consulte o arquivo [LICENSE](LICENSE) para conhecer os termos completos da licença.

---

**Serifa Music — Free Forever.**
