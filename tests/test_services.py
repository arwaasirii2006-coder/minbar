"""Pure service units: segmentation, text quality, verse span alignment, config."""

from services.segmenter import Segmenter
from services.text_quality import classify, looks_like_hadith
from services.verse_service import _normalize_with_map, detect_verse
from verses import _CORPUS, normalize


def test_segmenter_sentences_and_flush():
    s = Segmenter()
    assert s.add("الحمد لله رب العالمين.") == ["الحمد لله رب العالمين."]
    assert s.add("أما بعد فيا عباد الله") == []
    assert s.add("اتقوا الله؟ ثم") == ["أما بعد فيا عباد الله اتقوا الله؟"]
    assert s.flush() == ["ثم"] and s.flush() == []


def test_segmenter_cuts_run_on_text():
    s = Segmenter(max_chars=60)
    out = s.add(" ".join(["كلمة"] * 40))
    assert out and all(len(x) <= 60 for x in out)


def test_classify():
    assert classify("") == "empty"
    assert classify("ترجمة نانسي قنقر") == "empty"
    assert classify("اشتركوا في القناة") == "empty"
    assert classify("okay yes thank you") == "unclear"
    assert classify("الحمد لله رب العالمين") == "ok"


def test_hadith_marker():
    assert looks_like_hadith("قال رسول الله صلى الله عليه وسلم إنما الأعمال بالنيات")
    assert not looks_like_hadith("اتقوا الله عباد الله")


def test_normalize_map_matches_verses_normalize():
    for v in _CORPUS[:500]:
        for text in (v["aya_text_unicode"], v["aya_text_emlaey"]):
            assert _normalize_with_map(text)[0] == normalize(text)


def test_verse_context_split():
    text = "أيها الإخوة تذكروا قول ربنا يا أيها الذين آمنوا اتقوا الله حق تقاته ولا تموتن إلا وأنتم مسلمون فهذه وصية عظيمة"
    v = detect_verse(text)
    assert (v["sura"], v["ayah"]) == (3, 102)
    assert v["context"]["before"] == "أيها الإخوة تذكروا قول ربنا"
    assert v["context"]["after"] == "فهذه وصية عظيمة"
    assert v["sources"]["en"]["translation_id"] == "english_hilali_khan"


def test_partial_quote_inside_commentary():
    v = detect_verse("أيها الإخوة الكرام تذكروا قول ربنا إنما يخشى الله من عباده العلماء فالعلم طريق الخشية والتقوى.")
    assert (v["sura"], v["ayah"], v["method"]) == (35, 28, "embedded")
    assert v["context"] == {"before": "أيها الإخوة الكرام تذكروا قول ربنا", "after": "فالعلم طريق الخشية والتقوى"}


def test_stock_phrases_are_not_quotations():
    for text in (
        "إن الله على كل شيء قدير وهو الغفور الرحيم فاستغفروا ربكم وتوبوا إليه",
        "إن الله غفور رحيم فلا تقنطوا من رحمته وأقبلوا عليه بقلوب صادقة",
        "إن الحمد لله نحمده ونستعينه ونستغفره ونعوذ بالله من شرور أنفسنا ومن سيئات أعمالنا",
    ):
        assert detect_verse(text) is None, text


def test_verse_only_when_little_context():
    v = detect_verse("قال تعالى: يا أيها الذين آمنوا اتقوا الله حق تقاته ولا تموتن إلا وأنتم مسلمون")
    assert v["verse_only"] and v["context"] is None
    expected = next(x for x in _CORPUS if (x["sura_no"], x["aya_no"]) == (3, 102))
    assert v["arabic"] == expected["aya_text_unicode"]
