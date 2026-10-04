def validate_text(text: str):
    """
    دالة مؤقتة للتحقق من النص قبل معالجته.
    """

    if text is None:
        return False

    text = text.strip()

    if not text:
        return False

    return True