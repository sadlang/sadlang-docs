#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# (AR) مولّد صفحات المرجع التابعة من مصدر الحقيقة (language-truth/).
#      يقرأ keywords.yaml / operators.yaml / types.yaml في المستودع الأساسيّ
#      للغة ص، ويُنتج src/reference/{keywords,operators,types}.md آليًّا.
#      الهدف: منع تباعد التوثيق عن SoT — تُعاد كتابة هذه الصفحات ولا تُحرَّر يدويًّا.
#      يدعم القنوات: يُمرَّر --source-ref (sadlang للمستقرّ، dev للقادم) فتُضبَط
#      روابط المصدر، وتُشتقّ رموز أمان العدم من العوامل الفعليّة للفرع.
# (EN) Generates the derived reference pages from the Single Source of Truth.
#      Channel-aware via --source-ref (sadlang=stable, dev=next).
# ----------------------------------------------------------------------------
# الاستعمال / Usage:
#   python scripts/gen_reference.py --fetch dev            # يجلب SoT بنفسه
#   python scripts/gen_reference.py --source-dir <repo-root> [--source-ref sadlang]
#         [--out-dir src/reference] [--check]
#   --fetch <ref>: يستنسخ language-truth/ من الفرع المطلوب استنساخًا ضحلًا متفرّقًا
#         إلى خبيئة محلّيّة (.sot-cache/) ثمّ يولّد منها — مسارُ جلبٍ **واحد**
#         يستعمله المساهم وسير الفحص وسير النشر معًا، فلا تنجرف نسخةٌ رابعة.
#   --check: لا يكتب؛ يفشل (خروج 1) إن اختلف المُولَّد عن الموجود.
# ============================================================================
import argparse
import subprocess
import sys
from pathlib import Path

# (AR) ضمان مخرجات UTF-8 على كل البيئات (كونسول ويندوز قد يكون cp غير لاتينيّ).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

try:
    import yaml
except ImportError:
    sys.exit("خطأ: pyyaml غير مثبّت. ثبّته بـ: pip install pyyaml")

REPO = "sadlang/s-programming-language"
CLONE_URL = f"https://github.com/{REPO}.git"
CACHE_ROOT = Path(".sot-cache")


def _git(*argv: str, cwd: Path = None) -> str:
    """تشغيل git وإرجاع مخرجه؛ يرفع CalledProcessError عند الفشل."""
    res = subprocess.run(
        ["git", *argv], cwd=str(cwd) if cwd else None,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if res.returncode != 0:
        raise subprocess.CalledProcessError(
            res.returncode, ["git", *argv], output=res.stdout, stderr=res.stderr
        )
    return res.stdout.strip()


def fetch_sot(ref: str, cache_root: Path = CACHE_ROOT) -> Path:
    """(AR) يجلب language-truth/ من الفرع المطلوب إلى خبيئة محلّيّة ويُرجع جذرها.

    استنساخ ضحل (--depth 1) ومتفرّق (sparse) على language-truth/ وحده، فالجلب
    ثوانٍ لا دقائق. الخبيئة تُعاد استعمالها بين النداءات؛ نُحدّثها في كل مرّة كي
    لا نولّد من لقطةٍ بائتة صامتة.
    """
    dest = cache_root / ref.replace("/", "_")
    try:
        if not (dest / ".git").is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            _git("init", "-q", str(dest))
            _git("remote", "add", "origin", CLONE_URL, cwd=dest)
            _git("sparse-checkout", "set", "--cone", "language-truth", cwd=dest)
        _git("fetch", "--depth", "1", "origin", ref, cwd=dest)
        _git("checkout", "-q", "--detach", "FETCH_HEAD", cwd=dest)
        sha = _git("rev-parse", "--short", "HEAD", cwd=dest)
    except FileNotFoundError:
        sys.exit("خطأ: الأمر git غير موجود في المسار — --fetch يحتاجه.")
    except subprocess.CalledProcessError as exc:
        tail = (exc.stderr or "").strip().splitlines()
        sys.exit(
            "\n".join([
                f"خطأ: تعذّر جلب الفرع «{ref}» من {REPO}.",
                "      تحقّق من اسم الفرع ومن الاتّصال بالشبكة.",
                f"      git: {tail[-1] if tail else exc}",
            ])
        )
    if not (dest / "language-truth").is_dir():
        sys.exit(f"خطأ: الفرع «{ref}» لا يحوي language-truth/ — أهو فرع مستودع اللغة؟")
    print(f"جُلب SoT: {ref} @ {sha} → {dest}")
    return dest

# ── لافتة تُوضَع رأس كل ملف مُولَّد ───────────────────────────────────────────
BANNER = (
    "<!-- ⚠️ ملف مُولَّد آليًّا — لا تحرّره يدويًّا، ولا يُودَع في git.\n"
    "     المصدر: language-truth/{src} في {repo} (فرع: {ref}).\n"
    "     أعِد التوليد بـ: python scripts/gen_reference.py --fetch {ref}\n"
    "     يحرسه CI: اختبارات ذهبيّة (tests/) + حارس --verify قبل كلّ بناء. -->\n\n"
)

TYPE_FORMS = {
    "مفرد": "نوع", "مفرد_صفة": "مدمج",
    "مثنى": "نوعان", "مثنى_صفة": "مدمجان",
    "جمع": "أنواع", "جمع_صفة": "مدمجة",
    "منصوب": "نوعًا", "منصوب_صفة": "مدمجًا",
}
PROP_FORMS = {
    "مفرد": "مفتاح", "مثنى": "مفتاحان", "جمع": "مفاتيح", "منصوب": "مفتاحًا",
}
PAGE_FORMS = {
    "مفرد": "صفحة", "مفرد_صفة": "مرجعيّة", "مثنى": "صفحتان",
    "مثنى_صفة": "مرجعيّتان", "جمع": "صفحات", "جمع_صفة": "مرجعيّة",
    "منصوب": "صفحةً", "منصوب_صفة": "مرجعيّةً",
}


def TYPES_COUNT_PHRASE(n: int) -> str:
    return counted(n, TYPE_FORMS)


def PROPS_COUNT_PHRASE(n: int) -> str:
    return counted(n, PROP_FORMS)


ASSOC_AR = {"left": "يسار", "right": "يمين", "none": "بلا"}
ARITY_AR = {"binary": "ثنائيّ", "unary": "أحاديّ", "ternary": "ثلاثيّ"}
OP_CATEGORY_AR = {
    "assignment": "إسناد", "ternary": "ثلاثيّ", "null_safety": "أمان العدم",
    "logical": "منطقيّ", "bitwise": "بتّيّ", "comparison": "مقارنة",
    "membership": "عضويّة", "arithmetic": "حسابيّ", "access": "وصول",
}
KW_SUBCATEGORY_AR = {
    "functions_classes": "الدوال والبنيات والأصناف",
    "control_flow": "التحكّم في التدفّق",
    "pattern_matching": "مطابقة الأنماط",
    "error_handling": "معالجة الأخطاء",
    "access_control": "التحكّم بالوصول",
    "modules": "الوحدات",
    "variables": "المتغيّرات",
    "literals": "القيم الحرفيّة",
}
TYPE_CATEGORY_AR = {
    "numeric": "عدديّ", "text": "نصّيّ", "logic": "منطقيّ",
    "special": "خاصّ", "composite": "مركّب",
}


def md_escape(text) -> str:
    """تهريبٌ لمحتوى **مدى شيفرة** (بين علامتَي `): العمود | وحده.

    لا يجوز هنا تهريب < و> بكيانات HTML: مدى الشيفرة لا يفكّ الكيانات، فتظهر
    `&lt;` حرفيًّا. لذلك للنثر دالّةٌ أخرى — md_text.
    """
    return str(text).replace("|", "\\|")


def md_text(text) -> str:
    """تهريبٌ لخليّة **نثريّة** (خارج مدى الشيفرة).

    قِيس: وصف SoT «مصفوفة<T> ديناميكية» كان يُصيَّر «مصفوفة ديناميكية» —
    mdBook يعدّ <T> وسمَ HTML مفتوحًا فيبتلعه ويحذّر
    (unclosed HTML tag `<t>`)، فيفقد القارئ معامل النوع كلّه.
    """
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("|", "\\|")
    )


