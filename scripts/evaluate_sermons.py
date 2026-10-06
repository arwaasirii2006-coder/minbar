"""End-to-end evaluation of Minbar on real sermon recordings kept OUTSIDE the repo.

Runs the production path against a running server for each file:
  broadcast start → listener WebSocket (en/ur/hi) → upload recording →
  speech-to-text → segmentation → Quran detection → translation →
  listeners receive segments → broadcast stop → listeners receive ENDED

Usage (server running with OPENAI_API_KEY and MINBAR_BROADCAST_CODES set):
  python scripts/evaluate_sermons.py --code YOUR_CODE "D:/sermons/1.mp3" "D:/sermons/2.m4a"

Nothing is uploaded anywhere except your own Minbar server. Results are printed
and, with --out, written to a JSON file of your choice (keep it outside git if
it contains sermon text).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import mimetypes
import time
from pathlib import Path

import httpx
import websockets


async def listen(ws_url: str, lang: str, out: dict, done: asyncio.Event):
    async with websockets.connect(f"{ws_url}&language={lang}") as ws:
        async for raw in ws:
            m = json.loads(raw)
            if m["type"] == "segment":
                out.setdefault("segments", []).append({"t": time.perf_counter(), **m})
            elif m["type"] == "ended":
                out["ended"] = True
                done.set()
                return


async def evaluate(base: str, room: str, code: str, path: Path, timeout: float) -> dict:
    ws_base = base.replace("http", "ws", 1) + f"/ws/{room}?role=listener"
    async with httpx.AsyncClient(base_url=base, timeout=120) as http:
        r = await http.post("/broadcast/start", json={"room_id": room, "code": code, "resume": True})
        r.raise_for_status()
        token = r.json()["broadcaster_token"]
        headers = {"X-Broadcaster-Token": token}

        received = {lang: {} for lang in ("en", "ur", "hi")}
        done = asyncio.Event()
        listeners = [asyncio.create_task(listen(ws_base, lang, received[lang], done)) for lang in received]
        await asyncio.sleep(0.5)

        t0 = time.perf_counter()
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        with open(path, "rb") as f:
            r = await http.post(f"/live/{room}/recorded", headers=headers, files={"file": (path.name, f, mime)})
        if r.status_code != 202:
            await http.post(f"/broadcast/{room}/stop", headers=headers)
            for task in listeners:
                task.cancel()
            return {"file": path.name, "error": r.json().get("detail")}

        state = {}
        while time.perf_counter() - t0 < timeout:
            state = (await http.get(f"/broadcast/{room}")).json().get("processing") or {}
            if state.get("state") in ("done", "failed"):
                break
            await asyncio.sleep(1)
        processing_seconds = time.perf_counter() - t0

        stop = (await http.post(f"/broadcast/{room}/stop", headers=headers)).json()
        try:
            await asyncio.wait_for(done.wait(), 15)
        except asyncio.TimeoutError:
            pass
        for task in listeners:
            task.cancel()

    segs = received["en"].get("segments", [])
    first = segs[0]["t"] - t0 if segs else None
    return {
        "file": path.name,
        "size_mb": round(path.stat().st_size / 1048576, 2),
        "processing_state": state.get("state"),
        "processing_error": state.get("error"),
        "processing_seconds": round(processing_seconds, 1),
        "seconds_to_first_segment": round(first, 1) if first else None,
        "segments": len(segs),
        "verified_verses": stop.get("verified_verses"),
        "unclear_segments": stop.get("unclear_segments"),
        "translation_failures": {lang: sum(lang in s.get("failed_languages", []) for s in segs) for lang in ("en", "ur", "hi")},
        "listeners_received": {lang: len(v.get("segments", [])) for lang, v in received.items()},
        "listeners_got_ended": {lang: bool(v.get("ended")) for lang, v in received.items()},
        "verses": [f'{s["verse"]["sura"]}:{s["verse"]["ayah"]} ({s["verse"]["score"]})' for s in segs if s.get("verse")],
        "sample": [{"ar": s["arabic"][:160], "en": s["translations"].get("en", "")[:160]} for s in segs[:3]],
    }


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--room", default="KHATAM-2026")
    ap.add_argument("--code", required=True)
    ap.add_argument("--timeout", type=float, default=900)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    results = []
    for path in args.files:
        print(f"\n=== {path.name}")
        result = await evaluate(args.base.rstrip("/"), args.room, args.code, path, args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        results.append(result)
    if args.out:
        args.out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nSaved {args.out}")


if __name__ == "__main__":
    asyncio.run(main())
