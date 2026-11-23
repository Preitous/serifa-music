# Serifa Music — Guia de Personalização

Este guia explica como modificar a aparência do aplicativo usando
os arquivos da pasta `customization/`.

Após alterar configurações, reinicie o aplicativo.

## 1. Cores — colors.toml

Define as cores da interface em hexadecimal, no formato `#RRGGBB`.

O arquivo possui seções para fundos, textos, destaques, bordas,
estados, paleta Qt e tons individuais.

O arquivo `INVENTARIO_CORES.md` ajuda a localizar as cores
identificadas no código original.

## 2. Tipografia — typography.toml

Permite configurar:

- Família tipográfica principal e alternativas.
- Tamanhos de texto.
- Pesos tipográficos.
- Tamanhos utilizados nos estilos QSS.

As fontes escolhidas precisam estar instaladas no sistema.

Tamanhos são expressos em pixels. Pesos seguem a escala usual:
400 regular, 500 médio, 600 semibold e 700 negrito.

## 3. Componentes — components.toml

Controla dimensões específicas da interface:

- Sidebar e seus botões.
- Cartões de álbuns e artistas.
- Capas e linhas de músicas.
- Player e seus controles.
- Pesquisa.
- Player em tela cheia.
- Fila de reprodução.
- Arredondamentos.

As medidas são expressas em pixels.

## 4. Layout — layout.toml

A seção [window] controla as dimensões iniciais e mínimas
da janela principal.

As seções [spacing] e [margins] reúnem valores de espaçamento
e margens para uso no layout.

Componentes que possuem configurações próprias continuam
sendo ajustados em components.toml.

## 5. Tela de abertura — splash.toml

Controla textos, cores, dimensões e tempo de exibição da abertura.

Imagem principal:
- Caminho: customization/images/splash.png
- Formato recomendado: PNG.
- Dimensão recomendada: 1360 × 760 pixels.
- Proporção: 16:9.

Logotipo:
- Caminho: customization/logos/logo.png
- Formato recomendado: PNG com transparência.
- Dimensão de referência: 512 × 512 pixels.
- Largura e altura de exibição configuráveis no TOML.

Os caminhos e opções de uso são definidos no próprio splash.toml.

## 6. Ícones — icons/

Os ícones da interface ficam organizados em subpastas.

Formato: SVG.
Recomendação: preservar nomes, caminhos e viewBox dos arquivos.

O arquivo icons.json relaciona os identificadores usados pelo
aplicativo aos respectivos arquivos.

Consulte INVENTARIO_SVG.md para localizar os ícones e verificar
suas dimensões e viewBoxes.

## 7. Estilos avançados — theme.qss

Utiliza Qt Style Sheets, uma linguagem semelhante ao CSS.

Exemplo:

    QPushButton {
        color: #ffffff;
        background-color: #302a3b;
        border-radius: 8px;
        padding: 7px 12px;
    }

Seletores comuns incluem QPushButton, QLabel, QLineEdit,
QComboBox, QScrollBar e QToolTip.

Propriedades comuns incluem color, background-color, border,
border-radius, padding, margin, font-size e font-weight.

As regras externas são carregadas pelo sistema de aparência
e podem personalizar os estilos dos componentes.

## 8. Cuidados

- Faça cópias antes de alterações extensas.
- Preserve os nomes e caminhos dos recursos.
- Mantenha a sintaxe TOML e JSON válida.
- Utilize cores no formato hexadecimal.
- Instale as fontes antes de selecioná-las.
- Reinicie o aplicativo após as alterações.
- Se algo apresentar problemas, restaure o backup anterior.

A pasta customization concentra os recursos externos de aparência
do Serifa Music, reduzindo a necessidade de editar os módulos Python.
