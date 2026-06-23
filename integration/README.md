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

## ما يتبقّى (في مستودع اللغة)

1. انسخ [`notify-sadlang-docs.yml`](notify-sadlang-docs.yml) إلى
   `s-programming-language/.github/workflows/` — **عبر مسار الحوكمة المعتاد (RFC/PR إلى dev)**.
2. أضِف السرّ `DOCS_DISPATCH_TOKEN` في إعدادات مستودع اللغة
   (Settings → Secrets and variables → Actions):
   - PAT كلاسيكيّ بصلاحية `repo`، أو دقيق بـ **Contents = Read and write** على `sadlang-docs`.
   - السبب: `GITHUB_TOKEN` الافتراضيّ لا يَعبُر إلى مستودع آخر.

## الاختبار اليدويّ (بلا انتظار حدث)

من أيّ بيئة بها صلاحية الكتابة على sadlang-docs:

```bash
gh api -X POST repos/sadlang/sadlang-docs/dispatches -f event_type=language-update
```

ثم راقب تشغيلات `repository_dispatch` في تبويب Actions — يُفترض أن ينطلق سيرا
النشر والمزامنة معًا (هكذا تحقّقنا من الجانب المُستقبِل).
