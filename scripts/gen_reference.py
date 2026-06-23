#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# (AR) مولّد صفحات المرجع التابعة من مصدر الحقيقة (language-truth/).
#      يقرأ keywords.yaml / operators.yaml / types.yaml في المستودع الأساسيّ
#      للغة ص، ويُنتج src/reference/{keywords,operators,types}.md آليًّا.
#      الهدف: منع تباعد التوثيق عن SoT — تُعاد كتابة هذه الصفحات ولا تُحرَّر يدويًّا.
# (EN) Generates the derived reference pages from the Single Source of Truth.
#      Reads language-truth/{keywords,operators,types}.yaml and emits
#      src/reference/{keywords,operators,types}.md. Do not edit those by hand.
# ----------------------------------------------------------------------------
# الاستعمال / Usage:
#   python scripts/gen_reference.py --source-dir <path-to-language-repo-root>
#                                   [--out-dir src/reference] [--check]
#   --check: لا يكتب؛ يفشل (خروج 1) إن اختلف المُولَّد عن الموجود (لفحص CI).
# ============================================================================
import argparse
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

# ── لافتة تُوضَع رأس كل ملف مُولَّد ───────────────────────────────────────────
BANNER = (
    "<!-- ⚠️ ملف مُولَّد آليًّا — لا تحرّره يدويًّا.\n"
    "     المصدر: language-truth/{src} في sadlang/s-programming-language.\n"
    "     أعِد التوليد بـ: python scripts/gen_reference.py --source-dir <repo>\n"
    "     يفرضه CI (sync.yml) — أيّ تحرير يدويّ يُمحى عند إعادة التوليد. -->\n\n"
)

# ── ترجمات للعرض ─────────────────────────────────────────────────────────────
ASSOC_AR = {"left": "يسار", "right": "يمين", "none": "بلا"}

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


def md_escape(text: str) -> str:
    """تهريب الرموز التي تكسر جداول ماركداون (أهمّها العمود |)."""
    return str(text).replace("|", "\\|")


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── توليد keywords.md ────────────────────────────────────────────────────────
def gen_keywords(src_dir: Path) -> str:
    data = load_yaml(src_dir / "language-truth" / "keywords.yaml")
    cats = data["categories"]
    reserved = cats["reserved"]["keywords"]
    operators = cats["operators"]["keywords"]
    contextual = cats.get("contextual", {}).get("keywords", [])
    builtin = cats.get("builtin_types", {}).get("keywords", [])

    out = [BANNER.format(src="keywords.yaml"), "# الكلمات المحجوزة الأربعون\n"]
    out.append(
        "تُصنِّف لغة ص كلماتها بحسب طريقة معالجة المعجمي (Lexer) لها:\n"
    )
    out.append("| الفئة | العدد | سلوك المعجمي | صالحة كاسم متغيّر؟ |")
    out.append("|------|:----:|---------------|:------------------:|")
    out.append(f"| **محجوزة** (reserved) | {len(reserved)} | يُصدر `KEYWORD_*` | ❌ |")
    out.append(f"| **عوامل منطقيّة** (operators) | {len(operators)} | يُصدر `OP_*` | ❌ |")
    out.append(f"| **سياقيّة** (contextual) | {len(contextual)} | يُصدر `IDENTIFIER` (يقرّره المحلّل) | ✅ |")
    out.append(f"| **أنواع مدمجة** (builtin) | {len(builtin)} | يُصدر `IDENTIFIER` | ✅ |")
    out.append("")
    out.append(
        "> **المصدر:** [`language-truth/keywords.yaml`]"
        "(https://github.com/sadlang/s-programming-language/blob/sadlang/language-truth/keywords.yaml)"
        " — المصدر الوحيد المطلق.\n"
    )
    out.append("---\n")
    out.append(f"## الكلمات المحجوزة ({len(reserved)})\n")
    out.append("تُصدرها المعجمي رمزًا خاصًّا، ولا يجوز استعمالها أسماءً.\n")

    # تجميع حسب الفئة الفرعيّة مع الحفاظ على ترتيب الورود
    order, groups = [], {}
    for kw in reserved:
        sub = kw.get("subcategory", "أخرى")
        if sub not in groups:
            groups[sub] = []
            order.append(sub)
        groups[sub].append(kw)

    for sub in order:
        title = KW_SUBCATEGORY_AR.get(sub, sub)
        items = groups[sub]
        out.append(f"### {title} ({len(items)})\n")
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
    out.append(
        "للقائمة الكاملة راجع [`language-truth/keywords.yaml`]"
        "(https://github.com/sadlang/s-programming-language/blob/sadlang/language-truth/keywords.yaml).\n"
    )
    out.append("## انظر أيضًا\n")
    out.append("- [الأنواع المدمجة](types.md) — الأنواع المدمجة (`رقم`، `نص`...).")
    out.append("- [العوامل والأسبقيّة](operators.md) — العوامل الرمزيّة ودرجاتها.")
    return "\n".join(out) + "\n"


