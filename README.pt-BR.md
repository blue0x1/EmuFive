<h1 align="center"><img src="assets/emufive-logo.png" alt="EmuFive" width="480"></h1>

<p align="center">
  <img src="https://img.shields.io/badge/platform-PS4-003791?logo=playstation&logoColor=white" alt="Platform: PS4">
  <img src="https://img.shields.io/badge/status-experimental-red" alt="Status: experimental">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--2.0-blue" alt="License: GPL-2.0"></a>
</p>

<p align="center">
  <a href="README.md">EN</a> · <a href="README.ar.md">AR</a> · <a href="README.zh-CN.md">ZH</a> · <a href="README.fr.md">FR</a> · <a href="README.es.md">ES</a> · <a href="README.de.md">DE</a> · <a href="README.it.md">IT</a> · <b>PT</b> · <a href="README.tr.md">TR</a>
</p>

Um emulador de PS5 para o PS4.

Criado por **[Chokri Hammedi (blue0x1)](https://github.com/blue0x1)**. Baseado no [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot).

> **Status: pesquisa experimental.** Em um PS4 Pro, "Sons of Sparta" roda a cerca de 40 FPS ou mais. O KytyPS5 reescreve as instruções de CPU exclusivas do PS5 no código dos jogos (patch `0004`). Outros jogos ainda estão em teste, e muitos estão lentos por enquanto. Veja [O problema da CPU](#the-cpu-problem).

<p align="center"><img src="assets/home-screen.png" alt="A tela inicial do EmuFive em um PS4 Pro, com God of War Sons of Sparta selecionado" width="900"></p>

<p align="center">
  <b><a href="#installing">Instalação</a></b> · <b><a href="#games">Jogos</a></b> · <b><a href="#changelog">Registro de alterações</a></b> · <a href="#how-it-works">Como funciona</a> · <a href="#the-cpu-problem">O problema da CPU</a> · <a href="#plan">Plano</a> · <a href="#building">Compilação</a> · <a href="#credits">Créditos</a>
</p>

<a id="how-it-works"></a>
## Como funciona

- **[PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot)** inicia o Linux no PS4 e instala sistemas Linux no disco interno dele, pelo controle.
- **PS4 Mesa**, parte do PS4 Multiboot, dá Vulkan 1.3 à GPU do PS4 (Liverpool no PS4 e no Slim, Gladius no Pro). O KytyPS5 precisa de recursos esparsos (sparse resources), que o RADV oferece nessa GPU com `RADV_EXPERIMENTAL=sparse`.
- **KytyPS5**, o projeto original em um commit fixo com os patches deste projeto (`patches/kytyps5/`), compilado com `-march=btver2` para a CPU AMD Jaguar do PS4. A versão oficial usa AVX2 e para no PS4 com "Illegal instruction".
  - `0001`: a opção de compilação `KYTY_HOST_ARCH` (a CPU para a qual o emulador é compilado).
  - `0002`: uma biblioteca C para homebrew. O homebrew de PS5 feito com ps5-native-app-boilerplate traz um módulo substituto `sce_module/libc.prx` cujas funções retornam todas 0 (o console usa a própria biblioteca C), por isso o `malloc` dele falhava no KytyPS5. O patch adiciona as funções da biblioteca C que esse homebrew importa e só as usa para um módulo substituto assim.
  - `0003`: mais para homebrew: arquivos e pastas, chamadas de sistema, o usuário em primeiro plano e pontos de montagem extras (`KYTY_MOUNTS`).
  - `0004`: código do PS5 na CPU do PS4. Cada instrução AVX2, FMA e BMI2 é reescrita como código SSE4.2/AVX/BMI1 quando um módulo carrega; a que não pode ser reescrita nesse momento é substituída na primeira vez que é executada. Veja [O problema da CPU](#the-cpu-problem).
- **EmuFive** junta tudo isso em um pequeno sistema Linux que inicia direto no emulador, em tela cheia, sem área de trabalho. Ele é instalado pelo PS4 Multiboot como qualquer outro sistema.

<a id="the-cpu-problem"></a>

## O problema da CPU

O KytyPS5 não emula a CPU do PS5: ele executa diretamente o código x86-64 do jogo. Os jogos de PS5 são compilados para a CPU Zen 2 do PS5 e usam instruções AVX2, BMI2 e FMA em todo lugar. A CPU Jaguar do PS4 não tem nenhuma delas, então o código do jogo para na primeira dessas instruções.

O patch `0004` adiciona isso ao corretor de instruções do convidado do KytyPS5. Quando falta AVX2, FMA ou BMI2 à CPU do hospedeiro, cada uma dessas instruções é substituída por código com o mesmo efeito: operações inteiras de 256 bits como duas metades de 128 bits, permutações entre as metades com movimentos e misturas AVX, deslocamentos por elemento um de cada vez, FMA calculada em precisão dupla, gathers um elemento de cada vez, BMI2 com registradores salvos. O salto para a substituição é escrito onde a instrução estava; uma instrução curta demais para um salto, em um ponto que o corretor não consegue reorganizar, gera uma falha e é substituída em tempo de execução.

`tools/jaguar-test/` verifica cada substituição em um PC que tem essas instruções: ele pega cada forma de instrução encontrada no código de um programa, executa o original e a substituição a partir do mesmo estado aleatório e compara todos os registradores, flags e a memória. As formas encontradas nos programas testados até agora batem: 287 em God of War Sons of Sparta (gathers e VFMADDSUB incluídos) e 227 nos programas testados antes. As exceções são raras diferenças no último bit em FMA (a precisão simples é arredondada duas vezes, a dupla é uma multiplicação e uma soma) e um caso especial de NaN para 0 vezes infinito.

O Jaguar ainda é muito mais lento que a CPU do PS5, e as substituições somam a isso, então mesmo um jogo que roda pode rodar devagar.

<a id="plan"></a>
## Plano

| Etapa | Status |
|---|---|
| Vulkan na GPU do PS4 atende aos requisitos do KytyPS5 | Feito (`RADV_EXPERIMENTAL=sparse`) |
| KytyPS5 compilado para a CPU do PS4 | Feito (`KYTY_HOST_ARCH=btver2`) |
| KytyPS5 inicia no PS4 e configura a GPU | Feito, PS4 Pro |
| Imagem do sistema EmuFive, instalada pelo PS4 Multiboot | Feito, PS4 Pro |
| Um app homebrew de PS5 sem AVX2 roda e desenha | Feito: Snes9x PS5 2.11 recompilado para btver2, PS4 Pro |
| Controle, armazenamento `/data` e USB, carregar um jogo nesse app | Feito em uma versão de teste para PC (mesmos patches); PS4 em seguida |
| Tradução de AVX2, BMI2 e FMA para o código dos jogos | Feito (`0004`), verificado em um PC |
| Um jogo de PS5 roda no PS4 | Feito: God of War Sons of Sparta, cerca de 40 FPS ou mais, PS4 Pro |
| Hollow Knight: Silksong roda no PS4 | Feito desde a 1.0.1 (patches `0006` e `0007`), PS4 Pro |
| Tela inicial: escolher um jogo com o controle; Wi-Fi; Configurações | Feito, verificado em um PC |
| Jogos do pendrive USB, do disco do PS4 ou de uma pasta compartilhada de PC | Feito, verificado em um PC; PS4 em seguida |

<a id="building"></a>

## Compilação

Precisa de Docker, git e do PS4 Mesa do PS4 Multiboot (`../PS4-Multiboot/out/ps4-mesa.tar.xz`, compilado lá com `make mesa`). O `build-kyty.sh` clona o KytyPS5 em `build/kytyps5` na primeira vez e, a cada compilação, volta ao commit fixo e aplica os patches.

```bash
scripts/build-kyty.sh      # out/kytyps5-ps4.tar.xz
scripts/build-rootfs.sh    # out/ps5-ps4-rootfs.tar.xz
```

`PS4_MESA` e `KYTY` indicam outros caminhos ao `build-rootfs.sh`.

<a id="installing"></a>

## Instalação

O EmuFive é instalado pelo [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot), como qualquer outro sistema Linux.

Você precisa de:

- Um PS4 desbloqueado com **GoldHEN** (pelo servidor FTP e pelo carregador de payloads).
- Um PC na mesma rede com um cliente FTP (por exemplo o FileZilla).
- Cerca de 28 GB livres no PS4 (um disco de 16 GB, e 10 GB sempre livres para o PS4), ou um pendrive USB de 8 GB ou mais.
- Um DualShock 4 (em um cabo USB, ou pareado por Bluetooth depois).

Passos:

1. Nas [versões do PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot/releases), baixe `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` e `linux-2048mb.bin`. (O `ps4-mesa.tar.xz` não é necessário: o EmuFive já inclui o PS4 Mesa.)
2. Nas [versões do EmuFive](https://github.com/blue0x1/EmuFive/releases), baixe `ps5-ps4-rootfs.tar.xz` (ou compile-o, veja [Compilação](#building)). Mantenha o nome: o PS4 Multiboot encontra os sistemas pelo `-ps4-rootfs` que ele contém.
3. Ligue o servidor FTP do GoldHEN e copie os arquivos para o PS4 (porta 2121):

   | Arquivo | Pasta no PS4 |
   |---|---|
   | `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` | `/data/linux/boot/` |
   | `ps5-ps4-rootfs.tar.xz` | `/user/home/` |
   | `linux-2048mb.bin` | `/data/payloads/` |

4. Execute `linux-2048mb.bin` pelo menu de payloads do GoldHEN.

   > **Tenha paciência:** depois que o payload inicia, a TV pode mostrar **"No signal" ou uma tela preta por 1 a 2 minutos** enquanto o Linux inicia. Isso é normal.

5. No menu do PS4 Multiboot, escolha **EmuFive** e depois **Install to PS4** ou **Install to USB drive**. Leva alguns minutos.
6. Coloque seus jogos em um dos lugares abaixo. Um jogo é uma pasta com `eboot.bin` (e `sce_sys`), ou um dump ZArchive (`.zar`).

Depois disso, execute o payload para iniciar o EmuFive: com só o EmuFive instalado ele inicia direto; com outros sistemas, o menu do PS4 Multiboot aparece primeiro. Desligue ou reinicie pela tela inicial para voltar ao sistema do PS4. Para instalar o EmuFive de novo, apague `/user/home/ps5-ps4.img` por FTP e execute o payload.

As atualizações vêm das versões do EmuFive: Configurações, Sistema, Atualização de software (sem reinstalar).

O sistema inicia na tela inicial e não precisa de teclado:

- Os jogos aparecem como blocos, cada um com o lugar onde está: **USB**, **PS4** ou **PC**. Escolha um e pressione Jogar; quando ele fechar, a tela inicial volta.
- No topo: o Wi-Fi (com um teclado na tela para a senha) e Configurações, e duas abas, **Jogos** e **Mídia** (L1 / R1). Mídia mostra suas capturas de tela; abra uma, e Quadrado a apaga.
- OPTIONS em um jogo: favorito, ocultar, as configurações dele, os troféus e quanto tempo você jogou.
- **Internet**, o bloco depois dos jogos: um navegador web usado com o controle. O analógico esquerdo (ou o touchpad) move o ponteiro e X clica; o analógico direito rola a página; O ou L1 volta, R1 avança; L2 e R2 dão zoom. Triângulo digita um endereço ou uma busca, e escolher uma caixa de texto em uma página abre o teclado na tela. OPTIONS abre o menu: favoritos, página inicial, zoom, mecanismo de busca (Google, DuckDuckGo ou Bing), sites móveis (páginas mais leves) e limpar o histórico e os cookies. O botão PS volta à tela inicial, e a mesma página abre na próxima vez. É o WebKitGTK mostrando uma página por vez, cerca de 450 MB de memória com uma página de texto e mais com sites de vídeo; a tela inicial fecha enquanto ele roda, e um jogo pausado precisa ser fechado antes. Downloads, uploads, câmera, microfone e localização são recusados. Os favoritos ficam em `~/.config/ps5-on-ps4/browser.json`, os cookies em `~/.local/share/ps5-browser`.
- O botão PS durante um jogo o pausa e abre o menu rápido: Continuar, **Início** (a tela inicial, com o jogo ainda pausado: PS ou Continuar volta para ele; iniciar outro jogo pergunta antes e depois o fecha), fechar o jogo, volume, energia.
- Capturas de tela: PS + Quadrado, ou Share, também dentro de um jogo. Elas vão para `PS5-screenshots` no pendrive USB (ou `~/Screenshots` sem um), com um pequeno aviso no canto. Para passar uma para o celular, abra-a em Mídia e pressione Triângulo (Compartilhar): escaneie o QR code com o celular (na mesma rede) para abri-la nele, e depois salve ou compartilhe. O PS4 serve só essa imagem, em um endereço aleatório, e só enquanto o código está na tela. Os QR codes vêm do `python3-segno`.
- Configurações, Aparência: cor de destaque, tema (escuro, meia-noite, claro), fundo (a arte do jogo, um degradê, uma cor sólida ou uma imagem sua do pendrive USB), escurecimento do fundo, orbes flutuantes, animações, tamanho e formato dos blocos, tamanho e fonte do texto, relógio, o que a barra superior mostra (a bateria é a do controle), sons do menu, vibração, dicas de botões, bordas da tela (overscan) e um protetor de tela.
- Configurações, Controles: cor e brilho da barra de luz, vibração ligada ou não e sua intensidade, o microfone do controle ligado ou não (com o controle em um cabo USB; o Linux não tem som do controle por Bluetooth), trocar X e O, e uma página de teste para cada botão e analógico. Configurações, Jogos: padrões para todos os jogos, idioma dos jogos, HDR e ritmo de quadros. Configurações, Data e hora: automática pela internet (o padrão) ou manual. Configurações, Sistema: o idioma do menu (inglês, árabe, francês, turco, espanhol, alemão, italiano ou português do Brasil), temperatura e carga da CPU, backup das configurações no pendrive USB, ou redefinir todas.
- Perfis (Configurações, Perfil, e Trocar de perfil no menu rápido): até 8, cada um com nome, avatar, jogos salvos, troféus e tempo de jogo próprios. Com mais de um, "Quem está jogando?" abre no início. Cada perfil tem a própria pasta do KytyPS5 (`~/.kytyps5/users/<ID>`, o primeiro perfil mantém `~/.kytyps5`), com o cache de shaders compartilhado.
- Avisos no canto superior esquerdo, também dentro de um jogo: uma captura foi salva, um controle conectou (com o tipo de conexão e o nível da bateria), a bateria do controle está fraca (15%). A bateria da barra superior fica verde, amarela ou vermelha conforme o nível, com um raio enquanto carrega.
- Falta de memória: um arquivo de swap de 4 GB no disco do sistema (`ps5-swap.service`, criado uma vez quando há espaço) deixa um jogo grande ficar mais lento em vez de travar o PS4, e se a memória e o swap acabarem mesmo assim, o jogo é fechado antes de o PS4 travar e a tela inicial diz o motivo.
- Idiomas do menu: as traduções ficam em `lib/ps5/translations.json`, uma entrada por texto em inglês. O árabe é alinhado à direita e desenhado com DejaVu Sans; suas letras são ligadas em `lib/ps5/i18n.py`, já que o SDL_ttf aqui não as liga.
- O programa vê o pendrive USB como `/mnt/usb0` e uma pasta do sistema (`~/data`, mantida entre as inicializações) como `/data`. Para o Snes9x PS5, as ROMs vão em `snes9x/roms` no pendrive USB ou em `~/data/snes9x/roms`.
- Se o emulador parar com um erro, a tela inicial mostra o motivo.
- `PS5_GAME` em `/etc/ps5-on-ps4.conf` executa um jogo direto em vez da tela inicial.
- Controles: um DualShock 4 no cabo, ou por Bluetooth depois de segurar SHARE + PS até a barra de luz piscar duas vezes.
- O som vai para a TV pelo HDMI, também quando um controle no cabo traz a própria placa de som (`/etc/wireplumber/wireplumber.conf.d/51-ps5-hdmi.conf`).

### Onde os jogos podem ficar

- **Pendrive USB:** a pasta `PS5` na raiz do pendrive. exFAT é o melhor (arquivos acima de 4 GB); NTFS também funciona.
- **Disco do PS4:** `/user/home/PS5` no PS4, copiado para lá pelo FTP do GoldHEN. O sistema lê o disco do PS4 somente para leitura e nunca o altera. Não disponível quando o próprio sistema foi instalado em um pendrive USB.
- **Um PC:** uma pasta compartilhada no Windows ou no Linux. Em Configurações, ligue **Usar jogos do PC** e informe o endereço do PC, a pasta compartilhada e, a menos que seja um compartilhamento de convidado, um usuário e uma senha; depois Conectar. Os jogos podem ficar na raiz da pasta compartilhada ou em uma pasta `PS5` dentro dela. Um cabo de rede é mais rápido que o Wi-Fi.
  - Windows: compartilhe a pasta (Propriedades, Compartilhamento). Para um compartilhamento de convidado, compartilhe com Everyone e desligue *Password protected sharing* nas configurações de compartilhamento avançadas.
  - Linux (Samba): um compartilhamento com `guest ok = yes` para convidados, ou um usuário do Samba (`smbpasswd -a`).
  - O kernel do PS4 não tem cliente SMB, então o sistema usa o smbnetfs (FUSE). As configurações, senha incluída, ficam em `~/.config/ps5-on-ps4/pc-share.json`, que só o usuário `ps5` pode ler.

`tools/make-pad-test-rom.py` cria uma ROM de SNES minúscula para testar um controle: azul, e verde enquanto um botão é segurado.

Login: `ps5` / `ps5` no tty2 ou por SSH. A saída do emulador fica em `~/kytyps5.log` (a execução anterior: `~/kytyps5.log.1`).

<a id="games"></a>
## Jogos

Este projeto não contém software de sistema do PS5 nem jogos. Use apenas jogos que você possui e dos quais você mesmo fez o dump.

Jogos testados:

| Jogo | Console | Resultado |
|---|---|---|
| God of War Sons of Sparta | PS4 Pro | Jogável, cerca de 40 FPS ou mais |
| Hollow Knight: Silksong | PS4 Pro | Jogável, de 50 a 60 FPS |
| Plants vs. Zombies: Replanted | PS4 Pro | Jogável, 60 FPS travados |
| Vampire Survivors | PS4 Slim | Jogável, 60 FPS estáveis |
| Spider-Man 2 | | Ainda não testado |

Testou um jogo? Abra uma [issue](https://github.com/blue0x1/EmuFive/issues) com o jogo, o modelo do seu console e como ele rodou.

<a id="changelog"></a>
## Registro de alterações

### 1.0.6 (2026-11-14)

- Melhorado: a tela inicial usa muito menos CPU enquanto ninguém a usa (em 4K, cerca de um terço de um núcleo; antes, um núcleo inteiro), então o PS4 esquenta menos e faz menos barulho.

Para atualizar a partir da 1.0.3 ou anterior, inicie a atualização uma vez à mão, pois a atualização de software antiga não consegue: ative o SSH nas Configurações, conecte com `ssh ps5@<endereço do PS4>` (senha `ps5`, se não a mudou) e execute

```bash
sudo systemd-run --unit=emufive-update --collect /opt/ps5-on-ps4/bin/ps5-update install
```

Ela instala todas as atualizações que faltam (a partir da 1.0.0 ou 1.0.1 isso inclui os pacotes do navegador da 1.0.2, cerca de 110 MB); depois reinicie pela tela inicial. A partir da 1.0.4, a atualização de software nas Configurações funciona. Instalações novas usam o `ps5-ps4-rootfs.tar.xz` da versão 1.0.6.

## Estrutura do projeto

| Caminho | Conteúdo |
|---|---|
| `scripts/build-kyty.sh` | Compila o KytyPS5 (o original mais `patches/kytyps5/`) para a CPU do PS4 |
| `patches/kytyps5/` | As alterações deste projeto no KytyPS5 |
| `scripts/build-rootfs.sh` | Cria a imagem do sistema para o PS4 Multiboot |
| `scripts/make-release.sh` | Cria o pacote de atualização de uma versão (instalado por Configurações, Sistema, Atualização de software) |
| `scripts/updates/` | Scripts que uma atualização executa no PS4 depois que os arquivos dela estão no lugar (`--post`) |
| `docker/` | Ambientes de compilação para os dois |
| `overlay/` | Arquivos adicionados ao sistema: sessão, tela inicial, configurações, montagem do pendrive USB e do disco do PS4, pareamento de controles |
| `tools/` | Conversor do logo, ROM de teste do controle, `extract-code.py` (o código de um SELF/ELF de PS5) |
| `tools/jaguar-test/` | Verifica as substituições do patch `0004` contra as instruções reais |

## Agradecimentos especiais

- [KytyPS5](https://github.com/KytyPS5/KytyPS5), o emulador de PS5 em que o EmuFive se baseia (GPL-2.0)
- [Kyty](https://github.com/InoriRus/Kyty) de InoriRus, o emulador em que o KytyPS5 se baseia

<a id="credits"></a>
## Créditos

- [Mesa](https://mesa3d.org), e os patches de GPU do PS4 de fail0verflow, DionKill e striker91n
- Os desenvolvedores do kernel Linux para PS4 ([sony-jaguar-devs/ps4-linux](https://github.com/sony-jaguar-devs/ps4-linux))

## Licença

Copyright (C) 2026 [Chokri Hammedi (blue0x1)](https://github.com/blue0x1).

GPL-2.0 (veja `LICENSE`). KytyPS5, Mesa e o kernel Linux estão sob suas próprias licenças. PlayStation é uma marca registrada da Sony Interactive Entertainment; este projeto não é afiliado à Sony.
