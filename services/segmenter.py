from __future__ import annotations

import re

_SENTENCE = re.compile(r"(.+?[.!؟?؛;\n])(?:\s+|$)", re.S)


class Segmenter:
    """Accumulates transcript text and emits complete sentences.

    Sentences end at Arabic/Latin terminal punctuation. Text that grows past
    *max_chars* without punctuation is cut at the last space so listeners are
    never left waiting on a run-on transcript.
    """

    def __init__(self, max_chars: int = 260):
        self.buffer = ""
        self.max_chars = max_chars

    def add(self, text: str) -> list[str]:
        text = (text or "").strip()
        if not text:
            return []
        self.buffer = f"{self.buffer} {text}".strip()
        out: list[str] = []

        while True:
            m = _SENTENCE.search(self.buffer)
            if m:
                out.append(m.group(1).strip())
                self.buffer = self.buffer[m.end():].strip()
                continue

            if len(self.buffer) > self.max_chars:
                cut = self.buffer.rfind(" ", 40, self.max_chars)
                if cut == -1:
                    cut = self.max_chars
                out.append(self.buffer[:cut].strip())
                self.buffer = self.buffer[cut:].strip()
                continue
            break
        return [s for s in out if s]

    def flush(self) -> list[str]:
        if not self.buffer:
            return []
        text = self.buffer
        self.buffer = ""
        return [text]
