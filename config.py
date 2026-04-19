import os
from pathlib import Path


def _load_local_env():
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"\'')
        os.environ.setdefault(key, value)


_load_local_env()


_load_local_env()

BOT_NAME = "Islomobod choyxonasi rasmiy boti"
BOT_USERNAME = "islomobodbuyurtma_bot"
PROJECT_NAME = "Elektron choyxona"

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS = {708053153,8325893970}
ADMIN_CHAT_ID = -1003367945654

CONTACT_PHONE = "+998997665597"
CONTACT_ADDRESS = "Andijon shahar, Samarqand ko'chasi 54-uy"
CONTACT_LANDMARK = "Toshkent mexmonxonasi ro'parasidan 100 metr kiriladi"

LOCATION_LAT = 40.756010
LOCATION_LON = 72.374123

CLICK_CARD_NUMBER = os.getenv("CLICK_CARD_NUMBER", "5614 6827 0667 9166")
CLICK_CARD_OWNER = os.getenv("CLICK_CARD_OWNER", "Karimjonov Abduvohid")

MINI_APP_URL = os.getenv("MINI_APP_URL", "https://syndicateee.github.io/islomobod-bot/miniapp/")

PRIORITY_THRESHOLD = 600000
VIP_THRESHOLD = 1000000

DB_NAME = "islomobod_bot.db"

DELIVERY_MENU = {
    "osh": {
        "title": "Osh",
        "options": ["400 gr", "600 gr", "800 gr", "1.0 kg", "1.2 kg", "1.4 kg", "1.6 kg", "1.8 kg", "2.0 kg"],
        "options_map": {
            "400 gr": 255000,
            "600 gr": 305000,
            "800 gr": 355000,
            "1.0 kg": 425000,
            "1.2 kg": 510000,
            "1.4 kg": 595000,
            "1.6 kg": 660000,
            "1.8 kg": 765000,
            "2.0 kg": 950000,
        },
        "plate_rules": {
            "400 gr": [("400 grlik lagan", 1, 12000)],
            "600 gr": [("600 grlik lagan", 1, 15000)],
            "800 gr": [("400 grlik lagan", 2, 12000)],
            "1.0 kg": [("1.0 kg lagan", 1, 25000)],
            "1.2 kg": [("1.0 kg lagan", 1, 25000), ("400 grlik lagan", 1, 12000)],
            "1.4 kg": [("1.0 kg lagan", 1, 25000), ("400 grlik lagan", 1, 12000)],
            "1.6 kg": [("1.0 kg lagan", 1, 25000), ("600 grlik lagan", 1, 15000)],
            "1.8 kg": [("1.0 kg lagan", 1, 25000), ("400 grlik lagan", 2, 12000)],
            "2.0 kg": [("1.0 kg lagan", 2, 25000)],
        },
    },
    "achchiq_osh": {
        "title": "Achchiq osh",
        "options": ["400 gr", "600 gr", "800 gr", "1.0 kg", "1.2 kg", "1.4 kg", "1.6 kg", "1.8 kg", "2.0 kg"],
        "options_map": {
            "400 gr": 255000,
            "600 gr": 305000,
            "800 gr": 355000,
            "1.0 kg": 425000,
            "1.2 kg": 510000,
            "1.4 kg": 595000,
            "1.6 kg": 660000,
            "1.8 kg": 765000,
            "2.0 kg": 950000,
        },
        "plate_rules": {
            "400 gr": [("400 grlik lagan", 1, 12000)],
            "600 gr": [("600 grlik lagan", 1, 15000)],
            "800 gr": [("400 grlik lagan", 2, 12000)],
            "1.0 kg": [("1.0 kg lagan", 1, 25000)],
            "1.2 kg": [("1.0 kg lagan", 1, 25000), ("400 grlik lagan", 1, 12000)],
            "1.4 kg": [("1.0 kg lagan", 1, 25000), ("400 grlik lagan", 1, 12000)],
            "1.6 kg": [("1.0 kg lagan", 1, 25000), ("600 grlik lagan", 1, 15000)],
            "1.8 kg": [("1.0 kg lagan", 1, 25000), ("400 grlik lagan", 2, 12000)],
            "2.0 kg": [("1.0 kg lagan", 2, 25000)],
        },
    },
    "dimlama": {
        "title": "Dimlama",
        "options": ["1.0 kg"],
        "options_map": {"1.0 kg": 300000},
        "price_note": "1.0 kg — 300 000 so'mdan 350 000 so'mgacha. Buyurtma yakunlangach choyxonadan aloqaga chiqilib aniqlashtiriladi.",
    },
    "qozon_kabob": {
        "title": "Qozon kabob",
        "options": ["1.0 kg"],
        "options_map": {"1.0 kg": 300000},
        "price_note": "1.0 kg — 300 000 so'mdan 350 000 so'mgacha. Buyurtma yakunlangach choyxonadan aloqaga chiqilib aniqlashtiriladi.",
    },
    "shorva": {
        "title": "Sho'rva",
        "options": ["1.0 kg"],
        "options_map": {"1.0 kg": 290000},
        "price_note": "1.0 kg — 290 000 so'm. Buyurtma yakunlangach choyxonadan aloqaga chiqilib aniqlashtiriladi.",
    },
    "boshqa_taom": {
        "title": "Boshqa taom buyurtma qilish",
        "options": [],
        "mode": "description",
        "description_prompt": "Qanday taom kerakligini, miqdorini va taxminiy odam sonini bitta xabarda yozing.",
        "price_note": "Narx buyurtma yakunlangach choyxonadan aloqaga chiqilib aniqlashtiriladi.",
    },
}

