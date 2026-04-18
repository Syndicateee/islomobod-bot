from telegram import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo


def main_menu_keyboard(is_admin: bool = False, mini_app_url: str | None = None):
    row1 = [KeyboardButton("🍽 Buyurtma berish"), KeyboardButton("🏠 Xona band qilish")]
    row2 = [KeyboardButton("🖼 Taomlar")]
    if mini_app_url:
        row2.append(KeyboardButton("📱 Mini App", web_app=WebAppInfo(url=mini_app_url)))
    else:
        row2.append(KeyboardButton("📱 Mini App"))
    rows = [row1, row2, [KeyboardButton("📍 Kontakt")]]
    if is_admin:
        rows.append([KeyboardButton("⚙️ Admin panel")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def phone_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Telefon yuborish", request_contact=True)], ["⬅️ Bekor qilish"]],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Telefon tugmasini bosing",
    )


def location_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📍 Lokatsiya yuborish", request_location=True)], ["⬅️ Bekor qilish"]],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Lokatsiya tugmasini bosing",
    )
