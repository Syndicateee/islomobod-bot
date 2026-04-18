from datetime import date

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ConversationHandler

from config import (
    ADMIN_IDS,
    BOT_NAME,
    CONTACT_ADDRESS,
    CONTACT_LANDMARK,
    CONTACT_PHONE,
    LOCATION_LAT,
    LOCATION_LON,
    MINI_APP_URL,
)
from database import get_user_bookings, get_user_orders
from keyboards.inline import admin_panel_keyboard, date_keyboard, food_keyboard, mini_app_keyboard
from keyboards.reply import main_menu_keyboard
from states import BOOK_DATE, DELIVERY_FOOD
from utils import format_price, safe_json_loads


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        f"🌿 Assalomu alaykum!\n\n"
        f"✨ {BOT_NAME} ga xush kelibsiz.\n\n"
        "Bu yerda siz mazali taomlarga buyurtma berishingiz, xonani oldindan band qilishingiz va kerakli ma'lumotlarni tezda olishingiz mumkin.\n\n"
        "Kerakli bo'limni tanlang:",
        reply_markup=main_menu_keyboard(update.effective_user.id in ADMIN_IDS, MINI_APP_URL),
    )


async def route_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    is_admin = update.effective_user.id in ADMIN_IDS

    if text == "🍽 Buyurtma berish":
        await update.message.reply_text(
            "🛵 Yetkazib berish bo'limi.", reply_markup=ReplyKeyboardRemove()
        )
        await update.message.reply_text("🍽 Menyudan taom tanlang:", reply_markup=food_keyboard())
        return DELIVERY_FOOD

    if text == "🏠 Xona band qilish":
        await update.message.reply_text("📅 Sanani tanlang:", reply_markup=ReplyKeyboardRemove())
        await update.message.reply_text(
            "To'liq kalendardan kerakli sanani tanlang:", reply_markup=date_keyboard()
        )
        return BOOK_DATE


    if text == "🖼 Taomlar":
        await update.message.reply_text(
            "🖼 Taomlar bo‘limi tez orada ishga tushadi.\n\nTez orada taomlarimiz ko‘rinishi bo‘yicha rasmlar yuklanadi va siz menyuni yanada qulay ko‘rishingiz mumkin bo‘ladi 🙂",
            reply_markup=main_menu_keyboard(is_admin, MINI_APP_URL),
        )
        return ConversationHandler.END


    if text == "📱 Mini App":
        await update.message.reply_text(
            "📱 Mini App tugmasi orqali ilova ochiladi. Agar ilova ochilmagan bo‘lsa, shu yerdagi tugma orqali sinab ko‘ring.",
            reply_markup=mini_app_keyboard(MINI_APP_URL),
        )
        return ConversationHandler.END

    if text == "📍 Kontakt":
        await update.message.reply_text(
            f"📞 {BOT_NAME}\n\n"
            f"📍 Manzil: {CONTACT_ADDRESS}\n"
            f"☎️ Telefon: {CONTACT_PHONE}\n"
            f"🧭 Mo'ljal: {CONTACT_LANDMARK}",
            reply_markup=main_menu_keyboard(is_admin, MINI_APP_URL),
        )
        await update.message.reply_location(latitude=LOCATION_LAT, longitude=LOCATION_LON)
        return ConversationHandler.END

    if text == "📦 Mening buyurtmalarim":
        orders = get_user_orders(update.effective_user.id)
        bookings = get_user_bookings(update.effective_user.id)
        msgs = []
        if orders:
            msgs.append("🛵 Buyurtmalar:")
            for o in orders:
                addons = safe_json_loads(o["addons_json"])
                addon_text = ", ".join(f"{k} x{v}" for k, v in addons.items()) if addons else "Yo'q"
                msgs.append(
                    f"#{o['id']} | {o['food_title']} | {o['amount_value']} | {addon_text} | {format_price(o['total_price'])} | {o['status']}"
                )
        if bookings:
            msgs.append("\n🏠 Bandlar:")
            for b in bookings:
                msgs.append(
                    f"#{b['id']} | {b['booking_date']} {b['booking_time']} | xona {b['room_no']} | {b['status']}"
                )
        if not msgs:
            msgs = ["Sizda hozircha buyurtmalar yo'q."]
        await update.message.reply_text("\n".join(msgs), reply_markup=main_menu_keyboard(is_admin, MINI_APP_URL))
        return ConversationHandler.END




    if text == "⚙️ Admin panel":
        if not is_admin:
            await update.message.reply_text(
                "Bu bo'lim faqat adminlar uchun.", reply_markup=main_menu_keyboard(False, MINI_APP_URL)
            )
            return ConversationHandler.END
        await update.message.reply_text(
            "🛠 Admin panel bo'limlari:", reply_markup=admin_panel_keyboard()
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Iltimos, menyudan tanlang.", reply_markup=main_menu_keyboard(is_admin)
    )
    return ConversationHandler.END


async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data.clear()
    await q.message.reply_text(
        "🏠 Bosh menyu.", reply_markup=main_menu_keyboard(q.from_user.id in ADMIN_IDS, MINI_APP_URL)
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Bekor qilindi.", reply_markup=main_menu_keyboard(update.effective_user.id in ADMIN_IDS, MINI_APP_URL)
    )
    return ConversationHandler.END
