class SentenceSegmenter:
    def __init__(self):
        self.buffer = ""

    def add(self, text: str):
        if not text:
            return None

        self.buffer += " " + text.strip()
        self.buffer = self.buffer.strip()

        # نعتبر الجملة مكتملة عند علامات الوقف
        end_marks = (".", "!", "?", "؟", "؛", "\n")

        if self.buffer.endswith(end_marks):
            complete_sentence = self.buffer
            self.buffer = ""
            return complete_sentence

        return None

    def flush(self):
        if not self.buffer:
            return None

        remaining_text = self.buffer
        self.buffer = ""
        return remaining_text