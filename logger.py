import logging
import os

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "minbar.log")

# إنشاء مجلد السجلات إذا لم يكن موجودًا
os.makedirs(LOG_DIR, exist_ok=True)

# إعداد نظام التسجيل
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("minbar")


def log_error(message: str):
    logger.error(message)


def log_info(message: str):
    logger.info(message)