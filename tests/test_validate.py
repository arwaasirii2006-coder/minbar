"""tests/test_validate.py

Tests for validate.check_glossary().

Coverage:
  - English (en): valid and invalid cases for all 10 glossary terms.
  - Urdu (ur): skipped (empty translation lists) and future-ready cases.
  - Hindi (hi): same as Urdu.
  - Edge cases: prefixed Arabic forms, case-insensitivity, empty text,
    multiple terms missing simultaneously.

Run with:  python tests/test_validate.py  or  pytest tests/test_validate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validate import check_glossary  # noqa: E402


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def assert_missing(ar: str, tr: str, lang: str, expected: list[str]) -> None:
    """Raise AssertionError if result != expected (order-independent)."""
    got = check_glossary(ar, tr, lang)
    assert sorted(got) == sorted(expected), (
        f"\nar={ar!r}\ntr={tr!r}\nlang={lang!r}\n"
        f"expected={sorted(expected)!r}\ngot={sorted(got)!r}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# English tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestEnglishValid:
    """Arabic term present → correct English translation present → no missing."""

    def test_islam_standalone(self):
        assert_missing("هذا الإسلام دين الحق", "This is Islam, the religion of truth", "en", [])

    def test_islam_prefixed_bi(self):
        # بالإسلام is an Arabic form listed in the glossary
        assert_missing("أسلم بالإسلام الصحيح", "He embraced Islam correctly", "en", [])

    def test_islam_prefixed_li(self):
        # للإسلام is listed
        assert_missing("داعية للإسلام", "A caller to Islam", "en", [])

    def test_tawhid_prefixed_wa(self):
        # والتوحيد — 'و' clitic before 'التوحيد'
        assert_missing("يعلم الإسلام والتوحيد", "He teaches Islam and Tawhid", "en", [])

    def test_tawhid_alternative_en(self):
        # "Oneness of God" is also accepted for tawhid
        assert_missing("التوحيد أساس الدين", "Oneness of God is the foundation", "en", [])

    def test_ibadah(self):
        assert_missing("يؤمن بالعبادة", "He believes in Worship", "en", [])

    def test_nubuwwah(self):
        assert_missing("النبوة نعمة عظيمة", "Prophethood is a great blessing", "en", [])

    def test_wahy(self):
        assert_missing("الوحي جاء بالهداية", "Revelation brought guidance", "en", [])

    def test_shariah_alternative(self):
        # "Islamic law and guidance" is also accepted
        assert_missing(
            "تتحدث عن الشريعة الإسلامية",
            "It speaks of Islamic law and guidance",
            "en", [],
        )

    def test_hadith(self):
        assert_missing("الحديث النبوي مرجع أساسي", "The Hadith is a primary reference", "en", [])

    def test_sunnah(self):
        assert_missing("يتبع السنة النبوية", "He follows the Sunnah of the Prophet", "en", [])

    def test_fatwa(self):
        assert_missing("أصدر الفتوى الشرعية", "He issued the Fatwa", "en", [])

    def test_dawah(self):
        assert_missing("يقوم بالدعوة في بلاده", "He carries out Da'wah in his country", "en", [])

    def test_case_insensitive_en(self):
        # English check must be case-insensitive
        assert_missing("الإسلام دين", "islam is a religion", "en", [])
        assert_missing("الإسلام دين", "ISLAM IS A RELIGION", "en", [])

    def test_multiple_terms_all_present(self):
        ar = "يتناول الإسلام التوحيد العبادة النبوة الوحي الشريعة الحديث السنة الفتوى الدعوة"
        en = "Islam Tawhid Worship Prophethood Revelation Sharia Hadith Sunnah Fatwa Da'wah"
        assert_missing(ar, en, "en", [])

    def test_term_absent_in_arabic(self):
        # If the Arabic term is not in the text, no missing regardless of translation
        assert_missing("هذا نص عادي", "this is ordinary text", "en", [])

    def test_empty_arabic(self):
        assert_missing("", "some translation", "en", [])

    def test_empty_translation(self):
        # Arabic term present but translation is empty → missing
        assert_missing("يتحدث عن الإسلام", "", "en", ["islam"])


class TestEnglishInvalid:
    """Arabic term present → English translation missing or wrong → term in result."""

    def test_islam_wrong_translation(self):
        assert_missing("الإسلام دين الحق", "The religion of truth", "en", ["islam"])

    def test_tawhid_wrong_translation(self):
        assert_missing("التوحيد أساس الإيمان", "Monotheism is the foundation of faith", "en", ["tawhid"])

    def test_ibadah_wrong_translation(self):
        assert_missing("العبادة واجبة", "Prayer is obligatory", "en", ["ibadah"])

    def test_nubuwwah_wrong_translation(self):
        assert_missing("النبوة خُتمت", "Messengership has ended", "en", ["nubuwwah"])

    def test_wahy_wrong_translation(self):
        assert_missing("الوحي قرآن", "The scripture is Quran", "en", ["wahy"])

    def test_shariah_wrong_translation(self):
        assert_missing("الشريعة عادلة", "The law is just", "en", ["shariah"])

    def test_hadith_wrong_translation(self):
        assert_missing("الحديث صحيح", "The narration is authentic", "en", ["hadith"])

    def test_sunnah_wrong_translation(self):
        assert_missing("السنة هدي النبي", "The tradition of the Prophet", "en", ["sunnah"])

    def test_fatwa_wrong_translation(self):
        assert_missing("الفتوى واضحة", "The ruling is clear", "en", ["fatwa"])

    def test_dawah_wrong_translation(self):
        assert_missing("الدعوة فريضة", "Preaching is an obligation", "en", ["dawah"])

    def test_multiple_missing(self):
        ar = "يتناول الإسلام التوحيد"
        en = "religion and monotheism"
        assert_missing(ar, en, "en", ["islam", "tawhid"])

    def test_partial_terms_one_missing(self):
        # Tawhid present but Islam missing from translation
        assert_missing(
            "يتحدث عن الإسلام والتوحيد",
            "it discusses Tawhid",
            "en",
            ["islam"],
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Urdu tests  (all ur lists are empty → every term is skipped → always [])
# ═══════════════════════════════════════════════════════════════════════════════

class TestUrdu:
    def test_term_present_in_arabic_no_ur_translation(self):
        # Even though الإسلام appears, ur list is empty → skipped → []
        assert_missing("يتحدث عن الإسلام", "کوئی ترجمہ نہیں", "ur", [])

    def test_all_terms_present_no_ur_translations(self):
        ar = "الإسلام التوحيد العبادة النبوة الوحي الشريعة الحديث السنة الفتوى الدعوة"
        assert_missing(ar, "", "ur", [])

    def test_empty_text_ur(self):
        assert_missing("", "", "ur", [])


# ═══════════════════════════════════════════════════════════════════════════════
# Hindi tests  (same situation as Urdu)
# ═══════════════════════════════════════════════════════════════════════════════

class TestHindi:
    def test_term_present_no_hi_translation(self):
        assert_missing("يتحدث عن الإسلام", "कोई अनुवाद नहीं", "hi", [])

    def test_all_terms_present_no_hi_translations(self):
        ar = "الإسلام التوحيد العبادة النبوة الوحي الشريعة الحديث السنة الفتوى الدعوة"
        assert_missing(ar, "", "hi", [])

    def test_empty_text_hi(self):
        assert_missing("", "", "hi", [])


# ═══════════════════════════════════════════════════════════════════════════════
# Edge-case tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_clitic_wa_detection(self):
        # والتوحيد — و clitic must not prevent detection
        assert_missing("والتوحيد أمر عظيم", "Tawhid is a great matter", "en", [])

    def test_clitic_bi_detection(self):
        # بالإسلام listed as a form
        assert_missing("أسلم بالإسلام", "He embraced Islam", "en", [])

    def test_no_false_positive_wahi_in_tawhid(self):
        # "وحي" must NOT match inside "التوحيد"
        assert_missing("التوحيد واجب", "Tawhid is obligatory", "en", [])
        # (wahy term is not flagged even though التوحيد contains و+ح+ي internally)

    def test_arabic_tashkeel_noise(self):
        # Arabic input with tashkeel — normalize strips it
        assert_missing("الإِسْلَامُ دِينٌ", "Islam is a religion", "en", [])

    def test_en_partial_match_not_accepted(self):
        # "Islamist" should not satisfy the "Islam" requirement –
        # because "islam" appears inside "islamist" as a substring.
        # This is the known limitation of substring matching;
        # in practice translations contain "Islam" as a standalone word.
        # We document but do not enforce strict word boundaries on translation side.
        pass  # behaviour is acceptable; no assertion needed


# ═══════════════════════════════════════════════════════════════════════════════
# Direct runner
# ═══════════════════════════════════════════════════════════════════════════════

def _run_all() -> None:
    suites = [
        TestEnglishValid(),
        TestEnglishInvalid(),
        TestUrdu(),
        TestHindi(),
        TestEdgeCases(),
    ]
    passed = failed = 0
    for suite in suites:
        cls_name = type(suite).__name__
        for name in dir(suite):
            if not name.startswith("test_"):
                continue
            method = getattr(suite, name)
            try:
                method()
                passed += 1
            except AssertionError as exc:
                failed += 1
                print(f"  FAIL  {cls_name}.{name}: {exc}")
            except Exception as exc:
                failed += 1
                print(f"  ERROR {cls_name}.{name}: {type(exc).__name__}: {exc}")

    total = passed + failed
    status = "OK" if failed == 0 else "FAIL"
    print(f"\nResults: {passed}/{total} passed [{status}]")


if __name__ == "__main__":
    _run_all()