# ── توليد operators.md ───────────────────────────────────────────────────────
def gen_operators(src_dir: Path) -> str:
    path = src_dir / "language-truth" / "operators.yaml"
    data = load_yaml(path)
    ops = data["operators"]
    # ترتيب: الأسبقيّة تصاعديًّا (1 الأعلى)، ثم الحفاظ على ترتيب الملف
    ops_sorted = sorted(enumerate(ops), key=lambda t: (t[1].get("precedence", 99), t[0]))

    out = [BANNER.format(src="operators.yaml"), "# العوامل والأسبقيّة\n"]
    out.append(
        "جميع عوامل لغة ص مرتّبةً حسب **الأسبقيّة**: الدرجة **1 هي الأعلى** (تُحسَب "
        "أوّلًا) و**15 هي الأدنى**. الترابط يحدّد اتجاه التجميع عند تساوي الأسبقيّة.\n"
    )
    out.append(
        "> **المصدر:** [`language-truth/operators.yaml`]"
        "(https://github.com/sadlang/s-programming-language/blob/sadlang/language-truth/operators.yaml)"
        " — المشتقّ من ترتيب الأسبقيّة الفعليّ في المحلّل.\n"
    )
    out.append("| الأسبقيّة | العامل | الاسم | الترابط | الفئة | النوعيّة |")
    out.append("|:--------:|:------:|------|:-------:|------|:--------:|")
    for _, op in ops_sorted:
        sym = md_escape(op["symbol"])
        if "aliases" in op:
            sym += " / " + " / ".join(f"{md_escape(a)}" for a in op["aliases"])
        assoc = ASSOC_AR.get(op.get("associativity", ""), op.get("associativity", "—"))
        cat = OP_CATEGORY_AR.get(op.get("category", ""), op.get("category", "—"))
        arity = op.get("arity", "—")
        arity_ar = {"binary": "ثنائيّ", "unary": "أحاديّ", "ternary": "ثلاثيّ"}.get(arity, arity)
        out.append(
            f"| {op.get('precedence', '—')} | `{sym}` | {op['name_ar']} | {assoc} | {cat} | {arity_ar} |"
        )
    out.append("")
    out.append("## ملاحظات\n")
    out.append(
        "- **العوامل المنطقيّة بصيغتين:** كلمات (`و`، `أو`، `ليس`) ورموز "
        "(`&&`، `||`، `!`) بالأسبقيّة نفسها؛ الكلمات هي المفضّلة عربيًّا."
    )
    out.append(
        "- **أمان العدم عربيّ حصرًا:** الرمز `؟` هو U+061F (لا `?` اللاتينيّة) — "
        "`ADR-NS-002`: `؟؟` اندماج فارغ، `؟.` وصول آمن، `مؤكد` تأكيد عدم الفراغ."
    )
    out.append("")
    out.append("## انظر أيضًا\n")
    out.append("- [التعبيرات والعمليات](../language/expressions.md) — أمثلة استعمال.")
    out.append("- [الأنواع المدمجة](types.md) — الأنواع الاختياريّة `T؟` وأمان العدم.")
    return "\n".join(out) + "\n"


