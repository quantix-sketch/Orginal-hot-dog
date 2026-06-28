import os

# ============================================
#   ORGINAL XOTDOG BOT - CONFIG
# ============================================

def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int_list(name: str, default: str = "") -> list[int]:
    raw = os.getenv(name, default)
    ids: list[int] = []
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError:
            raise ValueError(f"{name} faqat raqamli Telegram IDlardan iborat bo'lishi kerak") from None
    return ids


BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_IDS = _env_int_list("ADMIN_IDS", "123456789")

# To'lov tizimi
PAYME_MERCHANT_ID = os.getenv("PAYME_MERCHANT_ID", "YOUR_PAYME_MERCHANT_ID")
PAYME_SECRET_KEY = os.getenv("PAYME_SECRET_KEY", "YOUR_PAYME_SECRET_KEY")
PAYME_TEST_MODE = _env_bool("PAYME_TEST_MODE", True)

CLICK_SERVICE_ID = os.getenv("CLICK_SERVICE_ID", "YOUR_CLICK_SERVICE_ID")
CLICK_MERCHANT_ID = os.getenv("CLICK_MERCHANT_ID", "YOUR_CLICK_MERCHANT_ID")
CLICK_SECRET_KEY = os.getenv("CLICK_SECRET_KEY", "YOUR_CLICK_SECRET_KEY")

# Mini App URL (deploy qilgandan keyin o'zgartiring)
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-app.railway.app").rstrip("/")
PORT = int(os.getenv("PORT", "8080"))

# Database
DB_PATH = os.getenv("DB_PATH", "xotdog.db")

# Restoran ma'lumoti
RESTAURANT_NAME = os.getenv("RESTAURANT_NAME", "Orginal Xotdog")
RESTAURANT_PHONE = os.getenv("RESTAURANT_PHONE", "+998 XX XXX XX XX")
RESTAURANT_ADDRESS = os.getenv("RESTAURANT_ADDRESS", "Toshkent, ...")
