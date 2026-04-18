from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from keyboards.inline import slot_keyboard, time_keyboard, admin_booking_keyboard, date_keyboard
from keyboards.reply import main_menu_keyboard, phone_keyboard
from database import free_rooms, create_booking
from states import (
    BOOK_SLOT, BOOK_TIME, BOOK_CUSTOM_TIME, BOOK_PEOPLE, BOOK_NAME, BOOK_PHONE, BOOK_DATE,
    ADMIN_BOOK_DATE, ADMIN_BOOK_SLOT, ADMIN_BOOK_TIME, ADMIN_BOOK_CUSTOM_TIME,
    ADMIN_BOOK_PEOPLE, ADMIN_BOOK_NAME, ADMIN_BOOK_PHONE,
)
from config import ADMIN_IDS, ADMIN_CHAT_ID
from utils import normalize_phone


def _booking_state_keys(admin_mode: bool):
    if admin_mode:
        return {
            "date": ADMIN_BOOK_DATE,
            "slot": ADMIN_BOOK_SLOT,
            "time": ADMIN_BOOK_TIME,
            "custom_time": ADMIN_BOOK_CUSTOM_TIME,
            "people": ADMIN_BOOK_PEOPLE,
            "name": ADMIN_BOOK_NAME,
            "phone": ADMIN_BOOK_PHONE,
        }
    return {
        "date": BOOK_DATE,
        "slot": BOOK_SLOT,
        "time": BOOK_TIME,
        "custom_time": BOOK_CUSTOM_TIME,
        "people": BOOK_PEOPLE,
        "name": BOOK_NAME,
        "phone": BOOK_PHONE,
    }


