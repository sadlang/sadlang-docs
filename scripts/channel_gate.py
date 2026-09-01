#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# (AR) بوّابة القناة: تجعل وعدَ «المستقرّ لا يرى الميزات غير المنشورة» **مقيسًا**.
#
# المشكلة التي يعالجها هذا الملفّ:
#   deploy.yml يجلب مستودع التوثيق **مرّة واحدة** (من main) ويبني منه قناتين
#   بـlanguage-truth مختلف. فالقناتان تختلفان في أربع صفحاتٍ مُولَّدة فقط،
#   ويتطابق نثرُهما (٢٢ صفحة) حرفيًّا. أيّ فصلٍ نثريٍّ يوثّق ميزةً على dev وحدها
#   كان يظهر للمستخدم في القناة المستقرّة. الوعد كان أوسع من البنية.
#
# الثابت المقيس:
#   بناءُ القناة المستقرّة لا يحوي رمزًا غائبًا عن SoT المستقرّ.
#
# آليّتان:
#   --strip  : يجرّد كتل «القادم» من النثر قبل بناء القناة المستقرّة.
#              الصيغة (تعليقات HTML، فلا تُرى محلّيًّا ولا تكسر أيّ محرّر):
#                  <!-- قادم:بداية -->
#                  نصّ لا يظهر إلّا في /next/
#                  <!-- قادم:نهاية -->
#   --guard  : يشتقّ قائمة المراقبة = (رموز dev − رموز sadlang) من SoT نفسه،
#              ثمّ يمسح النثر عنها بحدود كلمة. قائمةٌ **مُشتقّة** لا مكتوبة:
#              القائمة المكتوبة بيدٍ تتعفّن في الاتّجاهين.
#
# حدود مقصودة (تُذكر ولا تُخفى):
#   • المقيس **معرِّفات** (كلمات/أنواع) لا رموز العوامل: رمزٌ مثل «؟.» ليس كلمة،
#     ومطابقته النصّيّة تُنتج ضجيجًا. فرق العوامل بين القناتين يظهر في صفحة
#     operators.md المُولَّدة أصلًا، وهي صحيحةٌ لكلّ قناة بالبناء.
#   • يُمسح النثر تحت src/ دون src/reference/ — تلك مُولَّدةٌ من SoT قناتِها.
#
# الاستعمال:
#   python scripts/channel_gate.py --channel sadlang --strip --guard
#   python scripts/channel_gate.py --channel dev --strip
# ============================================================================
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_reference import fetch_sot, load_yaml  # noqa: E402

BEGIN = "<!-- قادم:بداية -->"
END = "<!-- قادم:نهاية -->"

STABLE_REF = "sadlang"
NEXT_REF = "dev"

# حدود الكلمة: حرفٌ عربيّ أو لاتينيّ أو رقمٌ قبلها/بعدها يعني أنّها جزءُ كلمةٍ
# أخرى لا الرمزَ نفسه. مقيس: «الطبيعيّ» في فصل الاستيعابات كان يُطابق «طبيعي»
# مطابقةً كاذبة بلا هذه الحدود — والتشكيل اللاحق يُعدّ من الكلمة.
_LETTER = r"\wء-ي٠-٩"
_TRAIL = _LETTER + r"ً-ْٰ"


def word_pattern(word: str) -> re.Pattern:
    return re.compile(
        "(?<![" + _LETTER + "])" + re.escape(word) + "(?![" + _TRAIL + "])"
    )


def strip_next_blocks(text: str, channel: str) -> str:
    """يحذف كتل «القادم» في القناة المستقرّة، ويرفع علاماتها في القادمة."""
    if channel == STABLE_REF:
        pattern = re.compile(
            re.escape(BEGIN) + r".*?" + re.escape(END), re.DOTALL
        )
        return pattern.sub("", text)
    return text.replace(BEGIN, "").replace(END, "")


def sot_words(src_dir: Path) -> set:
    """كلّ المعرّفات المعرَّفة في keywords.yaml (بكلّ فئاتها وبدائلها)."""
    data = load_yaml(src_dir / "language-truth" / "keywords.yaml")
    words = set()
    for category in data.get("categories", {}).values():
        for keyword in category.get("keywords", []) or []:
            if keyword.get("word"):
                words.add(keyword["word"])
            for alias in keyword.get("aliases", []) or []:
                words.add(alias)
    return words


def prose_files(root: Path):
    """صفحات النثر وحدها — صفحات reference/ مُولَّدةٌ من SoT قناتِها."""
    for path in sorted(root.glob("src/**/*.md")):
        if path.parent.name == "reference" or path.name == "SUMMARY.md":
            continue
        yield path


def guard(root: Path) -> int:
    next_words = sot_words(fetch_sot(NEXT_REF))
    stable_words = sot_words(fetch_sot(STABLE_REF))
    watchlist = sorted(next_words - stable_words)

    if not watchlist:
        print("قائمة المراقبة فارغة: القناتان متطابقتان في المعرّفات — لا شيء يُمنع.")
        return 0
    print(f"قائمة المراقبة ({len(watchlist)} معرّفًا في dev دون sadlang): "
          + "، ".join(watchlist))

    patterns = [(word, word_pattern(word)) for word in watchlist]
    hits = []
    for path in prose_files(root):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for word, pattern in patterns:
                if pattern.search(line):
                    hits.append((path, lineno, word, line.strip()))

    if hits:
        print("\nبوّابة القناة: نثرٌ يذكر ميزةً غير منشورة في القناة المستقرّة.")
        for path, lineno, word, line in hits:
            print(f"  ✗ {path}:{lineno} «{word}» — {line[:90]}")
        print("\nالعلاج: لُفّ الفقرة بكتلة القادم:")
        print(f"  {BEGIN}\n  ...\n  {END}")
        return 1

    print("✓ لا نثرَ يذكر ميزةً غائبةً عن القناة المستقرّة.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="بوّابة القناة للتوثيق")
    ap.add_argument("--channel", required=True, choices=[STABLE_REF, NEXT_REF])
    ap.add_argument("--strip", action="store_true",
                    help="عالِج كتل «القادم» في النثر (تعديلٌ في المكان)")
    ap.add_argument("--guard", action="store_true",
                    help="امنع ذكرَ معرّفٍ غائبٍ عن SoT المستقرّ (يجلب القناتين)")
    ap.add_argument("--root", default=".", help="جذر مستودع التوثيق")
    args = ap.parse_args()

    if not (args.strip or args.guard):
        ap.error("لا عمل: مرّر --strip أو --guard أو كليهما.")

    root = Path(args.root)
    if args.strip:
        touched = 0
        for path in prose_files(root):
            original = path.read_text(encoding="utf-8")
            stripped = strip_next_blocks(original, args.channel)
            if stripped != original:
                path.write_text(stripped, encoding="utf-8")
                touched += 1
        print(f"كتل «القادم»: عولجت في {touched} ملفًّا (القناة: {args.channel}).")

    if args.guard:
        if args.channel != STABLE_REF:
            print("لا حراسة على القناة القادمة — هي موضع الميزات غير المنشورة.")
            return 0
        return guard(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