# ── توليد types.md ───────────────────────────────────────────────────────────
def gen_types(src_dir: Path) -> str:
    kw = load_yaml(src_dir / "language-truth" / "keywords.yaml")
    builtin = kw["categories"]["builtin_types"]["keywords"]
    # إثراء الأوصاف من types.yaml عبر مطابقة الكلمة العربيّة
    desc_by_word = {}
    types_path = src_dir / "language-truth" / "types.yaml"
    if types_path.exists():
        for t in load_yaml(types_path).get("types", []):
            if "word" in t and t.get("description_ar"):
                desc_by_word[t["word"]] = t["description_ar"]

    cat_ar = {
        "numeric": "عدديّ", "text": "نصّيّ", "logic": "منطقيّ",
        "special": "خاصّ", "composite": "مركّب",
    }
    out = [BANNER.format(src="keywords.yaml (builtin_types) + types.yaml"),
           "# الأنواع المدمجة\n"]
    out.append(
        f"تُقدّم لغة ص **{len(builtin)} أنواع مدمجة**. أسماؤها يُصدرها المعجمي "
        "**مُعرِّفات** (لا كلمات محجوزة)، فيجوز استعمالها أسماءً خارج موضع النوع.\n"
    )
    out.append(
        "> **المصدر:** [`language-truth/keywords.yaml`]"
        "(https://github.com/sadlang/s-programming-language/blob/sadlang/language-truth/keywords.yaml)"
        " (فئة `builtin_types`) + "
        "[`types.yaml`]"
        "(https://github.com/sadlang/s-programming-language/blob/sadlang/language-truth/types.yaml).\n"
    )
    out.append("| النوع | الإنجليزيّة | الفئة | الوصف |")
    out.append("|------|-------------|------|-------|")
    for t in builtin:
        word = t["word"]
        cat = cat_ar.get(t.get("subcategory", ""), t.get("subcategory", "—"))
        desc = desc_by_word.get(word, "—")
        out.append(f"| `{md_escape(word)}` | {t['english']} | {cat} | {md_escape(desc)} |")
    out.append("")
    out.append("## القيم الحرفيّة المحجوزة\n")
    out.append("```sad\nمتغير يعمل = صحيح     # true\nمتغير متوقّف = خطأ    # false\nمتغير قيمة = لاشيء    # null\n```\n")
    out.append("## الأنواع الاختياريّة وأمان العدم\n")
    out.append(
        "يُكتب النوع الاختياريّ باللاحقة `؟` (العربيّة، U+061F) ليقبل القيمة أو "
        "`لاشيء`، ويُعالَج بعوامل `؟.` و`؟؟` و`مؤكد`:\n"
    )
    out.append("```sad\nمتغير الوسط: نص؟ = لاشيء\nمتغير الطول = الوسط؟.الطول\nمتغير قيمة = الوسط ؟؟ \"مجهول\"\n```\n")
    out.append("راجع [العوامل والأسبقيّة](operators.md) لعوامل أمان العدم.")
    return "\n".join(out) + "\n"


GENERATORS = {
    "keywords.md": gen_keywords,
    "operators.md": gen_operators,
    "types.md": gen_types,
}


def main() -> int:
    ap = argparse.ArgumentParser(description="مولّد صفحات المرجع من language-truth/")
    ap.add_argument("--source-dir", required=True,
                    help="جذر مستودع لغة ص (يحوي language-truth/)")
    ap.add_argument("--out-dir", default="src/reference",
                    help="مجلّد إخراج صفحات المرجع")
    ap.add_argument("--check", action="store_true",
                    help="لا يكتب؛ يفشل إن اختلف المُولَّد عن الموجود (لفحص CI)")
    args = ap.parse_args()

    src_dir = Path(args.source_dir)
    out_dir = Path(args.out_dir)
    lt = src_dir / "language-truth"
    if not lt.is_dir():
        sys.exit(f"خطأ: لم يُعثر على {lt} — تحقّق من --source-dir")

    drift = False
    for name, fn in GENERATORS.items():
        content = fn(src_dir)
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