# ── العدد العربيّ وتمييزه ────────────────────────────────────────────────────
# القاعدة: ٣–١٠ ⇒ جمعٌ مجرور («٩ أنواعٍ مدمجة»)، ١١–٩٩ ⇒ مفردٌ منصوب
# («١٧ نوعًا مدمجًا»)، ١٠٠ فأكثر ⇒ مفردٌ مجرور. كان النصّ يقول «17 أنواع
# مدمجة» — صحيحًا مصادفةً عند ٩ ثمّ خاطئًا عند ١١ فأكثر. الصفةُ تتبع التمييز.
def counted(number: int, forms: dict) -> str:
    """يبني عبارةَ عددٍ وتمييزٍ وصفةٍ صحيحةً نحويًّا.

    forms: مفرد، مثنى، جمع، منصوب — ولكلٍّ صفته الاختياريّة بلاحقة `_صفة`.
    """
    if number == 1:
        key = "مفرد"
    elif number == 2:
        key = "مثنى"
    elif 3 <= number <= 10:
        key = "جمع"
    elif number >= 100:
        key = "مفرد"
    else:
        key = "منصوب"

    noun = forms[key]
    adjective = forms.get(key + "_صفة", "")
    prefix = "" if number in (1, 2) else f"{number} "
    return (prefix + noun + (" " + adjective if adjective else "")).strip()


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def blob(ref: str, path: str) -> str:
    return f"https://github.com/{REPO}/blob/{ref}/{path}"


def banner(src: str, ref: str) -> str:
    return BANNER.format(src=src, repo=REPO, ref=ref)


def op_symbol(ops: list, op_id: str, default: str) -> str:
    """رمز عامل بمعرّفه — يُمكّن النثر من تتبّع رمز الفرع الفعليّ (?. مقابل ؟.)."""
    for op in ops:
        if op.get("id") == op_id:
            return op["symbol"]
    return default


