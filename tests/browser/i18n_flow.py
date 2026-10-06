"""Interface language (ar/en/ur/hi) on every screen in a real browser.

Run against a server started with an INVALID OpenAI key (see docs/TESTING.md).
Usage: python tests/browser/i18n_flow.py
"""
import asyncio, re, sys

import httpx
from playwright.async_api import async_playwright

from common import BASE as B, CODE, FAKE_MIC, REPO, ROOM, launch, out_dir

OUT = out_dir("i18n_flow")
PHONE = dict(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True, bypass_csp=True)
DIR = {"ar": "rtl", "ur": "rtl", "en": "ltr", "hi": "ltr"}
SRC = (REPO / "frontend" / "js" / "i18n.js").read_text(encoding="utf-8")
AR_BLOCK = re.split(r"^    (?:en): \{$", SRC, flags=re.M)[0]
AR_VALUES = {v for v in re.findall(r"^\s+'[\w.]+': '((?:[^'\\]|\\.)*)',$", AR_BLOCK, flags=re.M) if len(v) > 3}
def lang_values(code):
    blocks = re.split(r"^    (ar|en|ur|hi): \{$", SRC, flags=re.M)
    body = dict(zip(blocks[1::2], blocks[2::2]))[code]
    return set(re.findall(r"^\s+'[\w.]+': '((?:[^'\\]|\\.)*)',$", body, flags=re.M))
# Arabic dictionary strings (with Arabic letters) that don't legitimately exist in the target language.
AR_ONLY = {code: {v for v in AR_VALUES if re.search(r"[؀-ۿ]", v)} - lang_values(code) for code in ("en", "ur", "hi")}
results = []

def check(name, ok, detail=""):
    results.append(ok); print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))

# Visible interface text, excluding content explicitly marked as Arabic/Urdu
# (sermon text, verses, native language names) and mosque directory data.
VISIBLE = """() => {
  const out = [];
  const walker = document.createTreeWalker(document.querySelector('.screen.active') || document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const n = walker.currentNode, el = n.parentElement, txt = n.textContent.trim();
    if (!txt || !el || !el.offsetParent && getComputedStyle(el).position !== 'fixed') continue;
    if (el.closest('.js-mosque-name, .js-mosque-location, .js-mosque, #greeting, option, .en-title')) continue;
    const marked = el.closest('[lang]');
    if (marked && marked !== document.documentElement && ['ar', 'ur'].includes(marked.lang) && !marked.matches('.screen')) continue;
    out.push(txt);
  }
  return out;
}"""

async def audit(page, ui, where):
    texts = await page.evaluate(VISIBLE)
    d = await page.evaluate("[document.documentElement.dir, document.documentElement.lang]")
    untranslated = [t for t in texts if ui != "ar" and t in AR_ONLY[ui]]
    arabic = [t for t in texts if ui in ("en", "hi") and re.search(r"[\u0600-\u06FF]", t)]
    ok = d == [DIR[ui], ui] and not untranslated and not arabic
    check(f"[{ui}] {where}: dir={d[0]} lang={d[1]}, no leftover Arabic", ok, "; ".join((untranslated + arabic)[:3])[:160])

async def pick(page, ui):
    await page.click("[data-ui-lang] .lang-pill")
    await page.click(f'[data-ui-lang] [role=option][data-lang="{ui}"]')

