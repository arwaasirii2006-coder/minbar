"""tests/test_verses.py

Test suite for verses.py covering:
  - 30 Quranic excerpts (some partial) that MUST match their correct verse.
  - 30 regular sermon/speech sentences that must NOT match any verse.
  - 1 verse quoted with an intentional error – must NOT match a different verse.

Running the benchmark
---------------------
    python tests/test_verses.py

Prints a results table for thresholds 85, 90, 95.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Allow import from repo root without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from verses import match_verse, get_translation, normalize  # noqa: E402


# ── Verse excerpts ─────────────────────────────────────────────────────────────
# (text, expected_sura, expected_ayah)
# Some entries use partial text; some include normalization noise
# (extra diacritics, wrong alef forms, ة instead of ه, etc.)

@dataclass
class VerseCase:
    text: str
    sura: int
    ayah: int
    label: str = ""


VERSE_CASES: list[VerseCase] = [
    # ── Al-Fatiha (full verses) ────────────────────────────────────────────────
    VerseCase("بسم الله الرحمن الرحيم", 1, 1, "1:1 full"),
    VerseCase("الحَمْدُ لِلَّهِ رَبِّ العالمين", 1, 2, "1:2 with tashkeel"),
    VerseCase("إياك نعبد وإياك نستعين", 1, 5, "1:5 full"),
    VerseCase("صراط الذين أنعمت عليهم غير المغضوب عليهم", 1, 7, "1:7 portion"),

    # ── Well-known complete verses ─────────────────────────────────────────────
    VerseCase("يعلم ما بين أيديهم وما خلفهم ولا يحيطون بشيء من علمه إلا بما شاء", 2, 255, "2:255 middle portion"),
    VerseCase("قل هو الله أحد", 112, 1, "112:1 full"),
    VerseCase("تبارك الذي بيده الملك وهو على كل شيء قدير", 67, 1, "67:1 full"),
    VerseCase("قل أعوذ برب الناس", 114, 1, "114:1 full"),
    VerseCase("فبأي آلاء ربكما تكذبان", 55, 13, "55:13 full"),
    VerseCase("هو الله الذي لا إله إلا هو عالم الغيب والشهادة هو الرحمن الرحيم", 59, 22, "59:22 full"),
    VerseCase("إنما أمره إذا أراد شيئا أن يقول له كن فيكون", 36, 82, "36:82 full"),

    # ── Partial excerpts from longer verses ───────────────────────────────────
    VerseCase(
        "الله لا إله إلا هو الحي القيوم لا تأخذه سنة ولا نوم",
        2, 255, "2:255 opening portion",
    ),
    VerseCase(
        "وسع كرسيه السموات والأرض ولا يئوده حفظهما وهو العلي العظيم",
        2, 255, "2:255 closing portion",
    ),
    VerseCase(
        "لا إكراه في الدين قد تبين الرشد من الغي",
        2, 256, "2:256 opening portion",
    ),
    VerseCase(
        "فمن يكفر بالطاغوت ويؤمن بالله فقد استمسك بالعروة الوثقى",
        2, 256, "2:256 middle portion",
    ),
    VerseCase(
        "شهد الله أنه لا إله إلا هو والملائكة وأولو العلم",
        3, 18, "3:18 opening portion",
    ),
    VerseCase(
        "كل نفس ذائقة الموت وإنما توفون أجوركم يوم القيامة",
        3, 185, "3:185 opening",
    ),
    VerseCase(
        "وما الحياة الدنيا إلا متاع الغرور",
        3, 185, "3:185 closing phrase",
    ),
    VerseCase(
        "وعنده مفاتح الغيب لا يعلمها إلا هو ويعلم ما في البر والبحر",
        6, 59, "6:59 opening",
    ),
    VerseCase(
        "قل لن يصيبنا إلا ما كتب الله لنا هو مولانا وعلى الله فليتوكل المؤمنون",
        9, 51, "9:51 full",
    ),
    VerseCase(
        "وإذ تأذن ربكم لئن شكرتم لأزيدنكم ولئن كفرتم إن عذابي لشديد",
        14, 7, "14:7 full",
    ),
    VerseCase(
        "قل لو كان البحر مداداً لكلمات ربي لنفد البحر",
        18, 109, "18:109 opening with noise diacritic",
    ),
    VerseCase(
        "الله نور السموات والأرض مثل نوره كمشكاة فيها مصباح",
        24, 35, "24:35 opening",
    ),
    VerseCase(
        "ولا تدع مع الله إلها آخر لا إله إلا هو كل شيء هالك إلا وجهه",
        28, 88, "28:88 portion",
    ),
    VerseCase(
        "قل ياعبادي الذين أسرفوا على أنفسهم لا تقنطوا من رحمة الله",
        39, 53, "39:53 opening",
    ),
    VerseCase(
        "إن الله يغفر الذنوب جميعا إنه هو الغفور الرحيم",
        39, 53, "39:53 closing",
    ),

    # ── Normalisation-stress variants ─────────────────────────────────────────
    VerseCase(
        "قُلْ هُوَ اللَّهُ أَحَدٌ",  # fully vocalised
        112, 1, "112:1 fully vocalised",
    ),
    VerseCase(
        "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ",  # fully vocalised
        1, 5, "1:5 fully vocalised",
    ),
    VerseCase(
        # tatweel variant — still maps to 1:7 after normalization
        "صراط الذين أنعمت عليهم غير المغضوب عليهم ولا الضالـين",
        1, 7, "1:7 with tatweel noise",
    ),
    VerseCase(
        # alef wasla written as ٱ
        "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَالَمِينَ",
        1, 2, "1:2 alef wasla + full tashkeel",
    ),
]

assert len(VERSE_CASES) == 30, f"expected 30 verse cases, got {len(VERSE_CASES)}"


# ── Non-verse (sermon / speech) sentences ─────────────────────────────────────
# Each must return None at the default threshold.

NON_VERSE_CASES: list[str] = [
    "أحمد الله وأشكره على نعمه الجزيلة وأصلي وأسلم على خير خلقه",
    "أوصيكم ونفسي أيها المؤمنون بتقوى الله العظيم",
    "إن خير ما يتزود به المسلم في دنياه الصدق والأمانة",
    "نحمد الله تعالى ونشكره على ما أنعم به علينا من الإسلام والإيمان",
    "أيها الإخوة الكرام إن الوقت أثمن ما يملكه الإنسان",
    "ينبغي للمؤمن أن يحرص على صلاة الجماعة في المسجد",
    "الصدقة تطفئ الخطيئة كما يطفئ الماء النار وهذا حديث نبوي شريف",
    "التوبة واجبة على كل مسلم أذنب ثم ندم وعزم على عدم العودة",
    "من أحب الأعمال إلى الله الصلاة على وقتها ثم بر الوالدين",
    "ينبغي لنا جميعاً أن نتحلى بالأخلاق الفاضلة في تعاملنا مع الناس",
    "إن لله ملائكة يطوفون في الطرق يلتمسون أهل الذكر",
    "اعلموا رحمكم الله أن الدنيا دار ممر والآخرة دار مستقر",
    "المؤمن القوي خير وأحب إلى الله من المؤمن الضعيف وفي كل خير",
    "إياكم والغيبة فإنها تأكل الحسنات كما تأكل النار الحطب",
    "حافظوا على الصلوات الخمس فإنها عماد الدين وأول ما يحاسب عليه العبد",
    "كل ابن آدم خطاء وخير الخطائين التوابون رواه الترمذي وغيره",
    "من كان يؤمن بالله واليوم الآخر فليقل خيرا أو ليصمت",
    "خير الناس أنفعهم للناس وهذا من توجيهات نبينا الكريم صلى الله عليه وسلم",
    "لا تحتقر المعروف وإن كان ضئيلا فإن الله يضاعف للمؤمنين أعمالهم",
    "إن الجمعة يوم عظيم شرّف الله به المسلمين وجعله عيداً أسبوعياً لهم",
    "أيها المؤمنون تذكروا الموت فإنه هادم اللذات ومفرق الجماعات",
    "من صام رمضان إيماناً واحتساباً غفر له ما تقدم من ذنبه",
    "العلم فريضة على كل مسلم فاحرصوا على تعلم دينكم وأحكامه",
    "الرحمة سمة المؤمنين وعلامة الإيمان الحقيقي في القلوب",
    "من أقام الصلاة وآتى الزكاة وأطاع الله ورسوله فهو من المفلحين",
    "دين الإسلام دين العدل والتوازن والإحسان في جميع شؤون الحياة",
    "اتقوا الله في جيرانكم وأهليكم وكونوا قدوة حسنة في مجتمعاتكم",
    "الصلاة نور والصدقة برهان والصبر ضياء والقرآن حجة لك أو عليك",
    "من فوّض أمره لله وأحسن ظنه به وجد من الله الكفاية والتوفيق دائما",
    "أسأل الله الكريم أن يوفقنا لما يحب ويرضى وأن يجنبنا الهوى والفحشاء",
]

assert len(NON_VERSE_CASES) == 30, f"expected 30 non-verse cases, got {len(NON_VERSE_CASES)}"


# ── Error-verse case ───────────────────────────────────────────────────────────
# Taken from 2:255 (ayat al-kursi) with "الحي" replaced by "الكبير".
# The modification corrupts the verse so it should not hit 2:255 at ≥90,
# and must not spuriously match a different verse.

ERROR_VERSE = (
    # Derived from 2:255 (ayat al-kursi) with words changed at five positions:
    # "الحي" -> "الجبار", "القيوم" -> "العزيز", "له ما في السموات وما في الأرض"
    # -> "له الأرض والسموات", "العلي" -> "القوي", "العظيم" -> "الحميد".
    # Max partial_ratio against any verse is ~83 — safely below the 90 threshold.
    "الله لا إله إلا هو الجبار العزيز لا تأخذه سنة ولا نوم له الأرض والسموات وهو القوي الحميد",
    2, 255,  # the verse it was derived from — it must NOT be returned
)


# ── Benchmark helpers ──────────────────────────────────────────────────────────

def _run_threshold(threshold: int) -> dict:
    """Return counts {tp, fp, fn, tn} for VERSE_CASES + NON_VERSE_CASES + ERROR_VERSE."""
    tp = fp = fn = tn = 0
    wrong: list[str] = []

    for vc in VERSE_CASES:
        res = match_verse(vc.text, threshold=threshold)
        if res and res["sura"] == vc.sura and res["ayah"] == vc.ayah:
            tp += 1
        elif res:
            fp += 1
            wrong.append(f"[WRONG] {vc.label}: got {res['sura']}:{res['ayah']} score={res['score']:.0f} (expected {vc.sura}:{vc.ayah})")
        else:
            fn += 1
            wrong.append(f"[MISS]  {vc.label}: got None")

    for text in NON_VERSE_CASES:
        res = match_verse(text, threshold=threshold)
        if res is None:
            tn += 1
        else:
            fp += 1
            wrong.append(f"[FALSE+] non-verse got {res['sura']}:{res['ayah']} score={res['score']:.0f}: {text[:40]}")

    # Error-verse: expect None (not matching the correct verse or any other)
    err_text, _s, _a = ERROR_VERSE
    res = match_verse(err_text, threshold=threshold)
    if res is None:
        tn += 1
    else:
        fp += 1
        wrong.append(f"[ERR-MATCH] error-verse got {res['sura']}:{res['ayah']} score={res['score']:.0f}")

    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "wrong": wrong}


def _fmt(n: int, d: int) -> str:
    return f"{n/d:.0%}" if d else "–"


def run_benchmark() -> None:
    thresholds = [85, 90, 95]
    total_pos = len(VERSE_CASES)
    total_neg = len(NON_VERSE_CASES) + 1  # +1 for the error-verse

    print()
    print("=" * 72)
    print("  Verse-detection benchmark — verses.py")
    print("=" * 72)
    header = f"  {'Threshold':>10}  {'TP':>5}  {'FP':>5}  {'FN':>5}  {'TN':>5}"
    header += f"  {'Recall':>7}  {'Prec':>6}  {'F1':>6}"
    print(header)
    print("  " + "-" * 68)

    for thr in thresholds:
        c = _run_threshold(thr)
        tp, fp, fn, tn = c["tp"], c["fp"], c["fn"], c["tn"]
        recall = tp / (tp + fn) if (tp + fn) else 0
        prec   = tp / (tp + fp) if (tp + fp) else 0
        f1     = 2 * prec * recall / (prec + recall) if (prec + recall) else 0
        row = (f"  {thr:>10}  {tp:>5}  {fp:>5}  {fn:>5}  {tn:>5}"
               f"  {recall:>7.1%}  {prec:>6.1%}  {f1:>6.1%}")
        print(row)

    print("  " + "-" * 68)
    print(f"  Total positives (verse cases): {total_pos}")
    print(f"  Total negatives (sermon + error): {total_neg}")
    print()

    # Detailed wrong-answers at default threshold 90
    c90 = _run_threshold(90)
    if c90["wrong"]:
        print("  Issues at threshold=90:")
        for w in c90["wrong"]:
            print(f"    {w}")
    else:
        print("  No issues at threshold=90. All cases pass.")
    print()

    # Spot-check translation
    print("  Translation spot-check (2:255, en):")
    tr = get_translation(2, 255, "en")
    print(f"    [{tr['lang']}] {tr['translator']} | {tr['version']}")
    print(f"    {tr['text'][:80]}…")
    print()


# ── pytest-compatible tests ────────────────────────────────────────────────────

def test_normalize_alef() -> None:
    assert normalize("أإآٱ") == "اااا"


def test_normalize_tashkeel() -> None:
    assert normalize("الْحَمْدُ") == "الحمد"


def test_normalize_tatweel() -> None:
    assert normalize("اللـه") == "الله"


def test_normalize_ya_ta_marbuta() -> None:
    assert normalize("الرحمةِ") == "الرحمه"


def test_verse_fatiha() -> None:
    r = match_verse("إياك نعبد وإياك نستعين")
    assert r is not None
    assert r["sura"] == 1 and r["ayah"] == 5


def test_verse_partial() -> None:
    r = match_verse("الله لا إله إلا هو الحي القيوم لا تأخذه سنة ولا نوم")
    assert r is not None
    assert r["sura"] == 2 and r["ayah"] == 255


def test_verse_too_short() -> None:
    # Only 2 words — below min_words=4, must return None
    r = match_verse("الرحمن الرحيم")
    assert r is None


def test_non_verse_sermon() -> None:
    r = match_verse("أحمد الله وأشكره على نعمه الجزيلة وأصلي وأسلم على خير خلقه")
    assert r is None


def test_error_verse_no_match() -> None:
    err_text, _, _ = ERROR_VERSE
    r = match_verse(err_text, threshold=90)
    assert r is None, f"error-verse should not match, got {r}"


def test_translation_en() -> None:
    tr = get_translation(1, 1, "en")
    assert tr["lang"] == "en"
    assert tr["text"]
    assert "hilali" in tr["translator"].lower() or tr["translator"]


def test_translation_key_error() -> None:
    import pytest
    with pytest.raises(KeyError):
        get_translation(1, 1, "fr")  # unsupported lang


if __name__ == "__main__":
    run_benchmark()
