# Sorun giderme

<p align="center">
  <a href="TROUBLESHOOTING.md">EN</a> · <a href="TROUBLESHOOTING.ar.md">AR</a> · <a href="TROUBLESHOOTING.zh-CN.md">ZH</a> · <a href="TROUBLESHOOTING.fr.md">FR</a> · <a href="TROUBLESHOOTING.es.md">ES</a> · <a href="TROUBLESHOOTING.de.md">DE</a> · <a href="TROUBLESHOOTING.it.md">IT</a> · <a href="TROUBLESHOOTING.pt-BR.md">PT</a> · <b>TR</b>
</p>

İnsanların [issue](https://github.com/blue0x1/EmuFive/issues)'larda bildirdiği sorunlar ve onlar için işe yarayan çözümler. Adımları sırayla deneyin. Hâlâ olmuyor mu? [Ne gönderilmeli](#what-to-send) bölümündekilerle bir issue açın.

- [Önce dosyaları kontrol edin](#check-the-files-first)
- [Payload'dan sonra siyah ekran veya "Sinyal yok"](#black-screen-or-no-signal-after-the-payload)
- [Menüden veya EmuFive logosundan sonra siyah ekran](#black-screen-after-the-menu-or-the-emufive-logo)
- [Yeşil ekran, yanlış renkler veya titreme](#green-screen-wrong-colors-or-flickering)
- [PS4 kapanıyor veya ışık beyaz kalıyor](#the-ps4-turns-off-or-the-light-stays-white)
- ["No Linux install or archive found"](#no-linux-install-or-archive-found)
- [Kurulum çok uzun sürüyor](#installing-takes-very-long)
- [Yarıda kalan kurulumdan sonra EmuFive açılmıyor](#emufive-doesnt-start-after-a-stopped-install)
- [Sadece USB sürücü takılıyken çalışıyor](#it-only-works-with-the-usb-drive-plugged-in)
- [Oyunlar görünmüyor](#games-dont-show-up)
- [Harici sürücü bulunmuyor](#an-external-drive-isnt-found)
- [Kontrolcü çalışmıyor](#the-controller-doesnt-work)
- [Oyun kapanıyor, donuyor veya yavaş çalışıyor](#a-game-closes-freezes-or-runs-slowly)
- [Günlükler nasıl kaydedilir](#how-to-save-the-logs)
- [Ne gönderilmeli](#what-to-send)

<a id="check-the-files-first"></a>
## Önce dosyaları kontrol edin

"Hiçbir şey olmuyor" bildirimlerinin çoğu bunlardan birinden çıktı:

- **Aynı sürüm:** `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` ve `linux-2048mb.bin` dosyalarının hepsi aynı [PS4 Multiboot sürümünden](https://github.com/blue0x1/ps4-multiboot/releases) gelmeli (en yenisi en iyisi). Karışık dosyalarla açılmaz.
- **Küçük harfli klasör adları:** PS4, `LINUX` ve `linux`'u farklı klasörler olarak görür. Yollar tam olarak `/data/linux/boot/bzImage`, `/data/linux/boot/initramfs.cpio.gz` ve `/data/linux/boot/bootargs.txt` olmalı.
- **Arşivin tam adı:** `/user/home/ps5-ps4-rootfs.tar.xz`. Tarayıcı bazen onu `ps5-ps4-rootfs (1).tar.xz` diye kaydeder, o zaman menü onu bulamaz.
- **İkili aktarım:** FileZilla'da yüklemeden önce Aktarım → Aktarım türü → **İkili** seçin. Metin kipinde yüklenen dosya bozulur. PS4'teki her dosyanın sürümdekiyle aynı boyutta olduğunu kontrol edin.
- **Bizim payload'ımız:** PS4 Multiboot'un `linux-2048mb.bin` dosyasını kullanın (14.02 yazılımında: `linux-2048mb-14.02.bin`). 5.05'ten 14.02'ye kadar yazılımlarda çalışır. Başka Linux payload'ları desteklenmez.

<a id="black-screen-or-no-signal-after-the-payload"></a>
## Payload'dan sonra siyah ekran veya "Sinyal yok"

Payload başladıktan sonra Linux açılırken TV **1-2 dakika** "Sinyal yok" veya siyah ekran gösterir. Bu normaldir. Payload'dan hemen sonra ekranın ve kontrolcünün kapanması da normaldir: PS4 sistemi kapanır ve Linux devralır.

**Ekran karanlıkken PS tuşuna basmayın**: PS4'ü kapatır. PS4'te yalnızca EmuFive varsa, kurulum 60 saniye sonra kendiliğinden başlar, yani zaten kuruyor olabilir.

3 dakika sonra hâlâ bir şey görünmüyorsa:

1. PS4'ü HDMI switch, AV alıcı veya yakalama kartı olmadan, TV'ye **doğrudan** bağlayın.
2. PS4'te **Ayarlar → Sistem → HDCP'yi Etkinleştir**'i kapatın, sonra payload'ı yeniden çalıştırın.
3. Başka bir HDMI kablosu ve başka bir HDMI girişi deneyin.
4. Bir kez başka bir TV veya monitör deneyin. Bazı TV'ler PS4'ün Linux sinyalini almaz; başka bir ekran sorunun TV'de olup olmadığını gösterir.
5. Hâlâ bir şey yok mu? [PS4BOOT günlüğünü](#the-ps4boot-stick-boot-problems) kaydedip bir issue açın. TV'nin **"Sinyal yok"** mu dediğini, yoksa açık ama siyah mı olduğunu yazın.

<a id="black-screen-after-the-menu-or-the-emufive-logo"></a>
## Menüden veya EmuFive logosundan sonra siyah ekran

PS4 Multiboot menüsünü veya EmuFive logosunu görüp sonra ekran kararıyorsa, EmuFive TV'nizin tercih ettiği ama PS4'ün gönderemediği bir moda geçmiştir.

1. EmuFive'ı güncelleyin (Ayarlar → Sistem → Yazılım güncellemesi).
2. FTP ile `/data/linux/boot/bootargs.txt` dosyasını açın ve satırın sonuna ` emufive.mode=1920x1080@60` ekleyin. `video=HDMI-A-1:1920x1080@60D` de kalsın. Dosya **tek satır** kalmalı.
3. Payload'ı yeniden çalıştırın.

Ekran siyah olduğu için güncelleyemiyor musunuz? Bir kez başka bir TV veya monitör bağlayıp güncelleyin ya da EmuFive'ı en yeni `ps5-ps4-rootfs.tar.xz` ile yeniden kurun.

<a id="green-screen-wrong-colors-or-flickering"></a>
## Yeşil ekran, yanlış renkler veya titreme

Yeşil bir katman, siyahın yeşil ya da beyazın camgöbeği görünmesi veya titreme: TV, PS4'ün sinyalini yanlış renk biçiminde okuyor.

1. `bootargs.txt` dosyasına ` emufive.mode=1920x1080@60` ekleyin (yukarıya bakın).
2. Başka bir HDMI kablosu veya girişi deneyin. TV'nin o giriş için ayarlarında **HDMI UHD Color**, **Gelişmiş biçim**, **Deep Colour** veya **Input Signal Plus** gibi seçenekleri değiştirin (açıktan kapalıya veya tersi) ve HDMI-CEC'i kapatın (**Anynet+**, **Bravia Sync**...).
3. Başka bir TV veya monitör deneyin.

<a id="the-ps4-turns-off-or-the-light-stays-white"></a>
## PS4 kapanıyor veya ışık beyaz kalıyor

- **14.02'de** payload'ın ilk çalıştırılması bazen PS4'ü kapatır. Yeniden çalıştırın: ikinci deneme genelde çalışır.
- **Işık beyaz kalıyor** ve 5 dakika boyunca bir şey olmuyorsa: PS4'ü kapatmak için güç tuşunu basılı tutun, yeniden açın ve payload'ı yeniden çalıştırın.
- Kurulumdan sonra **mor ışık** normaldir.
- Siyah ekranda **PS tuşuna basınca PS4 kapanıyor**: basmayın, bekleyin (yukarıya bakın).

<a id="no-linux-install-or-archive-found"></a>
## "No Linux install or archive found"

Menü ne kurulu bir EmuFive ne de `ps5-ps4-rootfs.tar.xz` buldu.

1. Arşivin adını ve yerini kontrol edin: tam olarak `/user/home/ps5-ps4-rootfs.tar.xz`.
2. **Fat PS4**'te (CUH-10xx, 11xx veya 12xx), PS4 Multiboot v1.5.0-beta.3 ile beta.7 arası dahili diski bulamıyordu. [v1.5.0-beta.8](https://github.com/blue0x1/ps4-multiboot/releases/tag/v1.5.0-beta.8) veya daha yenisinin `bzImage` ve `initramfs.cpio.gz` dosyalarını kullanın.

<a id="installing-takes-very-long"></a>
## Kurulum çok uzun sürüyor

- **Diskin oluşturulması** çubuğun ilk %25'idir ve yavaş olan kısım budur: PS4'ün diskine yazılan her şey PS4'ün disk şifrelemesinden geçer. Baikal konsollar bunda daha yavaştır. Büyük disk daha uzun sürer, bu yüzden ilk deneme için daha küçüğünü seçin (16 GB yeterli). %25'ten sonraki kısım daha hızlıdır.
- Yüzde ilerlediği sürece **PS4'ü kapatmayın**. 30 dakika boyunca kıpırdamazsa, bir issue açıp nerede durduğunu yazın.
- **Sonda siyah ekran:** TV hâlâ sinyal alıyorsa kurulum büyük ihtimalle bitmiştir ve EmuFive açılıyordur. PS4'ün güç tuşu onu normal şekilde kapatıyorsa EmuFive çalışıyordur ve yalnızca görüntü siyahtır: [Menüden sonra siyah ekran](#black-screen-after-the-menu-or-the-emufive-logo) bölümüne bakın.

<a id="emufive-doesnt-start-after-a-stopped-install"></a>
## Yarıda kalan kurulumdan sonra EmuFive açılmıyor

PS4 kurulum sırasında kapatıldıysa, yarım oluşturulmuş disk geride kalabilir. Hata ekranında **"The EmuFive disk is incomplete"** yazar ya da günlükte `is a hole` yazar.

1. FTP ile `/user/home/ps5-ps4.img` dosyasını silin. `ps5-ps4-rootfs.tar.xz` kalsın.
2. Payload'ı çalıştırıp yeniden kurun. PS4'ü kapatmadan bitmesini bekleyin.

<a id="it-only-works-with-the-usb-drive-plugged-in"></a>
## Sadece USB sürücü takılıyken çalışıyor

**Install to USB drive**'ı seçtiniz, yani EmuFive o sürücüde duruyor ve ona ihtiyaç duyuyor. Onu PS4'e almak için: sürücüyü çıkarın, payload'ı çalıştırın ve **Install to PS4**'ü seçin.

<a id="games-dont-show-up"></a>
## Oyunlar görünmüyor

Bir oyun, içinde `eboot.bin` ve `sce_sys` olan bir **klasördür** ya da tek bir `.zar` dosyasıdır. `.pkg` ve fpkg dosyaları kullanılamaz: önce oyunu çıkarın. Sahip olduğunuz oyunların dump'larını kullanın.

USB sürücüde şöyle görünmeli:

```
USB sürücü (exFAT, tek bölüm; NTFS de çalışır)
└── PS5/                      <- tam olarak "PS5", büyük harfle, sürücünün en üstünde
    ├── PPSA01234/            <- her oyun için bir klasör (herhangi bir ad)
    │   ├── eboot.bin         <- doğrudan oyun klasöründe
    │   ├── sce_sys/
    │   │   └── param.json    <- oyunun adını ve resmini verir
    │   └── ...
    └── OyunAdi.zar           <- tek dosya hâlinde bir .zar dump'ı
```

Sık yapılan hatalar:

- `ps5/` veya `Ps5/`: ad tam olarak `PS5` olmalı.
- `Oyunlar/PS5/...`: `PS5` klasörü sürücünün en üstünde olmalı.
- `PS5/PPSA01234/PPSA01234/eboot.bin`: fazladan bir klasör seviyesi (arşivden çıkarınca sık olur). İçteki klasörü yukarı taşıyın.
- `PS5/eboot.bin`: oyun dosyaları kendi klasörü olmadan doğrudan `PS5` içinde.
- Bir klasörde iki oyun: yalnızca biri görünür. Kutucuktaki ad klasör adından değil, `sce_sys/param.json`'dan gelir; bu yüzden her oyuna kendi klasörünü verin.

PS4'ün diskinde klasör `/user/home/PS5`'tir ve yalnızca EmuFive PS4'e kuruluysa çalışır (USB sürücüye değil). Oyunları PS4 sisteminden GoldHEN FTP ile kopyalayın, sonra EmuFive'ı açın: bu klasörü açılışta okur.

Yalnızca oyun sürücüsü takılı kalsın. Oynarken `PS4BOOT` günlük belleğini çıkarın.

<a id="an-external-drive-isnt-found"></a>
## Harici sürücü bulunmuyor

- Harici SSD'ler ve sabit diskler EmuFive 1.0.5'ten itibaren çalışır. Önce güncelleyin.
- Daha önce Linux olan bir sürücü normal biçimlendirmeden sonra da görünmeyebilir. Tüm bölümlerini silin (Windows: Disk Yönetimi), sonra tek bir **exFAT** bölümü oluşturun.
- EmuFive bir USB sürücüye kuruluysa, oyunlar ikinci bir USB sürücüye konur (EmuFive 1.0.4'ten itibaren).

<a id="the-controller-doesnt-work"></a>
## Kontrolcü çalışmıyor

- **PS4 Multiboot menüsünde ve kurulum ile hata ekranlarında** kontrolcü yalnızca **USB kabloyla** çalışır. Bluetooth daha sonra, EmuFive'da başlar.
- **Bluetooth** için EmuFive ile bir kez eşlemek gerekir, çünkü PS4 sistemindeki eşleme geçerli değildir. Kabloyu çıkarın, ışık çubuğu çift yanıp sönene kadar **SHARE + PS**'ye basılı tutun ve birkaç saniye bekleyin. Bağlanmazsa Ayarlar → Kontrolcüler → Yeni kontrolcü eşle'yi kullanın.
- Veri taşıyan bir kablo kullanın. Bazı kablolar yalnızca şarj eder.
- **Baikal** konsollarda (birçok CUH-71xx/72xx Pro ve yeni Slim'ler; Ayarlar → Sistem → Sistem Bilgileri'ne bakın) USB için PS4 Multiboot v1.5.0-beta.7 veya daha yenisi gerekir.

<a id="a-game-closes-freezes-or-runs-slowly"></a>
## Oyun kapanıyor, donuyor veya yavaş çalışıyor

- **`ErrorDeviceLost` ile "Oyun durdu (hata kodu 65)":** PS4'ün GPU'su oyunun çizimine takılıp kaldı. Henüz oynanamayan ağır Unreal Engine oyunlarında sık olur. Bakmamızı istiyorsanız [oyun günlüğünü](#game-logs) gönderin.
- **Bellek yetmiyor:** bir PS5 oyunu yaklaşık 12,5 GB'a kadar kullanabilir, PS4'teki Linux'ta ise yaklaşık 6 GB var. EmuFive, PS4 donmadan önce oyunu kapatır. Ayarlar → Oyunlar → **GPU ile paylaşılan oyun belleği**'ni kapatıp yeniden deneyin. EmuFive 4 GB'lık takas dosyasını yalnızca diskinde 8 GB boş yer varsa oluşturur; disk doluysa yer açın.
- **Oyunda donma veya çökme:** bir kez **GPU ile paylaşılan oyun belleği** kapalıyken deneyin. Büyük 3D oyunları hızlandırır ama her oyuna uymaz (Minecraft onunla donuyor).
- **İlk seferde takılma:** bir sahne ilk kez gösterilirken shader'lar derlenir. İkinci sefer daha akıcıdır.
- **Yırtılma:** Ayarlar → Oyunlar → Kare zamanlaması → **Akıcı (yırtılma yok)**.
- **Düşük FPS:** PS4'ün CPU'su ve GPU'su PS5'inkinden çok daha yavaştır. 2D ve hafif oyunlar iyi çalışır; ağır 3D oyunlar çoğu zaman yüklenip menülerini gösterir, sonra oyunda çok yavaş çalışır ya da siyah kalır. Bir PS4 Pro, Slim'den yaklaşık iki kat hızlıdır. Büyük bir oyunu denemeden önce [Oyunlar](README.tr.md#games) tablosuna bakın.

<a id="how-to-save-the-logs"></a>
## Günlükler nasıl kaydedilir

<a id="the-ps4boot-stick-boot-problems"></a>
### PS4BOOT belleği (açılış sorunları)

1. Bir USB belleği **FAT32** olarak, **`PS4BOOT`** etiketiyle (büyük harfle) biçimlendirin. Windows 32 GB'tan büyük bellekleri FAT32 yapamaz: daha küçük bir bellek kullanın ya da [Rufus](https://rufus.ie) ile yapın (Önyükleme seçimi: *Önyüklenebilir değil*, Dosya sistemi: *Large FAT32*, Birim etiketi: `PS4BOOT`). NTFS ve exFAT bunun için çalışmaz.
2. Payload'ı çalıştırmadan **önce** PS4'e takın ve takılı bırakın.
3. Payload'ı çalıştırın ve ekran siyah kalsa bile **5 dakika** bekleyin. Bir hata ekranı çıkarsa ayrıntıları belleğe kendisi kaydeder.
4. PS4'ü kapatmak için güç tuşunu basılı tutun. Belleği bir bilgisayara takın ve `.log` dosyalarını issue'nuza ekleyin (`ps4-linux-boot.log`, `ps4-linux-late.log`, `ps4-linux-error.log` veya `ps4-linux-rescue.log`).

Bellek boş kalırsa bunu yazın: Linux'un o kadar ilerleyemediği anlamına gelir, bu da yardımcı olur.

<a id="game-logs"></a>
### Oyun günlükleri

Oyun durduktan hemen sonra Ayarlar → Sistem → **Günlükleri USB'ye kopyala**'ya gidin, sonra USB sürücüdeki `PS5-logs` klasöründeki dosyaları ekleyin (asıl olan `kytyps5.log`). Özet değil, gerçek dosyayı ekleyin.

<a id="what-to-send"></a>
## Ne gönderilmeli

- PS4 modeli (CUH-xxxx, arkadaki etikette), yazılım sürümü ve southbridge (Ayarlar → Sistem → Sistem Bilgileri, örn. Belize, Baikal, Aeolia).
- PS4 Multiboot sürümü ve çalıştırdığınız payload dosyası.
- `bootargs.txt` satırınız.
- EmuFive sürümünüz (Ayarlar → Sistem) ve PS4'e mi yoksa bir USB sürücüye mi kurulu olduğu.
- TV'nizin veya monitörünüzün modeli ve ne gösterdiği: "Sinyal yok" mu, yoksa açık ama siyah mı.
- PS4'ün ışığı: beyaz, mavi, mor veya kapalı.
- Yukarıdaki günlükler.