async def main():
    async with async_playwright() as pw:
        browser = await launch(pw, FAKE_MIC)
        async with httpx.AsyncClient(base_url=B) as h:
            for ui in ("en", "ur", "hi", "ar"):
                ctx = await browser.new_context(**PHONE, permissions=["microphone"])
                errors = []
                # ── home: switch via menu without reload, then persist ──
                p = await ctx.new_page(); p.on("pageerror", lambda e: errors.append(str(e)))
                await p.goto(B + "/"); await p.evaluate("window.__noReload = 1")
                await pick(p, ui)
                check(f"[{ui}] switched without reload", await p.evaluate("window.__noReload === 1"))
                await audit(p, ui, "home")
                await p.screenshot(path=OUT / f"{ui}-home.png")
                await p.reload()
                check(f"[{ui}] choice persisted after reload (localStorage)", await p.evaluate("document.documentElement.lang") == ui)
                await p.goto(B + "/privacy"); await audit(p, ui, "privacy")
                await p.screenshot(path=OUT / f"{ui}-privacy.png", full_page=True)

                # ── worshipper: interface ui, sermon language = Urdu (or English when ui is Urdu) ──
                sermon = "en" if ui == "ur" else "ur"
                lp = await ctx.new_page(); lp.on("pageerror", lambda e: errors.append(str(e)))
                await lp.goto(B + "/listen"); await audit(lp, ui, "welcome")
                await lp.click("#welcome .btn.primary"); await audit(lp, ui, "language selection")
                await lp.screenshot(path=OUT / f"{ui}-language.png")
                await lp.click(f'.lang-option[data-lang="{sermon}"]'); await lp.click("#language .btn.primary")
                await lp.wait_for_function("document.getElementById('conn-text').textContent.length > 0")
                await lp.wait_for_timeout(500)
                await audit(lp, ui, "waiting"); await lp.screenshot(path=OUT / f"{ui}-waiting.png")

                # ── supervisor ──
                bp = await ctx.new_page(); bp.on("pageerror", lambda e: errors.append(str(e)))
                bp.on("dialog", lambda d: asyncio.ensure_future(d.accept()))
                await bp.goto(B + "/broadcast"); await bp.wait_for_function("document.querySelectorAll('#mosque option').length > 0")
                await audit(bp, ui, "broadcast login")
                await bp.fill("#code", ""); await bp.click("#login-btn"); await bp.wait_for_timeout(200)
                await audit(bp, ui, "login: empty code error")
                await bp.fill("#code", CODE); await bp.click("#login-btn"); await bp.wait_for_selector("#ready.active")
                await bp.wait_for_function("document.getElementById('mic-text').textContent.length > 3")
                await audit(bp, ui, "ready"); await bp.screenshot(path=OUT / f"{ui}-ready.png", full_page=True)
                await bp.click("#start-btn"); await bp.wait_for_selector("#live.active", timeout=8000)
                tok = await bp.evaluate("token")
                for text in ("قال تعالى يا أيها الذين آمنوا اتقوا الله حق تقاته ولا تموتن إلا وأنتم مسلمون.", "okay okay yes"):
                    await h.post(f"/live/{ROOM}/text", data={"arabic": text}, headers={"X-Broadcaster-Token": tok})
                await bp.wait_for_function("document.getElementById('status').classList.contains('err')", timeout=30000)
                status = await bp.text_content("#status")
                check(f"[{ui}] server error (invalid key) shown in interface language", not (ui in ("en", "hi") and re.search(r"[\u0600-\u06FF]", status)) and status not in AR_ONLY.get(ui, set()) or ui == "ar", status[:70])
                await audit(bp, ui, "broadcasting"); await bp.screenshot(path=OUT / f"{ui}-broadcasting.png", full_page=True)

                await lp.wait_for_selector("#live.active", timeout=8000)
                await lp.wait_for_function("document.querySelectorAll('#feed .sermon-card').length >= 2", timeout=10000)
                await audit(lp, ui, f"live (sermon={sermon})")
                card = await lp.evaluate("(() => { const n = document.querySelector('#feed .card-tr'); return n && [n.lang, n.dir, getComputedStyle(n).direction]; })()")
                check(f"[{ui}] sermon cards keep sermon language/direction ({sermon})", card == [sermon, DIR[sermon], DIR[sermon]], str(card))
                await lp.screenshot(path=OUT / f"{ui}-live.png")

                await bp.click("#stop-btn"); await bp.wait_for_selector("#ended.active", timeout=20000)
                await audit(bp, ui, "broadcast ended"); await bp.screenshot(path=OUT / f"{ui}-broadcast-ended.png")
                await lp.wait_for_selector("#ended.active", timeout=8000)
                await audit(lp, ui, "sermon ended"); await lp.screenshot(path=OUT / f"{ui}-ended.png")
                await lp.click("#ended .btn.primary"); await lp.wait_for_function("document.querySelectorAll('#replay-feed .sermon-card').length >= 2")
                await audit(lp, ui, "replay")

                # denied screen
                await bp.evaluate("setDenied(false)"); await audit(bp, ui, "microphone denied")
                await bp.evaluate("setDenied(true)"); await audit(bp, ui, "insecure connection")
                check(f"[{ui}] no JavaScript errors", not errors, "; ".join(errors)[:150])
                await ctx.close()

            # ── switching on a live page re-renders everything in place ──
            ctx = await browser.new_context(**PHONE)
            p = await ctx.new_page()
            await p.goto(B + "/listen?replay=1"); await p.wait_for_function("document.querySelectorAll('#replay-feed .sermon-card').length >= 2")
            await p.evaluate("window.__noReload = 3")
            await p.evaluate("I18N.set('en')"); en_badge = await p.text_content("#replay-feed .badge.quran")
            await p.evaluate("I18N.set('hi')"); hi_badge = await p.text_content("#replay-feed .badge.quran")
            check("replay cards re-render on language switch without reload", en_badge.strip() == "Quran" and hi_badge.strip() == "क़ुरआन" and await p.evaluate("window.__noReload === 3"), f"{en_badge.strip()} → {hi_badge.strip()}")
            await ctx.close()
        await browser.close()
    print(f"\n{sum(results)}/{len(results)} checks passed")
    return all(results)


sys.exit(0 if asyncio.run(main()) else 1)
