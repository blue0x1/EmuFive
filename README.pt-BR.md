<h1 align="center"><img src="assets/emufive-logo.png" alt="EmuFive" width="480"></h1>

<p align="center">
  <img src="https://img.shields.io/badge/platform-PS4-003791?logo=playstation&logoColor=white" alt="Platform: PS4">
  <img src="https://img.shields.io/badge/status-experimental-red" alt="Status: experimental">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--2.0-blue" alt="License: GPL-2.0"></a>
  <a href="https://github.com/blue0x1/EmuFive/releases"><img src="https://img.shields.io/github/downloads/blue0x1/EmuFive/total?label=downloads" alt="Downloads"></a>
</p>

<p align="center">
  <a href="README.md">EN</a> · <a href="README.ar.md">AR</a> · <a href="README.zh-CN.md">ZH</a> · <a href="README.fr.md">FR</a> · <a href="README.es.md">ES</a> · <a href="README.de.md">DE</a> · <a href="README.it.md">IT</a> · <b>PT</b> · <a href="README.tr.md">TR</a>
</p>

Um emulador de PS5 para o PS4.

Criado por **[Chokri Hammedi (blue0x1)](https://github.com/blue0x1)**. Baseado no [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot).

> **Status: pesquisa experimental.** Em um PS4 Pro, "Sons of Sparta" roda a cerca de 40 FPS ou mais. O KytyPS5 reescreve as instruções de CPU exclusivas do PS5 no código dos jogos (patch `0004`). Outros jogos ainda estão em teste, e muitos estão lentos por enquanto. Veja [O problema da CPU](#the-cpu-problem).

<p align="center"><img src="assets/home-screen.png" alt="A tela inicial do EmuFive em um PS4 Pro, com God of War Sons of Sparta selecionado" width="900"></p>

<p align="center">
  <b><a href="#installing">Instalação</a></b> · <b><a href="#games">Jogos</a></b> · <b><a href="#changelog">Registro de alterações</a></b> · <b><a href="TROUBLESHOOTING.pt-BR.md">Solução de problemas</a></b> · <a href="#how-it-works">Como funciona</a> · <a href="#the-cpu-problem">O problema da CPU</a> · <a href="#plan">Plano</a> · <a href="#building">Compilação</a> · <a href="#credits">Créditos</a>
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

   > **Tela preta depois do menu do PS4 Multiboot?** Algumas TVs preferem um modo que o PS4 não consegue enviar. Adicione `emufive.mode=1920x1080@60` à linha em `/data/linux/boot/bootargs.txt` (mantenha também `video=HDMI-A-1:1920x1080@60D`) e execute o payload de novo.

5. No menu do PS4 Multiboot, escolha **EmuFive** e depois **Install to PS4** ou **Install to USB drive**. Leva alguns minutos.
6. Coloque seus jogos em um dos lugares abaixo. Um jogo é uma pasta com `eboot.bin` (e `sce_sys`), ou um dump ZArchive (`.zar`). Arquivos de pacote (`.pkg`, fpkg) não podem ser instalados nem executados: extraia o jogo primeiro.

Depois, rode o payload para iniciar o EmuFive (com outros sistemas instalados, o menu do PS4 Multiboot aparece primeiro). Para reinstalar, apague `/user/home/ps5-ps4.img` por FTP e rode o payload. Atualizações: Configurações, Sistema, Atualização de software.

Algo não funciona? Veja [Solução de problemas](TROUBLESHOOTING.pt-BR.md): as soluções para os problemas relatados, e como salvar os registros.

### Uso

- **Tela inicial:** seus jogos como blocos. Escolha um e aperte Jogar. OPTIONS num jogo: favorito, ocultar, configurações dele, troféus, tempo de jogo e informações do jogo.
- **Botão PS num jogo:** menu de pausa (Continuar, Início, Fechar o jogo, volume, energia).
- **Capturas de tela:** PS + Quadrado, ou Share. Veja em Mídia; Triângulo mostra um QR code para abrir uma no celular.
- **Clipes de vídeo:** PS + Triângulo começa a gravar, e PS + Triângulo de novo para (até 60 minutos). Os clipes tocam em Mídia e são compartilhados com o celular como as capturas. Onde são salvos (o PS4 ou uma unidade USB) e a qualidade (720p ou 1080p) ficam em Configurações > Armazenamento.
- **Internet:** um bloco de navegador web, usado com o controle.
- **Configurações:** Wi-Fi, aparência, controles, perfis (até 8), idioma do menu, data e hora, backup.
- **Controles:** um DualShock 4 no cabo, ou por Bluetooth (segure SHARE + PS até a barra de luz piscar duas vezes).
- **Login:** `ps5` / `ps5` por SSH ou no tty2. O log do emulador é `~/kytyps5.log`.

### Onde os jogos podem ficar

- **Pendrive ou HD USB:** a pasta `PS5` na raiz da unidade (exFAT é o melhor; NTFS também funciona).
- **Disco do PS4:** `/user/home/PS5`, copiado pelo FTP do GoldHEN (não quando o próprio EmuFive está numa unidade USB).
- **Um PC:** uma pasta compartilhada no Windows ou Linux. Em Configurações, ative **Usar jogos do PC**, informe o endereço, o compartilhamento e o login, e depois Conectar.

<a id="games"></a>
## Jogos

Este projeto não contém software de sistema do PS5 nem jogos. Use apenas jogos que você possui e dos quais você mesmo fez o dump.

<details>
<summary><b>Jogos que funcionam</b></summary>

| Jogo | Console | EmuFive | Resultado |
|---|---|---|---|
| God of War Sons of Sparta | PS4 Pro | 1.0.0 | Jogável, cerca de 40 FPS ou mais |
| Hollow Knight: Silksong | PS4 Pro | 1.0.1 | Jogável, 60 FPS |
| Plants vs. Zombies: Replanted | PS4 Pro | 1.0.4 | Jogável, 60 FPS travados |
| Vampire Survivors | PS4 Slim | 1.0.4 | Jogável, 60 FPS estáveis |
| My Little Puppy | PS4 Slim | 1.0.6 | Roda, 3–15 FPS (20–25 em áreas vazias) |
| DREDGE | PS4 Pro | 1.0.8 | Jogável |
| Animal Well | PS4 Pro | 1.0.9 | Jogável, 42–44 FPS |
| Teardown | PS4 Pro | 1.0.9 | Roda, 9–12 FPS no jogo (cerca de 20 em cenas leves) com memória compartilhada com a GPU |
| Invincible VS | PS4 Pro | 1.0.9 | Inicia, 4–5 FPS; ainda não jogável |
| Blue Prince | PS4 Pro | 1.0.10 | Jogável, cerca de 25 FPS |
| Wytchwood | PS4 Pro | 1.0.10 | Jogável, 30 FPS estáveis |
| Hades II | PS4 Slim | 1.0.10 | Roda, 20–25 FPS no jogo (10–15 nos menus), com travamentos |
| Minecraft | PS4 Slim | 1.0.10 | Jogável, 30–35 FPS no jogo (56–60 nos menus) com a memória compartilhada com a GPU desligada |
| Crusader Kings III | PS4 Pro | 1.0.10 | Jogável |
| Iron Lung | PS4 Pro | 1.0.12 | Jogável, 60 FPS |
| The King is Watching | PS4 Pro | 1.0.12 | Jogável, 55–60 FPS |
| Wizard with a Gun | PS4 Pro | 1.0.12 | Roda, 20–30 FPS com travamentos; o brilho de um portal fica na tela |
| Another Crab's Treasure | PS4 Pro | 1.0.15 | Roda, 12–17 FPS; artefatos gráficos ficam na tela |
| Minecraft Dungeons 2 | PS4 Slim | 1.0.12 | Roda com a internet desligada, 20–30 FPS |
| SteamWorld Build | PS4 Slim | 1.0.15 | Roda, 6–10 FPS; a primeira inicialização leva cerca de 40 min, as seguintes cerca de 17 min com Manter os shaders compilados |

</details>

<details>
<summary><b>Jogos que ainda não funcionam (uma versão mais nova pode corrigi-los)</b></summary>

| Jogo | Console | EmuFive | Resultado |
|---|---|---|---|
| DRAGON BALL: Sparking! ZERO | PS4 Pro | 1.0.10 | Mostra o EULA e as telas online, depois a GPU para |
| Hello Neighbor | PS4 Pro | 1.0.4 | Para ao iniciar (mesh shaders) |
| Need for Speed Unbound | PS4 Slim | 1.0.6 | Fecha ao iniciar (cópia de profundidade não suportada) |
| V Rising | PS4 Pro | 1.0.8 | Fecha ao iniciar |
| Serious Sam 4 | PS4 Slim | 1.0.10 | Fecha ao iniciar (serviços online) |
| Serious Sam: Siberian Mayhem | PS4 Slim | 1.0.9 | Fecha ao iniciar (serviços online) |
| The Long Dark | PS4 Slim | 1.0.10 | Fica preso no vídeo de abertura, sem menu |

</details>

Testou um jogo? Abra uma [issue](https://github.com/blue0x1/EmuFive/issues) com o jogo, o ID do título, o modelo do seu console, a versão do EmuFive e como ele rodou. Jogos que não funcionam também ajudam (por exemplo "não inicia" ou "fecha no menu"): eles entram na tabela, para que outros não tentem o mesmo jogo.

<a id="changelog"></a>
## Registro de alterações

### 1.0.16 (2026-11-26)

- Um novo visual para a tela inicial, agora o padrão: os blocos dos jogos em cima e a arte do jogo escolhido embaixo, na sua cor de destaque de Aparência. O layout antigo continua como Aurora (legado) em Configurações, Aparência.
- Uma página de perfil (escolha sua foto no topo) com nível de troféus, notificações, jogos e troféus; uma Central de controle no botão PS; uma Biblioteca de jogos com abas Todos os jogos, Disco do PS4, Unidade USB e PC; uma página de trapaças.
- YouTube em Mídia, com a interface de TV para o controle.
- Os jogos salvos podem ser copiados sozinhos para a unidade USB quando um jogo fecha (Configurações, Jogos salvos), e os backups agora incluem os salvamentos e troféus do KytyPS5 de todos os perfis.
- Shaders compilados podem ser exportados para uma unidade USB e importados dela, para os jogos carregarem mais rápido já na primeira vez em outro PS4 do mesmo modelo. Suas próprias capas podem ser importadas de uma pasta `PS5-covers`.
- O KytyPS5 passa para o upstream 93cce66: desenhos mesh do PS5 rodam como compute no PS4, interpolação mais suave e uma correção para jogos que esperavam a GPU para sempre (Invincible VS "GameThread timed out"). Nova configuração por jogo: Memória de GPU Garlic, desligada por padrão.
- Shaders que o Mesa não consegue compilar são guardados, e Copiar logs para USB os inclui (#76).

Para atualizar a partir da 1.0.3 ou anterior, inicie a atualização uma vez à mão, pois a atualização de software antiga não consegue: ative o SSH nas Configurações, conecte com `ssh ps5@<endereço do PS4>` (senha `ps5`, se não a mudou) e execute

```bash
sudo systemd-run --unit=emufive-update --collect /opt/ps5-on-ps4/bin/ps5-update install
```

Ela instala todas as atualizações que faltam (a partir da 1.0.0 ou 1.0.1 isso inclui os pacotes do navegador da 1.0.2, cerca de 110 MB); depois reinicie pela tela inicial. A partir da 1.0.4, a atualização de software nas Configurações funciona. Instalações novas usam o `ps5-ps4-rootfs.tar.xz` da versão 1.0.16.

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

## Apoie o projeto

Se o EmuFive é útil para você, pode apoiar o projeto com Bitcoin:

BTC: `bc1q7w5ns9vsguseppllpy609yhwrtq3v56g94mjde`

## Licença

Copyright (C) 2026 [Chokri Hammedi (blue0x1)](https://github.com/blue0x1).

GPL-2.0 (veja `LICENSE`). KytyPS5, Mesa e o kernel Linux estão sob suas próprias licenças. PlayStation é uma marca registrada da Sony Interactive Entertainment; este projeto não é afiliado à Sony.
