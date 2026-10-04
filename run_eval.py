import time

from validate import validate_text
from verses import find_verse
from segmenter import SentenceSegmenter
from logger import log_info, log_error


def calculate_term_accuracy(text, expected_terms):
    correct_terms = 0

    for term in expected_terms:
        if term in text:
            correct_terms += 1

    if len(expected_terms) == 0:
        return 0

    accuracy = (correct_terms / len(expected_terms)) * 100
    return accuracy


def run_evaluation():
    start_time = time.time()

    try:
        log_info("Starting Minbar evaluation")

        # نص تجريبي
        test_text = "الصلاة والزكاة والصيام من العبادات."

        # المصطلحات التي نتوقع وجودها في النص
        expected_terms = [
            "الصلاة",
            "الزكاة",
            "الصيام"
        ]

        # التحقق من النص
        is_valid = validate_text(test_text)

        # تجميع الجملة
        segmenter = SentenceSegmenter()
        complete_sentence = segmenter.add(test_text)

        # البحث عن آية
        verse_result = find_verse(test_text)

        # حساب دقة المصطلحات
        term_accuracy = calculate_term_accuracy(
            test_text,
            expected_terms
        )

        # حساب زمن التنفيذ
        elapsed_time = time.time() - start_time
        latency_ms = elapsed_time * 1000

        print("=== تقييم منبر ===")
        print("النص المدخل:", test_text)
        print("النص صالح:", "نعم" if is_valid else "لا")
        print("الجملة المكتملة:", complete_sentence)
        print("الآية:", verse_result if verse_result else "لا توجد")
        print("دقة المصطلحات:", round(term_accuracy, 2), "%")
        print("زمن التنفيذ:", round(elapsed_time, 4), "ثانية")
        print("السرعة (زمن الاستجابة):", round(latency_ms, 2), "مللي ثانية")

        log_info("Minbar evaluation completed successfully")

    except Exception as e:
        log_error(str(e))
        print("فشل التقييم:", str(e))


run_evaluation()