"""Interface-language (i18n) consistency: one dictionary, four complete languages,
every key used by the pages exists, every backend error code is translated."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
I18N = (FRONTEND / "js" / "i18n.js").read_text(encoding="utf-8")
PAGES = {p: (FRONTEND / f"{p}.html").read_text(encoding="utf-8") for p in ("index", "listen", "broadcast", "privacy")}
LANGS = ("ar", "en", "ur", "hi")
ARABIC = re.compile(r"[؀-ۿ]")
KEY = r"(?:ui|common|title|home|listen|bc|privacy|err)\.[A-Za-z_]+"


def dictionaries() -> dict[str, dict[str, str]]:
    blocks = re.split(r"^    (ar|en|ur|hi): \{$", I18N, flags=re.M)
    out = {}
    for code, body in zip(blocks[1::2], blocks[2::2]):
        out[code] = dict(re.findall(r"^\s+'(" + KEY + r")': '((?:[^'\\]|\\.)*)',$", body, flags=re.M))
    return out


DICTS = dictionaries()


def used_keys() -> set[str]:
    keys = set()
    for html in PAGES.values():
        keys |= set(re.findall(r'data-i18n(?:-placeholder|-aria-label|-title)?="(' + KEY + ')"', html))
        keys |= set(re.findall(r"'(" + KEY + r")'", html))
    keys |= {"listen." + s for s in ("connected", "connecting", "disconnected")}  # t('listen.' + state)
    return keys


def test_all_four_languages_have_the_same_keys():
    assert set(DICTS) == set(LANGS)
    reference = set(DICTS["ar"])
    assert len(reference) > 150
    for code in LANGS:
        assert set(DICTS[code]) == reference, f"{code}: missing {reference - set(DICTS[code])}, extra {set(DICTS[code]) - reference}"
        assert all(v.strip() for v in DICTS[code].values()), code


def test_every_key_used_by_the_pages_exists():
    missing = sorted(k for k in used_keys() if k not in DICTS["ar"])
    assert not missing, missing


def test_every_page_loads_i18n_and_has_a_language_switcher_or_title():
    for name, html in PAGES.items():
        assert '<script src="js/i18n.js"></script>' in html, name
        assert re.search(r'data-i18n-title="title\.' + name.replace("index", "home") + '"', html), name
        assert "data-ui-lang" in html, name


def _error_codes() -> set[str]:
    codes = set()
    for path in list((ROOT / "api").glob("*.py")) + list((ROOT / "services").glob("*.py")) + [ROOT / "realtime" / "ws.py"]:
        src = path.read_text(encoding="utf-8")
        codes |= set(re.findall(r'api_error\(\s*\d+,\s*"(\w+)"', src))
        codes |= set(re.findall(r'^\s+code = "(\w+)"', src, flags=re.M))
        codes |= set(re.findall(r'"code": "(\w+)"', src))
        codes |= set(re.findall(r'BroadcastAuthError\(\d+, "(\w+)"', src))
        codes |= set(re.findall(r'error_code="(\w+)"', src))
    return codes - {"audio_error"}


def test_every_backend_error_code_is_translated():
    codes = _error_codes()
    assert {"invalid_code", "ai_unavailable", "ai_key_invalid", "file_too_large", "already_live", "no_arabic_speech"} <= codes
    missing = sorted(c for c in codes if f"err.{c}" not in DICTS["ar"])
    assert not missing, missing


# Arabic intentionally inside an English/Hindi string: the bilingual privacy
# subtitle required by docs/screens.md ("title in Arabic and English").
ALLOWED_ARABIC = {"privacy.subtitle"}


@pytest.mark.parametrize("code", ["en", "hi"])
def test_no_arabic_left_in_ltr_languages(code):
    leaked = {k: v for k, v in DICTS[code].items() if ARABIC.search(v) and k not in ALLOWED_ARABIC}
    assert not leaked, leaked


def test_static_markup_has_no_untranslated_arabic():
    # Arabic may remain only as fallback text inside a translated element, in the
    # brand name, as native language names, or in Arabic sermon content.
    for name, html in PAGES.items():
        body = html.split("<body>", 1)[1].split("<script>", 1)[0]
        for line in body.splitlines():
            if not ARABIC.search(line):
                continue
            ok = ("data-i18n" in line or 'alt="منبر' in line or re.search(r'lang="(ar|ur)"', line)
                  or 'id="greeting"' in line)
            assert ok, f"{name}: {line.strip()[:100]}"


def test_interface_language_is_persisted_separately_from_sermon_language():
    assert "localStorage" in I18N and "'minbar.ui'" in I18N
    listen = PAGES["listen"]
    assert "sessionStorage" in listen and "minbar.lang" in listen
    assert "localStorage" not in listen
