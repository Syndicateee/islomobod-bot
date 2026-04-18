from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from config import ADMIN_IDS, ADMIN_CHAT_ID, CLICK_CARD_NUMBER, CLICK_CARD_OWNER
from keyboards.inline import amount_keyboard, addons_keyboard, addons_minus_keyboard, payment_keyboard, admin_order_keyboard
from keyboards.reply import main_menu_keyboard, phone_keyboard, location_keyboard
from database import create_order, set_order_payment_proof, get_delivery_addons
from states import (
    DELIVERY_AMOUNT,
    DELIVERY_MANUAL_AMOUNT,
    DELIVERY_ADDONS,
    DELIVERY_NAME,
    DELIVERY_PHONE,
    DELIVERY_ADDRESS,
    DELIVERY_NOTE,
    DELIVERY_PAYMENT,
    DELIVERY_PROOF,
)
from utils import addons_total, addons_text, format_price, normalize_phone, priority_label, safe_json_dumps


def calculate_food_total(food: dict, amount_value: str):
    options_map = food.get("options_map", {})
    if amount_value in options_map:
        return int(options_map[amount_value])
    price_per_unit = food.get("price_per_unit")
    if price_per_unit:
        return int(float(amount_value) * price_per_unit)
    return 0


def calculate_plate_details(food: dict, amount_value: str):
    rules = food.get("plate_rules", {})
    items = rules.get(amount_value, [])
    if not items:
        return 0, "Yo'q"
    total = sum(qty * price for _, qty, price in items)
    text = ", ".join(
        f"{title} x{qty} ({format_price(qty * price)})" for title, qty, price in items
    )
    return total, text


def selected_addons_price_lines(context, selected: dict) -> list[str]:
    addon_map = get_delivery_addons()
    if not selected:
        return ["   • Qo'shimcha tanlanmagan"]
    lines = []
    for key, qty in selected.items():
        addon = addon_map.get(key)
        if not addon or qty <= 0:
            continue
        unit_price = int(addon["price"])
        subtotal = unit_price * qty
        qty_text = f"{qty} ta" if qty > 1 else "1 ta"
        lines.append(
            f"   • {addon['title']} — {qty_text} × {format_price(unit_price)} = {format_price(subtotal)}"
        )
    return lines or ["   • Qo'shimcha tanlanmagan"]


def build_preview_text(context):
    food = context.bot_data["menu"][context.user_data["food_key"]]
    food_total = calculate_food_total(food, context.user_data["amount_value"])
    plate_total, plate_text = calculate_plate_details(food, context.user_data["amount_value"])
    extra_total = addons_total(context.user_data.get("selected_addons", {}))
    total_price = food_total + plate_total + extra_total

    context.user_data["food_total_price"] = food_total
    context.user_data["plate_total_price"] = plate_total
    context.user_data["plate_text"] = plate_text
    context.user_data["addons_total_price"] = extra_total
    context.user_data["addons_json"] = safe_json_dumps(context.user_data.get("selected_addons", {}))
    context.user_data["addons_text"] = addons_text(context.user_data.get("selected_addons", {}))
    context.user_data["total_price"] = total_price
    context.user_data["price_note"] = food.get("price_note", "")

    lines = [
        "🧾 Yakuniy preview",
        "━━━━━━━━━━━━━━",
        "🍽 BUYURTMA TARKIBI",
        f"   • Asosiy taom: {context.user_data['food_title']}",
        f"   • Miqdor / izoh: {context.user_data['amount_value']}",
    ]
    if food_total:
        lines.append(f"   • Asosiy summa: {format_price(food_total)}")
    if plate_total:
        lines.append("")
        lines.append("🍽 LAGANLAR")
        lines.append(f"   • {plate_text}")
        lines.append(f"   • Laganlar summasi: {format_price(plate_total)}")
    lines.append("")
    lines.append("➕ QO'SHIMCHALAR")
    lines.extend(selected_addons_price_lines(context, context.user_data.get("selected_addons", {})))
    lines.append(f"   • Qo'shimcha summa: {format_price(extra_total)}")
    if context.user_data["price_note"]:
        lines.append("")
        lines.append(f"ℹ️ Eslatma: {context.user_data['price_note']}")
    lines.append("━━━━━━━━━━━━━━")
    lines.append(f"✅ Umumiy summa: {format_price(total_price)}")
    lines.append("")
    lines.append("✍️ Ismingizni kiriting:")
    return "\n".join(lines)


