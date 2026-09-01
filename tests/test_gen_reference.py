#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# (AR) اختبارات ذهبيّة لمولّد صفحات المرجع.
#
# لماذا «ذهبيّة» ولمَ لا تكفي `--check`:
#   `--check` يقارن مخرج المولّد بمخرج المولّد نفسه من مصدرٍ **متحرّك** — طرفاه
#   من أصلٍ واحد. لو انحدر المولّد ثمّ أُعيد التوليد، مرّ أخضرَ وانتشر الانحدار
#   إلى الصفحات المنشورة. هنا الطرف الأوّل **مُجمَّد**: لقطة SoT مودَعة تحت
#   tests/fixtures/، ومخرجها المتوقَّع تحت tests/golden/. فما يُقاس هو المولّد
#   وحده، لا الاتّفاق بينه وبين نفسه.
#
# التشغيل:  python -m unittest discover -s tests -v
#
# تحديث الذهبيّ (عمدًا فقط، ويُراجَع في الـPR سطرًا سطرًا):
#   python scripts/gen_reference.py --source-dir tests/fixtures/sot-dev-1138f5e1 \
#          --source-ref dev --out-dir tests/golden/dev
# ============================================================================
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gen_reference  # noqa: E402

BS = chr(92)  # الشرطة المائلة — تُكتب هكذا لتجنّب تحذير الهروب غير الصالح

# (اسم القناة، مجلّد اللقطة المجمَّدة) — القناتان معًا: النشر يبني الاثنتين،
# فلا يجوز أن يُقاس المولّد على واحدةٍ فقط.
CHANNELS = [
    ("dev", "sot-dev-1138f5e1"),
    ("sadlang", "sot-sadlang-b40c7bfa"),
]
PAGES = sorted(gen_reference.GENERATORS)


class GoldenTest(unittest.TestCase):
    """المولّد على لقطةٍ مجمَّدة يُنتج الذهبيّ حرفًا بحرف."""

    def test_pages_match_golden(self):
        for channel, fixture in CHANNELS:
            src = ROOT / "tests" / "fixtures" / fixture
            self.assertTrue(
                (src / "language-truth").is_dir(),
                f"اللقطة المجمَّدة غائبة: {src} — الاختبار بلا مُدخَل لا يقيس شيئًا.",
            )
            for page in PAGES:
                with self.subTest(channel=channel, page=page):
                    golden = ROOT / "tests" / "golden" / channel / page
                    self.assertTrue(golden.is_file(), f"الذهبيّ غائب: {golden}")
                    expected = golden.read_text(encoding="utf-8")
                    actual = gen_reference.GENERATORS[page](src, channel)
                    self.assertEqual(
                        expected, actual,
                        f"انحدار في المولّد: {page} على القناة {channel} خالف الذهبيّ.",
                    )


class GuardTest(unittest.TestCase):
    """حرّاس على الاختبار نفسه: أخضرُ لا يكفي إن كان الشرط لا يمكن أن يكذب."""

    def test_generators_registry_is_not_empty(self):
        # لو أفرغ أحدهم GENERATORS لمرّ اختبار الذهبيّ أخضرَ بلا صفحةٍ واحدة.
        self.assertEqual(len(PAGES), 6, f"عدد الصفحات المولَّدة تغيّر: {PAGES}")

    def test_golden_files_are_substantial(self):
        # ذهبيٌّ فارغٌ يطابق مخرجًا فارغًا — نمنع هذا الأخضر الكاذب.
        for channel, _ in CHANNELS:
            for page in PAGES:
                golden = ROOT / "tests" / "golden" / channel / page
                with self.subTest(channel=channel, page=page):
                    self.assertGreater(len(golden.read_text(encoding="utf-8")), 500)

    def test_channels_actually_differ(self):
        # القناتان يجب أن تختلفا فعلًا، وإلّا فاللقطتان نسخةٌ واحدة والمصفوفة وهمٌ.
        dev = (ROOT / "tests" / "golden" / "dev" / "types.md").read_text(encoding="utf-8")
        stable = (ROOT / "tests" / "golden" / "sadlang" / "types.md").read_text(encoding="utf-8")
        self.assertNotEqual(dev, stable, "لقطتا القناتين متطابقتان — جمّد لقطتين مختلفتين.")


