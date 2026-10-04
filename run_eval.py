import time
import json

from verses import match_verse
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
        test_text = "الحمد لله رب العالمين الصلاة والزكاة والصيام"

        # المصطلحات المتوقع وجودها
        expected_terms = [
            "الصلاة",
            "الزكاة",
            "الصيام"
        ]

        # تجميع الجملة
        segmenter = SentenceSegmenter()
        complete_sentence = segmenter.add(test_text)

        # البحث عن آية وحساب دقتها
        verse_result = match_verse(test_text)

        if verse_result:
            verse_accuracy = verse_result["score"]
        else:
            verse_accuracy = 0

        # حساب دقة المصطلحات
        term_accuracy = calculate_term_accuracy(
            test_text,
            expected_terms
        )

        # حساب زمن التنفيذ
        elapsed_time = time.time() - start_time
        latency_ms = elapsed_time * 1000

        # تقدير تكلفة الترجمة باستخدام GPT-5 mini
        estimated_input_tokens = len(test_text) / 4
        estimated_output_tokens = estimated_input_tokens

        input_cost = (estimated_input_tokens / 1_000_000) * 0.25
        output_cost = (estimated_output_tokens / 1_000_000) * 2.00

        estimated_cost = input_cost + output_cost

        # النتائج
        results = {
            "latency_ms": round(latency_ms, 2),
            "term_accuracy": round(term_accuracy, 2),
            "verse_accuracy": round(verse_accuracy, 2),
            "estimated_cost_usd": round(estimated_cost, 8)
        }

        # حفظ النتائج
        with open(
            "evaluation_results.json",
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                results,
                f,
                ensure_ascii=False,
                indent=2
            )

        # طباعة النتائج
        print("=== تقييم مشروع منبر ===")
        print("النص التجريبي:", test_text)
        print("الجملة المكتملة:", complete_sentence)
        print("نتيجة الآية:", verse_result)
        print("دقة الآيات:", round(verse_accuracy, 2), "%")
        print("دقة المصطلحات:", round(term_accuracy, 2), "%")
        print("زمن التنفيذ:", round(elapsed_time, 4), "ثانية")
        print("زمن الاستجابة:", round(latency_ms, 2), "مللي ثانية")
        print("التكلفة التقديرية:", round(estimated_cost, 8), "دولار")

        log_info("Minbar evaluation completed successfully")

    except Exception as e:
        log_error(str(e))
        print("حدث خطأ:", e)


run_evaluation()