def build_addons_text(context, selected: dict, minus_mode: bool = False) -> str:
    food = context.bot_data["menu"][context.user_data["food_key"]]
    amount_value = context.user_data.get("amount_value", "-")
    food_total = calculate_food_total(food, amount_value)
    plate_total, plate_text = calculate_plate_details(food, amount_value)
    extra_total = addons_total(selected)
    grand_total = food_total + plate_total + extra_total

    lines = [
        "🛒 Buyurtmani to'ldiring",
        "━━━━━━━━━━━━━━",
        f"🍽 Taom: {context.user_data.get('food_title', '-')}",
        f"📏 Miqdor: {amount_value}",
        f"💰 Asosiy summa: {format_price(food_total)}",
    ]
    if plate_total:
        lines.append(f"🍽 Laganlar: {plate_text}")
        lines.append(f"💵 Laganlar summasi: {format_price(plate_total)}")
    lines.append("")
    lines.append("➕ Tanlangan qo'shimchalar:")
    lines.extend(selected_addons_price_lines(context, selected))
    lines.append(f"🧮 Qo'shimcha summa: {format_price(extra_total)}")
    lines.append("━━━━━━━━━━━━━━")
    lines.append(f"✅ Joriy umumiy summa: {format_price(grand_total)}")
    lines.append("")
    if minus_mode:
        lines.append("Keraksiz mahsulotni kamaytirish uchun tugmani bosing:")
    else:
        lines.append("Kerakli qo'shimchalarni tanlang. Har bosishda summa shu joyning o'zida yangilanadi.")
    return "\n".join(lines)


async def food_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    key = q.data.split(":", 1)[1]
    food = context.bot_data["menu"][key]
    context.user_data["food_key"] = key
    context.user_data["food_title"] = food["title"]

    if food.get("mode") == "description":
        await q.message.reply_text(food.get("description_prompt", "Buyurtma tafsilotlarini yozing."))
        return DELIVERY_MANUAL_AMOUNT

    if not food.get("options"):
        await q.message.reply_text("Miqdorni kiriting:", reply_markup=None)
        return DELIVERY_MANUAL_AMOUNT

    await q.message.reply_text("Miqdorni tanlang:", reply_markup=amount_keyboard(key))
    return DELIVERY_AMOUNT


async def amount_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    val = q.data.split(":", 1)[1]
    if val == "manual":
        await q.message.reply_text("Miqdorni qo'lda kiriting. Masalan: 1.3 kg yoki 3 porsiya")
        return DELIVERY_MANUAL_AMOUNT
    context.user_data["amount_value"] = val
    context.user_data["selected_addons"] = {}
    await q.message.reply_text(build_addons_text(context, {}), reply_markup=addons_keyboard({}))
    return DELIVERY_ADDONS


async def amount_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["amount_value"] = update.message.text.strip()
    context.user_data["selected_addons"] = {}
    await update.message.reply_text(build_addons_text(context, {}), reply_markup=addons_keyboard({}))
    return DELIVERY_ADDONS