class VerifyGuardTest(unittest.TestCase):
    """حارس --verify: يمنع نشر جذاذةٍ يُنشئها mdBook مكان صفحةٍ لم تُولَّد.

    الواقعة المقيسة: mdBook لا يفشل على ملفٍّ غائبٍ مذكورٍ في SUMMARY — يُنشئ
    ملفًّا من العنوان وحده (~32 بايتًا) ويبني بنجاح. فبلا هذا الحارس ينشر
    deploy.yml أربع صفحات مرجعٍ بيضاء بصمت.
    """

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.out = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def _fill(self, **overrides):
        """يملأ مجلّدًا بصفحاتٍ سليمة، ثمّ يطبّق ما يُطلب من إفساد."""
        for page in PAGES:
            (self.out / page).write_text(
                gen_reference.MARKER + "\n" + "س" * gen_reference.MIN_PAGE_BYTES,
                encoding="utf-8",
            )
        for page, content in overrides.items():
            target = self.out / page
            if content is None:
                target.unlink()
            else:
                target.write_text(content, encoding="utf-8")

    def test_healthy_pages_pass(self):
        self._fill()
        self.assertEqual(0, gen_reference.verify(self.out))

    def test_missing_page_fails(self):
        self._fill(**{"types.md": None})
        self.assertEqual(1, gen_reference.verify(self.out))

    def test_mdbook_stub_fails(self):
        # هذه حرفيًّا الجذاذة التي رُصدت: عنوانٌ وحده.
        self._fill(**{"types.md": "# الأنواع المدمجة\n"})
        self.assertEqual(1, gen_reference.verify(self.out))

    def test_page_without_banner_fails(self):
        self._fill(**{"operators.md": "ص" * (gen_reference.MIN_PAGE_BYTES * 2)})
        self.assertEqual(1, gen_reference.verify(self.out))

    def test_generated_pages_carry_the_marker(self):
        # لو غيّر أحدهم نصّ اللافتة في المولّد لصار الحارس يرفض كلّ صفحةٍ سليمة.
        src = ROOT / "tests" / "fixtures" / CHANNELS[0][1]
        page = gen_reference.GENERATORS["types.md"](src, CHANNELS[0][0])
        self.assertIn(gen_reference.MARKER, page)


class ArabicCountTest(unittest.TestCase):
    """تمييز العدد وصفتُه: «17 أنواع مدمجة» كان صحيحًا مصادفةً عند 9 وحدها."""

    def test_three_to_ten_uses_plural(self):
        self.assertEqual("9 أنواع مدمجة",
                         gen_reference.counted(9, gen_reference.TYPE_FORMS))

    def test_eleven_to_ninetynine_uses_accusative_singular(self):
        self.assertEqual("17 نوعًا مدمجًا",
                         gen_reference.counted(17, gen_reference.TYPE_FORMS))
        self.assertEqual("94 مفتاحًا",
                         gen_reference.counted(94, gen_reference.PROP_FORMS))

    def test_one_and_two_have_their_own_forms(self):
        self.assertEqual("نوع مدمج", gen_reference.counted(1, gen_reference.TYPE_FORMS))
        self.assertEqual("نوعان مدمجان", gen_reference.counted(2, gen_reference.TYPE_FORMS))

    def test_hundred_and_above_uses_singular(self):
        self.assertEqual("100 نوع مدمج",
                         gen_reference.counted(100, gen_reference.TYPE_FORMS))

    def test_every_branch_is_reachable(self):
        # حارس: لو التقت فرعان على صيغةٍ واحدة لصار الاختبار أخضرَ بلا معنى.
        phrases = {gen_reference.counted(n, gen_reference.TYPE_FORMS)
                   for n in (1, 2, 5, 17, 100)}
        self.assertEqual(5, len(phrases))


class EscapingTest(unittest.TestCase):
    """< و> في النثر تُبتلع وسمَ HTML؛ وفي مدى الشيفرة لا تُفكّ الكيانات."""

    def test_prose_escapes_angle_brackets(self):
        # الوصف الحقيقيّ في types.yaml: «مصفوفة<T> ديناميكية».
        self.assertEqual("مصفوفة&lt;T&gt; ديناميكية",
                         gen_reference.md_text("مصفوفة<T> ديناميكية"))

    def test_code_span_keeps_angle_brackets_raw(self):
        # عوامل مثل <= تعيش داخل ` ` — والكيان يظهر حرفيًّا هناك.
        self.assertEqual("<=", gen_reference.md_escape("<="))

    def test_both_escape_the_table_pipe(self):
        self.assertEqual("أ " + BS + "| ب", gen_reference.md_text("أ | ب"))
        self.assertEqual(BS + "|" + BS + "|", gen_reference.md_escape("||"))

    def test_generated_types_page_has_no_raw_tag(self):
        src = ROOT / "tests" / "fixtures" / CHANNELS[0][1]
        page = gen_reference.GENERATORS["types.md"](src, CHANNELS[0][0])
        self.assertIn("مصفوفة&lt;T&gt;", page)
        self.assertNotIn("مصفوفة<T>", page)