# ── توليد keywords.md ────────────────────────────────────────────────────────
def gen_keywords(src_dir: Path, ref: str) -> str:
    data = load_yaml(src_dir / "language-truth" / "keywords.yaml")
    cats = data["categories"]
    reserved = cats["reserved"]["keywords"]
    operators = cats["operators"]["keywords"]
    contextual = cats.get("contextual", {}).get("keywords", [])
    builtin = cats.get("builtin_types", {}).get("keywords", [])
    url = blob(ref, "language-truth/keywords.yaml")

    # (AR) العددُ يُشتقُّ من SoT: «الأربعون» عددٌ منثورٌ يصير كذبًا بأوّل كلمةٍ
    #      تُضاف، ولا حارسَ يراه — نسخةٌ ثانيةٌ لحقيقةٍ لها مصدرٌ واحد.
    out = [banner("keywords.yaml", ref),
           f"# الكلمات المحجوزة ({len(reserved)})\n"]
    out.append("تُصنِّف لغة ص كلماتها بحسب طريقة معالجة المعجمي (Lexer) لها:\n")
    out.append("| الفئة | العدد | سلوك المعجمي | صالحة كاسم متغيّر؟ |")
    out.append("|------|:----:|---------------|:------------------:|")
    out.append(f"| **محجوزة** (reserved) | {len(reserved)} | يُصدر `KEYWORD_*` | ❌ |")
    out.append(f"| **عوامل منطقيّة** (operators) | {len(operators)} | يُصدر `OP_*` | ❌ |")
    out.append(f"| **سياقيّة** (contextual) | {len(contextual)} | يُصدر `IDENTIFIER` (يقرّره المحلّل) | ✅ |")
    out.append(f"| **أنواع مدمجة** (builtin) | {len(builtin)} | يُصدر `IDENTIFIER` | ✅ |")
    out.append("")
    out.append(f"> **المصدر:** [`language-truth/keywords.yaml`]({url}) — المصدر الوحيد المطلق.\n")
    out.append("---\n")
    out.append(f"## الكلمات المحجوزة ({len(reserved)})\n")
    out.append("تُصدرها المعجمي رمزًا خاصًّا، ولا يجوز استعمالها أسماءً.\n")

    order, groups = [], {}
    for kw in reserved:
        sub = kw.get("subcategory", "أخرى")
        if sub not in groups:
            groups[sub] = []
            order.append(sub)
        groups[sub].append(kw)

    for sub in order:
        items = groups[sub]
        out.append(f"### {KW_SUBCATEGORY_AR.get(sub, sub)} ({len(items)})\n")
        out.append("| الكلمة | الإنجليزيّة | بدائل |")
        out.append("|--------|-------------|------|")
        for kw in items:
            aliases = "، ".join(kw.get("aliases", [])) or "—"
            out.append(f"| `{md_escape(kw['word'])}` | {md_text(kw['english'])} | {md_text(aliases)} |")
        out.append("")

    out.append("---\n")
    out.append(f"## العوامل المنطقيّة ({len(operators)})\n")
    out.append("تُلفظ كلماتٍ، يُصدرها المعجمي رموز عوامل، ولا تُستعمل أسماءً.\n")
    out.append("| الكلمة | الإنجليزيّة |")
    out.append("|--------|-------------|")
    for kw in operators:
        out.append(f"| `{md_escape(kw['word'])}` | {kw['english']} |")
    out.append("")

    out.append("## الكلمات السياقيّة (لمحة)\n")
    sample = "، ".join(f"`{md_escape(k['word'])}`" for k in contextual[:14])
    out.append(
        "كلمات يُصدرها المعجمي **مُعرِّفات**، ويميّزها المحلّل بحسب الموضع — فيجوز "
        "استعمالها أسماءَ متغيّرات خارج سياقها. أمثلة: " + sample + ".\n"
    )
    out.append(f"للقائمة الكاملة راجع [`language-truth/keywords.yaml`]({url}).\n")
    out.append("## انظر أيضًا\n")
    out.append("- [الأنواع المدمجة](types.md) — الأنواع المدمجة (`رقم`، `نص`...).")
    out.append("- [العوامل والأسبقيّة](operators.md) — العوامل الرمزيّة ودرجاتها.")
    return "\n".join(out) + "\n"


# ── توليد operators.md ───────────────────────────────────────────────────────
def gen_operators(src_dir: Path, ref: str) -> str:
    data = load_yaml(src_dir / "language-truth" / "operators.yaml")
    ops = data["operators"]
    ops_sorted = sorted(enumerate(ops), key=lambda t: (t[1].get("precedence", 99), t[0]))
    url = blob(ref, "language-truth/operators.yaml")

    out = [banner("operators.yaml", ref), "# العوامل والأسبقيّة\n"]
    out.append(
        "جميع عوامل لغة ص مرتّبةً حسب **الأسبقيّة**: الدرجة **1 هي الأعلى** (تُحسَب "
        "أوّلًا) و**15 هي الأدنى**. الترابط يحدّد اتجاه التجميع عند تساوي الأسبقيّة.\n"
    )
    out.append(f"> **المصدر:** [`language-truth/operators.yaml`]({url})"
               " — المشتقّ من ترتيب الأسبقيّة الفعليّ في المحلّل.\n")
    out.append("| الأسبقيّة | العامل | الاسم | الترابط | الفئة | النوعيّة |")
    out.append("|:--------:|:------:|------|:-------:|------|:--------:|")
    for _, op in ops_sorted:
        sym = md_escape(op["symbol"])
        if "aliases" in op:
            sym += " / " + " / ".join(md_escape(a) for a in op["aliases"])
        assoc = ASSOC_AR.get(op.get("associativity", ""), op.get("associativity", "—"))
        cat = OP_CATEGORY_AR.get(op.get("category", ""), op.get("category", "—"))
        arity = ARITY_AR.get(op.get("arity", ""), op.get("arity", "—"))
        out.append(f"| {op.get('precedence', '—')} | `{sym}` | {md_text(op['name_ar'])} | "
                   f"{assoc} | {cat} | {arity} |")
    out.append("")

    # رموز أمان العدم من بيانات الفرع الفعليّة (تختلف بين القنوات)
    chain = op_symbol(ops, "op.optional_chain", "?.")
    coalesce = op_symbol(ops, "op.null_coalesce", "??")
    has_assert = any(o.get("id") == "op.null_assert" for o in ops)
    out.append("## ملاحظات\n")
    out.append(
        "- **العوامل المنطقيّة بصيغتين:** كلمات (`و`، `أو`، `ليس`) ورموز "
        "(`&&`، `||`، `!`) بالأسبقيّة نفسها؛ الكلمات هي المفضّلة عربيًّا."
    )
    assert_note = "، و`مؤكد` تأكيد عدم الفراغ" if has_assert else ""
    out.append(
        f"- **أمان العدم:** `{coalesce}` اندماج فارغ، `{chain}` وصول آمن{assert_note} "
        "(تتبع رموز هذا الفرع تحديدًا)."
    )
    out.append("")
    out.append("## انظر أيضًا\n")
    out.append("- [التعبيرات والعمليات](../language/expressions.md) — أمثلة استعمال.")
    out.append("- [الأنواع المدمجة](types.md) — الأنواع الاختياريّة وأمان العدم.")
    return "\n".join(out) + "\n"


