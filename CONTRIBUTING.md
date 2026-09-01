# المساهمة في التوثيق التقنيّ للغة ص

شكرًا لاهتمامك! هذا المستودع توثيق فقط (mdBook)، فالمساهمة فيه سهلة ومباشرة.

## القاعدة الذهبيّة: لا تخترع قاعدة

هذا المستودع **يشرح** الحقيقة، ولا **يُنشئها**. مصدر الحقيقة الرسميّ هو
[`language-truth/`](https://github.com/sadlang/s-programming-language/tree/sadlang/language-truth)
في المستودع الأساسيّ. قبل توثيق أيّ سلوك:

1. تأكّد منه في `language-truth/` (الكلمات/الأنواع/العوامل/القواعد) أو في شيفرة المصدر.
2. إن خالف التوثيقُ المصدرَ، **المصدر هو الصواب** — أصلِح التوثيق وأبلِغ عن الخلل.
3. لا تنسخ جداول ضخمة يدويًّا إن أمكن الإحالة إلى SoT؛ كرّر فقط ما يخدم القارئ.

## ⚠️ صفحات مُولَّدة — غير موجودة في git

`src/reference/{keywords,operators,types,sadui-properties}.md` **مشتقّة بالكامل** من
`language-truth/` ولا تُودَع. تُولَّد عندك بأمرٍ واحد:

```bash
pip install pyyaml
python scripts/gen_reference.py --fetch dev    # أو --fetch sadlang للقناة المستقرّة
```

بدونها يفشل `mdbook build` لأنّ `SUMMARY.md` يشير إليها. لتعديل محتواها:

- الخطأ في **البيانات** (كلمة/نوع/عامل): أصلِح `language-truth/` في المستودع الأساسيّ.
- الخطأ في **شكل العرض**: عدّل [`scripts/gen_reference.py`](scripts/gen_reference.py)،
  ثمّ **حدّث الذهبيّ عمدًا** وراجع خلافه في الـPR:
  ```bash
  python -m unittest discover -s tests -v      # سيحمرّ — هذا مقصود
  python scripts/gen_reference.py     --source-dir tests/fixtures/sot-dev-1138f5e1 --source-ref dev     --out-dir tests/golden/dev
  ```
  التفصيل في [`tests/README.md`](tests/README.md).

## توثيق ميزةٍ لم تُنشر بعد

النثر مشتركٌ بين القناتين (فرعٌ واحد يُبنى مرّتين). فإن وثّقتَ ميزةً ما زالت على
`dev`، لُفّها بكتلةٍ تُحذف عند بناء المستقرّ:

```markdown
<!-- قادم:بداية -->
هذه الفقرة لا تظهر إلّا في /next/.
<!-- قادم:نهاية -->
```

وإلّا أحمرّت بوّابة القناة وسمّت لك السطر والمعرِّف:

```bash
python scripts/channel_gate.py --channel sadlang --guard
```

## سير العمل

```bash
git clone https://github.com/sadlang/sadlang-docs
cd sadlang-docs
cargo install mdbook mdbook-mermaid     # مرّة واحدة
mdbook-mermaid install .
pip install pyyaml
python scripts/gen_reference.py --fetch dev   # لازم: صفحات المرجع غير مودَعة
mdbook serve --open                     # حرّر تحت src/ وشاهد فوريًّا
```

ثم:

1. أنشئ فرعًا واصفًا (مثل `docs/grammar-match`).
2. حرّر أو أضِف صفحات تحت `src/`، وحدّث `src/SUMMARY.md` لأيّ صفحة جديدة.
3. شغّل `mdbook build` للتأكّد من عدم وجود أخطاء أو روابط مكسورة.
4. افتح Pull Request إلى `main`.

## معايير الكتابة

- **العربية أولًا**، مع المقابل الإنجليزيّ للمصطلحات التقنية عند أوّل ورود.
- كلّ صفحة تبدأ بعنوان `#` واحد وفقرة تُعرِّف موضوعها.
- أمثلة الشيفرة بلغة ص داخل كتل ```` ```sad ````، قصيرة وقابلة للتشغيل.
- استعمل المخطّطات (mermaid) عند شرح تدفّق أو علاقات.
- الروابط الداخليّة نسبيّة (مثل `../reference/keywords.md`) ليفحصها الـCI.

## الـCI

- **ci.yml**: على كل PR **وعلى الدفع إلى `main`** — ثلاث بوّابات حاجبة:
  1. اختبارات المولّد الذهبيّة (`python -m unittest discover -s tests`).
  2. توليد المرجع + بناء mdBook على **القناتين** (`sadlang` و`dev`).
  3. بوّابة القناة: لا معرِّفَ غائبًا عن SoT المستقرّ في نثر القناة المستقرّة.
  4. فحص الروابط بـ lychee.
- **deploy.yml**: على الدمج في `main` — ينشر القناتين إلى GitHub Pages تلقائيًّا.
