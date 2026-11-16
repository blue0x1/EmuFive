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

Ardından EmuFive'ı başlatmak için payload'ı çalıştırın (başka sistemler de kuruluysa önce PS4 Multiboot menüsü açılır). Yeniden kurmak için FTP ile `/user/home/ps5-ps4.img` dosyasını silip payload'ı çalıştırın. Güncellemeler: Ayarlar, Sistem, Yazılım güncellemesi.

### Kullanım

- **Ana ekran:** oyunlarınız kutucuk olarak. Birini seçip Oyna'ya basın. Bir oyunda OPTIONS: favori, gizle, oyunun ayarları, kupaları ve oynama süresi.
- **Oyunda PS tuşu:** duraklatma menüsü (Devam, Ana ekran, Oyunu kapat, ses, güç).
- **Ekran görüntüleri:** PS + Kare veya Share. Medya'da görün; Üçgen, birini telefonda açmak için QR kod gösterir.
- **İnternet:** kumandayla kullanılan bir web tarayıcısı kutucuğu.
- **Ayarlar:** Wi-Fi, görünüm, kumandalar, profiller (en fazla 8), menü dili, tarih ve saat, yedekleme.
- **Kumandalar:** kabloyla ya da Bluetooth ile bir DualShock 4 (ışık çubuğu iki kez yanıp sönene kadar SHARE + PS'ye basılı tutun).
- **Giriş:** SSH ile veya tty2'de `ps5` / `ps5`. Emülatör günlüğü `~/kytyps5.log`.

### Oyunlar nerede olabilir

- **USB sürücü:** sürücünün en üstündeki `PS5` klasörü (en iyisi exFAT; NTFS de olur).
- **PS4 diski:** GoldHEN FTP ile kopyalanan `/user/home/PS5` (EmuFive'ın kendisi USB sürücüdeyse olmaz).
- **Bir PC:** Windows veya Linux'ta paylaşılan bir klasör. Ayarlar'da **PC'deki oyunları kullan**'ı açın, adresi, paylaşımı ve girişi yazın, sonra Bağlan.

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

### 1.0.8 (2026-11-16)

- İyileştirildi: çok büyük arabellekli oyunlar çok daha hızlı. Artık her karede yalnızca küçük arabellekler tümüyle yükleniyor; büyükler yeniden sayfa sayfa izleniyor. Teardown, PS4 Pro'da 1 FPS'nin altından yaklaşık 2,4 FPS'ye çıktı. Teardown ayrıca 5 GB GPU belleği istiyor: PS4 Multiboot v1.5.0-beta-5'in `bootargs.txt` dosyasını kullanın.

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

## Destek

EmuFive işinize yarıyorsa, geliştirilmesini Bitcoin bağışıyla destekleyebilirsiniz:

BTC: `bc1q7w5ns9vsguseppllpy609yhwrtq3v56g94mjde`

## Lisans

Copyright (C) 2026 [Chokri Hammedi (blue0x1)](https://github.com/blue0x1).

GPL-2.0 (bkz. `LICENSE`). KytyPS5, Mesa ve Linux çekirdeği kendi lisanslarına tabidir. PlayStation, Sony Interactive Entertainment'ın ticari markasıdır; bu proje Sony ile bağlantılı değildir.