# ── توليد types.md ───────────────────────────────────────────────────────────
def gen_types(src_dir: Path, ref: str) -> str:
    kw = load_yaml(src_dir / "language-truth" / "keywords.yaml")
    builtin = kw["categories"]["builtin_types"]["keywords"]

    desc_by_word = {}
    types_path = src_dir / "language-truth" / "types.yaml"
    if types_path.exists():
        for t in load_yaml(types_path).get("types", []):
            if "word" in t and t.get("description_ar"):
                desc_by_word[t["word"]] = t["description_ar"]

    # رموز أمان العدم من عوامل الفرع (تجعل المثال صحيحًا لكل قناة)
    ops_path = src_dir / "language-truth" / "operators.yaml"
    chain, coalesce = "?.", "??"
    if ops_path.exists():
        ops = load_yaml(ops_path).get("operators", [])
        chain = op_symbol(ops, "op.optional_chain", "?.")
        coalesce = op_symbol(ops, "op.null_coalesce", "??")
    opt = chain[0]  # رمز اللاحقة الاختياريّة (? أو ؟)

    kw_url = blob(ref, "language-truth/keywords.yaml")
    ty_url = blob(ref, "language-truth/types.yaml")
    out = [banner("keywords.yaml (builtin_types) + types.yaml", ref), "# الأنواع المدمجة\n"]
    out.append(
        f"تُقدّم لغة ص **{TYPES_COUNT_PHRASE(len(builtin))}**. أسماؤها يُصدرها المعجمي "
        "**مُعرِّفات** (لا كلمات محجوزة)، فيجوز استعمالها أسماءً خارج موضع النوع.\n"
    )
    out.append(f"> **المصدر:** [`keywords.yaml`]({kw_url}) (فئة `builtin_types`) + "
               f"[`types.yaml`]({ty_url}).\n")
    out.append("| النوع | الإنجليزيّة | الفئة | الوصف |")
    out.append("|------|-------------|------|-------|")
    for t in builtin:
        cat = TYPE_CATEGORY_AR.get(t.get("subcategory", ""), t.get("subcategory", "—"))
        desc = desc_by_word.get(t["word"], "—")
        out.append(f"| `{md_escape(t['word'])}` | {md_text(t['english'])} | {cat} | {md_text(desc)} |")
    out.append("")
    out.append("## القيم الحرفيّة المحجوزة\n")
    out.append("```sad\nمتغير يعمل = صحيح     # true\nمتغير متوقّف = خطأ    # false\nمتغير قيمة = لاشيء    # null\n```\n")
    out.append("## الأنواع الاختياريّة وأمان العدم\n")
    out.append(
        f"يُكتب النوع الاختياريّ باللاحقة `{opt}` ليقبل القيمة أو `لاشيء`، "
        f"ويُعالَج بعوامل `{chain}` (وصول آمن) و`{coalesce}` (اندماج فارغ):\n"
    )
    out.append(f"```sad\nمتغير الوسط: نص{opt} = لاشيء\nمتغير الطول = الوسط{chain}الطول\n"
               f"متغير قيمة = الوسط {coalesce} \"مجهول\"\n```\n")
    out.append("راجع [العوامل والأسبقيّة](operators.md) لعوامل أمان العدم ورموزها الدقيقة.")
    return "\n".join(out) + "\n"


# ── توليد sadui-properties.md ────────────────────────────────────────────────
def gen_ui_props(src_dir: Path, ref: str) -> str:
    data = load_yaml(src_dir / "language-truth" / "ui_props.yaml")
    keys = data.get("المصطلحات") or data.get("keys") or []
    url = blob(ref, "language-truth/ui_props.yaml")
    out = [banner("ui_props.yaml", ref), "# خصائص واجهة SadUI والتخطيط\n"]
    out.append("> واجهة SadUI **عربيّة RTL-أوّلًا**: محتوى الشاشة يبدأ من **اليمين**. "
               "تُوصَف العناصر بخصائص عربيّة قانونيّة معرَّفة في مصدر الحقيقة.\n")
    out.append(f"> **المصدر:** [`language-truth/ui_props.yaml`]({url}) — "
               f"{PROPS_COUNT_PHRASE(len(keys))}. لكلّ مفتاح ثابت مولَّد `sad::ui::props::<ID>` يُقرأ "
               "في كود الرسوميّات (لا سلاسل خام).\n")

    out.append("## المحاذاة المتقاطعة\n")
    out.append("خاصّيّة **`محاذاة`** تضبط المحاذاة المتقاطعة لأبناء العمود/الصفّ:\n")
    out.append("| الوضع | العمود (RTL) | الصفّ |")
    out.append("|---|---|---|")
    out.append("| `بداية` (افتراضيّ) | يمينًا | أعلى |")
    out.append("| `وسط` | توسيط | توسيط عموديّ |")
    out.append("| `نهاية` | يسارًا | أسفل |")
    out.append("| `تمدّد` | يملأ العرض | يملأ الارتفاع |\n")
    out.append("- «محاذاة» يُكرِّمها **العمود والصفّ** حصرًا (الشبكة/المكدّس/الالتفاف لها "
               "تموضع RTL مبيَّت خاصّ).\n")

    out.append(f"## كلّ المفاتيح ({len(keys)})\n")
    out.append("| المفتاح | الثابت `props::` | النوع | لاتينيّ؟ | الوصف |")
    out.append("|---|---|---|---|---|")
    for k in keys:
        cid = k.get("id", "")
        canon = md_escape(k.get("canonical", ""))
        vt = md_text(k.get("value_type", "—"))
        latin = "✔" if k.get("latin_alias") else ""
        desc = md_text(k.get("description_ar", "—"))
        out.append(f"| `{canon}` | `{cid}` | {vt} | {latin} | {desc} |")
    out.append("")
    out.append("> التفصيل المعماريّ (المحاور، الأوضاع، الهامش/الأوزان، الحرّاس) في مستودع "
               "اللغة: `docs/architecture/sadui-layout-alignment.md`.\n")
    return "\n".join(out) + "\n"