async def addons_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except Exception:
        pass

    parts = q.data.split(":")
    action = parts[1]
    selected = dict(context.user_data.get("selected_addons", {}))

    if action == "add":
        key = parts[2]
        selected[key] = selected.get(key, 0) + 1
        context.user_data["selected_addons"] = selected
        text = build_addons_text(context, selected)
        markup = addons_keyboard(selected)
    elif action == "minus_menu":
        text = build_addons_text(context, selected, minus_mode=True)
        markup = addons_minus_keyboard(selected)
    elif action == "minus":
        key = parts[2]
        if key in selected:
            selected[key] -= 1
            if selected[key] <= 0:
                selected.pop(key)
        context.user_data["selected_addons"] = selected
        text = build_addons_text(context, selected, minus_mode=True)
        markup = addons_minus_keyboard(selected)
    elif action == "back":
        text = build_addons_text(context, selected)
        markup = addons_keyboard(selected)
    elif action == "done":
        text = build_preview_text(context)
        markup = None
    else:
        return DELIVERY_ADDONS

    try:
        await q.edit_message_text(text, reply_markup=markup)
    except Exception as e:
        err = str(e).lower()
        if "message is not modified" not in err:
            try:
                if action == "done":
                    await q.message.reply_text(text)
                else:
                    await q.message.reply_text(text, reply_markup=markup)
            except Exception:
                pass

    return DELIVERY_NAME if action == "done" else DELIVERY_ADDONS


async def name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = (update.message.text or "").strip()
    if len(name) < 2:
        await update.message.reply_text("Iltimos, ismingizni to'g'ri kiriting.")
        return DELIVERY_NAME

    context.user_data["name"] = name
    await update.message.reply_text(
        "📱 Telefon raqamingizni pastdagi tugma orqali yuboring:",
        reply_markup=phone_keyboard(),
    )
    return DELIVERY_PHONE


async def phone_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        context.user_data["phone"] = update.message.contact.phone_number
    else:
        text = (update.message.text or "").strip()
        phone = normalize_phone(text)
        if not phone or len(phone) < 9:
            await update.message.reply_text(
                "Iltimos, telefon raqamingizni pastdagi tugma orqali yuboring.",
                reply_markup=phone_keyboard(),
            )
            return DELIVERY_PHONE
        context.user_data["phone"] = phone

    await update.message.reply_text(
        "📍 Lokatsiyangizni pastdagi tugma orqali yuboring:",
        reply_markup=location_keyboard(),
    )
    return DELIVERY_ADDRESS


async def address_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.location:
        loc = update.message.location
        context.user_data["address"] = "Telegram lokatsiya yuborildi 📍"
        context.user_data["address_lat"] = loc.latitude
        context.user_data["address_lon"] = loc.longitude
    else:
        text = (update.message.text or "").strip()
        if not text or text == "📍 Lokatsiya yuborish":
            await update.message.reply_text(
                "Iltimos, lokatsiyangizni pastdagi tugma orqali yuboring.",
                reply_markup=location_keyboard(),
            )
            return DELIVERY_ADDRESS
        context.user_data["address"] = text
    await update.message.reply_text("Izoh bo'lsa yozing. Bo'lmasa 0 yuboring:")
    return DELIVERY_NOTE


async def note_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    note = update.message.text.strip()
    context.user_data["note"] = "" if note == "0" else note
    await update.message.reply_text("To'lov turini tanlang:", reply_markup=payment_keyboard())
    return DELIVERY_PAYMENT


def order_card(order_id, data, payment):
    note_line = f"📝 Izoh: {data['note']}\n" if data.get("note") else ""
    price_note_line = f"ℹ️ Eslatma: {data['price_note']}\n" if data.get("price_note") else ""
    plate_line = (
        f"🍽 Laganlar: {data['plate_text']}\n"
        f"💵 Laganlar summasi: {format_price(data['plate_total_price'])}\n"
        if data.get("plate_total_price") else ""
    )
    addons_line = f"➕ Qo'shimchalar: {data.get('addons_text', 'Yo\'q')}\n"
    return (
        f"🧾 BUYURTMA #{order_id}\n"
        f"━━━━━━━━━━━━━━\n"
        f"👤 Mijoz: {data['name']}\n"
        f"📞 Telefon: {data['phone']}\n"
        f"📍 Yetkazib berish manzili: {data['address']}\n"
        f"💳 To'lov turi: {payment}\n"
        f"━━━━━━━━━━━━━━\n"
        f"🍽 Asosiy taom: {data['food_title']}\n"
        f"📏 Miqdor / izoh: {data['amount_value']}\n"
        f"💰 Asosiy summa: {format_price(data['food_total_price'])}\n"
        f"{plate_line}"
        f"{addons_line}"
        f"🧮 Qo'shimcha summa: {format_price(data.get('addons_total_price', 0))}\n"
        f"{note_line}"
        f"{price_note_line}"
        f"━━━━━━━━━━━━━━\n"
        f"✅ Umumiy summa: {format_price(data['total_price'])}"
    )



