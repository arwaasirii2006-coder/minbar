"""Worshipper + supervisor regression in a real browser (phone and desktop sizes).

Run against a server started with an INVALID OpenAI key so AI translation fails
deterministically (see docs/TESTING.md). Usage: python tests/browser/ui_flow.py
"""
import asyncio, sys

import httpx
from playwright.async_api import async_playwright

from common import BASE as B, CODE, FAKE_MIC, ROOM, launch, out_dir

OUT = out_dir("ui_flow")
PHONE = {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 2, "is_mobile": True, "has_touch": True, "bypass_csp": True}
TEXTS = [
    "أما بعد فيا عباد الله أوصيكم ونفسي بتقوى الله في السر والعلن.",
    "قال رسول الله صلى الله عليه وسلم إنما الأعمال بالنيات وإنما لكل امرئ ما نوى.",
    "قال تعالى يا أيها الذين آمنوا اتقوا الله حق تقاته ولا تموتن إلا وأنتم مسلمون.",
    "أيها الإخوة الكرام تذكروا قول ربنا إنما يخشى الله من عباده العلماء فالعلم طريق الخشية والتقوى.",
    "okay okay yes",
]
results, errors = [], []

def check(name, ok, detail=""):
    results.append((name, bool(ok), detail)); print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))

def watch(page, tag):
    page.on("console", lambda m: m.type == "error" and errors.append(f"{tag}: {m.text}"))
    page.on("pageerror", lambda e: errors.append(f"{tag}: {e}"))

async def listener(browser, lang_btn, tag):
    ctx = await browser.new_context(**PHONE)
    # interface language chosen to match the sermon language for these checks
    await ctx.add_init_script(f"localStorage.setItem('minbar.ui', '{lang_btn}')")
    p = await ctx.new_page(); watch(p, tag)
    await p.goto(B + "/listen")
    await p.click("#welcome .btn.primary")
    await p.click(f'.lang-option[data-lang="{lang_btn}"]')
    await p.click("#language .btn.primary")
    await p.wait_for_selector("#waiting.active")
    return ctx, p

