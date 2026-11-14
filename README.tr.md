<h1 align="center"><img src="assets/emufive-logo.png" alt="EmuFive" width="480"></h1>

<p align="center">
  <img src="https://img.shields.io/badge/platform-PS4-003791?logo=playstation&logoColor=white" alt="Platform: PS4">
  <img src="https://img.shields.io/badge/status-experimental-red" alt="Status: experimental">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--2.0-blue" alt="License: GPL-2.0"></a>
</p>

<p align="center">
  <a href="README.md">EN</a> · <a href="README.ar.md">AR</a> · <a href="README.zh-CN.md">ZH</a> · <a href="README.fr.md">FR</a> · <a href="README.es.md">ES</a> · <a href="README.de.md">DE</a> · <a href="README.it.md">IT</a> · <a href="README.pt-BR.md">PT</a> · <b>TR</b>
</p>

PS4 için bir PS5 emülatörü.

Geliştiren: **[Chokri Hammedi (blue0x1)](https://github.com/blue0x1)**. [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot) üzerine kurulu.

> **Durum: deneysel araştırma.** Bir PS4 Pro'da "Sons of Sparta" yaklaşık 40 FPS ve üzerinde çalışıyor. KytyPS5, oyun kodundaki PS5'e özgü CPU komutlarını yeniden yazar (yama `0004`). Diğer oyunlar hâlâ test ediliyor ve birçoğu şimdilik yavaş. Bkz. [CPU sorunu](#the-cpu-problem).

<p align="center"><img src="assets/home-screen.png" alt="Bir PS4 Pro'da EmuFive ana ekranı, God of War Sons of Sparta seçili" width="900"></p>

<p align="center">
  <b><a href="#installing">Kurulum</a></b> · <b><a href="#games">Oyunlar</a></b> · <b><a href="#changelog">Değişiklik günlüğü</a></b> · <a href="#how-it-works">Nasıl çalışır</a> · <a href="#the-cpu-problem">CPU sorunu</a> · <a href="#plan">Plan</a> · <a href="#building">Derleme</a> · <a href="#credits">Katkıda bulunanlar</a>
</p>

<a id="how-it-works"></a>
## Nasıl çalışır

- **[PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot)**, PS4'te Linux'u başlatır ve kontrolcüyle Linux sistemlerini PS4'ün dahili diskine kurar.
- PS4 Multiboot'un bir parçası olan **PS4 Mesa**, PS4'ün GPU'suna (PS4 ve Slim'de Liverpool, Pro'da Gladius) Vulkan 1.3 desteği verir. KytyPS5'in seyrek kaynaklara (sparse resources) ihtiyacı vardır; RADV bunları bu GPU'da `RADV_EXPERIMENTAL=sparse` ile sunar.
- **KytyPS5**: sabitlenmiş bir commit'teki orijinal proje ve bu projenin yamaları (`patches/kytyps5/`), PS4'ün AMD Jaguar CPU'su için `-march=btver2` ile derlenmiş hâli. Resmî sürüm AVX2 kullanır ve PS4'te "Illegal instruction" ile durur.
  - `0001`: `KYTY_HOST_ARCH` derleme seçeneği (emülatörün derlendiği CPU).
  - `0002`: homebrew için bir C kütüphanesi. ps5-native-app-boilerplate ile yapılan PS5 homebrew'ları, tüm fonksiyonları 0 döndüren yedek bir `sce_module/libc.prx` modülüyle gelir (konsol kendi C kütüphanesini kullanır); bu yüzden KytyPS5'te `malloc` başarısız oluyordu. Yama, bu homebrew'ların içe aktardığı C kütüphanesi fonksiyonlarını ekler ve bunları yalnızca böyle bir yedek modül için kullanır.
  - `0003`: homebrew için daha fazlası: dosyalar ve klasörler, sistem çağrıları, ön plandaki kullanıcı ve ek bağlama noktaları (`KYTY_MOUNTS`).
  - `0004`: PS4'ün CPU'sunda PS5 kodu. Her AVX2, FMA ve BMI2 komutu, bir modül yüklenirken SSE4.2/AVX/BMI1 koduna yeniden yazılır; o sırada yeniden yazılamayan bir komut, ilk çalıştığında değiştirilir. Bkz. [CPU sorunu](#the-cpu-problem).
- **EmuFive** tüm bunları, masaüstü olmadan, tam ekran doğrudan emülatörle açılan küçük bir Linux sisteminde toplar. Diğer sistemler gibi PS4 Multiboot ile kurulur.

<a id="the-cpu-problem"></a>

## CPU sorunu

KytyPS5, PS5'in CPU'sunu emüle etmez: oyunun kendi x86-64 kodunu doğrudan çalıştırır. PS5 oyunları PS5'in Zen 2 CPU'su için derlenir ve her yerde AVX2, BMI2 ve FMA komutları kullanır. PS4'ün Jaguar CPU'sunda bunların hiçbiri yoktur, bu yüzden oyun kodu bu tür ilk komutta durur.

Yama `0004`, bunu KytyPS5'in misafir komut yamalayıcısına ekler. Ana CPU'da AVX2, FMA veya BMI2 yoksa, bu tür her komut aynı etkiye sahip bir kodla değiştirilir: 256 bitlik tamsayı işlemleri iki 128 bitlik yarı olarak, yarılar arası permütasyonlar AVX taşıma ve karıştırma komutlarıyla, eleman başına kaydırmalar tek tek, FMA çift duyarlıkta, gather'lar tek tek eleman eleman, BMI2 ise kaydedilen yazmaçlarla. Değiştirilen koda atlama, komutun bulunduğu yere yazılır; atlama için çok kısa olan ve yamalayıcının yeniden düzenleyemediği bir yerdeki komut hata verir ve çalışma anında değiştirilir.

`tools/jaguar-test/`, bu komutlara sahip bir PC'de her değiştirmeyi kontrol eder: bir programın kodunda bulunan her komut biçimini alır, orijinali ve değiştirileni aynı rastgele durumdan çalıştırır ve tüm yazmaçları, bayrakları ve belleği karşılaştırır. Şimdiye kadar test edilen programlardaki biçimler eşleşiyor: God of War Sons of Sparta'da 287 (gather ve VFMADDSUB dahil) ve önceden test edilen programlarda 227. İstisnalar, FMA'da nadir son bit farkları (tek duyarlık iki kez yuvarlanır, çift duyarlık bir çarpma ve bir toplamadır) ve 0 çarpı sonsuz için bir NaN özel durumudur.

Jaguar, PS5'in CPU'sundan hâlâ çok daha yavaştır ve değiştirmeler buna eklenir; bu yüzden çalışan bir oyun bile yavaş çalışabilir.

<a id="plan"></a>
## Plan

| Adım | Durum |
|---|---|
| PS4 GPU'sunda Vulkan, KytyPS5'in gereksinimlerini karşılıyor | Tamam (`RADV_EXPERIMENTAL=sparse`) |
| KytyPS5, PS4'ün CPU'su için derlendi | Tamam (`KYTY_HOST_ARCH=btver2`) |
| KytyPS5 PS4'te başlıyor ve GPU'yu hazırlıyor | Tamam, PS4 Pro |
| EmuFive sistem imajı, PS4 Multiboot ile kuruluyor | Tamam, PS4 Pro |
| AVX2 kullanmayan bir PS5 homebrew uygulaması çalışıyor ve çiziyor | Tamam: btver2 için yeniden derlenmiş Snes9x PS5 2.11, PS4 Pro |
| Kontrolcü, `/data` ve USB depolama, o uygulamada oyun yükleme | Bir PC test sürümünde tamam (aynı yamalar); sırada PS4 var |
| Oyun kodu için AVX2, BMI2 ve FMA çevirisi | Tamam (`0004`), bir PC'de doğrulandı |
| Bir PS5 oyunu PS4'te çalışıyor | Tamam: God of War Sons of Sparta, yaklaşık 40 FPS ve üzeri, PS4 Pro |
| Hollow Knight: Silksong PS4'te çalışıyor | 1.0.1'den beri tamam (yamalar `0006` ve `0007`), PS4 Pro |
| Ana ekran: kontrolcüyle oyun seçme; Wi-Fi; Ayarlar | Tamam, bir PC'de doğrulandı |
| USB sürücüden, PS4 diskinden veya bir PC paylaşımından oyunlar | Tamam, bir PC'de doğrulandı; sırada PS4 var |

<a id="building"></a>

## Derleme

Docker, git ve PS4 Multiboot'tan PS4 Mesa gerekir (`../PS4-Multiboot/out/ps4-mesa.tar.xz`, orada `make mesa` ile derlenir). `build-kyty.sh` ilk seferde KytyPS5'i `build/kytyps5` içine klonlar, sonra her derlemede onu sabitlenmiş commit'e döndürür ve yamaları uygular.

```bash
scripts/build-kyty.sh      # out/kytyps5-ps4.tar.xz
scripts/build-rootfs.sh    # out/ps5-ps4-rootfs.tar.xz
```

`PS4_MESA` ve `KYTY`, `build-rootfs.sh`'ye başka yollar gösterir.

<a id="installing"></a>

## Kurulum

EmuFive, diğer Linux sistemleri gibi [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot) ile kurulur.

Gerekenler:

- **GoldHEN** yüklü, jailbreak yapılmış bir PS4 (FTP sunucusu ve payload yükleyicisi için).
- Aynı ağda, bir FTP istemcisi (örneğin FileZilla) olan bir PC.
- PS4'te yaklaşık 28 GB boş alan (16 GB'lık bir disk ve PS4 için her zaman boş bırakılan 10 GB) ya da 8 GB veya daha büyük bir USB sürücü.
- Bir DualShock 4 (USB kabloyla ya da daha sonra Bluetooth ile eşleştirilmiş).

Adımlar:

1. [PS4 Multiboot sürümlerinden](https://github.com/blue0x1/ps4-multiboot/releases) `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` ve `linux-2048mb.bin` dosyalarını indirin. (`ps4-mesa.tar.xz` gerekmez: EmuFive'da PS4 Mesa zaten var.)
2. [EmuFive sürümlerinden](https://github.com/blue0x1/EmuFive/releases) `ps5-ps4-rootfs.tar.xz` dosyasını indirin (veya derleyin, bkz. [Derleme](#building)). Adını değiştirmeyin: PS4 Multiboot sistemleri adındaki `-ps4-rootfs` kısmından tanır.
3. GoldHEN'in FTP sunucusunu açın ve dosyaları PS4'e kopyalayın (port 2121):

   | Dosya | PS4'teki klasör |
   |---|---|
   | `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` | `/data/linux/boot/` |
   | `ps5-ps4-rootfs.tar.xz` | `/user/home/` |
   | `linux-2048mb.bin` | `/data/payloads/` |

4. GoldHEN'in payload menüsünden `linux-2048mb.bin` dosyasını çalıştırın.

   > **Sabırlı olun:** payload başladıktan sonra Linux açılırken TV **1 ila 2 dakika boyunca "No signal" ya da siyah ekran** gösterebilir. Bu normaldir.

5. PS4 Multiboot menüsünde **EmuFive**'ı, ardından **Install to PS4** veya **Install to USB drive** seçeneğini seçin. Birkaç dakika sürer.
6. Oyunlarınızı aşağıdaki yerlerden birine koyun. Bir oyun, içinde `eboot.bin` (ve `sce_sys`) olan bir klasör veya bir ZArchive (`.zar`) dökümüdür.

Bundan sonra EmuFive'ı başlatmak için payload'ı çalıştırın: yalnızca EmuFive kuruluysa hemen başlar, başka sistemler de varsa önce PS4 Multiboot menüsü gelir. PS4 sistemine dönmek için ana ekrandan kapatın veya yeniden başlatın. EmuFive'ı yeniden kurmak için FTP ile `/user/home/ps5-ps4.img` dosyasını silin ve payload'ı çalıştırın.

Güncellemeler EmuFive sürümlerinden gelir: Ayarlar, Sistem, Yazılım güncellemesi (yeniden kurulum gerekmez).

Sistem ana ekranla açılır ve klavye gerektirmez:

- Oyunlar kutucuklar olarak görünür; her birinde bulunduğu yer yazar: **USB**, **PS4** veya **PC**. Birini seçip Oyna'ya basın; oyun kapanınca ana ekran geri gelir.
- Üstte: Wi-Fi (şifre için ekran klavyesiyle) ve Ayarlar, ayrıca iki sekme, **Oyunlar** ve **Medya** (L1 / R1). Medya ekran görüntülerinizi gösterir; birini açın, Kare onu siler.
- Bir oyunda OPTIONS: favori, gizle, oyunun kendi ayarları, kupaları ve ne kadar oynadığınız.
- **Internet**, oyunlardan sonraki kutucuk: kontrolcüyle kullanılan bir web tarayıcısı. Sol çubuk (veya dokunmatik yüzey) işaretçiyi hareket ettirir ve X tıklar; sağ çubuk kaydırır; O veya L1 geri, R1 ileri gider; L2 ve R2 yakınlaştırır. Üçgen bir adres veya arama yazar, bir sayfadaki metin kutusunu seçmek de ekran klavyesini açar. OPTIONS menüyü açar: yer imleri, başlangıç sayfası, yakınlaştırma, arama motoru (Google, DuckDuckGo veya Bing), mobil siteler (daha hafif sayfalar) ve geçmişle çerezleri temizleme. PS tuşu ana ekrana döner ve bir dahaki sefere aynı sayfa açılır. Bir seferde tek sayfa gösteren WebKitGTK'dir; metin sayfasında yaklaşık 450 MB bellek, video sitelerinde daha fazlasını kullanır; çalışırken ana ekran kapanır ve duraklatılmış bir oyunun önce kapatılması gerekir. İndirmeler, yüklemeler, kamera, mikrofon ve konum reddedilir. Yer imleri `~/.config/ps5-on-ps4/browser.json` içinde, çerezler `~/.local/share/ps5-browser` içindedir.
- Oyun sırasında PS tuşu oyunu duraklatır ve hızlı menüyü açar: Devam et, **Ana ekran** (oyun duraklatılmış hâlde ana ekran: PS veya Devam et oyuna döner; başka bir oyun başlatmak önce sorar, sonra onu kapatır), oyunu kapat, ses, güç.
- Ekran görüntüleri: PS + Kare veya Share, oyun içinde de. USB sürücüdeki `PS5-screenshots` klasörüne (yoksa `~/Screenshots` içine) kaydedilir ve köşede küçük bir bildirim çıkar. Birini telefonunuza almak için Medya'da açın ve Üçgen'e (Paylaş) basın: telefonla (aynı ağda) QR kodunu tarayarak orada açın, sonra kaydedin veya paylaşın. PS4 yalnızca o tek resmi, rastgele bir adreste ve yalnızca kod ekrandayken sunar. QR kodları `python3-segno` ile oluşturulur.
- Ayarlar, Görünüm: vurgu rengi, tema (koyu, gece yarısı, açık), arka plan (oyunun görseli, bir geçiş, düz bir renk veya USB sürücüden kendi resminiz), arka plan karartma, yüzen küreler, animasyonlar, kutucuk boyutu ve şekli, yazı boyutu ve yazı tipi, saat, üst çubukta görünenler (pil kontrolcünün pilidir), menü sesleri, titreşim, tuş ipuçları, ekran kenarları (overscan) ve bir ekran koruyucu.
- Ayarlar, Kontrolcüler: ışık çubuğunun rengi ve parlaklığı, titreşimin açık/kapalı olması ve gücü, kontrolcü mikrofonunun açık/kapalı olması (kontrolcü USB kabloyla bağlıyken; Linux'ta Bluetooth üzerinden kontrolcü sesi yoktur), X ve O'yu değiştirme ve her tuş ile çubuk için bir test sayfası. Ayarlar, Oyunlar: tüm oyunlar için varsayılanlar, oyun dili, HDR ve kare zamanlaması. Ayarlar, Tarih ve saat: internetten otomatik (varsayılan) veya elle. Ayarlar, Sistem: menü dili (İngilizce, Arapça, Fransızca, Türkçe, İspanyolca, Almanca, İtalyanca veya Brezilya Portekizcesi), sıcaklık ve CPU yükü, ayarları USB sürücüye yedekleme veya hepsini sıfırlama.
- Profiller (Ayarlar, Profil ve hızlı menüde Profil değiştir): en fazla 8 tane; her birinin kendi adı, avatarı, kayıtları, kupaları ve oyun süresi vardır. Birden fazla profil varsa açılışta "Kim oynuyor?" gelir. Her profilin kendi KytyPS5 klasörü vardır (`~/.kytyps5/users/<ID>`, ilk profil `~/.kytyps5` klasörünü kullanır); gölgelendirici (shader) önbelleği ortaktır.
- Sol üst köşede bildirimler, oyun içinde de: ekran görüntüsü kaydedildi, bir kontrolcü bağlandı (bağlantı türü ve pil düzeyiyle), kontrolcü pili zayıf (%15). Üst çubuktaki pil, düzeyine göre yeşil, sarı veya kırmızıdır ve şarj olurken bir şimşek gösterir.
- Belleğin bitmesi: sistem diskindeki 4 GB'lık bir swap dosyası (`ps5-swap.service`, yer olduğunda bir kez oluşturulur), büyük bir oyunun PS4'ü dondurmak yerine yavaşlamasını sağlar; bellek ve swap yine de biterse oyun PS4 donmadan önce kapatılır ve ana ekran nedenini söyler.
- Menü dilleri: çeviriler `lib/ps5/translations.json` içindedir, her İngilizce metin için bir kayıt. Arapça sağa hizalıdır ve DejaVu Sans ile çizilir; buradaki SDL_ttf Arapça harfleri birleştirmediği için harfler `lib/ps5/i18n.py` içinde birleştirilir.
- Program USB sürücüyü `/mnt/usb0`, sistemdeki bir klasörü (`~/data`, açılışlar arasında korunur) ise `/data` olarak görür. Snes9x PS5 için ROM'lar USB sürücüdeki `snes9x/roms` veya `~/data/snes9x/roms` klasörüne konur.
- Emülatör bir hatayla durursa ana ekran nedenini gösterir.
- `/etc/ps5-on-ps4.conf` içindeki `PS5_GAME`, ana ekran yerine doğrudan bir oyunu çalıştırır.
- Kontrolcüler: kabloyla bağlı bir DualShock 4 ya da ışık çubuğu iki kez yanıp sönene kadar SHARE + PS basılı tutulduktan sonra Bluetooth ile.
- Ses HDMI üzerinden TV'ye gider; kabloyla bağlı bir kontrolcü kendi ses kartını getirse bile (`/etc/wireplumber/wireplumber.conf.d/51-ps5-hdmi.conf`).

### Oyunlar nerede olabilir

- **USB sürücü:** sürücünün kökündeki `PS5` klasörü. En iyisi exFAT'tir (4 GB'tan büyük dosyalar); NTFS de çalışır.
- **PS4 diski:** PS4'teki `/user/home/PS5`, oraya GoldHEN FTP ile kopyalanır. Sistem PS4 diskini salt okunur olarak okur ve asla değiştirmez. Sistemin kendisi bir USB sürücüye kuruluysa kullanılamaz.
- **Bir PC:** Windows veya Linux'ta paylaşılan bir klasör. Ayarlar'da **PC'deki oyunları kullan** seçeneğini açın ve PC adresini, paylaşılan klasörü ve misafir paylaşımı değilse bir kullanıcı adı ile şifreyi girin; ardından Bağlan. Oyunlar paylaşılan klasörün kökünde veya içindeki bir `PS5` klasöründe olabilir. Ağ kablosu Wi-Fi'dan daha hızlıdır.
  - Windows: klasörü paylaşın (Özellikler, Paylaşım). Misafir paylaşımı için Everyone ile paylaşın ve gelişmiş paylaşım ayarlarında *Password protected sharing* seçeneğini kapatın.
  - Linux (Samba): misafir paylaşımı için `guest ok = yes` içeren bir paylaşım veya bir Samba kullanıcısı (`smbpasswd -a`).
  - PS4 çekirdeğinde SMB istemcisi yoktur, bu yüzden sistem smbnetfs (FUSE) kullanır. Şifre dahil ayarlar `~/.config/ps5-on-ps4/pc-share.json` içinde tutulur ve yalnızca `ps5` kullanıcısı okuyabilir.

`tools/make-pad-test-rom.py`, bir kontrolcüyü denemek için küçük bir SNES ROM'u oluşturur: mavi, bir tuşa basılı tutulurken yeşil.

Giriş: tty2'de veya SSH ile `ps5` / `ps5`. Emülatörün çıktısı `~/kytyps5.log` içindedir (bir önceki çalıştırma: `~/kytyps5.log.1`).

<a id="games"></a>
## Oyunlar

Bu proje hiçbir PS5 sistem yazılımı ve hiçbir oyun içermez. Yalnızca sahip olduğunuz ve dökümünü kendiniz aldığınız oyunları kullanın.

Denenen oyunlar:

| Oyun | Konsol | Sonuç |
|---|---|---|
| God of War Sons of Sparta | PS4 Pro | Oynanabilir, yaklaşık 40 FPS ve üzeri |
| Hollow Knight: Silksong | PS4 Pro | Oynanabilir, 50 ile 60 FPS arası |
| Plants vs. Zombies: Replanted | PS4 Pro | Oynanabilir, sabit 60 FPS |
| Vampire Survivors | PS4 Slim | Oynanabilir, kararlı 60 FPS |
| Spider-Man 2 | | Henüz denenmedi |

Bir oyun mu denediniz? Oyunu, konsol modelinizi ve nasıl çalıştığını yazarak bir [issue](https://github.com/blue0x1/EmuFive/issues) açın.

<a id="changelog"></a>
## Değişiklik günlüğü

### 1.0.6 (2026-11-14)

- İyileştirildi: ana ekran kullanılmadığı sürece çok daha az CPU kullanıyor (4K'da bir çekirdeğin yaklaşık üçte biri, önceden bir çekirdeğin tamamı); böylece PS4 daha serin ve sessiz çalışıyor.

1.0.3 veya önceki bir sürümden güncellemek için, eski yazılım güncellemesi bunu yapamadığından güncellemeyi bir kez elle başlatın: Ayarlar'da SSH'yi açın, `ssh ps5@<PS4 adresi>` ile bağlanın (değiştirmediyseniz parola `ps5`) ve çalıştırın:

```bash
sudo systemd-run --unit=emufive-update --collect /opt/ps5-on-ps4/bin/ps5-update install
```

Eksik tüm güncellemeleri kurar (1.0.0 veya 1.0.1'den buna 1.0.2'nin yaklaşık 110 MB'lık tarayıcı paketleri dahildir); ardından ana ekrandan yeniden başlatın. 1.0.4'ten itibaren Ayarlar'daki yazılım güncellemesi çalışır. Yeni kurulumlar 1.0.6 sürümündeki `ps5-ps4-rootfs.tar.xz` dosyasını kullanır.

## Proje yapısı

| Yol | İçerik |
|---|---|
| `scripts/build-kyty.sh` | KytyPS5'i (orijinal artı `patches/kytyps5/`) PS4'ün CPU'su için derler |
| `patches/kytyps5/` | Bu projenin KytyPS5'te yaptığı değişiklikler |
| `scripts/build-rootfs.sh` | PS4 Multiboot için sistem imajını oluşturur |
| `scripts/make-release.sh` | Bir sürümün güncelleme paketini oluşturur (Ayarlar, Sistem, Yazılım güncellemesi kurar) |
| `scripts/updates/` | Bir güncellemenin, dosyaları yerleştikten sonra PS4'te çalıştırdığı betikler (`--post`) |
| `docker/` | İkisi için derleme ortamları |
| `overlay/` | Sisteme eklenen dosyalar: oturum, ana ekran, ayarlar, USB sürücü ve PS4 diski bağlama, kontrolcü eşleştirme |
| `tools/` | Logo dönüştürücü, kontrolcü test ROM'u, `extract-code.py` (bir PS5 SELF/ELF dosyasının kodu) |
| `tools/jaguar-test/` | Yama `0004`'ün değiştirmelerini gerçek komutlarla karşılaştırır |

## Özel teşekkürler

- [KytyPS5](https://github.com/KytyPS5/KytyPS5), EmuFive'ın temel aldığı PS5 emülatörü (GPL-2.0)
- InoriRus'un [Kyty](https://github.com/InoriRus/Kyty) projesi, KytyPS5'in temel aldığı emülatör

<a id="credits"></a>
## Katkıda bulunanlar

- [Mesa](https://mesa3d.org) ve fail0verflow, DionKill ile striker91n'nin PS4 GPU yamaları
- PS4 Linux çekirdeği geliştiricileri ([sony-jaguar-devs/ps4-linux](https://github.com/sony-jaguar-devs/ps4-linux))

## Lisans

Copyright (C) 2026 [Chokri Hammedi (blue0x1)](https://github.com/blue0x1).

GPL-2.0 (bkz. `LICENSE`). KytyPS5, Mesa ve Linux çekirdeği kendi lisanslarına tabidir. PlayStation, Sony Interactive Entertainment'ın ticari markasıdır; bu proje Sony ile bağlantılı değildir.
