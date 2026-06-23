# ربط مستودع اللغة بالتوثيق (إطلاق آليّ)

كيف يتحدّث التوثيق آليًّا لحظة تقدّم مصدر الحقيقة، بدل انتظار الجدولة الأسبوعيّة.

## المعماريّة

```
مستودع اللغة (s-programming-language)            مستودع التوثيق (sadlang-docs)
  دفع إلى sadlang / dev، أو نشر إصدار
        │  notify-sadlang-docs.yml
        │  (repository_dispatch + PAT)
        ▼
   POST /repos/sadlang/sadlang-docs/dispatches  ──►  deploy.yml  → يعيد بناء القناتين
        event_type = language-release|language-update    sync.yml   → يزامن لقطة المرجع
```

- **language-release** (دفع إلى `sadlang` أو نشر إصدار): تتغيّر القناة **المستقرّة**.
- **language-update** (دفع إلى `dev`): تتغيّر القناة **القادمة** (`/next/`).

الجانب المُستقبِل **جاهز ومُختبَر** في هذا المستودع: يستمع
[`deploy.yml`](../.github/workflows/deploy.yml) و[`sync.yml`](../.github/workflows/sync.yml)
لكلا الحدثين عبر `repository_dispatch`.

## الحالة

1. ✅ **سير العمل مُركَّب** في مستودع اللغة عبر
   [PR sadlang/s-programming-language#85](https://github.com/sadlang/s-programming-language/pull/85)
   (مسار الحوكمة المعتاد: PR إلى `dev`). الملف هنا
   [`notify-sadlang-docs.yml`](notify-sadlang-docs.yml) نسخةٌ مطابقة للمرجع.
2. ⏳ **يتبقّى (خطوة يدويّة):** أضِف السرّ `DOCS_DISPATCH_TOKEN` في إعدادات مستودع اللغة
   (Settings → Secrets and variables → Actions):
   - PAT كلاسيكيّ بصلاحية `repo`، أو دقيق بـ **Contents = Read and write** على `sadlang-docs`.
   - السبب: `GITHUB_TOKEN` الافتراضيّ لا يَعبُر إلى مستودع آخر.
   - بدون السرّ يُتخطّى الإطلاق بأمان (تبقى المزامنة الأسبوعيّة عاملة) — فالدمج لا يكسر شيئًا.

## الاختبار اليدويّ (بلا انتظار حدث)

من أيّ بيئة بها صلاحية الكتابة على sadlang-docs:

```bash
gh api -X POST repos/sadlang/sadlang-docs/dispatches -f event_type=language-update
```

ثم راقب تشغيلات `repository_dispatch` في تبويب Actions — يُفترض أن ينطلق سيرا
النشر والمزامنة معًا (هكذا تحقّقنا من الجانب المُستقبِل).
