# التوثيق التقنيّ للغة ص · Sad Language Technical Docs

> المرجع التقنيّ الرسميّ للغة البرمجة العربية **ص** (Sad): النحو، الكلمات المحجوزة
> الأربعون، الأنواع المدمجة، العوامل وأسبقيّتها، والميزات المتقدّمة — مكتوبًا كـ
> **mdBook عربيّ (RTL)** يُنشَر آليًّا على GitHub Pages.

[![نشر التوثيق](https://github.com/sadlang/sadlang-docs/actions/workflows/deploy.yml/badge.svg)](https://github.com/sadlang/sadlang-docs/actions/workflows/deploy.yml)

---

## ما هذا المستودع؟

هذا المستودع هو **الوجه المنشور للتوثيق التقنيّ للغة ص الموجَّه للمستخدم**: من يكتب
برامج بلغة ص ويريد مرجعًا دقيقًا للنحو والكلمات والأنواع والعوامل والميزات.

| المستودع | الجمهور | المحتوى |
|----------|---------|---------|
| **`sadlang-docs`** (هذا) | مستخدمو اللغة | مرجع اللغة نفسها: نحو، كلمات، أنواع، عوامل، ميزات |
| [`dev-guide`](https://github.com/sadlang/dev-guide) | مطوّرو المترجم | الأنظمة الداخلية: المعجمي/النحوي/AST/SIR/LLVM/المفسّر |
| [`s-programming-language`](https://github.com/sadlang/s-programming-language) | الجميع | شيفرة المصدر + `language-truth/` (مصدر الحقيقة) + `وثائق/` |

## قناتان: المستقرّ والقادم 📕🚧

التوثيق **مُوسوم بالإصدار** عبر قناتين تُبنيان معًا عند كل نشر، فيكتب المطوّر التوثيق
وقت التطوير دون أن يراه المستخدم قبل الإصدار الرسميّ:

| القناة | المسار | المصدر | الجمهور |
|--------|--------|--------|---------|
| 📕 **المستقرّ** | [`/`](https://sadlang.github.io/sadlang-docs/) | فرع `sadlang` | المستخدم (الافتراضيّ) |
| 🚧 **القادم** | [`/next/`](https://sadlang.github.io/sadlang-docs/next/) | فرع `dev` | المطوّر (ميزات غير منشورة) |

لكلّ قناة تُعاد توليد صفحات المرجع من `language-truth/` في فرعها — فمثلًا تظهر رموز
أمان العدم بصيغتها المنشورة في «المستقرّ» وبصيغتها القادمة في «القادم» تلقائيًّا.
لافتة أعلى كل صفحة تتيح التنقّل بين القناتين. يبنيهما [`deploy.yml`](.github/workflows/deploy.yml).

## مصدر الحقيقة (SoT)

الحقيقة الرسمية للقواعد والكلمات والأنواع تعيش **داخل المستودع الأساسيّ** في
[`language-truth/`](https://github.com/sadlang/s-programming-language/tree/sadlang/language-truth)
(ملفّات YAML مُحكَّمة بمخطّطات JSON). هذا المستودع **يعرض ويشرح** تلك الحقيقة بصيغة
قابلة للقراءة، ولا يخترع قواعد جديدة. عند أيّ تعارض، **`language-truth/` هو الفيصل**.

### صفحات مشتقّة لا تُودَع

صفحات المرجع التابعة **تُولَّد عند كلّ بناء** من `language-truth/`، ولا توجد في git:

| الصفحة (مُولَّدة) | المصدر |
|--------|--------|
| `src/reference/keywords.md` | `language-truth/keywords.yaml` |
| `src/reference/operators.md` | `language-truth/operators.yaml` |
| `src/reference/types.md` | `language-truth/keywords.yaml` + `types.yaml` |
| `src/reference/sadui-properties.md` | `language-truth/ui_props.yaml` |

```bash
python scripts/gen_reference.py --fetch dev        # يجلب SoT بنفسه ويولّد
```

**لماذا لا تُودَع؟** النسخةُ المودَعةُ لمشتقٍّ تنجرف عن أصلها حتمًا — حدث مرّتين
(القضيّتان #1 و#8). وحين لا تُودَع، يصير الانجراف **مستحيلًا بنيويًّا** لا مرصودًا
بعد أسابيع. الثمن أنّ الحارس القديم (`--check`) فقد معناه، وكان معناه ضعيفًا أصلًا:
يقارن مخرج المولّد بمخرج المولّد من مصدرٍ متحرّك — طرفان من أصلٍ واحد. بدلَه
**اختباراتٌ ذهبيّة** على لقطة SoT مجمَّدة تقيس المولّد وحده: [`tests/`](tests/README.md).

- **المولّد:** [`scripts/gen_reference.py`](scripts/gen_reference.py) — و`--fetch` فيه هو
  **مسار الجلب الوحيد** الذي يستعمله المساهم و`ci.yml` و`deploy.yml` معًا.
- **بيان المنشأ:** [`sync/sources.yaml`](sync/sources.yaml) — وصفيّ لا تنفيذيّ.

## البناء محليًّا

```bash
cargo install mdbook mdbook-mermaid            # مرّة واحدة
mdbook-mermaid install .                       # توليد أصول المخطّطات
pip install pyyaml                             # للمولّد
python scripts/gen_reference.py --fetch dev    # ⚠️ لازم: صفحات المرجع غير مودَعة
mdbook serve --open                            # تطوير حيّ على المتصفّح
mdbook build                                   # بناء ثابت في book/
```

الخطوة الرابعة **ليست اختياريّة**، وفخُّها مقيس: `SUMMARY.md` يشير إلى صفحات
`reference/` المُولَّدة، و**mdBook لا يفشل** إن غابت — بل يُنشئ جذاذةً من العنوان وحده
(٣٢ بايتًا) ويبني بنجاح، فتُنشَر صفحات مرجعٍ بيضاء بصمت. لذلك يسبق البناءَ حارسٌ في
السيرين: `python scripts/gen_reference.py --verify`. مرّة واحدة تكفي (تُخبَّأ في `.sot-cache/`).

## البنية

```
sadlang-docs/
├── book.toml              # إعداد mdBook (عربي RTL، سمة navy، mermaid)
├── src/
│   ├── SUMMARY.md         # فهرس الكتاب (شجرة الفصول)
│   ├── introduction.md    # المقدّمة
│   ├── getting-started/   # البدء: التثبيت + أوّل برنامج
│   ├── language/          # دروس اللغة موضوعًا موضوعًا
│   └── reference/         # المرجع الدقيق: الكلمات/العوامل/الأنواع/النحو
├── theme/                 # دعم RTL + تكبير الخط (عربيّ)
├── tests/                 # لقطة SoT مجمَّدة + الذهبيّ + اختبارات المولّد
└── .github/workflows/     # ci.yml (ذهبيّ + بناء القناتين + روابط) + deploy.yml
```

## المساهمة

اقرأ [`CONTRIBUTING.md`](CONTRIBUTING.md). باختصار: عدّل تحت `src/`، شغّل `mdbook build`
محليًّا، افتح PR إلى `main`. الـCI يشغّل الاختبارات الذهبيّة ويبني **القناتين** ويفحص
الروابط؛ الدمج في `main` ينشر تلقائيًّا. والدفع المباشر إلى `main` يمرّ بالفحص نفسه.

## الرخصة

التوثيق متاح للعموم تحت رخصة المنظمة (راجع المستودع الأساسيّ للغة ص).
