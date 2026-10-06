"""Cross-origin setup in a real browser: pages from a static dev server such as
VS Code Live Server (:5500), backend on another port (:8765).

Usage: python tests/browser/cross_origin.py badkey   (server has an invalid OPENAI_API_KEY)
       python tests/browser/cross_origin.py nokey    (server has no OPENAI_API_KEY)
See docs/TESTING.md.
"""
import asyncio, base64, json, sys

from playwright.async_api import async_playwright

from common import BASE as API, CODE, FAKE_MIC, FRONTEND as FE, ROOM, launch, out_dir

MODE = sys.argv[1] if len(sys.argv) > 1 else ""
if MODE not in ("nokey", "badkey"):
    sys.exit("usage: python tests/browser/cross_origin.py nokey|badkey")
OUT = out_dir("cross_origin")
results = []
def check(name, ok, detail=""):
    results.append(ok); print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))

async def main():
    async with async_playwright() as pw:
        b = await launch(pw, FAKE_MIC)
        ctx = await b.new_context(permissions=["microphone"], bypass_csp=True)
        failed, audio_responses = [], []
        p = await ctx.new_page()
        p.on("requestfailed", lambda r: failed.append(f"{r.method} {r.url} {r.failure}"))
        p.on("response", lambda r: "/live/" in r.url and audio_responses.append(r.status))
        p.on("dialog", lambda d: asyncio.ensure_future(d.accept()))

        # Without ?api the page cannot know where the backend is: it must say so clearly.
        await p.goto(FE + "/broadcast.html"); await p.wait_for_timeout(1500)
        hint = await p.text_content("#login-err")
        check("5500 without ?api: actionable hint instead of a silent failure", "?api=" in hint, hint[:60])

        await p.goto(FE + "/broadcast.html?api=" + API)
        await p.wait_for_function("document.querySelectorAll('#mosque option').length > 0", timeout=8000)
        check("5500 → 8765: mosques loaded cross-origin (CORS ok)", True)
        styled = await p.evaluate("getComputedStyle(document.querySelector('.btn.primary')).backgroundColor")
        check("assets load from Live Server (relative paths)", styled == "rgb(14, 88, 71)", styled)
        await p.fill("#code", CODE); await p.click("#login-btn")
        await p.wait_for_selector("#ready.active", timeout=8000)
        check("login → Ready", True)
        await p.wait_for_function("document.getElementById('mic-text').textContent === 'الميكروفون يعمل'", timeout=10000)
        check("real microphone stream + level meter", True)

        lp = await (await b.new_context(bypass_csp=True)).new_page()
        await lp.goto(FE + "/listen.html?api=" + API)
        await lp.click("#welcome .btn.primary"); await lp.click('.lang-option[data-lang="en"]'); await lp.click("#language .btn.primary")
        await lp.wait_for_function("document.getElementById('conn-dot').className === 'dot'", timeout=10000)
        check("listener on 5500 connected to WebSocket on 8765", True)

        if MODE == "nokey":
            err = await p.text_content("#ready-err")
            check("no key: Ready explains OPENAI_API_KEY", "OPENAI_API_KEY" in err, err[:70])
            await p.click("#start-btn"); await p.wait_for_timeout(1500)
            check("no key: start refused, stays on Ready (no broken live state)", await p.evaluate("document.querySelector('.screen.active').id") == "ready")
            st = json.loads(await lp.evaluate(f"fetch('{API}/broadcast/{ROOM}').then(r => r.text())"))
            check("no key: room not set LIVE", st["status"] == "READY", st["status"])

            # Capture three consecutive chunks exactly as the page's recorder produces them.
            data = await p.evaluate("""async () => {
              const got = [];
              const mime = pickMime();
              for (let i = 0; i < 3; i++) {
                const rec = new MediaRecorder(stream, mime ? {mimeType: mime} : {});
                const parts = [];
                rec.ondataavailable = e => e.data.size && parts.push(e.data);
                const done = new Promise(r => rec.onstop = r);
                rec.start(); await new Promise(r => setTimeout(r, 3000)); rec.stop(); await done;
                const blob = new Blob(parts, {type: rec.mimeType || mime});
                const buf = await blob.arrayBuffer();
                let decoded = 0;
                try { decoded = (await new AudioContext().decodeAudioData(buf.slice(0))).duration; } catch (e) { decoded = -1; }
                const bytes = new Uint8Array(buf); let s = ''; for (const x of bytes) s += String.fromCharCode(x);
                got.push({type: blob.type, size: blob.size, decoded, b64: btoa(s)});
              }
              return got;
            }""")
            for i, c in enumerate(data, 1):
                raw = base64.b64decode(c["b64"]); (OUT / f"chunk{i}.webm").write_bytes(raw)
                check(f"chunk {i}: {c['type']} {c['size']} B is a complete, independently decodable file", c["decoded"] > 1.5 and raw[:4] == b"\x1a\x45\xdf\xa3", f"duration {c['decoded']:.2f}s")
            await b.close()
        else:
            check("key present: Ready has no blocking error", await p.text_content("#ready-err") == "")
            await p.click("#start-btn"); await p.wait_for_selector("#live.active", timeout=8000)
            check("start broadcast (5500 → 8765)", True)
            await lp.wait_for_selector("#live.active", timeout=8000)
            check("listener receives 'started' cross-origin", True)
            await p.wait_for_function("document.getElementById('status').classList.contains('err')", timeout=30000)
            status = await p.text_content("#status")
            check("real chunk reached backend → OpenAI → actionable error shown", "OPENAI_API_KEY" in status, status[:80])
            check("no 'Failed to fetch' / network failures", not failed, "; ".join(failed)[:200])
            check("audio requests answered by backend (503, not network error)", audio_responses and set(audio_responses) == {503}, str(audio_responses))
            await p.wait_for_timeout(8000)
            check("recorder stopped after non-retryable error (no request storm)", len(audio_responses) == 1, f"{len(audio_responses)} request(s)")
            await p.click("#stop-btn"); await p.wait_for_selector("#ended.active", timeout=20000)
            check("stop broadcast → Broadcast Ended", True)
            await lp.wait_for_selector("#ended.active", timeout=8000)
            check("listener receives 'ended' cross-origin", True)
            await b.close()
    print(f"\n{sum(results)}/{len(results)} checks passed")
    return all(results)


sys.exit(0 if asyncio.run(main()) else 1)
