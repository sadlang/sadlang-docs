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

## مصدر الحقيقة (SoT)

الحقيقة الرسمية للقواعد والكلمات والأنواع تعيش **داخل المستودع الأساسيّ** في
[`language-truth/`](https://github.com/sadlang/s-programming-language/tree/sadlang/language-truth)
(ملفّات YAML مُحكَّمة بمخطّطات JSON). هذا المستودع **يعرض ويشرح** تلك الحقيقة بصيغة
قابلة للقراءة، ولا يخترع قواعد جديدة. عند أيّ تعارض، **`language-truth/` هو الفيصل**.

### مزامنة آليّة (لا تحرّر الصفحات المُولَّدة يدويًّا)

صفحات المرجع التابعة تُولَّد آليًّا من `language-truth/` لمنع التباعد:

| الصفحة | المصدر |
|--------|--------|
| `src/reference/keywords.md` | `language-truth/keywords.yaml` |
| `src/reference/operators.md` | `language-truth/operators.yaml` |
| `src/reference/types.md` | `language-truth/keywords.yaml` + `types.yaml` |

- **المولّد:** [`scripts/gen_reference.py`](scripts/gen_reference.py) — يقرأ SoT ويُنتج الصفحات.
- **سير المزامنة:** [`.github/workflows/sync.yml`](.github/workflows/sync.yml) يُعيد التوليد
  أسبوعيًّا/عند إصدار لغة/يدويًّا، وإن رصد انجرافًا يرفع الصفحات أثرًا ويفتح قضيّة
  بالتعليمات (نمط `dev-guide`). البيان في [`sync/sources.yaml`](sync/sources.yaml).
- إعادة التوليد محليًّا: `python scripts/gen_reference.py --source-dir <مسار-مستودع-اللغة>`.

## البناء محليًّا

```bash
cargo install mdbook mdbook-mermaid   # مرّة واحدة
mdbook-mermaid install .              # توليد أصول المخطّطات
mdbook serve --open                   # تطوير حيّ على المتصفّح
mdbook build                          # بناء ثابت في book/
```

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
└── .github/workflows/     # ci.yml (فحص) + deploy.yml (نشر Pages)
```

## المساهمة

اقرأ [`CONTRIBUTING.md`](CONTRIBUTING.md). باختصار: عدّل تحت `src/`، شغّل `mdbook build`
محليًّا، افتح PR إلى `main`. الـCI يفحص البناء والروابط؛ الدمج في `main` ينشر تلقائيًّا.

## الرخصة

التوثيق متاح للعموم تحت رخصة المنظمة (راجع المستودع الأساسيّ للغة ص).
