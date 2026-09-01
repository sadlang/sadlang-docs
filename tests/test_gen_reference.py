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
        self.assertEqual(len(PAGES), 4, f"عدد الصفحات المولَّدة تغيّر: {PAGES}")

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


if __name__ == "__main__":
    unittest.main()
