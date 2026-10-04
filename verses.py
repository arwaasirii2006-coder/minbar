QURAN_VERSES = {}


def find_verse(text: str):
    """
    دالة مؤقتة للبحث عن آية قرآنية داخل النص.
    سيتم ربطها لاحقًا بقاعدة بيانات الآيات.
    """
    if not text:
        return None

    for verse, data in QURAN_VERSES.items():
        if verse in text:
            return {
                "verse": verse,
                "data": data
            }

    return None