class SummarizeTest(unittest.TestCase):
    """الاختصار يُعلَن ولا يُخفى، ولا يمسّ ما يقصر أصلًا."""

    def test_short_text_untouched(self):
        self.assertEqual("طول النص", gen_reference.summarize("طول النص"))

    def test_long_text_is_cut_and_marked(self):
        long_text = "جملةٌ أولى، " * 40
        out = gen_reference.summarize(long_text)
        self.assertLess(len(out), len(long_text))
        self.assertTrue(out.endswith("…"),
                        "الاختصارُ بلا علامةٍ يُقرأ نصًّا كاملًا.")

    def test_cut_stays_within_the_limit(self):
        out = gen_reference.summarize("الأوّل، " + "ح" * 300)
        self.assertLessEqual(len(out), gen_reference.DESC_LIMIT + 2)

    def test_no_table_row_explodes_the_cell(self):
        # قِيس على SoT الحقيقيّ: أطول وصفٍ ٣٧٢٤ محرفًا في خليّةٍ واحدة.
        src = ROOT / "tests" / "fixtures" / CHANNELS[0][1]
        page = gen_reference.GENERATORS["builtins.md"](src, CHANNELS[0][0])
        rows = [line for line in page.splitlines() if line.startswith("| `")]
        self.assertTrue(rows, "صفحة المدمَجات بلا صفوف — المُدخَل لم يُقرأ.")
        widest = max(len(row) for row in rows)
        self.assertLess(widest, 400,
                        f"خليّةٌ بعرض {widest} محرفًا تُفقِد الجدول قابليّة المسح.")


# (AR) مُدخَلٌ صغيرٌ مصنوعٌ في الاختبار: الغرضُ قياسُ **فرعَي الشرط** لا مطابقةُ
#      الواقع. والفرعُ الثاني (بلا سِجِلِّ قياس) ليس افتراضًا: القناةُ المستقرّةُ
#      تسبقُ وصولَ السِّجِلِّ إليها، فيجب أن يُبنى الكتابُ ويُقالَ سببُ الغياب.
_FAKE_BUILTIN = (
    "functions:\n"
    "- canonical: مدمَج_وهميّ\n"
    "  namespace: Core\n"
    "  module: NONE\n"
    "  description_ar: وصف\n"
)
_FAKE_SUPPORT = (
    "measured_commit: abcdef123456\n"
    "counts: {both: 0, interpreter_only: 1, compiler_only: 0, neither: 0}\n"
    "functions:\n"
    "- canonical: مدمَج_وهميّ\n"
    "  compiler: false\n"
    "  interpreter: true\n"
)


class EngineColumnTest(unittest.TestCase):
    """عمودا المحرّكَين مقيسان: يظهران بسِجِلِّ قياس، ويُحذفان بلا سِجِلّ."""

    @staticmethod
    def _make(td: str, with_record: bool) -> Path:
        src = Path(td)
        truth = src / "language-truth"
        (truth / "builtins").mkdir(parents=True)
        (truth / "builtins" / "x.yaml").write_text(_FAKE_BUILTIN, encoding="utf-8")
        if with_record:
            (truth / "_meta").mkdir(parents=True)
            (truth / "_meta" / "builtin_engine_support.yaml").write_text(
                _FAKE_SUPPORT, encoding="utf-8")
        return src

    def test_columns_absent_when_measurement_missing(self):
        with TemporaryDirectory() as td:
            page = gen_reference.GENERATORS["builtins.md"](
                self._make(td, False), "sadlang")
            self.assertNotIn("| المترجّم |", page)
            self.assertIn("غير موجود في هذا الفرع", page)

    def test_columns_present_and_verdict_is_carried_through(self):
        with TemporaryDirectory() as td:
            page = gen_reference.GENERATORS["builtins.md"](
                self._make(td, True), "dev")
            self.assertIn("| المترجّم |", page)
            rows = [line for line in page.splitlines()
                    if line.startswith("| `مدمَج_وهميّ`")]
            self.assertEqual(1, len(rows), "صفُّ المدمَج مفقودٌ أو مكرّر.")
            # الحكمُ يُنقَل كما قِيس، ولا يُقلَب: ❌ للمترجّم و✅ للمفسّر.
            self.assertIn("| ❌ | ✅ |", rows[0])
            self.assertIn("abcdef123456", page)


if __name__ == "__main__":
    unittest.main()