# ── توليد builtins.md ────────────────────────────────────────────────────────
# (AR) عمودا المحرّكَين **مقيسان لا معلَنان**: مصدرهما
# `language-truth/_meta/builtin_engine_support.yaml` الذي يُنتجه مِجَسٌّ يسأل
# المحرّكَين أنفسَهما (scripts/codegen/probe_builtin_engines.py في مستودع
# اللغة). ولا يُشتقّان من `status` — الـ١٢٠٥ كلُّها `stable` بينما يرفضُ
# المترجّمُ مئاتٍ منها بـSEM047 المسمّى؛ فالحقلُ دعوى والمِجَسُّ قياس.
# وإن غاب ملفُّ القياس (فرعٌ لم يبلغه بعد) تُحذف الأعمدةُ وتُقال العلّة —
# ولا تُملأ بقيمةٍ مخمَّنة.
ENGINE_SUPPORT_REL = "language-truth/_meta/builtin_engine_support.yaml"

NAMESPACE_AR = {
    "Core": "النواة", "TypeCtor": "بناة الأنواع", "Concurrency": "التزامن",
    "Math": "الرياضيات", "Strings": "النصوص", "Arrays": "المصفوفات",
    "Basics": "الأساسيّات", "Assertions": "التأكيدات", "Maps": "الخرائط",
    "Sockets": "المقابس", "HttpClient": "عميل HTTP", "HttpServer": "خادم HTTP",
    "NetworkUtils": "أدوات الشبكة", "WebSocketClient": "عميل WebSocket",
    "WebSocketServer": "خادم WebSocket", "Platform": "المنصّة",
    "Crypto": "التشفير", "String": "النصّ", "Array": "المصفوفة", "Map": "الخريطة",
    "IO": "الدخل والخرج", "System": "النظام", "AsyncAdvanced": "اللاتزامن المتقدّم",
    "Exceptions": "الاستثناءات", "FFI": "الاستدعاء الأجنبيّ",
    "KernelAudio": "نواة · الصوت", "KernelCpu": "نواة · المعالج",
    "KernelGpu": "نواة · معالج الرسوم", "KernelMemory": "نواة · الذاكرة",
    "KernelNet": "نواة · الشبكة", "KernelSerial": "نواة · التسلسليّ",
    "KernelStorage": "نواة · التخزين", "CompilerIo": "مترجم · الدخل والخرج",
    "CompilerCpuCtl": "مترجم · تحكّم المعالج", "CompilerHw": "مترجم · العتاد",
    "CompilerSys": "مترجم · النظام", "CompilerSec": "مترجم · الأمان",
    "CompilerSimd": "مترجم · SIMD", "CompilerMem": "مترجم · الذاكرة",
    "CompilerEmbed": "مترجم · المضمَّنات", "CompilerUefi": "مترجم · UEFI",
    "CompilerUi": "مترجم · الواجهة",
    "Kernel": "نواة · العامّ", "KernelThreads": "نواة · الخيوط",
    "KernelTimers": "نواة · المؤقّتات", "KernelUSB": "نواة · USB",
    "Processes": "العمليّات", "SadNet": "شبكة ص (SadNet)",
    "UIAudio": "واجهة · الصوت", "UICore": "واجهة · النواة",
    "UICrypto": "واجهة · التشفير", "UIDevice": "واجهة · الجهاز",
    "UIDialog": "واجهة · الحوارات", "UIIO": "واجهة · الدخل والخرج",
    "UINetwork": "واجهة · الشبكة", "UIPlatform": "واجهة · المنصّة",
    "UIStorage": "واجهة · التخزين", "UITimer": "واجهة · المؤقّت",
    "UIWidgets": "واجهة · الودجات",
}

MODULE_IMPORT_AR = {
    "STRINGS": "نصوص", "BASICS": "أساسيات", "MATH": "رياضيات",
    "ASSERTIONS": "تأكيدات", "MAPS": "خرائط", "ASYNC": "تزامن_متقدم",
    "PLATFORM": "منصة", "NETWORK": "شبكة", "SOCKETS": "مقابس",
    "CRYPTO": "تشفير", "PROCESSES": "منصة",
}

BUILTIN_FORMS = {"مفرد": "دالّة", "مفرد_صفة": "مدمجة", "مثنى": "دالّتان",
                 "مثنى_صفة": "مدمجتان", "جمع": "دوالّ", "جمع_صفة": "مدمجة",
                 "منصوب": "دالّةً", "منصوب_صفة": "مدمجةً"}
GROUP_FORMS = {"مفرد": "مجموعة", "مثنى": "مجموعتان", "جمع": "مجموعات",
               "منصوب": "مجموعةً"}
FILE_FORMS = {"مفرد": "ملفّ", "مثنى": "ملفّان", "جمع": "ملفّات",
              "منصوب": "ملفًّا"}