DELIVERY_ADDONS = {
    "bedana_tuxum": {"title": "Bedana tuxum (1 dona)", "price": 1000},
    "post_dumba_100": {"title": "Po'st dumba 100 gr", "price": 35000},
    "qazi_100": {"title": "Qazi 100 gr", "price": 45000},
    "shakarop": {"title": "Shakarop", "price": 12000},
    "suzma": {"title": "Suzma", "price": 12000},
    "svezhiy_salat": {"title": "Свежий салат", "price": 12000},
    "cola_1": {"title": "Cola 1.0 l", "price": 12000},
    "cola_15": {"title": "Cola 1.5 l", "price": 15000},
    "cola_2": {"title": "Cola 2.0 l", "price": 20000},
    "fanta_1": {"title": "Fanta 1.0 l", "price": 12000},
    "fanta_15": {"title": "Fanta 1.5 l", "price": 15000},
    "fanta_2": {"title": "Fanta 2.0 l", "price": 20000},
    "pepsi_1": {"title": "Pepsi 1.0 l", "price": 12000},
    "pepsi_15": {"title": "Pepsi 1.5 l", "price": 15000},
    "pepsi_2": {"title": "Pepsi 2.0 l", "price": 20000},
    "chortoq_05": {"title": "Chortoq suvi 0.5 l", "price": 12000},
    "chortoq_07": {"title": "Chortoq suvi 0.7 l", "price": 17000},
    "chortoq_05_premium": {"title": "Chortoq suvi 0.5 premium", "price": 17000},
    "chortoq_07_premium": {"title": "Chortoq suvi 0.7 premium", "price": 20000},
    "raya_025": {"title": "RAYA suvi 0.25 l", "price": 7000},
    "lipton_1": {"title": "Lipton 1.0 l", "price": 12000},
    "lipton_15": {"title": "Lipton 1.5 l", "price": 15000},
    "sok_1": {"title": "Sok 1.0 l", "price": 20000},
    "nataxtari_1": {"title": "Nataxtari 1.0 l", "price": 20000},
    "garden_1": {"title": "Garden 1.0 l", "price": 20000},
    "novvot_choy": {"title": "Novvot choy", "price": 10000},
    "limon_novvot_choy": {"title": "Limon + novvot choy", "price": 15000},
    "pista_100": {"title": "Pista 100 gr", "price": 35000},
    "bodom_100": {"title": "Bodom 100 gr", "price": 35000},
    "meva_assorti": {"title": "Meva assorti", "price": 65000},
    "non": {"title": "Non", "price": 7000},
}

LUNCH_TIMES = ["11:30", "12:00", "12:30", "13:00"]
DINNER_TIMES = ["17:00", "18:00", "19:00", "20:00", "21:00"]

ROOMS = [
    (105, 5), (108, 5), (109, 5), (110, 5), (111, 5), (114, 5), (208, 5), (211, 5),
    (101, 10), (102, 10), (103, 10), (106, 10), (107, 10), (112, 10), (113, 10),
    (201, 10), (202, 10), (203, 10), (206, 10), (207, 10), (212, 10), (213, 10),
    (104, 15), (115, 15), (204, 15), (215, 15),
    (100, 20),
]
