# Solução de problemas

<p align="center">
  <a href="TROUBLESHOOTING.md">EN</a> · <a href="TROUBLESHOOTING.ar.md">AR</a> · <a href="TROUBLESHOOTING.zh-CN.md">ZH</a> · <a href="TROUBLESHOOTING.fr.md">FR</a> · <a href="TROUBLESHOOTING.es.md">ES</a> · <a href="TROUBLESHOOTING.de.md">DE</a> · <a href="TROUBLESHOOTING.it.md">IT</a> · <b>PT</b> · <a href="TROUBLESHOOTING.tr.md">TR</a>
</p>

Os problemas que as pessoas relataram nas [issues](https://github.com/blue0x1/EmuFive/issues), com as soluções que funcionaram. Siga os passos em ordem. Ainda não deu? Abra uma issue com o que está em [O que enviar](#what-to-send).

- [Confira os arquivos primeiro](#check-the-files-first)
- [Tela preta ou «Sem sinal» depois do payload](#black-screen-or-no-signal-after-the-payload)
- [Tela preta depois do menu ou do logo do EmuFive](#black-screen-after-the-menu-or-the-emufive-logo)
- [Tela verde, cores erradas ou piscando](#green-screen-wrong-colors-or-flickering)
- [O PS4 desliga, ou a luz fica branca](#the-ps4-turns-off-or-the-light-stays-white)
- [«No Linux install or archive found»](#no-linux-install-or-archive-found)
- [A instalação demora muito](#installing-takes-very-long)
- [O EmuFive não inicia depois de uma instalação interrompida](#emufive-doesnt-start-after-a-stopped-install)
- [Só funciona com o pendrive/HD USB conectado](#it-only-works-with-the-usb-drive-plugged-in)
- [Os jogos não aparecem](#games-dont-show-up)
- [Um HD externo não é encontrado](#an-external-drive-isnt-found)
- [O controle não funciona](#the-controller-doesnt-work)
- [Um jogo fecha, trava ou fica lento](#a-game-closes-freezes-or-runs-slowly)
- [Como salvar os registros](#how-to-save-the-logs)
- [O que enviar](#what-to-send)

<a id="check-the-files-first"></a>
## Confira os arquivos primeiro

A maioria dos casos de «não acontece nada» vinha de um destes pontos:

- **Mesma versão:** `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` e `linux-2048mb.bin` precisam vir todos da mesma [versão do PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot/releases) (de preferência a mais nova). Arquivos misturados não iniciam.
- **Pastas em minúsculas:** o PS4 vê `LINUX` e `linux` como pastas diferentes. Os caminhos têm que ser exatamente `/data/linux/boot/bzImage`, `/data/linux/boot/initramfs.cpio.gz` e `/data/linux/boot/bootargs.txt`.
- **O nome exato do arquivo:** `/user/home/ps5-ps4-rootfs.tar.xz`. Às vezes o navegador salva como `ps5-ps4-rootfs (1).tar.xz`, e aí o menu não encontra.
- **Transferência binária:** no FileZilla, escolha Transferência → Tipo de transferência → **Binário** antes de enviar. Um arquivo enviado em modo texto fica danificado. Confira se cada arquivo no PS4 tem o mesmo tamanho da versão.
- **Nosso payload:** use o `linux-2048mb.bin` do PS4 Multiboot (no firmware 14.02: `linux-2048mb-14.02.bin`). Ele funciona do firmware 5.05 ao 14.02. Outros payloads de Linux não são suportados.

<a id="black-screen-or-no-signal-after-the-payload"></a>
## Tela preta ou «Sem sinal» depois do payload

Depois que o payload inicia, a TV mostra «Sem sinal» ou uma tela preta por **1 a 2 minutos**, enquanto o Linux inicia. Isso é normal. A tela e o controle desligarem logo depois do payload também é normal: o sistema do PS4 fecha e o Linux assume.

**Não aperte o botão PS enquanto a tela está preta**: isso desliga o PS4. Com só o EmuFive no PS4, o instalador começa sozinho depois de 60 segundos, então pode já estar instalando.

Se nada aparecer depois de 3 minutos:

1. Ligue o PS4 **direto** na TV, sem switch HDMI, receiver ou placa de captura.
2. No PS4, desative **Configurações → Sistema → Ativar HDCP** e rode o payload de novo.
3. Tente outro cabo HDMI e outra porta HDMI.
4. Tente uma vez outra TV ou outro monitor. Algumas TVs não aceitam o sinal do Linux do PS4, e outra tela mostra se o problema é a TV.
5. Ainda nada? Salve o [registro PS4BOOT](#the-ps4boot-stick-boot-problems) e abra uma issue. Diga se a TV mostra **«Sem sinal»** ou se está ligada, mas preta.

<a id="black-screen-after-the-menu-or-the-emufive-logo"></a>
## Tela preta depois do menu ou do logo do EmuFive

Se você vê o menu do PS4 Multiboot ou o logo do EmuFive e depois fica preto, o EmuFive mudou para um modo que a sua TV prefere, mas que o PS4 não consegue enviar.

1. Atualize o EmuFive (Configurações → Sistema → Atualização de software).
2. Por FTP, abra `/data/linux/boot/bootargs.txt` e adicione ` emufive.mode=1920x1080@60` no fim da linha. Mantenha também `video=HDMI-A-1:1920x1080@60D`. O arquivo tem que continuar sendo **uma linha só**.
3. Rode o payload de novo.

Não dá para atualizar porque a tela está preta? Ligue uma vez outra TV ou monitor e atualize, ou instale o EmuFive de novo com o `ps5-ps4-rootfs.tar.xz` mais novo.

<a id="green-screen-wrong-colors-or-flickering"></a>
## Tela verde, cores erradas ou piscando

Uma camada verde, preto aparecendo verde ou branco aparecendo ciano, ou a tela piscando: a TV está lendo o sinal do PS4 no formato de cor errado.

1. Adicione ` emufive.mode=1920x1080@60` ao `bootargs.txt` (veja acima).
2. Tente outro cabo ou porta HDMI. Nas configurações da TV para essa porta, mude opções como **HDMI UHD Color**, **Formato aprimorado**, **Deep Colour** ou **Input Signal Plus** (de ligado para desligado, ou o contrário), e desative o HDMI-CEC (**Anynet+**, **Bravia Sync**...).
3. Tente outra TV ou outro monitor.

<a id="the-ps4-turns-off-or-the-light-stays-white"></a>
## O PS4 desliga, ou a luz fica branca

- **No 14.02**, a primeira vez que você roda o payload às vezes desliga o PS4. Rode de novo: a segunda tentativa costuma funcionar.
- **A luz fica branca** e nada acontece por 5 minutos: segure o botão de ligar para desligar o PS4, ligue de novo e rode o payload outra vez.
- **Uma luz roxa** depois de instalar é normal.
- **O PS4 desliga quando você aperta o botão PS** com a tela preta: não aperte, espere (veja acima).

<a id="no-linux-install-or-archive-found"></a>
## «No Linux install or archive found»

O menu não encontrou nem um EmuFive instalado nem o `ps5-ps4-rootfs.tar.xz`.

1. Confira o nome e o lugar do arquivo: exatamente `/user/home/ps5-ps4-rootfs.tar.xz`.
2. Num **PS4 fat** (CUH-10xx, 11xx ou 12xx), o PS4 Multiboot da v1.5.0-beta.3 à beta.7 não encontrava o HD interno. Use o `bzImage` e o `initramfs.cpio.gz` da [v1.5.0-beta.8](https://github.com/blue0x1/ps4-multiboot/releases/tag/v1.5.0-beta.8) ou mais nova.

<a id="installing-takes-very-long"></a>
## A instalação demora muito

- **Criar o disco** é o primeiro 25% da barra, e é a parte lenta: tudo o que é gravado no HD do PS4 passa pela criptografia do PS4. Consoles Baikal são mais lentos nisso. Um disco grande demora mais, então na primeira tentativa escolha um menor (16 GB está bom). A parte depois de 25% vai mais rápido.
- **Não desligue o PS4** enquanto a porcentagem ainda estiver andando. Se ela não se mexer por 30 minutos, abra uma issue e diga onde parou.
- **Tela preta no fim:** se a TV ainda tem sinal, a instalação provavelmente terminou e o EmuFive está iniciando. Se o botão de ligar do PS4 desliga ele normalmente, o EmuFive está rodando e só a imagem está preta: veja [Tela preta depois do menu](#black-screen-after-the-menu-or-the-emufive-logo).

<a id="emufive-doesnt-start-after-a-stopped-install"></a>
## O EmuFive não inicia depois de uma instalação interrompida

Se o PS4 foi desligado durante uma instalação, o disco criado pela metade pode ficar para trás. A tela de erro diz **«The EmuFive disk is incomplete»**, ou o registro diz `is a hole`.

1. Apague `/user/home/ps5-ps4.img` por FTP. Mantenha o `ps5-ps4-rootfs.tar.xz`.
2. Rode o payload e instale de novo. Deixe terminar sem desligar o PS4.

<a id="it-only-works-with-the-usb-drive-plugged-in"></a>
## Só funciona com o pendrive/HD USB conectado

Você escolheu **Install to USB drive**, então o EmuFive fica nesse pendrive/HD e precisa dele. Para ter no PS4: desconecte o pendrive/HD, rode o payload e escolha **Install to PS4**.

<a id="games-dont-show-up"></a>
## Os jogos não aparecem

Um jogo é uma **pasta** com `eboot.bin` e `sce_sys` dentro, ou um único arquivo `.zar`. Arquivos `.pkg` e fpkg não funcionam: extraia o jogo antes. Use dumps de jogos que você tem.

Num pendrive/HD USB, tem que ficar assim:

```
Pendrive/HD USB (exFAT, uma partição; NTFS também funciona)
└── PS5/                      <- exatamente "PS5", em maiúsculas, na raiz do pendrive/HD
    ├── PPSA01234/            <- uma pasta por jogo (qualquer nome)
    │   ├── eboot.bin         <- direto na pasta do jogo
    │   ├── sce_sys/
    │   │   └── param.json    <- dá o nome e a imagem do jogo
    │   └── ...
    └── MeuJogo.zar           <- um dump .zar, como um único arquivo
```

Erros comuns:

- `ps5/` ou `Ps5/`: o nome tem que ser exatamente `PS5`.
- `Jogos/PS5/...`: a pasta `PS5` tem que ficar na raiz do pendrive/HD.
- `PS5/PPSA01234/PPSA01234/eboot.bin`: um nível de pasta a mais (comum depois de descompactar). Mova a pasta de dentro para cima.
- `PS5/eboot.bin`: os arquivos do jogo soltos na `PS5`, sem pasta própria.
- Dois jogos na mesma pasta: só um aparece. O nome no ícone vem do `sce_sys/param.json`, não do nome da pasta, então dê a cada jogo a sua pasta.

No HD do PS4, a pasta é `/user/home/PS5`, e ela só funciona quando o EmuFive está instalado no PS4 (não num pendrive/HD USB). Copie os jogos com o FTP do GoldHEN pelo sistema do PS4 e depois inicie o EmuFive: ele lê essa pasta quando inicia.

Deixe conectado só o pendrive/HD dos jogos. Tire o pendrive de registros `PS4BOOT` enquanto joga.

<a id="an-external-drive-isnt-found"></a>
## Um HD externo não é encontrado

- SSDs e HDs externos funcionam a partir do EmuFive 1.0.5. Atualize primeiro.
- Um HD que já teve Linux pode continuar não aparecendo depois de uma formatação normal. Apague todas as partições dele (Windows: Gerenciamento de disco) e crie uma única partição **exFAT**.
- Se o EmuFive está instalado num pendrive/HD USB, os jogos vão num segundo pendrive/HD USB (a partir do EmuFive 1.0.4).

<a id="the-controller-doesnt-work"></a>
## O controle não funciona

- **No menu do PS4 Multiboot e nas telas de instalação e de erro**, o controle só funciona **no cabo USB**. O Bluetooth começa depois, no EmuFive.
- **No Bluetooth**, ele precisa ser pareado uma vez com o EmuFive, porque o pareamento do sistema do PS4 não vale. Tire o cabo, segure **SHARE + PS** até a barra de luz piscar duas vezes e espere alguns segundos. Se não conectar, use Configurações → Controles → Parear um controle novo.
- Use um cabo que transmite dados. Alguns cabos só carregam.
- Nos consoles **Baikal** (muitos Pro CUH-71xx/72xx e Slim mais novos; veja Configurações → Sistema → Informações do sistema), o USB precisa do PS4 Multiboot v1.5.0-beta.7 ou mais novo.

<a id="a-game-closes-freezes-or-runs-slowly"></a>
## Um jogo fecha, trava ou fica lento

- **«O jogo parou (código de erro 65)» com `ErrorDeviceLost`:** a GPU do PS4 travou no desenho do jogo. Isso é comum com jogos pesados de Unreal Engine, que ainda não são jogáveis. Envie o [registro do jogo](#game-logs) se quiser que a gente veja.
- **Sem memória:** um jogo de PS5 pode usar até uns 12,5 GB, e o Linux no PS4 tem uns 6 GB. O EmuFive fecha o jogo antes que o PS4 trave. Desative Configurações → Jogos → **Memória de jogo compartilhada com a GPU** e tente de novo. O EmuFive só cria um arquivo de troca de 4 GB quando o disco dele tem 8 GB livres, então libere espaço se o disco estiver cheio.
- **Um jogo trava ou fecha:** tente uma vez com a **Memória de jogo compartilhada com a GPU** desativada. Ela acelera jogos 3D grandes, mas não serve para todos (o Minecraft trava com ela).
- **Engasgos na primeira vez:** na primeira vez que uma cena aparece, os shaders são compilados. Na segunda vez fica mais suave.
- **Tearing:** Configurações → Jogos → Ritmo de quadros → **Suave (sem tearing)**.
- **FPS baixo:** a CPU e a GPU do PS4 são bem mais lentas que as do PS5. Jogos 2D e leves rodam bem; jogos 3D pesados muitas vezes carregam e mostram os menus, e depois ficam muito lentos ou com a tela preta no jogo. Um PS4 Pro é mais ou menos duas vezes mais rápido que um Slim. Veja a tabela de [Jogos](README.pt-BR.md#games) antes de testar um jogo grande.

<a id="how-to-save-the-logs"></a>
## Como salvar os registros

<a id="the-ps4boot-stick-boot-problems"></a>
### O pendrive PS4BOOT (problemas de inicialização)

1. Formate um pendrive em **FAT32** com o rótulo **`PS4BOOT`** (em maiúsculas). O Windows não formata em FAT32 pendrives maiores que 32 GB: use um menor, ou o [Rufus](https://rufus.ie) (Seleção de boot: *Não inicializável*, Sistema de arquivos: *Large FAT32*, Rótulo do volume: `PS4BOOT`). NTFS e exFAT não servem para isso.
2. Conecte no PS4 **antes** de rodar o payload, e deixe conectado.
3. Rode o payload e espere **5 minutos**, mesmo que a tela continue preta. Se aparecer uma tela de erro, ela mesma salva os detalhes no pendrive.
4. Segure o botão de ligar para desligar o PS4. Coloque o pendrive num PC e anexe os arquivos `.log` na sua issue (`ps4-linux-boot.log`, `ps4-linux-late.log`, `ps4-linux-error.log` ou `ps4-linux-rescue.log`).

Se o pendrive continuar vazio, diga isso: significa que o Linux não chegou até ali, e isso também ajuda.

<a id="game-logs"></a>
### Registros dos jogos

Logo depois que o jogo parar, vá em Configurações → Sistema → **Copiar registros para o pendrive** e anexe os arquivos da pasta `PS5-logs` do pendrive (`kytyps5.log` é o principal). Anexe o arquivo de verdade, não um resumo.

<a id="what-to-send"></a>
## O que enviar

- O modelo do PS4 (CUH-xxxx, na etiqueta atrás), o firmware e o southbridge (Configurações → Sistema → Informações do sistema, por exemplo Belize, Baikal, Aeolia).
- A versão do PS4 Multiboot e o arquivo de payload que você roda.
- A sua linha do `bootargs.txt`.
- A sua versão do EmuFive (Configurações → Sistema), e se ele está instalado no PS4 ou num pendrive/HD USB.
- O modelo da sua TV ou monitor, e o que ela mostra: «Sem sinal», ou ligada, mas preta.
- A luz do PS4: branca, azul, roxa ou apagada.
- Os registros acima.