# (AR) «رمز خطأ» إضافةٌ: لا تنوينَ على المضافِ الأوّل، فالمنصوبُ «رمزَ خطأ»
#      لا «رمزًا خطأ». وقاعدةُ counted تُطبَّق على المركَّبِ كلِّه لا على صدره.
ERROR_FORMS = {"مفرد": "رمز خطأ", "مثنى": "رمزا خطأ", "جمع": "رموز أخطاء",
               "منصوب": "رمزَ خطأ"}


def _arity_text(fn: dict) -> str:
    """رتبةُ الدالّة كما يفحصها المحرّك — لا عددُ أوصافِ params النثريّة."""
    arity = fn.get("arity") or {}
    if not arity:
        return "—"
    low = arity.get("min", 0)
    if arity.get("variadic"):
        return f"{low}+"
    high = arity.get("max", low)
    return str(low) if low == high else f"{low}–{high}"


# (AR) بعضُ أوصافِ SoT نمت مقالاتٍ (أقصاها ٣٧٢٤ محرفًا في خليّةِ جدول) فتُفقِدُ
#      الجدولَ قابليّةَ المسحِ بالعين. الاختصارُ عند حدِّ جملةٍ **يُعلَنُ بـ«…»**
#      ولا يُخفى، والكاملُ باقٍ في المصدرِ المرتبطِ أعلى الصفحة. والعلاجُ الجذريُّ
#      في مستودعِ اللغة: حقلُ `summary_ar` قصيرٌ إلى جانبِ `description_ar`.
DESC_LIMIT = 200


def summarize(text: str, limit: int = DESC_LIMIT) -> str:
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    window = text[:limit]
    for sep in ("، ", ". ", " — ", " ("):
        cut = window.rfind(sep)
        if cut > limit // 2:
            return window[:cut].rstrip("،. —(") + " …"
    return window.rstrip() + " …"


def _load_engine_support(src_dir: Path):
    """يُرجع (خريطةُ الاسم ← الدعم، بياناتُ القياس) أو (None, None) إن غاب."""
    path = src_dir / ENGINE_SUPPORT_REL
    if not path.exists():
        return None, None
    data = load_yaml(path) or {}
    rows = data.get("functions") or []
    if not rows:
        return None, None
    return {r["canonical"]: r for r in rows}, data


def gen_builtins(src_dir: Path, ref: str) -> str:
    sot_dir = src_dir / "language-truth" / "builtins"
    fns = []
    for path in sorted(sot_dir.glob("*.yaml")):
        doc = load_yaml(path) or {}
        for fn in doc.get("functions") or []:
            fns.append(fn)
    fns.sort(key=lambda f: (f.get("namespace", ""), f["canonical"]))

    support, measurement = _load_engine_support(src_dir)
    url = blob(ref, "language-truth/builtins/")

    out = [banner("builtins/*.yaml", ref), "# الدوالّ المدمجة\n"]
    groups = {}
    for fn in fns:
        groups.setdefault(fn.get("namespace", "—"), []).append(fn)

    out.append(
        f"تُقدّم لغة ص **{counted(len(fns), BUILTIN_FORMS)}** موزّعةً على "
        f"**{counted(len(groups), GROUP_FORMS)}**.\n"
    )
    out.append(f"> **المصدر:** [`language-truth/builtins/`]({url}) — "
               f"{counted(len(list(sot_dir.glob('*.yaml'))), FILE_FORMS)} YAML.\n")

    if support:
        counts = (measurement or {}).get("counts", {})
        commit = (measurement or {}).get("measured_commit", "—")
        out.append("## على أيّ محرّك تعمل؟\n")
        out.append(
            "للغة ص محرّكان: **المفسّر** (`sad-run`) و**المترجّم** (`sad-build`). "
            "وليس كلّ مدمَجٍ معلَنٍ يعمل عليهما معًا. الجدول أدناه **مقيسٌ** بسؤال "
            "المحرّكَين أنفسهما — لا مأخوذٌ من حقل `status` (فكلّ المدمَجات "
            "`stable` فيه بينما يرفض المترجّم مئاتٍ منها).\n"
        )
        out.append("| الحالة | العدد |")
        out.append("|---|:---:|")
        out.append(f"| ✅ يعمل على المحرّكَين | {counts.get('both', '—')} |")
        out.append(f"| 🟡 المفسّر وحده | {counts.get('interpreter_only', '—')} |")
        out.append(f"| 🟠 المترجّم وحده | {counts.get('compiler_only', '—')} |")
        out.append(f"| ❌ لا يحلّه أيّ محرّك | {counts.get('neither', '—')} |")
        out.append("")
        out.append(
            "> **حدّ القياس (يُذكر ولا يُخفى):** المقيسُ **حلُّ الاسم** في المحرّك، "
            "لا صحّةُ التنفيذ ولا سلامةُ العائد. «✅» تعني «المحرّك يعرفه»، "
            "ولا تعني «قِيس أثره».\n"
        )
        out.append(f"> القياس على الإيداع `{commit[:12]}` — سِجِلُّه في "
                   f"[`{ENGINE_SUPPORT_REL}`]({blob(ref, ENGINE_SUPPORT_REL)}).\n")
        out.append(
            "> 🟡 **المفسّر وحده** ليست عيبًا في برنامجك: شغّله بـ`sad-run` "
            "ريثما يُوصَل المدمَج بالمترجّم. والمترجّم يقولها صراحةً بالرمز "
            "`SEM047` ولا يتبخّر النداء صامتًا.\n"
        )
    else:
        out.append("> **ملاحظة:** سِجِلُّ قياس المحرّكَين "
                   f"(`{ENGINE_SUPPORT_REL}`) غير موجود في هذا الفرع، "
                   "فعمودا «المترجّم» و«المفسّر» محذوفان. لا تُملأ خانةٌ "
                   "بقيمةٍ مخمَّنة.\n")

    out.append("## الفهرس\n")
    for ns in sorted(groups, key=lambda n: NAMESPACE_AR.get(n, n)):
        label = NAMESPACE_AR.get(ns, ns)
        anchor = ns.lower()
        out.append(f"- [{label} (`{ns}`)](#{anchor}) — "
                   f"{counted(len(groups[ns]), BUILTIN_FORMS)}")
    out.append("")

    for ns in sorted(groups, key=lambda n: NAMESPACE_AR.get(n, n)):
        members = groups[ns]
        label = NAMESPACE_AR.get(ns, ns)
        out.append(f"## {ns}\n")
        out.append(f"**{label}** — {counted(len(members), BUILTIN_FORMS)}.\n")

        needs = {f.get("module") for f in members if f.get("require_import")}
        needs.discard("NONE")
        needs.discard(None)
        if needs:
            imports = sorted({MODULE_IMPORT_AR.get(m, m) for m in needs})
            lines = "\n".join(f"استورد {m}" for m in imports)
            out.append(f"```sad\n{lines}\n```\n")

        if support:
            out.append("| الدالّة | الرتبة | العائد | المترجّم | المفسّر | الوصف |")
            out.append("|---|:---:|---|:---:|:---:|---|")
        else:
            out.append("| الدالّة | الرتبة | العائد | الوصف |")
            out.append("|---|:---:|---|---|")
        for fn in members:
            name = md_escape(fn["canonical"])
            arity = _arity_text(fn)
            returns = md_text(fn.get("returns") or "—")
            desc = md_text(summarize(fn.get("description_ar") or "—"))
            if support:
                row = support.get(fn["canonical"])
                comp = "—" if row is None else ("✅" if row["compiler"] else "❌")
                interp = "—" if row is None else ("✅" if row["interpreter"] else "❌")
                out.append(f"| `{name}` | {arity} | {returns} | {comp} | {interp} | {desc} |")
            else:
                out.append(f"| `{name}` | {arity} | {returns} | {desc} |")
        out.append("")

    out.append("## انظر أيضًا\n")
    out.append("- [رموز الأخطاء](errors.md) — ما تعنيه `SEM047` وأخواتها.")
    out.append("- [الأنواع المدمجة](types.md) — أنواع الوسائط والعوائد.")
    out.append("- [التشغيل والترجمة](../tools/run-build.md) — الفرق بين المحرّكَين.")
    return "\n".join(out) + "\n"


