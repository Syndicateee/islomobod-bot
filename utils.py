import json
from database import get_delivery_addons


def format_price(v):
    return f"{int(v):,}".replace(",", " ") + " so'm"


def normalize_phone(text: str) -> str:
    return text.strip()


def addons_total(selected: dict) -> int:
    addon_map = get_delivery_addons()
    total = 0
    for key, qty in selected.items():
        if key in addon_map and qty > 0:
            total += addon_map[key]["price"] * qty
    return total


def addons_text(selected: dict) -> str:
    addon_map = get_delivery_addons()
    if not selected:
        return "Yo'q"
    parts = []
    for key, qty in selected.items():
        if key in addon_map and qty > 0:
            parts.append(f"{addon_map[key]['title']} x{qty}")
    return ", ".join(parts) if parts else "Yo'q"


def priority_label(total_price: int) -> str:
    from config import PRIORITY_THRESHOLD, VIP_THRESHOLD
    if total_price >= VIP_THRESHOLD:
        return "🚨🔥 VIP BUYURTMA"
    if total_price >= PRIORITY_THRESHOLD:
        return "🚨 MUHIM BUYURTMA"
    return "🆕 YANGI BUYURTMA"


def safe_json_dumps(data):
    return json.dumps(data, ensure_ascii=False)


def safe_json_loads(text):
    try:
        return json.loads(text) if text else {}
    except Exception:
        return {}
