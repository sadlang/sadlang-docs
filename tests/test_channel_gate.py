#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# (AR) اختبارات بوّابة القناة.
#
# ما تحرسه: وعدُ «القناة المستقرّة لا تُري المستخدم ميزةً غير منشورة». كان
# وعدًا نثريًّا لا يقيسه أحد — والنثر مشتركٌ بين القناتين لأنّ deploy.yml يبني
# فرعًا واحدًا مرّتين. التسرّب كان صفرًا حين قِيس، لكنّه صفرٌ **بالصدفة لا
# بالحراسة**؛ هذه الاختبارات تحرس الآليّة التي تحوّله إلى صفرٍ مبرهَن.
#
# التشغيل:  python -m unittest discover -s tests -v
# ============================================================================
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import channel_gate  # noqa: E402


class WordBoundaryTest(unittest.TestCase):
    """حدود الكلمة — المطابقة الكاذبة التي رُصدت فعليًّا قبل وجود البوّابة."""

    def test_bare_identifier_matches(self):
        pattern = channel_gate.word_pattern("طبيعي")
        self.assertTrue(pattern.search("متغير عدد: طبيعي = ٥"))

    def test_prefixed_word_does_not_match(self):
        # «الترتيب العربيّ الطبيعيّ» في فصل الاستيعابات: مطابقةٌ كاذبة بلا حدود.
        pattern = channel_gate.word_pattern("طبيعي")
        self.assertIsNone(pattern.search("تتبع لغة ص الترتيب العربيّ الطبيعيّ:"))

    def test_trailing_tashkeel_does_not_match(self):
        pattern = channel_gate.word_pattern("طبيعي")
        self.assertIsNone(pattern.search("العدد طبيعيّة هنا"))

    def test_digit_suffixed_identifier_is_distinct(self):
        # «طبيعي» يجب ألّا يُطابق داخل «طبيعي32» وإلّا صار الإبلاغ مضاعفًا مضلّلًا.
        self.assertIsNone(channel_gate.word_pattern("طبيعي").search("طبيعي32"))
        self.assertTrue(channel_gate.word_pattern("طبيعي32").search("نوعه طبيعي32."))


class StripTest(unittest.TestCase):
    """تجريد كتل «القادم»: تُحذف في المستقرّ، ويبقى محتواها في القادم."""

    SAMPLE = (
        "مقدّمة تظهر في القناتين.\n"
        + channel_gate.BEGIN
        + "\nنصّ خاصّ بالقناة القادمة.\n"
        + channel_gate.END
        + "\nخاتمة تظهر في القناتين.\n"
    )

    def test_stable_drops_the_block(self):
        out = channel_gate.strip_next_blocks(self.SAMPLE, channel_gate.STABLE_REF)
        self.assertNotIn("خاصّ بالقناة القادمة", out)
        self.assertIn("مقدّمة", out)
        self.assertIn("خاتمة", out)

    def test_next_keeps_content_and_drops_markers(self):
        out = channel_gate.strip_next_blocks(self.SAMPLE, channel_gate.NEXT_REF)
        self.assertIn("خاصّ بالقناة القادمة", out)
        self.assertNotIn(channel_gate.BEGIN, out)
        self.assertNotIn(channel_gate.END, out)

    def test_multiple_blocks(self):
        doubled = self.SAMPLE + self.SAMPLE
        out = channel_gate.strip_next_blocks(doubled, channel_gate.STABLE_REF)
        self.assertNotIn("خاصّ بالقناة القادمة", out)

    def test_text_without_blocks_is_untouched(self):
        plain = "فقرةٌ بلا كتلٍ إطلاقًا.\n"
        for channel in (channel_gate.STABLE_REF, channel_gate.NEXT_REF):
            self.assertEqual(plain, channel_gate.strip_next_blocks(plain, channel))


class WatchlistTest(unittest.TestCase):
    """القائمة تُشتقّ من SoT ولا تُكتب بيد — تُقاس على اللقطتين المجمَّدتين."""

    DEV = ROOT / "tests" / "fixtures" / "sot-dev-1138f5e1"
    STABLE = ROOT / "tests" / "fixtures" / "sot-sadlang-b40c7bfa"

    def test_watchlist_is_non_empty_on_frozen_snapshots(self):
        # لو صار الفرق فارغًا لصارت البوّابة خضراء لأنّها لا تستطيع أن تحمرّ.
        extra = channel_gate.sot_words(self.DEV) - channel_gate.sot_words(self.STABLE)
        self.assertTrue(extra, "لا فرق بين اللقطتين — البوّابة بلا شيءٍ تمنعه.")

    def test_known_dev_only_type_is_watched(self):
        extra = channel_gate.sot_words(self.DEV) - channel_gate.sot_words(self.STABLE)
        self.assertIn("طبيعي32", extra)

    def test_shared_word_is_not_watched(self):
        extra = channel_gate.sot_words(self.DEV) - channel_gate.sot_words(self.STABLE)
        self.assertNotIn("رقم", extra)

    def test_aliases_are_collected(self):
        # البدائل معرّفاتٌ صالحة في الشيفرة، فإغفالها ثغرةٌ في القائمة.
        words = channel_gate.sot_words(self.DEV)
        self.assertGreater(len(words), 80, f"عدد المعرّفات صغير مريب: {len(words)}")


class ProseScanTest(unittest.TestCase):
    """المسح يشمل النثر ويستثني الصفحات المُولَّدة (فهي صحيحةٌ لكلّ قناة بالبناء)."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "src" / "language").mkdir(parents=True)
        (self.root / "src" / "reference").mkdir(parents=True)
        self.addCleanup(self.tmp.cleanup)

    def test_reference_and_summary_are_excluded(self):
        (self.root / "src" / "language" / "types.md").write_text("نثر", encoding="utf-8")
        (self.root / "src" / "reference" / "types.md").write_text("مُولَّد", encoding="utf-8")
        (self.root / "src" / "SUMMARY.md").write_text("فهرس", encoding="utf-8")
        found = {p.name for p in channel_gate.prose_files(self.root)}
        self.assertEqual({"types.md"}, found)
        self.assertEqual(
            1, len(list(channel_gate.prose_files(self.root))),
            "صفحةُ reference/ أو SUMMARY تسرّبت إلى المسح.",
        )


if __name__ == "__main__":
    unittest.main()