# ── توليد errors.md ──────────────────────────────────────────────────────────
ERROR_CATEGORY_AR = {
    "lexical": "معجميّة (Lexical)",
    "syntactic": "نحويّة (Syntactic)",
    "semantic": "دلاليّة (Semantic)",
    "runtime": "وقت التشغيل (Runtime)",
    "internal": "داخليّة (Internal)",
    "import": "الاستيراد (Import)",
    "io": "الدخل والخرج (I/O)",
    "ownership": "الملكيّة والاستعارة (Ownership)",
}


def _ar(field) -> str:
    """يلتقط النصّ العربيّ من حقلٍ ثنائيّ اللغة أو من نصٍّ مجرّد."""
    if isinstance(field, dict):
        return field.get("ar") or field.get("en") or ""
    return field or ""


def gen_errors(src_dir: Path, ref: str) -> str:
    err_dir = src_dir / "language-truth" / "errors"
    cats = []
    total = 0
    for path in sorted(err_dir.glob("*.yaml")):
        doc = load_yaml(path) or {}
        errors = doc.get("errors") or []
        if not errors:
            continue
        errors.sort(key=lambda e: e.get("id", ""))
        cats.append((doc.get("category", path.stem), path.name, errors))
        total += len(errors)
    cats.sort(key=lambda c: -len(c[2]))

    url = blob(ref, "language-truth/errors/")
    out = [banner("errors/*.yaml", ref), "# رموز الأخطاء\n"]
    out.append(
        f"يُصدر محرّكا لغة ص **{counted(total, ERROR_FORMS)}**. كلّ رمزٍ ثابتٌ "
        "عبر الإصدارات، فيصلح للبحث وللإحالة في تقرير عطب.\n"
    )
    out.append(f"> **المصدر:** [`language-truth/errors/`]({url}) — الرسائل "
               "نفسها تُولَّد منه للمحرّكَين، فلا تنجرف رسالةٌ عن رمزها.\n")

    out.append("| الفئة | البادئة | العدد |")
    out.append("|---|---|:---:|")
    for cat, _fname, errors in cats:
        prefix = errors[0].get("id", "")[:3] if errors else "—"
        out.append(f"| {ERROR_CATEGORY_AR.get(cat, cat)} | `{prefix}` | {len(errors)} |")
    out.append("")
    out.append("> **كيف تقرأ الرمز:** البادئة تقول **أيّ طبقةٍ** رفضت البرنامج — "
               "معجميّة (الحروف) ثمّ نحويّة (الشكل) ثمّ دلاليّة (المعنى) ثمّ وقت "
               "التشغيل. وطبقةٌ أبكر تعني عطبًا أقربَ إلى النصّ الذي كتبتَه.\n")

    for cat, fname, errors in cats:
        label = ERROR_CATEGORY_AR.get(cat, cat)
        out.append(f"## {label}\n")
        out.append(f"{counted(len(errors), ERROR_FORMS)} — "
                   f"[`{fname}`]({blob(ref, 'language-truth/errors/' + fname)}).\n")
        out.append("| الرمز | العنوان | الرسالة | العلاج المقترح |")
        out.append("|---|---|---|---|")
        for err in errors:
            eid = md_escape(err.get("id", "—"))
            title = md_text(_ar(err.get("title")) or "—")
            brief = md_text(_ar(err.get("brief")) or "—")
            hint = md_text(_ar(err.get("fix_hint")) or "—")
            out.append(f"| `{eid}` | {title} | {brief} | {hint} |")
        out.append("")

    out.append("## انظر أيضًا\n")
    out.append("- [معالجة الأخطاء](../language/errors.md) — التقاط الاستثناءات في لغة ص.")
    out.append("- [الدوالّ المدمجة](builtins.md) — `SEM047` وتغطية المحرّكَين.")
    return "\n".join(out) + "\n"


