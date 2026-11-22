<p align="center">
  <a href="TROUBLESHOOTING.md">EN</a> · <b>AR</b> · <a href="TROUBLESHOOTING.zh-CN.md">ZH</a> · <a href="TROUBLESHOOTING.fr.md">FR</a> · <a href="TROUBLESHOOTING.es.md">ES</a> · <a href="TROUBLESHOOTING.de.md">DE</a> · <a href="TROUBLESHOOTING.it.md">IT</a> · <a href="TROUBLESHOOTING.pt-BR.md">PT</a> · <a href="TROUBLESHOOTING.tr.md">TR</a>
</p>

<div dir="rtl">

# حل المشاكل

المشاكل التي أبلغ عنها الناس في [الـ issues](https://github.com/blue0x1/EmuFive/issues)، مع الحلول التي نجحت معهم. جرّب الخطوات بالترتيب. ما زالت المشكلة؟ افتح issue وأرفق ما في قسم [ماذا ترسل](#what-to-send).

- [افحص الملفات أولاً](#check-the-files-first)
- [شاشة سوداء أو «لا توجد إشارة» بعد الـ payload](#black-screen-or-no-signal-after-the-payload)
- [شاشة سوداء بعد القائمة أو شعار EmuFive](#black-screen-after-the-menu-or-the-emufive-logo)
- [شاشة خضراء أو ألوان خاطئة أو وميض](#green-screen-wrong-colors-or-flickering)
- [يطفأ PS4 أو يبقى الضوء أبيض](#the-ps4-turns-off-or-the-light-stays-white)
- [«No Linux install or archive found»](#no-linux-install-or-archive-found)
- [التثبيت يستغرق وقتاً طويلاً جداً](#installing-takes-very-long)
- [لا يعمل EmuFive بعد تثبيت توقف في المنتصف](#emufive-doesnt-start-after-a-stopped-install)
- [لا يعمل إلا مع توصيل قرص USB](#it-only-works-with-the-usb-drive-plugged-in)
- [الألعاب لا تظهر](#games-dont-show-up)
- [القرص الخارجي غير موجود](#an-external-drive-isnt-found)
- [وحدة التحكم لا تعمل](#the-controller-doesnt-work)
- [اللعبة تُغلق أو تتجمد أو بطيئة](#a-game-closes-freezes-or-runs-slowly)
- [كيف تحفظ السجلات](#how-to-save-the-logs)
- [ماذا ترسل](#what-to-send)

<a id="check-the-files-first"></a>
## افحص الملفات أولاً

معظم بلاغات «لا يحدث شيء» كان سببها واحداً من هذه:

- **نفس الإصدار:** يجب أن تكون `bzImage` و`initramfs.cpio.gz` و`bootargs.txt` و`linux-2048mb.bin` كلها من نفس [إصدار PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot/releases) (والأحدث أفضل). الملفات المختلطة لا تعمل.
- **أسماء المجلدات بأحرف صغيرة:** يرى PS4 أن `LINUX` و`linux` مجلدان مختلفان. يجب أن تكون المسارات بالضبط `/data/linux/boot/bzImage` و`/data/linux/boot/initramfs.cpio.gz` و`/data/linux/boot/bootargs.txt`.
- **اسم الأرشيف بالضبط:** `/user/home/ps5-ps4-rootfs.tar.xz`. أحياناً يحفظه المتصفح باسم `ps5-ps4-rootfs (1).tar.xz`، وعندها لا تجده القائمة.
- **النقل الثنائي:** في FileZilla اختر نقل ← نوع النقل ← **ثنائي** قبل الرفع. الملف المرفوع بوضع النص يتلف. تأكد أن حجم كل ملف على PS4 مثل حجمه في الإصدار.
- **الـ payload الخاص بنا:** استخدم `linux-2048mb.bin` من PS4 Multiboot (على إصدار النظام 14.02: `linux-2048mb-14.02.bin`). يعمل على إصدارات النظام من 5.05 إلى 14.02. ملفات payload أخرى لـ Linux غير مدعومة.

<a id="black-screen-or-no-signal-after-the-payload"></a>
## شاشة سوداء أو «لا توجد إشارة» بعد الـ payload

بعد تشغيل الـ payload يعرض التلفاز «لا توجد إشارة» أو شاشة سوداء لمدة **دقيقة إلى دقيقتين** بينما يبدأ Linux. هذا طبيعي. وانطفاء الشاشة ووحدة التحكم مباشرة بعد الـ payload طبيعي أيضاً: نظام PS4 يُغلق ويتولى Linux.

**لا تضغط زر PS والشاشة سوداء**: فهو يطفئ PS4. إذا كان EmuFive وحده على PS4، يبدأ المثبّت تلقائياً بعد 60 ثانية، فربما يكون يثبّت الآن.

إذا لم يظهر شيء بعد 3 دقائق:

1. وصّل PS4 **مباشرة** بالتلفاز، بدون موزّع HDMI أو جهاز استقبال صوتي أو بطاقة التقاط.
2. على PS4 أوقف **الإعدادات ← النظام ← تمكين HDCP**، ثم شغّل الـ payload مرة أخرى.
3. جرّب كابل HDMI آخر ومنفذ HDMI آخر.
4. جرّب مرة واحدة تلفازاً أو شاشة أخرى. بعض أجهزة التلفاز لا تقبل إشارة Linux من PS4، والشاشة الأخرى تبيّن إن كانت المشكلة في التلفاز.
5. ما زال لا شيء؟ احفظ [سجل PS4BOOT](#the-ps4boot-stick-boot-problems) وافتح issue. أخبرنا إن كان التلفاز يقول **«لا توجد إشارة»** أم أنه يعمل لكن الشاشة سوداء.

<a id="black-screen-after-the-menu-or-the-emufive-logo"></a>
## شاشة سوداء بعد القائمة أو شعار EmuFive

إذا رأيت قائمة PS4 Multiboot أو شعار EmuFive ثم أصبحت الشاشة سوداء، فقد انتقل EmuFive إلى وضع يفضّله تلفازك لكن PS4 لا يستطيع إرساله.

1. حدّث EmuFive (الإعدادات ← النظام ← تحديث البرنامج).
2. افتح عبر FTP الملف `/data/linux/boot/bootargs.txt` وأضف ` emufive.mode=1920x1080@60` في آخر السطر. أبقِ `video=HDMI-A-1:1920x1080@60D` أيضاً. يجب أن يبقى الملف **سطراً واحداً**.
3. شغّل الـ payload مرة أخرى.

لا تستطيع التحديث لأن الشاشة سوداء؟ وصّل تلفازاً أو شاشة أخرى مرة واحدة وحدّث، أو ثبّت EmuFive من جديد بأحدث `ps5-ps4-rootfs.tar.xz`.

<a id="green-screen-wrong-colors-or-flickering"></a>
## شاشة خضراء أو ألوان خاطئة أو وميض

طبقة خضراء، أو الأسود يظهر أخضر والأبيض سماوياً، أو وميض: التلفاز يقرأ إشارة PS4 بصيغة ألوان خاطئة.

1. أضف ` emufive.mode=1920x1080@60` إلى `bootargs.txt` (انظر أعلاه).
2. جرّب كابل HDMI أو منفذاً آخر. في إعدادات التلفاز لذلك المنفذ غيّر خيارات مثل **HDMI UHD Color** أو **Enhanced format** أو **Deep Colour** أو **Input Signal Plus** (من تشغيل إلى إيقاف أو العكس)، وأوقف HDMI-CEC (**Anynet+** و**Bravia Sync**...).
3. جرّب تلفازاً أو شاشة أخرى.

<a id="the-ps4-turns-off-or-the-light-stays-white"></a>
## يطفأ PS4 أو يبقى الضوء أبيض

- **على 14.02** يطفئ التشغيل الأول للـ payload جهاز PS4 أحياناً. شغّله مرة أخرى: المحاولة الثانية تنجح عادةً.
- **يبقى الضوء أبيض** ولا يحدث شيء لمدة 5 دقائق: اضغط مطولاً على زر التشغيل لإطفاء PS4، ثم شغّله وشغّل الـ payload من جديد.
- **الضوء البنفسجي** بعد التثبيت طبيعي.
- **يطفأ PS4 عند الضغط على زر PS** والشاشة سوداء: لا تضغطه، انتظر (انظر أعلاه).

<a id="no-linux-install-or-archive-found"></a>
## «No Linux install or archive found»

لم تجد القائمة EmuFive مثبّتاً ولا `ps5-ps4-rootfs.tar.xz`.

1. افحص اسم الأرشيف ومكانه: بالضبط `/user/home/ps5-ps4-rootfs.tar.xz`.
2. على **PS4 الفات** (CUH-10xx أو 11xx أو 12xx)، لم يكن PS4 Multiboot من v1.5.0-beta.3 إلى beta.7 يجد القرص الداخلي. استخدم `bzImage` و`initramfs.cpio.gz` من [v1.5.0-beta.8](https://github.com/blue0x1/ps4-multiboot/releases/tag/v1.5.0-beta.8) أو أحدث.

<a id="installing-takes-very-long"></a>
## التثبيت يستغرق وقتاً طويلاً جداً

- **إنشاء القرص** هو أول 25% من الشريط، وهو الجزء البطيء: كل ما يُكتب على قرص PS4 يمر عبر تشفير PS4. أجهزة Baikal أبطأ في ذلك. القرص الكبير يأخذ وقتاً أطول، فاختر قرصاً أصغر في المحاولة الأولى (16 GB كافية). الجزء بعد 25% أسرع.
- **لا تطفئ PS4** ما دامت النسبة تتقدم. إذا لم تتحرك لمدة 30 دقيقة، افتح issue واذكر أين توقفت.
- **شاشة سوداء في النهاية:** إذا كان التلفاز ما زال يستقبل إشارة، فالأرجح أن التثبيت انتهى وأن EmuFive يبدأ. إذا كان زر تشغيل PS4 يطفئه بشكل عادي، فـ EmuFive يعمل والصورة فقط سوداء: انظر [شاشة سوداء بعد القائمة](#black-screen-after-the-menu-or-the-emufive-logo).

<a id="emufive-doesnt-start-after-a-stopped-install"></a>
## لا يعمل EmuFive بعد تثبيت توقف في المنتصف

إذا أُطفئ PS4 أثناء التثبيت، قد يبقى قرص نصف مكتمل. تقول شاشة الخطأ **«The EmuFive disk is incomplete»**، أو يقول السجل `is a hole`.

1. احذف `/user/home/ps5-ps4.img` عبر FTP. أبقِ `ps5-ps4-rootfs.tar.xz`.
2. شغّل الـ payload وثبّت من جديد. اتركه حتى ينتهي بدون إطفاء PS4.

<a id="it-only-works-with-the-usb-drive-plugged-in"></a>
## لا يعمل إلا مع توصيل قرص USB

اخترت **Install to USB drive**، لذلك EmuFive موجود على ذلك القرص ويحتاجه. لتثبيته على PS4 بدلاً من ذلك: افصل القرص، شغّل الـ payload، واختر **Install to PS4**.

<a id="games-dont-show-up"></a>
## الألعاب لا تظهر

اللعبة **مجلد** بداخله `eboot.bin` و`sce_sys`، أو ملف `.zar` واحد. ملفات `.pkg` وfpkg لا تعمل: استخرج اللعبة أولاً. استخدم نسخاً من ألعاب تملكها.

على قرص USB يجب أن يكون الترتيب هكذا:

</div>

```
USB drive (exFAT, one partition; NTFS works too)
└── PS5/                      <- exactly "PS5", in capitals, at the top of the drive
    ├── PPSA01234/            <- one folder per game (any name)
    │   ├── eboot.bin         <- directly in the game folder
    │   ├── sce_sys/
    │   │   └── param.json    <- gives the game's name and picture
    │   └── ...
    └── MyGame.zar            <- a .zar dump, as a single file
```

<div dir="rtl">

أخطاء شائعة:

- `ps5/` أو `Ps5/`: يجب أن يكون الاسم `PS5` بالضبط.
- `Games/PS5/...`: يجب أن يكون مجلد `PS5` في أعلى القرص.
- `PS5/PPSA01234/PPSA01234/eboot.bin`: مستوى مجلد زائد (يحدث كثيراً بعد فك الضغط). انقل المجلد الداخلي إلى الأعلى.
- `PS5/eboot.bin`: ملفات اللعبة متناثرة في `PS5` بدون مجلد خاص بها.
- لعبتان في مجلد واحد: تظهر واحدة فقط. اسم اللعبة على المربع يأتي من `sce_sys/param.json` وليس من اسم المجلد، لذلك أعطِ كل لعبة مجلدها الخاص.

على قرص PS4 المجلد هو `/user/home/PS5`، ويعمل فقط إذا كان EmuFive مثبّتاً على PS4 (وليس على قرص USB). انسخ الألعاب عبر FTP الخاص بـ GoldHEN من نظام PS4، ثم شغّل EmuFive: فهو يقرأ هذا المجلد عند بدء التشغيل.

أبقِ قرص الألعاب فقط موصولاً. افصل فلاشة السجلات `PS4BOOT` أثناء اللعب.

<a id="an-external-drive-isnt-found"></a>
## القرص الخارجي غير موجود

- أقراص SSD والأقراص الصلبة الخارجية تعمل منذ EmuFive 1.0.5. حدّث أولاً.
- القرص الذي كان عليه Linux من قبل قد لا يظهر حتى بعد تهيئة عادية. احذف كل أقسامه (في Windows: إدارة الأقراص)، ثم أنشئ قسماً واحداً بصيغة **exFAT**.
- إذا كان EmuFive مثبّتاً على قرص USB، توضع الألعاب على قرص USB ثانٍ (منذ EmuFive 1.0.4).

<a id="the-controller-doesnt-work"></a>
## وحدة التحكم لا تعمل

- **في قائمة PS4 Multiboot وعلى شاشات التثبيت والخطأ** تعمل وحدة التحكم **بكابل USB فقط**. البلوتوث يبدأ لاحقاً داخل EmuFive.
- **عبر البلوتوث** يجب إقرانها مرة واحدة مع EmuFive، لأن إقران نظام PS4 لا ينتقل. افصل الكابل، اضغط مطولاً على **SHARE + PS** حتى يومض شريط الضوء مرتين، وانتظر بضع ثوانٍ. إذا لم تتصل، استخدم الإعدادات ← وحدات التحكم ← إقران وحدة تحكم جديدة.
- استخدم كابلاً ينقل البيانات. بعض الكابلات للشحن فقط.
- على أجهزة **Baikal** (كثير من أجهزة Pro بموديل CUH-71xx/72xx وأجهزة Slim الأحدث؛ انظر الإعدادات ← النظام ← معلومات النظام)، يحتاج USB إلى PS4 Multiboot v1.5.0-beta.7 أو أحدث.

<a id="a-game-closes-freezes-or-runs-slowly"></a>
## اللعبة تُغلق أو تتجمد أو بطيئة

- **«توقفت اللعبة (رمز الخطأ 65)» مع `ErrorDeviceLost`:** المعالج الرسومي في PS4 علق أثناء رسم اللعبة. يحدث هذا كثيراً مع ألعاب Unreal Engine الثقيلة، وهي غير قابلة للعب بعد. أرسل [سجل اللعبة](#game-logs) إذا أردت أن ننظر فيه.
- **نفدت الذاكرة:** لعبة PS5 قد تستخدم حتى نحو 12.5 GB، بينما لدى Linux على PS4 نحو 6 GB. يغلق EmuFive اللعبة قبل أن يتجمد PS4. أوقف الإعدادات ← الألعاب ← **ذاكرة الألعاب المشتركة مع المعالج الرسومي** وجرّب مرة أخرى. ينشئ EmuFive ملف تبديل بحجم 4 GB فقط إذا كان في قرصه 8 GB فارغة، فوفّر مساحة إذا كان القرص ممتلئاً.
- **تجمّد أو انهيار في لعبة:** جرّب مرة واحدة مع إيقاف **ذاكرة الألعاب المشتركة مع المعالج الرسومي**. فهي تسرّع ألعاب 3D الكبيرة، لكنها لا تناسب كل لعبة (Minecraft يتجمد معها).
- **تقطّع في المرة الأولى:** عند عرض مشهد لأول مرة تُترجَم الـ shaders. في المرة الثانية يكون أسلس.
- **تمزق الصورة:** الإعدادات ← الألعاب ← توقيت الإطارات ← **سلس (بدون تمزق)**.
- **إطارات قليلة (FPS):** المعالج والمعالج الرسومي في PS4 أبطأ بكثير من PS5. الألعاب ثنائية الأبعاد والخفيفة تعمل جيداً؛ أما ألعاب 3D الثقيلة فكثيراً ما تُحمَّل وتعرض قوائمها، ثم تعمل ببطء شديد أو تبقى سوداء أثناء اللعب. جهاز PS4 Pro أسرع من Slim بنحو الضعف. راجع جدول [الألعاب](README.ar.md#games) قبل تجربة لعبة كبيرة.

<a id="how-to-save-the-logs"></a>
## كيف تحفظ السجلات

<a id="the-ps4boot-stick-boot-problems"></a>
### فلاشة PS4BOOT (مشاكل الإقلاع)

1. هيّئ فلاشة USB بصيغة **FAT32** وباسم **`PS4BOOT`** (بأحرف كبيرة). لا يستطيع Windows تهيئة فلاشة أكبر من 32 GB بصيغة FAT32: استخدم فلاشة أصغر، أو [Rufus](https://rufus.ie) (Boot selection: *Non bootable*، File system: *Large FAT32*، Volume label: `PS4BOOT`). صيغتا NTFS وexFAT لا تعملان لهذا.
2. وصّلها بـ PS4 **قبل** تشغيل الـ payload، واتركها موصولة.
3. شغّل الـ payload وانتظر **5 دقائق**، حتى لو بقيت الشاشة سوداء. إذا ظهرت شاشة خطأ، فهي تحفظ التفاصيل على الفلاشة بنفسها.
4. اضغط مطولاً على زر التشغيل لإطفاء PS4. ضع الفلاشة في حاسوب وأرفق ملفات `.log` في الـ issue (`ps4-linux-boot.log` أو `ps4-linux-late.log` أو `ps4-linux-error.log` أو `ps4-linux-rescue.log`).

إذا بقيت الفلاشة فارغة، أخبرنا بذلك: فهذا يعني أن Linux لم يصل إلى هذه المرحلة، وهذا مفيد أيضاً.

<a id="game-logs"></a>
### سجلات الألعاب

مباشرة بعد توقف اللعبة، اذهب إلى الإعدادات ← النظام ← **نسخ السجلات إلى USB**، ثم أرفق الملفات من مجلد `PS5-logs` على قرص USB (أهمها `kytyps5.log`). أرفق الملف الحقيقي وليس ملخصاً.

<a id="what-to-send"></a>
## ماذا ترسل

- موديل PS4 (CUH-xxxx، على الملصق في الخلف)، وإصدار النظام، والـ southbridge (الإعدادات ← النظام ← معلومات النظام، مثل Belize أو Baikal أو Aeolia).
- إصدار PS4 Multiboot وملف الـ payload الذي تشغّله.
- سطر `bootargs.txt` الخاص بك.
- إصدار EmuFive (الإعدادات ← النظام)، وهل هو مثبّت على PS4 أم على قرص USB.
- موديل التلفاز أو الشاشة، وماذا تعرض: «لا توجد إشارة»، أم تعمل لكنها سوداء.
- ضوء PS4: أبيض أو أزرق أو بنفسجي أو مطفأ.
- السجلات المذكورة أعلاه.

</div>