def _is_admin_mode(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return bool(context.user_data.get("admin_booking_mode"))


def _admin_back_kwargs(context):
    if context.user_data.get('admin_booking_mode'):
        return {'back_callback': 'admin:home', 'back_label': '⬅️ Ortga qaytish'}
    return {}


async def admin_add_booking_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id not in ADMIN_IDS:
        if update.callback_query:
            try:
                await update.callback_query.answer("Bu bo'lim faqat adminlar uchun.", show_alert=True)
            except Exception:
                pass
        elif update.message:
            await update.message.reply_text("Bu buyruq faqat adminlar uchun.")
        return ConversationHandler.END

    context.user_data.clear()
    context.user_data["admin_booking_mode"] = True
    context.user_data["booking_source"] = "admin"

    text_msg = "Admin band kiritish rejimi yoqildi.\nMijoz uchun sanani tanlang:"
    markup = date_keyboard(**_admin_back_kwargs(context))

    if update.callback_query:
        q = update.callback_query
        try:
            await q.answer()
        except Exception:
            pass
        try:
            await q.edit_message_text(text_msg, reply_markup=markup)
        except Exception:
            await q.message.reply_text(text_msg, reply_markup=markup)
    else:
        await update.message.reply_text(text_msg, reply_markup=markup)
    return ADMIN_BOOK_DATE



async def calendar_navigate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, year, month = q.data.split(":")
    await q.message.edit_reply_markup(reply_markup=date_keyboard(int(year), int(month), **_admin_back_kwargs(context)))
    return _booking_state_keys(_is_admin_mode(context))["date"]


async def ignore_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    return _booking_state_keys(_is_admin_mode(context))["date"]


async def date_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["booking_date"] = q.data.split(":", 1)[1]
    await q.edit_message_text("Vaqt turini tanlang:", reply_markup=slot_keyboard(**_admin_back_kwargs(context)))
    return _booking_state_keys(_is_admin_mode(context))["slot"]


async def slot_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    slot = q.data.split(":", 1)[1]
    context.user_data["booking_slot"] = slot
    await q.edit_message_text("Vaqtni tanlang:", reply_markup=time_keyboard(slot, **_admin_back_kwargs(context)))
    return _booking_state_keys(_is_admin_mode(context))["time"]


async def time_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    value = q.data.split(":", 1)[1]

    if value == "manual":
        try:
            await q.edit_message_text("Vaqtni qo'lda kiriting. Masalan: 20:30\nYoki ⬅️ Bekor qilish deb yozing.")
        except Exception:
            await q.message.reply_text("Vaqtni qo'lda kiriting. Masalan: 20:30\nYoki ⬅️ Bekor qilish deb yozing.")
        return _booking_state_keys(_is_admin_mode(context))["custom_time"]

    context.user_data["booking_time"] = value
    try:
        await q.edit_message_text("Odam sonini yozing, men sizga mos xonani band qilaman:")
    except Exception:
        await q.message.reply_text("Odam sonini yozing, men sizga mos xonani band qilaman:")
    return _booking_state_keys(_is_admin_mode(context))["people"]


async def custom_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    if value == "⬅️ Bekor qilish":
        context.user_data.clear()
        await update.message.reply_text(
            "Bekor qilindi.",
            reply_markup=main_menu_keyboard(update.effective_user.id in ADMIN_IDS),
        )
        return ConversationHandler.END

    import re
    if not re.fullmatch(r"(?:[01]?\d|2[0-3]):[0-5]\d", value):
        await update.message.reply_text("Vaqtni HH:MM formatda kiriting. Masalan: 20:30")
        return _booking_state_keys(_is_admin_mode(context))["custom_time"]

    context.user_data["booking_time"] = value
    await update.message.reply_text("Odam sonini yozing, men sizga mos xonani band qilaman:")
    return _booking_state_keys(_is_admin_mode(context))["people"]


async def people_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "⬅️ Bekor qilish":
        context.user_data.clear()
        await update.message.reply_text(
            "Bekor qilindi.",
            reply_markup=main_menu_keyboard(update.effective_user.id in ADMIN_IDS),
        )
        return ConversationHandler.END

    if not text.isdigit():
        await update.message.reply_text("Faqat raqam kiriting.")
        return _booking_state_keys(_is_admin_mode(context))["people"]

    people_count = int(text)
    if people_count <= 0:
        await update.message.reply_text("Odam soni 1 dan katta bo'lishi kerak.")
        return _booking_state_keys(_is_admin_mode(context))["people"]
    if people_count > 22:
        await update.message.reply_text("22 kishidan katta guruh uchun admin bilan alohida bog'laning.")
        return _booking_state_keys(_is_admin_mode(context))["people"]

    context.user_data["people_count"] = people_count
    rooms = free_rooms(
        context.user_data["booking_date"],
        context.user_data["booking_time"],
        people_count,
    )

    if not rooms:
        await update.message.reply_text(
            "Afsuski, bu vaqt uchun mos bo'sh xona topilmadi.",
            reply_markup=main_menu_keyboard(update.effective_user.id in ADMIN_IDS),
        )
        context.user_data.clear()
        return ConversationHandler.END

    best_room = dict(rooms[0])
    context.user_data["room_no"] = best_room["room_no"]
    context.user_data["room_capacity"] = best_room["capacity"]

    await update.message.reply_text(
        f"Men sizga mos xonani topdim:\n\n"
        f"🚪 Xona: {best_room['room_no']}\n"
        f"👥 Sig'imi: {best_room['capacity']} kishi\n"
        f"🧍 Sizning mehmonlaringiz: {people_count} ta\n\n"
        "Davom etish uchun ismni kiriting:\n\n⬅️ Bekor qilish deb yozsangiz jarayon to'xtaydi."
    )
    return _booking_state_keys(_is_admin_mode(context))["name"]


async def name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if name == "⬅️ Bekor qilish":
        context.user_data.clear()
        await update.message.reply_text(
            "Bekor qilindi.",
            reply_markup=main_menu_keyboard(update.effective_user.id in ADMIN_IDS),
        )
        return ConversationHandler.END

    if len(name) < 2:
        await update.message.reply_text("Ismni to'g'ri kiriting.")
        return _booking_state_keys(_is_admin_mode(context))["name"]

    context.user_data["name"] = name
    if _is_admin_mode(context):
        await update.message.reply_text("Mijoz telefon raqamini yozing:")
    else:
        await update.message.reply_text("Telefon raqamingizni yuboring. Pastdagi 📱 Telefon yuborish tugmasini bosing yoki raqamni qo'lda yozing:", reply_markup=phone_keyboard())
    return _booking_state_keys(_is_admin_mode(context))["phone"]


async def phone_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone_value = update.message.contact.phone_number
    else:
        text = (update.message.text or "").strip()
        if text == "⬅️ Bekor qilish":
            context.user_data.clear()
            await update.message.reply_text(
                "Bekor qilindi.",
                reply_markup=main_menu_keyboard(update.effective_user.id in ADMIN_IDS),
            )
            return ConversationHandler.END
        if text == "📱 Telefon yuborish":
            await update.message.reply_text("Telefon raqamingizni yuborish uchun pastdagi maxsus tugmani bosing yoki raqamni qo'lda yozing:", reply_markup=phone_keyboard())
            return _booking_state_keys(_is_admin_mode(context))["phone"]
        if not text:
            await update.message.reply_text("Telefon kiriting yoki tugmani bosing.", reply_markup=phone_keyboard() if not _is_admin_mode(context) else None)
            return _booking_state_keys(_is_admin_mode(context))["phone"]
        phone_value = normalize_phone(text)

    if len(''.join(ch for ch in phone_value if ch.isdigit())) < 9:
        await update.message.reply_text("Telefon raqamini to'g'ri kiriting yoki tugmani bosing.", reply_markup=phone_keyboard() if not _is_admin_mode(context) else None)
        return _booking_state_keys(_is_admin_mode(context))["phone"]

    context.user_data["phone"] = phone_value

    booking_id = create_booking(context.user_data, update.effective_user.id)

    summary_text = (
        f"🏠 BAND #{booking_id}\n\n"
        f"👤 Mijoz: {context.user_data['name']}\n"
        f"📞 Tel: {context.user_data['phone']}\n"
        f"📅 Sana: {context.user_data['booking_date']}\n"
        f"🕒 Soat: {context.user_data['booking_time']}\n"
        f"👥 Odam: {context.user_data['people_count']}\n"
        f"🚪 Xona: {context.user_data['room_no']}\n"
        f"📦 Xona sig'imi: {context.user_data['room_capacity']} kishi\n\n"
        "✅ Xona avtomatik band qilindi"
    )

    if _is_admin_mode(context):
        await update.message.reply_text(
            summary_text + "\n\n🛠 Bu band admin tomonidan kiritildi.",
            reply_markup=main_menu_keyboard(update.effective_user.id in ADMIN_IDS),
        )
    else:
        await update.message.reply_text(summary_text, reply_markup=main_menu_keyboard(update.effective_user.id in ADMIN_IDS))

    admin_text = (
        f"🆕 YANGI BAND\n\n"
        f"👤 Mijoz: {context.user_data['name']}\n"
        f"📞 Tel: {context.user_data['phone']}\n"
        f"📅 Sana: {context.user_data['booking_date']}\n"
        f"🕒 Soat: {context.user_data['booking_time']}\n"
        f"👥 Odam: {context.user_data['people_count']}\n"
        f"🚪 Xona: {context.user_data['room_no']}\n"
        f"📦 Xona sig'imi: {context.user_data['room_capacity']} kishi\n"
        f"🧾 Manba: {'admin kiritdi' if _is_admin_mode(context) else 'mijoz bot orqali'}\n"
        f"🆔 Booking ID: #{booking_id}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=admin_text)
        except Exception:
            pass

    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_text,
            reply_markup=admin_booking_keyboard(booking_id, update.effective_user.id),
        )
    except Exception:
        pass

    context.user_data.clear()
    return ConversationHandler.END