# (AR) أقلّ حجمٍ معقول لصفحةٍ مُولَّدة — يكشف الجذاذة التي يُنشئها mdBook تلقائيًّا
# (عنوانٌ وحده، ~32 بايتًا) حين يكون الملفّ غائبًا. قِيس: mdBook لا يفشل على
# ملفٍّ غائبٍ مذكورٍ في SUMMARY، بل يُنشئ جذاذةً ويبني بنجاح — فتُنشَر صفحةٌ بيضاء.
MIN_PAGE_BYTES = 500
MARKER = "ملف مُولَّد آليًّا"


def verify(out_dir: Path) -> int:
    """(AR) يتحقّق أنّ صفحات المرجع مُولَّدةٌ فعلًا قبل البناء/النشر.

    لا يحتاج SoT ولا شبكة — يقرأ القرص وحده، فيصلح خطوةً حاجبةً قبل
    `mdbook build` في كلّ سيرٍ وعند المساهم.
    """
    problems = []
    for name in GENERATORS:
        page = out_dir / name
        if not page.is_file():
            problems.append(f"{page}: غير موجودة.")
            continue
        text = page.read_text(encoding="utf-8")
        if len(text.encode("utf-8")) < MIN_PAGE_BYTES:
            problems.append(f"{page}: جذاذة ({len(text)} محرفًا) — لم تُولَّد.")
        elif MARKER not in text:
            problems.append(f"{page}: بلا لافتة التوليد — محرَّرةٌ يدويًّا أو بائتة.")
    if problems:
        print("حارس الصفحات المُولَّدة: فشل.")
        for problem in problems:
            print(f"  ✗ {problem}")
        print("شغّل:  python scripts/gen_reference.py --fetch dev")
        return 1
    # (AR) العددُ يُشتقُّ ولا يُكتَب: «الأربع» نسخةٌ ثانيةٌ لحقيقةٍ تتعفّن بإضافة صفحة.
    print(f"✓ {counted(len(GENERATORS), PAGE_FORMS)} مُولَّدةٌ وسليمة في {out_dir}")
    return 0


GENERATORS = {
    "keywords.md": gen_keywords,
    "operators.md": gen_operators,
    "types.md": gen_types,
    "sadui-properties.md": gen_ui_props,
    "builtins.md": gen_builtins,
    "errors.md": gen_errors,
}


def main() -> int:
    ap = argparse.ArgumentParser(description="مولّد صفحات المرجع من language-truth/")
    ap.add_argument("--source-dir",
                    help="جذر مستودع لغة ص (يحوي language-truth/) — بديلٌ عن --fetch")
    ap.add_argument("--fetch", metavar="REF",
                    help="اجلب language-truth/ من هذا الفرع بنفسك (يضبط --source-ref تلقائيًّا)")
    ap.add_argument("--source-ref", default="sadlang",
                    help="فرع/وسم المصدر — يُستعمل في روابط المصدر (sadlang=مستقرّ، dev=قادم)")
    ap.add_argument("--out-dir", default="src/reference",
                    help="مجلّد إخراج صفحات المرجع")
    ap.add_argument("--verify", action="store_true",
                    help="لا يولّد؛ يتحقّق فقط أنّ صفحات --out-dir مُولَّدةٌ وغير جذاذات")
    ap.add_argument("--check", action="store_true",
                    help="لا يكتب؛ يفشل إن اختلف المُولَّد عن الموجود (لفحص CI)")
    args = ap.parse_args()

    out_dir_early = Path(args.out_dir)
    if args.verify:
        if args.fetch or args.source_dir:
            ap.error("--verify يقرأ القرص وحده — لا يقبل --fetch ولا --source-dir.")
        return verify(out_dir_early)

    if bool(args.fetch) == bool(args.source_dir):
        ap.error("مرّر إمّا --fetch <ref> أو --source-dir <مسار>، لا كليهما ولا واحدًا منهما.")

    if args.fetch:
        src_dir = fetch_sot(args.fetch)
        # الفرع المجلوب هو مصدر روابط المصدر — لا يُترك للمستعمِل ليخطئ فيه.
        args.source_ref = args.fetch
    else:
        src_dir = Path(args.source_dir)
    out_dir = Path(args.out_dir)
    if not (src_dir / "language-truth").is_dir():
        sys.exit(f"خطأ: لم يُعثر على {src_dir / 'language-truth'} — تحقّق من --source-dir")

    drift = False
    for name, fn in GENERATORS.items():
        content = fn(src_dir, args.source_ref)
        target = out_dir / name
        existing = target.read_text(encoding="utf-8") if target.exists() else None
        if args.check:
            if existing != content:
                drift = True
                print(f"✗ انجراف: {target} لا يطابق المُولَّد من SoT")
            else:
                print(f"✓ متطابق: {target}")
        else:
            out_dir.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            print(f"كُتب: {target}")

    if args.check and drift:
        print("\nفشل: صفحات المرجع متباعدة عن language-truth/. أعِد التوليد.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
