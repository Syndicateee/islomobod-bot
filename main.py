from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters,
)

from config import TOKEN
from database import init_db, get_delivery_menu
from handlers.common import start, route_main_menu, back_main, cancel
from handlers.delivery import (
    food_selected, amount_selected, amount_manual, addons_selected, name_received, phone_received,
    address_received, note_received, payment_selected, proof_received,
)
from handlers.booking import (
    date_selected, slot_selected, time_selected, custom_time, people_received,
    name_received as b_name_received, phone_received as b_phone_received, calendar_navigate, ignore_calendar, admin_add_booking_start,
)
from handlers.admin import (
    order_admin_action, booking_admin_action, admin_panel, free_today, bookings_today, rooms_today,
    stats_today, admin_ready_time_received, admin_panel_callback,
)
from states import *


async def error_handler(update, context):
    try:
        print("XATO:", context.error)
    except Exception:
        pass


def main():
    if TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        raise ValueError("config.py ichiga TOKEN yozing.")

    init_db()
    app = Application.builder().token(TOKEN).build()
    app.bot_data['menu'] = get_delivery_menu()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('add_booking', admin_add_booking_start),
            CallbackQueryHandler(admin_add_booking_start, pattern=r'^admin:add_booking$'),
            MessageHandler(filters.Regex(r'^(🍽 Buyurtma berish|🏠 Xona band qilish|🖼 Taomlar|📱 Mini App|📍 Kontakt|📦 Mening buyurtmalarim|⚙️ Admin panel)$'), route_main_menu),
        ],
        states={
            DELIVERY_FOOD: [CallbackQueryHandler(back_main, pattern=r'^back_main$'), CallbackQueryHandler(food_selected, pattern=r'^food:')],
            DELIVERY_AMOUNT: [CallbackQueryHandler(back_main, pattern=r'^back_main$'), CallbackQueryHandler(amount_selected, pattern=r'^amount:')],
            DELIVERY_MANUAL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount_manual)],
            DELIVERY_ADDONS: [CallbackQueryHandler(back_main, pattern=r'^back_main$'), CallbackQueryHandler(addons_selected, pattern=r'^addon:')],
            DELIVERY_NAME: [MessageHandler(filters.Regex(r'^⬅️ Bekor qilish$'), cancel), MessageHandler(filters.TEXT & ~filters.COMMAND, name_received)],
            DELIVERY_PHONE: [MessageHandler(filters.Regex(r'^⬅️ Bekor qilish$'), cancel), MessageHandler((filters.CONTACT | filters.TEXT) & ~filters.COMMAND, phone_received)],
            DELIVERY_ADDRESS: [MessageHandler(filters.Regex(r'^⬅️ Bekor qilish$'), cancel), MessageHandler((filters.LOCATION | filters.TEXT) & ~filters.COMMAND, address_received)],
            DELIVERY_NOTE: [MessageHandler(filters.Regex(r'^⬅️ Bekor qilish$'), cancel), MessageHandler(filters.TEXT & ~filters.COMMAND, note_received)],
            DELIVERY_PAYMENT: [CallbackQueryHandler(back_main, pattern=r'^back_main$'), CallbackQueryHandler(payment_selected, pattern=r'^pay:')],
            DELIVERY_PROOF: [MessageHandler(filters.Regex(r'^⬅️ Bekor qilish$'), cancel), MessageHandler(filters.PHOTO, proof_received)],
            BOOK_DATE: [CallbackQueryHandler(back_main, pattern=r'^back_main$'), CallbackQueryHandler(calendar_navigate, pattern=r'^bcnav:'), CallbackQueryHandler(ignore_calendar, pattern=r'^ignore$'), CallbackQueryHandler(date_selected, pattern=r'^bdate:')],
            BOOK_SLOT: [CallbackQueryHandler(back_main, pattern=r'^back_main$'), CallbackQueryHandler(slot_selected, pattern=r'^slot:')],
            BOOK_TIME: [CallbackQueryHandler(back_main, pattern=r'^back_main$'), CallbackQueryHandler(time_selected, pattern=r'^btime:')],
            BOOK_CUSTOM_TIME: [MessageHandler(filters.Regex(r'^⬅️ Bekor qilish$'), cancel), MessageHandler(filters.TEXT & ~filters.COMMAND, custom_time)],
            BOOK_PEOPLE: [MessageHandler(filters.Regex(r'^⬅️ Bekor qilish$'), cancel), MessageHandler(filters.TEXT & ~filters.COMMAND, people_received)],
            BOOK_NAME: [MessageHandler(filters.Regex(r'^⬅️ Bekor qilish$'), cancel), MessageHandler(filters.TEXT & ~filters.COMMAND, b_name_received)],
            BOOK_PHONE: [
                MessageHandler(filters.CONTACT, b_phone_received),
                MessageHandler(filters.TEXT & ~filters.COMMAND, b_phone_received),
            ],
            ADMIN_BOOK_DATE: [CallbackQueryHandler(back_main, pattern=r'^back_main$'), CallbackQueryHandler(calendar_navigate, pattern=r'^bcnav:'), CallbackQueryHandler(ignore_calendar, pattern=r'^ignore$'), CallbackQueryHandler(date_selected, pattern=r'^bdate:')],
            ADMIN_BOOK_SLOT: [CallbackQueryHandler(back_main, pattern=r'^back_main$'), CallbackQueryHandler(slot_selected, pattern=r'^slot:')],
            ADMIN_BOOK_TIME: [CallbackQueryHandler(back_main, pattern=r'^back_main$'), CallbackQueryHandler(time_selected, pattern=r'^btime:')],
            ADMIN_BOOK_CUSTOM_TIME: [MessageHandler(filters.Regex(r'^⬅️ Bekor qilish$'), cancel), MessageHandler(filters.TEXT & ~filters.COMMAND, custom_time)],
            ADMIN_BOOK_PEOPLE: [MessageHandler(filters.Regex(r'^⬅️ Bekor qilish$'), cancel), MessageHandler(filters.TEXT & ~filters.COMMAND, people_received)],
            ADMIN_BOOK_NAME: [MessageHandler(filters.Regex(r'^⬅️ Bekor qilish$'), cancel), MessageHandler(filters.TEXT & ~filters.COMMAND, b_name_received)],
            ADMIN_BOOK_PHONE: [
                MessageHandler(filters.CONTACT, b_phone_received),
                MessageHandler(filters.TEXT & ~filters.COMMAND, b_phone_received),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler('admin', admin_panel))
    app.add_handler(CommandHandler('free_today', free_today))
    app.add_handler(CommandHandler('bookings_today', bookings_today))
    app.add_handler(CommandHandler('rooms_today', rooms_today))
    app.add_handler(CommandHandler('stats_today', stats_today))
    app.add_handler(CallbackQueryHandler(order_admin_action, pattern=r'^oadmin:'))
    app.add_handler(CallbackQueryHandler(booking_admin_action, pattern=r'^badmin:'))
    app.add_handler(CallbackQueryHandler(admin_panel_callback, pattern=r'^admin(:|_)'))
    app.add_handler(MessageHandler(filters.Regex(r'^\d+$') & ~filters.COMMAND, admin_ready_time_received))
    app.add_error_handler(error_handler)

    print('Bot ishga tushdi...')
    app.run_polling(close_loop=False)


if __name__ == '__main__':
    main()
