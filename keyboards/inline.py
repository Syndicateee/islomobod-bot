from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from datetime import date
from calendar import monthcalendar, month_name
from config import LUNCH_TIMES, DINNER_TIMES
from database import get_delivery_menu, get_delivery_addons, list_menu_items, list_addons

WEEKDAYS = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]


def food_keyboard(back_callback="back_main", back_label="⬅️ Bosh menyu"):
    menu = get_delivery_menu()
    rows = []
    items = list(menu.items())
    for i in range(0, len(items), 2):
        row = []
        for key, item in items[i:i+2]:
            row.append(InlineKeyboardButton(item["title"], callback_data=f"food:{key}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(back_label, callback_data=back_callback)])
    return InlineKeyboardMarkup(rows)


def amount_keyboard(food_key, back_callback="back_main", back_label="⬅️ Ortga qaytish"):
    menu = get_delivery_menu()
    opts = menu[food_key]["options"]
    rows, cur = [], []
    for i, opt in enumerate(opts, start=1):
        cur.append(InlineKeyboardButton(opt, callback_data=f"amount:{opt}"))
        if i % 3 == 0:
            rows.append(cur)
            cur = []
    if cur:
        rows.append(cur)
    rows += [[InlineKeyboardButton("⌨️ Qo'lda kiritish", callback_data="amount:manual")],[InlineKeyboardButton(back_label, callback_data=back_callback)]]
    return InlineKeyboardMarkup(rows)


def addons_keyboard(selected):
    addon_map = get_delivery_addons()
    keys = list(addon_map.keys())
    rows = []
    for i in range(0, len(keys), 2):
        row = []
        for key in keys[i:i+2]:
            qty = selected.get(key, 0)
            row.append(InlineKeyboardButton(f"{addon_map[key]['title']} x{qty}", callback_data=f"addon:add:{key}"))
        rows.append(row)
    rows += [[InlineKeyboardButton("➖ Kamaytirish", callback_data="addon:minus_menu"), InlineKeyboardButton("➡️ Yakunlash", callback_data="addon:done")],[InlineKeyboardButton("⬅️ Bosh menyu", callback_data="back_main")]]
    return InlineKeyboardMarkup(rows)


def addons_minus_keyboard(selected):
    addon_map = get_delivery_addons()
    keys = list(addon_map.keys())
    rows = []
    for i in range(0, len(keys), 2):
        row = []
        for key in keys[i:i+2]:
            qty = selected.get(key, 0)
            row.append(InlineKeyboardButton(f"➖ {addon_map[key]['title']} ({qty})", callback_data=f"addon:minus:{key}"))
        rows.append(row)
    rows += [[InlineKeyboardButton("⬅️ Ro'yxatga qaytish", callback_data="addon:back")],[InlineKeyboardButton("➡️ Yakunlash", callback_data="addon:done")]]
    return InlineKeyboardMarkup(rows)


def payment_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("💵 Naqd", callback_data="pay:cash"), InlineKeyboardButton("💳 Click", callback_data="pay:click")],[InlineKeyboardButton("⬅️ Bosh menyu", callback_data="back_main")]])


def date_keyboard(year=None, month=None, prefix='bdate', nav_prefix='bcnav', back_callback='back_main', back_label='⬅️ Ortga qaytish'):
    today = date.today(); year = year or today.year; month = month or today.month
    rows = [[InlineKeyboardButton(f"{month_name[month]} {year}", callback_data="ignore")]]
    rows.append([InlineKeyboardButton(day, callback_data="ignore") for day in WEEKDAYS])
    for week in monthcalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="ignore")); continue
            current = date(year, month, day)
            if current < today and prefix != 'admin_report_date' and prefix != 'admin_export_date':
                row.append(InlineKeyboardButton("·", callback_data="ignore"))
            else:
                row.append(InlineKeyboardButton(str(day), callback_data=f"{prefix}:{current.isoformat()}"))
        rows.append(row)
    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    rows.append([InlineKeyboardButton("⬅️", callback_data=f"{nav_prefix}:{prev_year}:{prev_month}"), InlineKeyboardButton("Bugun", callback_data=f"{nav_prefix}:{today.year}:{today.month}"), InlineKeyboardButton("➡️", callback_data=f"{nav_prefix}:{next_year}:{next_month}")])
    rows.append([InlineKeyboardButton(back_label, callback_data=back_callback)])
    return InlineKeyboardMarkup(rows)


def slot_keyboard(back_callback='back_main', back_label='⬅️ Ortga qaytish'):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🍽 Tushlik", callback_data="slot:lunch"), InlineKeyboardButton("🌙 Kechki", callback_data="slot:dinner")],[InlineKeyboardButton(back_label, callback_data=back_callback)]])


