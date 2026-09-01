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
    """تهريب الرموز التي تكسر جداول ماركداون (أهمّها العمود |)."""
    return str(text).replace("|", "\\|")


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

    out = [banner("keywords.yaml", ref), "# الكلمات المحجوزة الأربعون\n"]
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
            out.append(f"| `{md_escape(kw['word'])}` | {kw['english']} | {aliases} |")
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
        out.append(f"| {op.get('precedence', '—')} | `{sym}` | {op['name_ar']} | {assoc} | {cat} | {arity} |")
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
        f"تُقدّم لغة ص **{len(builtin)} أنواع مدمجة**. أسماؤها يُصدرها المعجمي "
        "**مُعرِّفات** (لا كلمات محجوزة)، فيجوز استعمالها أسماءً خارج موضع النوع.\n"
    )
    out.append(f"> **المصدر:** [`keywords.yaml`]({kw_url}) (فئة `builtin_types`) + "
               f"[`types.yaml`]({ty_url}).\n")
    out.append("| النوع | الإنجليزيّة | الفئة | الوصف |")
    out.append("|------|-------------|------|-------|")
    for t in builtin:
        cat = TYPE_CATEGORY_AR.get(t.get("subcategory", ""), t.get("subcategory", "—"))
        desc = desc_by_word.get(t["word"], "—")
        out.append(f"| `{md_escape(t['word'])}` | {t['english']} | {cat} | {md_escape(desc)} |")
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
               f"{len(keys)} مفتاحًا. لكلّ مفتاح ثابت مولَّد `sad::ui::props::<ID>` يُقرأ "
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
        vt = md_escape(k.get("value_type", "—"))
        latin = "✔" if k.get("latin_alias") else ""
        desc = md_escape(k.get("description_ar", "—"))
        out.append(f"| `{canon}` | `{cid}` | {vt} | {latin} | {desc} |")
    out.append("")
    out.append("> التفصيل المعماريّ (المحاور، الأوضاع، الهامش/الأوزان، الحرّاس) في مستودع "
               "اللغة: `docs/architecture/sadui-layout-alignment.md`.\n")
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
    print(f"✓ صفحات المرجع الأربع مُولَّدةٌ وسليمة في {out_dir}")
    return 0


GENERATORS = {
    "keywords.md": gen_keywords,
    "operators.md": gen_operators,
    "types.md": gen_types,
    "sadui-properties.md": gen_ui_props,
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