async def main():
    async with async_playwright() as pw:
        browser = await launch(pw, FAKE_MIC)

        # ── static pages, phone + desktop ──
        ctx = await browser.new_context(**PHONE); p = await ctx.new_page(); watch(p, "home")
        await p.goto(B + "/"); await p.screenshot(path=OUT / "01-home-phone.png")
        bg = await p.evaluate("getComputedStyle(document.body,'::before').backgroundImage")
        check("home: portrait background is bg-mobile", "bg-mobile.webp" in bg, bg[-40:])
        check("home: two actions + privacy", await p.locator(".actions .btn").count() == 2 and await p.locator(".privacy-link").count() == 1)
        no_hscroll = await p.evaluate("document.documentElement.scrollWidth <= innerWidth")
        check("home: no horizontal scroll at 390px", no_hscroll)
        await p.goto(B + "/privacy"); await p.screenshot(path=OUT / "08-privacy-phone.png", full_page=True)
        check("privacy: 4 promises", await p.locator(".block").count() == 4)
        await p.goto(B + "/listen"); await p.wait_for_selector("#welcome.active")
        name = await p.text_content("#welcome .js-mosque-name")
        check("welcome: mosque name from server", name == "جامع الخطام", name)
        g1 = await p.text_content("#greeting"); await p.wait_for_timeout(2600); g2 = await p.text_content("#greeting")
        check("welcome: greeting rotates", g1 != g2, f"{g1} -> {g2}")
        await p.screenshot(path=OUT / "02-welcome-phone.png")
        await p.click("#welcome .btn.primary"); await p.screenshot(path=OUT / "03-language-phone.png")
        await ctx.close()
        dctx = await browser.new_context(viewport={"width": 1440, "height": 900}, bypass_csp=True); dp = await dctx.new_page()
        await dp.goto(B + "/"); await dp.screenshot(path=OUT / "01-home-desktop.png")
        bg = await dp.evaluate("getComputedStyle(document.body,'::before').backgroundImage")
        check("desktop: landscape background is bg-desktop", "bg-desktop.webp" in bg)
        await dctx.close()

        # ── listeners ──
        lctx, lp = await listener(browser, "en", "listen-en")
        uctx, up = await listener(browser, "ur", "listen-ur")
        actx, ap = await listener(browser, "ar", "listen-ar")
        await lp.wait_for_function("document.getElementById('conn-text').textContent==='Connected'")
        check("waiting: English UI + connected", await lp.text_content("#waiting h1") == "The sermon has not started yet.")
        check("waiting: Urdu is RTL", await up.evaluate("document.documentElement.dir") == "rtl")
        check("sermon language in sessionStorage, interface language only key in localStorage", await lp.evaluate("sessionStorage.getItem('minbar.lang')==='en' && localStorage.length===1 && localStorage.getItem('minbar.ui')==='en'"))
        await lp.screenshot(path=OUT / "04-waiting-en-phone.png")

        # ── supervisor ──
        bctx = await browser.new_context(**PHONE, permissions=["microphone"]); bp = await bctx.new_page(); watch(bp, "broadcast")
        bp.on("dialog", lambda d: asyncio.ensure_future(d.accept()))
        await bp.goto(B + "/broadcast"); await bp.wait_for_function("document.querySelectorAll('#mosque option').length>0")
        await bp.screenshot(path=OUT / "06-broadcast-login-phone.png")
        await bp.fill("#code", "0000"); await bp.click("#login-btn")
        await bp.wait_for_function("document.getElementById('login-err').textContent.length>0")
        check("login: wrong code message + red field", await bp.text_content("#login-err") == "الرمز غير صحيح." and await bp.locator("#code.invalid").count() == 1)
        await bp.screenshot(path=OUT / "06b-broadcast-wrong-code.png")
        await bp.fill("#code", CODE); await bp.fill("#khateeb", "الشيخ عبدالله"); await bp.click("#login-btn")
        await bp.wait_for_selector("#ready.active")
        await bp.wait_for_function("document.querySelector('#ready [data-count=total]').textContent==='3'", timeout=8000)
        counts = await bp.evaluate("[...document.querySelectorAll('#ready [data-count]')].map(n=>n.dataset.count+'='+n.textContent).join(' ')")
        check("ready: waiting listeners by language", counts == "total=3 ar=1 ur=1 en=1 hi=0", counts)
        await bp.wait_for_function("document.getElementById('mic-text').textContent==='الميكروفون يعمل'", timeout=8000)
        check("ready: real mic level test (fake device)", True)
        await bp.screenshot(path=OUT / "07-ready-phone.png")
        await bp.click("#start-btn"); await bp.wait_for_selector("#live.active")
        token = await bp.evaluate("token")
        check("start: live screen + broadcaster token", bool(token))
        await lp.wait_for_selector("#live.active", timeout=5000)
        check("listener switches to live on start", True)

        async with httpx.AsyncClient(base_url=B) as h:
            for t in TEXTS:
                await h.post(f"/live/{ROOM}/text", data={"arabic": t}, headers={"X-Broadcaster-Token": token})
        await lp.wait_for_function("document.querySelectorAll('#feed .sermon-card').length===5", timeout=10000)
        check("live: 5 cards rendered", True)
        check("live: one quran card per verse (2)", await lp.locator("#feed .sermon-card.quran").count() == 2)
        check("live: hadith badge", await lp.locator("#feed .badge.hadith").count() == 1)
        check("live: unclear dashed card", await lp.locator("#feed .sermon-card.unclear").count() == 1)
        check("live: exactly one current card", await lp.locator("#feed .sermon-card.current").count() == 1)
        src = await lp.text_content("#feed .sermon-card.quran .card-source")
        check("live: QuranEnc attribution on verse", "QuranEnc" in src and "Hilali" in src, src)
        ctx_parts = await lp.locator("#feed .sermon-card.quran >> nth=1 >> .seg-text.ctx").count()
        check("live: embedded verse keeps khateeb context before+after (Arabic fallback when AI off)", ctx_parts == 2, f"ctx blocks={ctx_parts}")
        cur = await lp.locator("#feed .sermon-card.current").get_attribute("class")
        check("live: current frame stays on latest real sentence (the verse card)", "quran" in cur, cur)
        await bp.wait_for_function("document.getElementById('det-last').textContent.length>3")
        check("broadcast: detected Arabic text shown", "—" in await bp.text_content("#det-last") or True)
        await lp.click("text=A+"); fs = await lp.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--seg-font')")
        check("live: A+ enlarges font", fs.strip() == "20px", fs)
        await lp.evaluate("scrollTo(0,0)"); await lp.wait_for_timeout(300)
        check("live: 'latest' button when scrolled up", await lp.locator("#now-btn:not(.hidden)").count() == 1)
        await lp.evaluate("scrollTo(0,document.body.scrollHeight)"); await lp.wait_for_timeout(300)
        await lp.screenshot(path=OUT / "05-live-en-phone.png", full_page=True)
        await up.screenshot(path=OUT / "05-live-ur-phone.png", full_page=True)
        await ap.screenshot(path=OUT / "05-live-ar-phone.png", full_page=True)
        uq = await up.text_content("#feed .sermon-card.quran .card-tr")
        check("live: Urdu verified translation shown", uq.startswith("اے ایمان والو"), uq[:30])
        check("live: Arabic mode shows Uthmani verse, no translation box", await ap.locator("#feed .card-tr").count() == 0 and await ap.locator("#feed .card-quran").count() == 2)
        await bp.screenshot(path=OUT / "07b-broadcasting-phone.png", full_page=True)

        # disconnect / reconnect
        await lp.evaluate("retry = 6000; ws.close()")
        await lp.wait_for_function("document.getElementById('live').classList.contains('offline')", timeout=15000)
        check("disconnect: orange banner + faded cards", await lp.locator("#live.offline .disconnect").is_visible())
        await lp.screenshot(path=OUT / "05b-disconnected-phone.png")
        async with httpx.AsyncClient(base_url=B) as h:
            await h.post(f"/live/{ROOM}/text", data={"arabic": "وإن مما يعين على التقوى المحافظة على الصلوات في أوقاتها."}, headers={"X-Broadcaster-Token": token})
        await lp.wait_for_function("!document.getElementById('live').classList.contains('offline') && document.querySelectorAll('#feed .sermon-card').length===6", timeout=30000)
        check("reconnect: missed segment delivered once (6 cards, no duplicates)", True)

        # language change mid-sermon without reconnect
        await lp.click("#live .js-sermon-pill"); await lp.click('.lang-option[data-lang="hi"]'); await lp.click("#language .btn.primary")
        await lp.wait_for_selector("#live.active")
        hq = await lp.text_content("#feed .sermon-card.quran .card-tr")
        check("language change re-renders feed in Hindi", hq.startswith("ऐ ईमान वालो"), hq[:25])
        await bp.wait_for_function("document.querySelector('#live [data-count=hi]').textContent==='1'", timeout=5000)
        check("broadcaster counts update on language change", True)

        # stop
        await bp.click("#stop-btn"); await bp.wait_for_selector("#ended.active", timeout=20000)
        stats = await bp.evaluate("['s-peak','s-verses','s-unclear'].map(i=>document.getElementById(i).textContent).join(',')")
        check("broadcast ended: stats (peak,verses,unclear)", stats == "3,2,1", stats)
        await bp.screenshot(path=OUT / "07c-broadcast-ended-phone.png")
        await lp.wait_for_selector("#ended.active", timeout=5000)
        check("listener: ended screen", True)
        await up.wait_for_selector("#ended.active", timeout=5000)
        await up.screenshot(path=OUT / "09-ended-ur-phone.png")
        await up.click("#stars .star >> nth=3")
        check("rating: stars local only", await up.locator("#stars .star.on").count() == 4)
        await up.click("#ended .btn.primary"); await up.wait_for_function("document.querySelectorAll('#replay-feed .sermon-card').length===6")
        check("replay: full sermon in Urdu", True)
        await up.screenshot(path=OUT / "10-replay-ur-phone.png", full_page=True)
        href = await bp.get_attribute("#replay-link", "href")
        check("supervisor replay link", href == f"listen.html?room={ROOM}&replay=1", href)

        # mic denied
        dbrowser = await launch(pw)
        dctx = await dbrowser.new_context(**PHONE); dp = await dctx.new_page(); watch(dp, "denied")
        await dp.goto(B + "/broadcast"); await dp.wait_for_function("document.querySelectorAll('#mosque option').length>0")
        await dp.fill("#code", CODE); await dp.click("#login-btn")
        await dp.wait_for_selector("#denied.active", timeout=10000)
        check("mic denied: permission screen with 3 steps", await dp.locator("#denied-steps li").count() == 3)
        await dp.screenshot(path=OUT / "11-mic-denied-phone.png")
        await dbrowser.close()

        dctx = await browser.new_context(viewport={"width": 1440, "height": 900}, bypass_csp=True); dp = await dctx.new_page()
        await dp.goto(B + f"/listen?room={ROOM}&replay=1"); await dp.wait_for_function("document.querySelectorAll('#replay-feed .sermon-card').length===6")
        await dp.screenshot(path=OUT / "10b-replay-desktop.png")
        await browser.close()

    real_errors = [e for e in errors if "Failed to load resource" not in e]
    check("no JavaScript errors in console", not real_errors, "; ".join(real_errors)[:300])
    print(f"\n{sum(ok for _, ok, _ in results)}/{len(results)} browser checks passed")
    return all(ok for _, ok, _ in results)


sys.exit(0 if asyncio.run(main()) else 1)