async def _send_order_location_if_available(context, chat_id, data):
    lat = data.get("address_lat")
    lon = data.get("address_lon")
    if lat is None or lon is None:
        return
    try:
        await context.bot.send_location(chat_id=chat_id, latitude=lat, longitude=lon)
    except Exception:
        pass


async def payment_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    method = q.data.split(":", 1)[1]
    context.user_data["payment_method"] = method
    if method == "cash":
        order_id = create_order(context.user_data, update.effective_user.id)
        user_text = order_card(order_id, context.user_data, "Naqd")
        await q.message.reply_text(
            user_text + "\n\n📞 Buyurtmani tasdiqlash uchun sizga qo'ng'iroq bo'ladi.",
            reply_markup=main_menu_keyboard(update.effective_user.id in ADMIN_IDS),
        )
        admin_text = f"{priority_label(context.user_data['total_price'])}\n\n{user_text}\n\n⚡ TEZKOR TASDIQLASH KERAK"
        for admin_id in ADMIN_IDS:
            try:
                await _send_order_location_if_available(context, admin_id, context.user_data)
                await context.bot.send_message(chat_id=admin_id, text=admin_text)
            except Exception:
                pass
        try:
            await _send_order_location_if_available(context, ADMIN_CHAT_ID, context.user_data)
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=admin_text,
                reply_markup=admin_order_keyboard(order_id, update.effective_user.id),
            )
        except Exception:
            pass
        context.user_data.clear()
        return ConversationHandler.END

    order_id = create_order(context.user_data, update.effective_user.id)
    context.user_data["current_order_id"] = order_id
    await q.message.reply_text(
        order_card(order_id, context.user_data, "Click")
        + f"\n\n💳 Click orqali to'lov qiling\n{CLICK_CARD_NUMBER}\n{CLICK_CARD_OWNER}\n\n📸 To'lovdan keyin screenshot yuboring."
    )
    return DELIVERY_PROOF


async def proof_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Iltimos, screenshotni rasm tarzida yuboring.")
        return DELIVERY_PROOF
    file_id = update.message.photo[-1].file_id
    order_id = context.user_data.get("current_order_id")
    if not order_id:
        await update.message.reply_text("Buyurtma topilmadi.", reply_markup=main_menu_keyboard())
        context.user_data.clear()
        return ConversationHandler.END
    set_order_payment_proof(order_id, file_id)
    user_text = order_card(order_id, context.user_data, "Click")
    caption = f"{priority_label(context.user_data['total_price'])}\n💳 CLICK TO'LOV KELDI\n\n{user_text}\n\n📸 Screenshot tekshiring"
    for admin_id in ADMIN_IDS:
        try:
            await _send_order_location_if_available(context, admin_id, context.user_data)
            await context.bot.send_photo(chat_id=admin_id, photo=file_id, caption=caption)
        except Exception:
            pass
    try:
        await _send_order_location_if_available(context, ADMIN_CHAT_ID, context.user_data)
        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=file_id,
            caption=caption,
            reply_markup=admin_order_keyboard(order_id, update.effective_user.id),
        )
    except Exception:
        pass
    await update.message.reply_text(
        order_card(order_id, context.user_data, "Click")
        + "\n\n✅ To'lov skrinshoti qabul qilindi. Tekshiruvdan so'ng tasdiqlanadi.",
        reply_markup=main_menu_keyboard(update.effective_user.id in ADMIN_IDS),
    )
    context.user_data.clear()
    return ConversationHandler.END