def time_keyboard(slot, back_callback='back_main', back_label='⬅️ Ortga qaytish'):
    times = LUNCH_TIMES if slot == "lunch" else DINNER_TIMES
    rows, cur = [], []
    for t in times:
        cur.append(InlineKeyboardButton(t, callback_data=f"btime:{t}"))
        if len(cur) == 2:
            rows.append(cur); cur = []
    if cur: rows.append(cur)
    if slot == "dinner": rows.append([InlineKeyboardButton("⌨️ Qo'lda kiriting", callback_data="btime:manual")])
    rows.append([InlineKeyboardButton(back_label, callback_data=back_callback)])
    return InlineKeyboardMarkup(rows)


def admin_order_keyboard(order_id, user_id):
    return InlineKeyboardMarkup([[InlineKeyboardButton("✅ Tasdiq", callback_data=f"oadmin:confirm:{order_id}:{user_id}"), InlineKeyboardButton("🔄 Jarayon", callback_data=f"oadmin:cooking:{order_id}:{user_id}")],[InlineKeyboardButton("🚚 Jo'natildi", callback_data=f"oadmin:sent:{order_id}:{user_id}"), InlineKeyboardButton("❌ Rad", callback_data=f"oadmin:cancel:{order_id}:{user_id}")]])


def admin_booking_keyboard(booking_id, user_id):
    return InlineKeyboardMarkup([[InlineKeyboardButton("✅ Tasdiq", callback_data=f"badmin:confirm:{booking_id}:{user_id}"), InlineKeyboardButton("❌ Bekor", callback_data=f"badmin:cancel:{booking_id}:{user_id}")]])


def admin_panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Hisobot", callback_data="admin:report_date_picker"), InlineKeyboardButton("📤 Excelga export", callback_data="admin:export_menu")],
        [InlineKeyboardButton("🏠 Xonalar holati", callback_data="admin:rooms_today"), InlineKeyboardButton("➕ Band kiritish", callback_data="admin:add_booking")],
    ])



def export_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Bugun", callback_data="admin:export_today"), InlineKeyboardButton("🗓 Kunni belgilash", callback_data="admin:export_date_picker")],
        [InlineKeyboardButton("📆 Oylik", callback_data="admin:export_month")],
        [InlineKeyboardButton("⬅️ Ortga qaytish", callback_data="admin:home")],
    ])



def export_month_picker_keyboard(year=None):
    today = date.today()
    year = year or today.year
    months = [
        [InlineKeyboardButton(f"{i:02d}-oy", callback_data=f"admin:export_month_select:{year}:{i}") for i in range(1, 4)],
        [InlineKeyboardButton(f"{i:02d}-oy", callback_data=f"admin:export_month_select:{year}:{i}") for i in range(4, 7)],
        [InlineKeyboardButton(f"{i:02d}-oy", callback_data=f"admin:export_month_select:{year}:{i}") for i in range(7, 10)],
        [InlineKeyboardButton(f"{i:02d}-oy", callback_data=f"admin:export_month_select:{year}:{i}") for i in range(10, 13)],
        [
            InlineKeyboardButton("⬅️", callback_data=f"admin:export_month_nav:{year-1}"),
            InlineKeyboardButton(str(year), callback_data="ignore"),
            InlineKeyboardButton("➡️", callback_data=f"admin:export_month_nav:{year+1}"),
        ],
        [InlineKeyboardButton("⬅️ Export menyu", callback_data="admin:export_menu")],
    ]
    return InlineKeyboardMarkup(months)

def menu_edit_keyboard():
    rows = []
    for item in list_menu_items():
        label = item['title'][:24]
        rows.append([InlineKeyboardButton(label, callback_data=f"admin:menu_item:{item['item_key']}")])
    rows.append([InlineKeyboardButton("⬅️ Ortga qaytish", callback_data="admin:home")])
    return InlineKeyboardMarkup(rows)


def menu_item_options_keyboard(item_key: str):
    item = next((x for x in list_menu_items() if x['item_key'] == item_key), None)
    rows = []
    if item:
        for opt in item['options']:
            rows.append([InlineKeyboardButton(f"{opt['option_label']} — {opt['price']}", callback_data=f"admin:menu_price:{item_key}:{opt['option_label']}")])
    rows.append([InlineKeyboardButton("⬅️ Menu ro'yxati", callback_data="admin:menu_edit")])
    return InlineKeyboardMarkup(rows)


def addon_edit_keyboard():
    rows = []
    for addon in list_addons():
        rows.append([InlineKeyboardButton(f"{addon['title']} — {addon['price']}", callback_data=f"admin:addon_price:{addon['addon_key']}")])
    rows.append([InlineKeyboardButton("⬅️ Ortga qaytish", callback_data="admin:home")])
    return InlineKeyboardMarkup(rows)


def mini_app_keyboard(url: str):
    return InlineKeyboardMarkup([[InlineKeyboardButton("📱 Mini Appni ochish", web_app=WebAppInfo(url=url))],[InlineKeyboardButton("⬅️ Bosh menyu", callback_data="back_main")]])
