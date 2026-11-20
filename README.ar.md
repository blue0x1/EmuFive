<h1 align="center"><img src="assets/emufive-logo.png" alt="EmuFive" width="480"></h1>

<p align="center">
  <img src="https://img.shields.io/badge/platform-PS4-003791?logo=playstation&logoColor=white" alt="Platform: PS4">
  <img src="https://img.shields.io/badge/status-experimental-red" alt="Status: experimental">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--2.0-blue" alt="License: GPL-2.0"></a>
  <a href="https://github.com/blue0x1/EmuFive/releases"><img src="https://img.shields.io/github/downloads/blue0x1/EmuFive/total?label=downloads" alt="Downloads"></a>
</p>

<p align="center">
  <a href="README.md">EN</a> · <b>AR</b> · <a href="README.zh-CN.md">ZH</a> · <a href="README.fr.md">FR</a> · <a href="README.es.md">ES</a> · <a href="README.de.md">DE</a> · <a href="README.it.md">IT</a> · <a href="README.pt-BR.md">PT</a> · <a href="README.tr.md">TR</a>
</p>

<div dir="rtl">

محاكي PS5 يعمل على PS4.

من إنشاء **[Chokri Hammedi (blue0x1)](https://github.com/blue0x1)**. مبني على [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot).

> **الحالة: بحث تجريبي.** على PS4 Pro تعمل لعبة "Sons of Sparta" بنحو 40 إطارًا في الثانية وأكثر. يعيد KytyPS5 كتابة تعليمات المعالج الخاصة بـ PS5 في كود اللعبة (الرقعة `0004`). ما زالت ألعاب أخرى قيد الاختبار، وكثير منها بطيء حاليًا. راجع [مشكلة المعالج](#the-cpu-problem).

</div>

<p align="center"><img src="assets/home-screen.png" alt="الشاشة الرئيسية لـ EmuFive على PS4 Pro، ولعبة God of War Sons of Sparta محددة" width="900"></p>

<p align="center">
  <b><a href="#installing">التثبيت</a></b> · <b><a href="#games">الألعاب</a></b> · <b><a href="#changelog">سجل التغييرات</a></b> · <a href="#how-it-works">كيف يعمل</a> · <a href="#the-cpu-problem">مشكلة المعالج</a> · <a href="#plan">الخطة</a> · <a href="#building">البناء</a> · <a href="#credits">شكر وتقدير</a>
</p>

<div dir="rtl">

<a id="how-it-works"></a>
## كيف يعمل

- **[PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot)** يشغّل Linux على PS4 ويثبّت أنظمة Linux على قرصه الداخلي، باستخدام وحدة التحكم.
- **PS4 Mesa**، وهو جزء من PS4 Multiboot، يمنح معالج الرسوميات في PS4 (Liverpool في PS4 وSlim، وGladius في Pro) دعم Vulkan 1.3. يحتاج KytyPS5 إلى الموارد المتفرقة (sparse resources)، ويوفرها RADV على هذا المعالج مع `RADV_EXPERIMENTAL=sparse`.
- **KytyPS5**، من المصدر الأصلي عند commit مثبّت مع رقع هذا المشروع (`patches/kytyps5/`)، مبني بـ `-march=btver2` لمعالج AMD Jaguar في PS4. النسخة الرسمية تستخدم AVX2 وتتوقف على PS4 برسالة "Illegal instruction".
  - `0001`: خيار البناء `KYTY_HOST_ARCH` (المعالج الذي يُبنى المحاكي له).
  - `0002`: مكتبة C لتطبيقات الـ homebrew. تطبيقات PS5 المبنية بـ ps5-native-app-boilerplate تأتي مع وحدة بديلة `sce_module/libc.prx` كل دوالها تُرجع 0 (الجهاز يستخدم مكتبة C الخاصة به)، لذلك كانت `malloc` تفشل فيها داخل KytyPS5. تضيف الرقعة دوال مكتبة C التي تستوردها هذه التطبيقات، ولا تستخدمها إلا مع مثل هذه الوحدة البديلة.
  - `0003`: المزيد للـ homebrew: الملفات والمجلدات، واستدعاءات النظام، والمستخدم الحالي، ونقاط تركيب إضافية (`KYTY_MOUNTS`).
  - `0004`: كود PS5 على معالج PS4. كل تعليمة AVX2 وFMA وBMI2 تُعاد كتابتها إلى كود SSE4.2/AVX/BMI1 عند تحميل الوحدة؛ والتعليمة التي لا يمكن إعادة كتابتها هناك تُستبدل في أول مرة تُنفَّذ فيها. راجع [مشكلة المعالج](#the-cpu-problem).
- **EmuFive** يجمع كل ذلك في نظام Linux صغير يقلع مباشرة إلى المحاكي، بملء الشاشة، بدون سطح مكتب. ويُثبَّت عبر PS4 Multiboot مثل أي نظام آخر.

<a id="the-cpu-problem"></a>

## مشكلة المعالج

لا يحاكي KytyPS5 معالج PS5: بل يشغّل كود x86-64 الخاص باللعبة مباشرة. ألعاب PS5 مبنية لمعالج Zen 2 في PS5 وتستخدم تعليمات AVX2 وBMI2 وFMA في كل مكان. معالج Jaguar في PS4 لا يملك أيًا منها، فيتوقف كود اللعبة عند أول تعليمة من هذا النوع.

تضيف الرقعة `0004` ذلك إلى أداة ترقيع التعليمات في KytyPS5. عندما يفتقد المعالج المضيف AVX2 أو FMA أو BMI2، تُستبدل كل تعليمة من هذا النوع بكود له نفس الأثر: عمليات الأعداد الصحيحة بعرض 256 بت كنصفين بعرض 128 بت، والتبديل بين النصفين بتعليمات نقل ومزج AVX، والإزاحة لكل عنصر عنصرًا عنصرًا، وFMA محسوبة بدقة مضاعفة، والتجميع (gather) عنصرًا عنصرًا، وBMI2 مع حفظ السجلات. القفزة إلى البديل تُكتب مكان التعليمة؛ والتعليمة الأقصر من أن تتسع لقفزة، في موضع لا تستطيع الأداة إعادة ترتيبه، تُسبب خطأً وتُستبدل أثناء التشغيل.

يتحقق `tools/jaguar-test/` من كل بديل على كمبيوتر يملك هذه التعليمات: يأخذ كل صيغة تعليمة موجودة في كود برنامج، ويشغّل الأصل والبديل من نفس الحالة العشوائية، ويقارن كل السجلات والأعلام والذاكرة. الصيغ الموجودة في البرامج المختبرة حتى الآن متطابقة: 287 في God of War Sons of Sparta (بما فيها gather وVFMADDSUB) و227 في البرامج المختبرة قبلها. الاستثناءات فروق نادرة في آخر بت في FMA (الدقة المفردة تُقرَّب مرتين، والدقة المضاعفة ضرب ثم جمع) وحالة NaN خاصة لصفر في ما لا نهاية.

يبقى Jaguar أبطأ بكثير من معالج PS5، والبدائل تزيد على ذلك، لذا قد تعمل حتى اللعبة التي تشتغل ببطء.

<a id="plan"></a>
## الخطة

| الخطوة | الحالة |
|---|---|
| Vulkan على معالج رسوميات PS4 يلبّي متطلبات KytyPS5 | تم (`RADV_EXPERIMENTAL=sparse`) |
| KytyPS5 مبني لمعالج PS4 | تم (`KYTY_HOST_ARCH=btver2`) |
| KytyPS5 يبدأ على PS4 ويهيّئ معالج الرسوميات | تم، PS4 Pro |
| صورة نظام EmuFive، تُثبَّت عبر PS4 Multiboot | تم، PS4 Pro |
| تطبيق homebrew لـ PS5 بدون AVX2 يعمل ويرسم | تم: Snes9x PS5 2.11 مُعاد بناؤه لـ btver2، PS4 Pro |
| وحدة التحكم، وتخزين `/data` وUSB، وتحميل لعبة في ذلك التطبيق | تم على نسخة اختبار للكمبيوتر (نفس الرقع)؛ PS4 لاحقًا |
| ترجمة AVX2 وBMI2 وFMA لكود الألعاب | تم (`0004`)، مُتحقَّق منه على كمبيوتر |
| لعبة PS5 تعمل على PS4 | تم: God of War Sons of Sparta، نحو 40 إطارًا في الثانية وأكثر، PS4 Pro |
| Hollow Knight: Silksong تعمل على PS4 | تم منذ 1.0.1 (الرقعتان `0006` و`0007`)، PS4 Pro |
| الشاشة الرئيسية: اختيار لعبة بوحدة التحكم؛ Wi-Fi؛ الإعدادات | تم، مُتحقَّق منه على كمبيوتر |
| ألعاب من قرص USB أو قرص PS4 أو مجلد مشترك على كمبيوتر | تم، مُتحقَّق منه على كمبيوتر؛ PS4 لاحقًا |

<a id="building"></a>

## البناء

يحتاج إلى Docker وgit وPS4 Mesa من PS4 Multiboot (`../PS4-Multiboot/out/ps4-mesa.tar.xz`، يُبنى هناك بالأمر `make mesa`). في أول مرة ينسخ `build-kyty.sh` مستودع KytyPS5 إلى `build/kytyps5`، ثم في كل بناء يعيده إلى الـ commit المثبّت ويطبّق الرقع.

</div>

```bash
scripts/build-kyty.sh      # out/kytyps5-ps4.tar.xz
scripts/build-rootfs.sh    # out/ps5-ps4-rootfs.tar.xz
```

<div dir="rtl">

المتغيران `PS4_MESA` و`KYTY` يوجّهان `build-rootfs.sh` إلى مسارات أخرى.

<a id="installing"></a>

## التثبيت

يُثبَّت EmuFive عبر [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot)، مثل أي نظام Linux آخر.

تحتاج إلى:

- جهاز PS4 مكسور الحماية مع **GoldHEN** (لخادم FTP ومحمّل الـ payload).
- كمبيوتر على نفس الشبكة مع برنامج FTP (مثل FileZilla).
- نحو 28 GB فارغة على PS4 (قرص بحجم 16 GB، مع ترك 10 GB فارغة دائمًا لـ PS4)، أو قرص USB بحجم 8 GB أو أكثر.
- وحدة تحكم DualShock 4 (بكابل USB، أو مقترنة عبر Bluetooth لاحقًا).

الخطوات:

1. من [إصدارات PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot/releases)، نزّل `bzImage` و`initramfs.cpio.gz` و`bootargs.txt` و`linux-2048mb.bin`. (لا حاجة إلى `ps4-mesa.tar.xz`: فـ EmuFive يتضمن PS4 Mesa.)
2. من [إصدارات EmuFive](https://github.com/blue0x1/EmuFive/releases)، نزّل `ps5-ps4-rootfs.tar.xz` (أو ابنِه، راجع [البناء](#building)). احتفظ باسمه: يتعرّف PS4 Multiboot على الأنظمة من خلال `-ps4-rootfs` في الاسم.
3. شغّل خادم FTP في GoldHEN وانسخ الملفات إلى PS4 (المنفذ 2121):

   | الملف | المجلد على PS4 |
   |---|---|
   | `bzImage`، `initramfs.cpio.gz`، `bootargs.txt` | `/data/linux/boot/` |
   | `ps5-ps4-rootfs.tar.xz` | `/user/home/` |
   | `linux-2048mb.bin` | `/data/payloads/` |

4. شغّل `linux-2048mb.bin` من قائمة الـ payload في GoldHEN.

   > **تحلَّ بالصبر:** بعد بدء الـ payload قد يعرض التلفاز **"No signal" أو شاشة سوداء لمدة 1 إلى 2 دقيقة** أثناء بدء Linux. هذا طبيعي.

   > **شاشة سوداء بعد قائمة PS4 Multiboot؟** بعض أجهزة التلفاز تفضّل وضعًا لا يستطيع PS4 إرساله. أضف `emufive.mode=1920x1080@60` إلى السطر في `/data/linux/boot/bootargs.txt` (واترك `video=HDMI-A-1:1920x1080@60D` أيضًا) ثم شغّل الـ payload مرة أخرى.

5. في قائمة PS4 Multiboot، اختر **EmuFive**، ثم **Install to PS4** أو **Install to USB drive**. يستغرق ذلك بضع دقائق.
6. ضع ألعابك في أحد الأماكن أدناه. اللعبة هي مجلد فيه `eboot.bin` (و`sce_sys`)، أو نسخة ZArchive (`.zar`). لا يمكن تثبيت ملفات الحزم (`.pkg`، fpkg) أو تشغيلها: استخرج اللعبة أولاً.

بعد ذلك، شغّل الحمولة (payload) لبدء EmuFive (إذا كانت هناك أنظمة أخرى مثبتة تظهر قائمة PS4 Multiboot أولًا). لإعادة التثبيت، احذف `/user/home/ps5-ps4.img` عبر FTP ثم شغّل الحمولة. التحديثات: الإعدادات، النظام، تحديث البرنامج.

### الاستخدام

- **الشاشة الرئيسية:** ألعابك على شكل مربعات. اختر لعبة واضغط تشغيل. زر OPTIONS على لعبة: مفضلة، إخفاء، إعداداتها، الجوائز ومدة اللعب ومعلومات اللعبة.
- **زر PS أثناء اللعب:** قائمة الإيقاف المؤقت (متابعة، الرئيسية، إغلاق اللعبة، الصوت، الطاقة).
- **لقطات الشاشة:** PS + المربع، أو Share. اعرضها في الوسائط؛ المثلث يعرض رمز QR لفتح اللقطة على هاتفك.
- **مقاطع الفيديو:** PS + المثلث يبدأ التسجيل، وPS + المثلث مرة أخرى يوقفه (حتى 60 دقيقة). تُشغَّل المقاطع في الوسائط وتُشارك إلى هاتفك مثل لقطات الشاشة. مكان الحفظ (الـ PS4 أو وحدة USB) والجودة (720p أو 1080p) في الإعدادات > التخزين.
- **الإنترنت:** مربع لمتصفح ويب يُستخدم بذراع التحكم.
- **الإعدادات:** Wi-Fi، المظهر، أذرع التحكم، الملفات الشخصية (حتى 8)، لغة القائمة، التاريخ والوقت، النسخ الاحتياطي.
- **أذرع التحكم:** DualShock 4 بكابل، أو عبر Bluetooth (اضغط مطولًا على SHARE + PS حتى يومض شريط الضوء مرتين).
- **تسجيل الدخول:** `ps5` / `ps5` عبر SSH أو على tty2. سجل المحاكي هو `~/kytyps5.log`.

### أين يمكن أن توجد الألعاب

- **وحدة USB:** مجلد `PS5` في أعلى الوحدة (exFAT هو الأفضل، وNTFS يعمل أيضًا).
- **قرص PS4:** المسار `/user/home/PS5`، يُنسخ إليه عبر FTP في GoldHEN (غير متاح إذا كان EmuFive نفسه مثبتًا على وحدة USB).
- **حاسوب:** مجلد مشترك على Windows أو Linux. في الإعدادات فعّل **استخدام ألعاب الحاسوب**، وأدخل العنوان والمجلد المشترك وبيانات الدخول، ثم اتصال.

## الألعاب

لا يحتوي هذا المشروع على أي برامج نظام PS5 ولا على أي ألعاب. استخدم فقط الألعاب التي تملكها ونسختها بنفسك.

<details>
<summary><b>الألعاب التي تعمل</b></summary>

| اللعبة | الجهاز | EmuFive | النتيجة |
|---|---|---|---|
| God of War Sons of Sparta | PS4 Pro | 1.0.0 | قابلة للعب، حوالي 40 إطاراً في الثانية وأكثر |
| Hollow Knight: Silksong | PS4 Pro | 1.0.1 | قابلة للعب، 60 إطاراً في الثانية |
| Plants vs. Zombies: Replanted | PS4 Pro | 1.0.4 | قابلة للعب، 60 إطاراً ثابتة |
| Vampire Survivors | PS4 Slim | 1.0.4 | قابلة للعب، 60 إطاراً مستقرة |
| My Little Puppy | PS4 Slim | 1.0.6 | تعمل، 3–15 إطاراً (20–25 في المناطق الفارغة) |
| DREDGE | PS4 Pro | 1.0.8 | قابلة للعب |
| Animal Well | PS4 Pro | 1.0.9 | قابلة للعب، 42–44 إطاراً في الثانية |
| Teardown | PS4 Pro | 1.0.9 | تعمل، 9–12 إطاراً داخل اللعبة (حوالي 20 في المشاهد الخفيفة) مع الذاكرة المشتركة مع المعالج الرسومي |
| Invincible VS | PS4 Pro | 1.0.9 | تبدأ، 4–5 إطارات؛ غير قابلة للعب بعد |
| Blue Prince | PS4 Pro | 1.0.10 | قابلة للعب، حوالي 25 إطارًا |
| Wytchwood | PS4 Pro | 1.0.10 | قابلة للعب، 30 إطاراً مستقرة |
| Hades II | PS4 Slim | 1.0.10 | تعمل، 20–25 إطاراً في اللعب (10–15 في القوائم)، مع تقطّع |
| Minecraft | PS4 Slim | 1.0.10 | قابلة للعب، 30–35 إطاراً في اللعب (56–60 في القوائم) مع إيقاف ذاكرة GPU المشتركة |
| Crusader Kings III | PS4 Pro | 1.0.10 | قابلة للعب |
| Iron Lung | PS4 Pro | 1.0.10 | قابلة للعب، 60 إطاراً |
| The King is Watching | PS4 Pro | 1.0.10 | قابلة للعب، 55–60 إطاراً |
| Wizard with a Gun | PS4 Pro | 1.0.10 | تعمل، 20–30 إطاراً مع تقطّع؛ يبقى توهّج البوابة على الشاشة |
| Mouse: P.I. For Hire | PS4 Pro | 1.0.10 | تعمل، 4–22 إطاراً مع تقطّع وطقطقة في الصوت (بايلود 1024 ميغابايت) |
| Another Crab's Treasure | PS4 Pro | 1.0.10 | تعمل، 4–10 إطارات؛ تبقى تشوّهات رسومية على الشاشة |
| Anger Foot | PS4 Pro | 1.0.10 | تبدأ، 4 إطارات (بايلود 1024 ميغابايت)؛ غير قابلة للعب بعد |

</details>

<details>
<summary><b>الألعاب التي لا تعمل بعد (قد يصلحها إصدار أحدث)</b></summary>

| اللعبة | الجهاز | EmuFive | النتيجة |
|---|---|---|---|
| DRAGON BALL: Sparking! ZERO | PS4 Pro | 1.0.10 | تعرض شاشة اتفاقية الترخيص وشاشات الاتصال بالإنترنت، ثم يتوقف معالج الرسوميات |
| Hello Neighbor | PS4 Pro | 1.0.4 | تتوقف عند البدء (mesh shaders) |
| Need for Speed Unbound | PS4 Slim | 1.0.6 | تنهار عند البدء (نسخ عمق غير مدعوم) |
| V Rising | PS4 Pro | 1.0.8 | تنهار عند البدء |
| Serious Sam 4 | PS4 Slim | 1.0.10 | تُغلق عند البدء (الخدمات عبر الإنترنت) |
| Serious Sam: Siberian Mayhem | PS4 Slim | 1.0.9 | تُغلق عند البدء (الخدمات عبر الإنترنت) |
| The Long Dark | PS4 Slim | 1.0.10 | تعلق في فيديو البداية، ولا تظهر القائمة |

</details>

جربت لعبة؟ افتح [مشكلة](https://github.com/blue0x1/EmuFive/issues) واذكر اللعبة ومعرّفها وطراز جهازك وإصدار EmuFive وكيف عملت. الألعاب التي لا تعمل مفيدة أيضاً (مثلاً «لا تبدأ» أو «تنهار في القائمة»): تُضاف إلى الجدول حتى لا يجرب الآخرون اللعبة نفسها.

<a id="changelog"></a>
## سجل التغييرات

### 1.0.12 (2026-11-19)

- إصلاح: شاشة سوداء عند استخدام `emufive.mode=` في `bootargs.txt`. كان EmuFive يضبط وضع التلفاز، ثم تبدّل الشاشة الرئيسية إلى وضع 1920x1080 آخر (59.96 هرتز) لا تقبله بعض أجهزة التلفاز. أصبحت الشاشة الرئيسية الآن تحتفظ بالوضع.

للتحديث من 1.0.3 أو أقدم، ابدأ التحديث يدويًا مرة واحدة، لأن تحديث البرنامج القديم لا يستطيع ذلك: فعّل SSH في الإعدادات، واتصل بـ `ssh ps5@<عنوان PS4>` (كلمة المرور `ps5` إن لم تغيّرها)، ثم شغّل

```bash
sudo systemd-run --unit=emufive-update --collect /opt/ps5-on-ps4/bin/ps5-update install
```

يثبّت كل التحديثات الناقصة (من 1.0.0 أو 1.0.1 يشمل ذلك حزم المتصفح في 1.0.2، نحو 110 MB)، ثم أعد التشغيل من الشاشة الرئيسية. ابتداءً من 1.0.4 يعمل تحديث البرنامج في الإعدادات. التثبيتات الجديدة تستخدم `ps5-ps4-rootfs.tar.xz` من إصدار 1.0.12.

## هيكل المشروع

| المسار | المحتوى |
|---|---|
| `scripts/build-kyty.sh` | يبني KytyPS5 (المصدر الأصلي مع `patches/kytyps5/`) لمعالج PS4 |
| `patches/kytyps5/` | تعديلات هذا المشروع على KytyPS5 |
| `scripts/build-rootfs.sh` | يبني صورة النظام لـ PS4 Multiboot |
| `scripts/make-release.sh` | يصنع حزمة التحديث لإصدار (يثبّتها: الإعدادات، النظام، تحديث البرنامج) |
| `scripts/updates/` | سكربتات يشغّلها التحديث على PS4 بعد نسخ ملفاته (`--post`) |
| `docker/` | بيئات البناء لكليهما |
| `overlay/` | ملفات تُضاف إلى النظام: الجلسة، والشاشة الرئيسية، والإعدادات، وتركيب قرص USB وقرص PS4، واقتران وحدات التحكم |
| `tools/` | محوّل الشعار، وملف ROM لاختبار وحدة التحكم، و`extract-code.py` (كود ملف PS5 SELF/ELF) |
| `tools/jaguar-test/` | يتحقق من بدائل الرقعة `0004` مقابل التعليمات الحقيقية |

## شكر خاص

- [KytyPS5](https://github.com/KytyPS5/KytyPS5)، محاكي PS5 الذي بُني عليه EmuFive (GPL-2.0)
- [Kyty](https://github.com/InoriRus/Kyty) من InoriRus، المحاكي الذي بُني عليه KytyPS5

<a id="credits"></a>
## شكر وتقدير

- [Mesa](https://mesa3d.org)، ورقع معالج رسوميات PS4 من fail0verflow وDionKill وstriker91n
- مطوّرو نواة Linux لـ PS4 ‏([sony-jaguar-devs/ps4-linux](https://github.com/sony-jaguar-devs/ps4-linux))

## ادعم المشروع

إذا كان EmuFive مفيدًا لك، يمكنك دعم المشروع بعملة البيتكوين:

BTC: `bc1q7w5ns9vsguseppllpy609yhwrtq3v56g94mjde`

## الرخصة

حقوق النشر (C) 2026 ‏[Chokri Hammedi (blue0x1)](https://github.com/blue0x1).

GPL-2.0 (راجع `LICENSE`). KytyPS5 وMesa ونواة Linux تخضع لرخصها الخاصة. PlayStation علامة تجارية لـ Sony Interactive Entertainment؛ وهذا المشروع غير تابع لـ Sony.

</div>
