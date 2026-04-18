import sqlite3
from datetime import datetime, date
from typing import Optional
from config import DB_NAME, ROOMS, DELIVERY_MENU, DELIVERY_ADDONS


def conn():
    c = sqlite3.connect(DB_NAME)
    c.row_factory = sqlite3.Row
    return c


def cleanup_expired_bookings():
    c = conn()
    cur = c.cursor()
    today = date.today().isoformat()
    cur.execute(
        """
        UPDATE room_bookings
        SET status = 'completed'
        WHERE booking_date < ?
          AND status NOT IN ('cancelled', 'completed')
        """,
        (today,),
    )
    c.commit()
    c.close()


def init_db():
    c = conn()
    cur = c.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            room_no INTEGER PRIMARY KEY,
            capacity INTEGER NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS delivery_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_user_id INTEGER,
            customer_name TEXT,
            customer_phone TEXT,
            food_key TEXT,
            food_title TEXT,
            amount_value TEXT,
            addons_json TEXT,
            addons_total_price INTEGER DEFAULT 0,
            total_price INTEGER DEFAULT 0,
            delivery_address TEXT,
            note TEXT,
            payment_method TEXT DEFAULT 'cash',
            payment_proof_file_id TEXT,
            status TEXT DEFAULT 'new',
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS room_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_user_id INTEGER,
            customer_name TEXT,
            customer_phone TEXT,
            booking_date TEXT,
            booking_time TEXT,
            people_count INTEGER,
            room_no INTEGER,
            source TEXT DEFAULT 'bot',
            status TEXT DEFAULT 'new',
            created_at TEXT,
            UNIQUE (booking_date, booking_time, room_no)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_key TEXT UNIQUE,
            title TEXT NOT NULL,
            mode TEXT DEFAULT 'options',
            description_prompt TEXT,
            price_note TEXT,
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS menu_item_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_key TEXT NOT NULL,
            option_label TEXT NOT NULL,
            price INTEGER NOT NULL DEFAULT 0,
            plate_rules_json TEXT,
            sort_order INTEGER DEFAULT 0,
            UNIQUE(item_key, option_label)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS addon_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            addon_key TEXT UNIQUE,
            title TEXT NOT NULL,
            price INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    cur.executemany(
        """
        INSERT INTO rooms (room_no, capacity, is_active)
        VALUES (?, ?, 1)
        ON CONFLICT(room_no) DO UPDATE SET
            capacity=excluded.capacity,
            is_active=1
        """,
        ROOMS,
    )

    cur.execute(
        f"UPDATE rooms SET is_active = 0 WHERE room_no NOT IN ({','.join('?' for _ in ROOMS)})",
        [room_no for room_no, _ in ROOMS],
    )

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    default_menu_keys = set()
    for index, (item_key, item) in enumerate(DELIVERY_MENU.items(), start=1):
        default_menu_keys.add(item_key)
        cur.execute(
            """
            INSERT INTO menu_items (item_key, title, mode, description_prompt, price_note, is_active, sort_order, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
            ON CONFLICT(item_key) DO UPDATE SET
                title=excluded.title,
                mode=excluded.mode,
                description_prompt=excluded.description_prompt,
                price_note=excluded.price_note,
                is_active=1,
                sort_order=excluded.sort_order,
                updated_at=excluded.updated_at
            """,
            (
                item_key,
                item['title'],
                item.get('mode', 'options'),
                item.get('description_prompt'),
                item.get('price_note'),
                index,
                now,
                now,
            ),
        )
        options = item.get('options', [])
        option_map = item.get('options_map', {})
        plate_rules = item.get('plate_rules', {})
        for opt_index, opt in enumerate(options, start=1):
            cur.execute(
                """
                INSERT INTO menu_item_options (item_key, option_label, price, plate_rules_json, sort_order)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(item_key, option_label) DO UPDATE SET
                    price=excluded.price,
                    plate_rules_json=excluded.plate_rules_json,
                    sort_order=excluded.sort_order
                """,
                (item_key, opt, int(option_map.get(opt, 0)), __import__('json').dumps(plate_rules.get(opt), ensure_ascii=False) if plate_rules.get(opt) else None, opt_index),
            )

    default_addon_keys = set()
    for index, (addon_key, addon) in enumerate(DELIVERY_ADDONS.items(), start=1):
        default_addon_keys.add(addon_key)
        cur.execute(
            """
            INSERT INTO addon_items (addon_key, title, price, is_active, sort_order, created_at, updated_at)
            VALUES (?, ?, ?, 1, ?, ?, ?)
            ON CONFLICT(addon_key) DO UPDATE SET
                title=excluded.title,
                price=excluded.price,
                is_active=1,
                sort_order=excluded.sort_order,
                updated_at=excluded.updated_at
            """,
            (addon_key, addon['title'], int(addon['price']), index, now, now),
        )

    c.commit()
    c.close()
    cleanup_expired_bookings()


def _slugify(text: str) -> str:
    import re
    slug = text.lower().strip()
    replacements = {
        "o'": 'o', "g'": 'g', 'sh': 'sh', 'ch': 'ch', 'yo': 'yo', 'ya': 'ya', 'yu': 'yu',
    }
    for k, v in replacements.items():
        slug = slug.replace(k, v)
    slug = slug.replace("'", '').replace('’','')
    slug = re.sub(r'[^a-z0-9]+', '_', slug)
    slug = re.sub(r'_+', '_', slug).strip('_')
    return slug or f'item_{int(datetime.now().timestamp())}'


def get_delivery_menu():
    c = conn(); cur = c.cursor()
    cur.execute("SELECT * FROM menu_items WHERE is_active = 1 ORDER BY sort_order ASC, id ASC")
    items = cur.fetchall()
    menu = {}
    for item in items:
        item_key = item['item_key']
        cur.execute("SELECT option_label, price, plate_rules_json FROM menu_item_options WHERE item_key = ? ORDER BY sort_order ASC, id ASC", (item_key,))
        option_rows = cur.fetchall()
        options = []
        options_map = {}
        plate_rules = {}
        for opt in option_rows:
            options.append(opt['option_label'])
            options_map[opt['option_label']] = int(opt['price'])
            if opt['plate_rules_json']:
                import json
                plate_rules[opt['option_label']] = json.loads(opt['plate_rules_json'])
        row = {
            'title': item['title'],
            'options': options,
            'options_map': options_map,
        }
        if item['mode']:
            row['mode'] = item['mode']
        if item['description_prompt']:
            row['description_prompt'] = item['description_prompt']
        if item['price_note']:
            row['price_note'] = item['price_note']
        if plate_rules:
            row['plate_rules'] = plate_rules
        menu[item_key] = row
    c.close()
    return menu


def get_delivery_addons():
    c = conn(); cur = c.cursor()
    cur.execute("SELECT addon_key, title, price FROM addon_items WHERE is_active = 1 ORDER BY sort_order ASC, id ASC")
    rows = cur.fetchall(); c.close()
    return {r['addon_key']: {'title': r['title'], 'price': int(r['price'])} for r in rows}


def list_menu_items():
    c = conn(); cur = c.cursor()
    cur.execute("SELECT id, item_key, title, mode, price_note FROM menu_items WHERE is_active = 1 ORDER BY sort_order ASC, id ASC")
    rows = [dict(r) for r in cur.fetchall()]
    for row in rows:
        cur.execute("SELECT option_label, price FROM menu_item_options WHERE item_key=? ORDER BY sort_order ASC, id ASC", (row['item_key'],))
        row['options'] = [dict(x) for x in cur.fetchall()]
    c.close(); return rows


def list_addons():
    c = conn(); cur = c.cursor()
    cur.execute("SELECT id, addon_key, title, price FROM addon_items WHERE is_active=1 ORDER BY sort_order ASC, id ASC")
    rows = [dict(r) for r in cur.fetchall()]
    c.close(); return rows


def update_menu_item_price(item_key: str, option_label: str, new_price: int):
    c = conn(); cur = c.cursor()
    cur.execute("UPDATE menu_item_options SET price=? WHERE item_key=? AND option_label=?", (int(new_price), item_key, option_label))
    c.commit(); c.close()


def update_addon_price(addon_key: str, new_price: int):
    c = conn(); cur = c.cursor()
    cur.execute("UPDATE addon_items SET price=?, updated_at=? WHERE addon_key=?", (int(new_price), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), addon_key))
    c.commit(); c.close()


def add_menu_item(title: str, price: int, option_label: str = '1 porsiya', price_note: Optional[str] = None):
    item_key = _slugify(title)
    c = conn(); cur = c.cursor(); now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur.execute("SELECT COALESCE(MAX(sort_order),0)+1 FROM menu_items")
    next_order = cur.fetchone()[0]
    cur.execute(
        "INSERT OR REPLACE INTO menu_items (item_key, title, mode, price_note, is_active, sort_order, created_at, updated_at) VALUES (?, ?, 'options', ?, 1, ?, ?, ?)",
        (item_key, title, price_note, next_order, now, now),
    )
    cur.execute(
        "INSERT OR REPLACE INTO menu_item_options (item_key, option_label, price, sort_order) VALUES (?, ?, ?, 1)",
        (item_key, option_label, int(price)),
    )
    c.commit(); c.close(); return item_key


def add_addon_item(title: str, price: int):
    addon_key = _slugify(title)
    c = conn(); cur = c.cursor(); now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur.execute("SELECT COALESCE(MAX(sort_order),0)+1 FROM addon_items")
    next_order = cur.fetchone()[0]
    cur.execute(
        "INSERT OR REPLACE INTO addon_items (addon_key, title, price, is_active, sort_order, created_at, updated_at) VALUES (?, ?, ?, 1, ?, ?, ?)",
        (addon_key, title, int(price), next_order, now, now),
    )
    c.commit(); c.close(); return addon_key


def create_order(data: dict, user_id: int):
    c = conn(); cur = c.cursor()
    cur.execute("""
        INSERT INTO delivery_orders (
            customer_user_id, customer_name, customer_phone, food_key, food_title,
            amount_value, addons_json, addons_total_price, total_price,
            delivery_address, note, payment_method, payment_proof_file_id,
            status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, data['name'], data['phone'], data['food_key'], data['food_title'],
        data['amount_value'], data.get('addons_json'), int(data.get('addons_total_price', 0)), int(data.get('total_price', 0)),
        data['address'], data.get('note', ''), data.get('payment_method', 'cash'), data.get('payment_proof_file_id'),
        data.get('status', 'new'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    ))
    order_id = cur.lastrowid; c.commit(); c.close(); return order_id


def set_order_payment_proof(order_id: int, file_id: str):
    c = conn(); cur = c.cursor(); cur.execute("UPDATE delivery_orders SET payment_proof_file_id = ?, status = 'payment_check' WHERE id = ?", (file_id, order_id)); c.commit(); c.close()


def update_order_status(order_id: int, status: str):
    c = conn(); cur = c.cursor(); cur.execute("UPDATE delivery_orders SET status = ? WHERE id = ?", (status, order_id)); c.commit(); c.close()


def create_booking(data: dict, user_id: int):
    c = conn(); cur = c.cursor()
    cur.execute("""
        INSERT INTO room_bookings (
            customer_user_id, customer_name, customer_phone,
            booking_date, booking_time, people_count, room_no,
            source, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)
    """, (
        user_id, data['name'], data['phone'], data['booking_date'], data['booking_time'], int(data['people_count']), int(data['room_no']), data.get('booking_source', 'bot'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    ))
    booking_id = cur.lastrowid; c.commit(); c.close(); return booking_id


def update_booking_status(booking_id: int, status: str):
    c = conn(); cur = c.cursor(); cur.execute("UPDATE room_bookings SET status = ? WHERE id = ?", (status, booking_id)); c.commit(); c.close()


def room_group_for_people(people_count: int):
    if people_count <= 0: return []
    if people_count <= 6: return [5]
    if people_count <= 11: return [10]
    if people_count <= 15: return [15]
    if people_count <= 22: return [20]
    return []


def free_rooms(date_str: str, time_str: str, people_count: int):
    cleanup_expired_bookings(); capacities = room_group_for_people(people_count)
    if not capacities: return []
    c = conn(); cur = c.cursor(); placeholders = ','.join('?' for _ in capacities)
    cur.execute(f"""
        SELECT r.room_no, r.capacity
        FROM rooms r
        WHERE r.is_active = 1
          AND r.capacity IN ({placeholders})
          AND r.room_no NOT IN (
              SELECT room_no FROM room_bookings
              WHERE booking_date = ? AND booking_time = ? AND status NOT IN ('cancelled', 'completed')
          )
        ORDER BY r.room_no ASC
    """, (*capacities, date_str, time_str))
    rows = cur.fetchall(); c.close(); return rows


def get_user_orders(user_id: int):
    c = conn(); cur = c.cursor(); cur.execute("SELECT * FROM delivery_orders WHERE customer_user_id = ? ORDER BY id DESC", (user_id,)); rows = cur.fetchall(); c.close(); return rows


def get_user_bookings(user_id: int):
    cleanup_expired_bookings(); c = conn(); cur = c.cursor(); cur.execute("SELECT * FROM room_bookings WHERE customer_user_id = ? ORDER BY id DESC", (user_id,)); rows = cur.fetchall(); c.close(); return rows


def get_today_free_rooms(selected_date: str):
    cleanup_expired_bookings(); c = conn(); cur = c.cursor(); cur.execute("""
        SELECT r.room_no, r.capacity FROM rooms r
        WHERE r.is_active = 1
          AND r.room_no NOT IN (
              SELECT room_no FROM room_bookings WHERE booking_date = ? AND status NOT IN ('cancelled', 'completed')
          )
        ORDER BY r.room_no ASC
    """, (selected_date,)); rows = cur.fetchall(); c.close(); return rows


def get_today_bookings(selected_date: str):
    cleanup_expired_bookings(); c = conn(); cur = c.cursor(); cur.execute("""
        SELECT id, booking_date, booking_time, people_count, room_no, customer_name, customer_phone, status, source
        FROM room_bookings
        WHERE booking_date = ? AND status NOT IN ('cancelled', 'completed')
        ORDER BY booking_time ASC, room_no ASC
    """, (selected_date,)); rows = cur.fetchall(); c.close(); return rows


def get_today_delivery_stats(selected_date: str):
    c = conn(); cur = c.cursor()
    cur.execute("""
        SELECT COUNT(*) AS total_orders, COALESCE(SUM(total_price), 0) AS total_revenue
        FROM delivery_orders
        WHERE DATE(created_at) = DATE(?) AND status != 'cancelled'
    """, (selected_date,)); totals = cur.fetchone()
    cur.execute("""
        SELECT payment_method, COUNT(*) AS cnt
        FROM delivery_orders
        WHERE DATE(created_at) = DATE(?) AND status != 'cancelled'
        GROUP BY payment_method
    """, (selected_date,)); payments = cur.fetchall()
    cur.execute("""
        SELECT food_title, COUNT(*) AS cnt
        FROM delivery_orders
        WHERE DATE(created_at) = DATE(?) AND status != 'cancelled'
        GROUP BY food_title
        ORDER BY cnt DESC, food_title ASC
        LIMIT 5
    """, (selected_date,)); top_foods = cur.fetchall(); c.close(); return totals, payments, top_foods


def get_today_booking_stats(selected_date: str):
    cleanup_expired_bookings(); c = conn(); cur = c.cursor()
    cur.execute("""
        SELECT COUNT(*) AS total_bookings FROM room_bookings
        WHERE booking_date = ? AND status NOT IN ('cancelled', 'completed')
    """, (selected_date,)); totals = cur.fetchone()
    cur.execute("""
        SELECT status, COUNT(*) AS cnt FROM room_bookings
        WHERE booking_date = ? AND status NOT IN ('cancelled', 'completed')
        GROUP BY status
    """, (selected_date,)); statuses = cur.fetchall()
    cur.execute("""
        SELECT COALESCE(SUM(people_count), 0) AS total_people FROM room_bookings
        WHERE booking_date = ? AND status NOT IN ('cancelled', 'completed')
    """, (selected_date,)); people = cur.fetchone(); c.close(); return totals, statuses, people


def set_room_status(room_no: int, is_active: int):
    c = conn(); cur = c.cursor(); cur.execute("UPDATE rooms SET is_active = ? WHERE room_no = ?", (is_active, room_no)); c.commit(); c.close()


def get_room_statuses(selected_date: str):
    cleanup_expired_bookings(); c = conn(); cur = c.cursor()
    cur.execute("SELECT room_no, capacity FROM rooms WHERE is_active = 1 ORDER BY room_no ASC")
    rooms = cur.fetchall()
    cur.execute("""
        SELECT room_no, booking_time, people_count, customer_name, customer_phone, status
        FROM room_bookings
        WHERE booking_date = ? AND status NOT IN ('cancelled', 'completed')
        ORDER BY booking_time ASC, room_no ASC
    """, (selected_date,)); bookings = cur.fetchall(); c.close()
    booking_map = {}
    for row in bookings: booking_map.setdefault(row['room_no'], []).append(dict(row))
    result = []
    for room in rooms:
        room_dict = dict(room)
        room_dict['bookings'] = booking_map.get(room_dict['room_no'], [])
        room_dict['is_busy'] = bool(room_dict['bookings'])
        result.append(room_dict)
    return result


def get_delivery_orders_by_date(selected_date: str):
    c = conn(); cur = c.cursor(); cur.execute("SELECT * FROM delivery_orders WHERE DATE(created_at)=DATE(?) ORDER BY id ASC", (selected_date,)); rows = [dict(r) for r in cur.fetchall()]; c.close(); return rows


def get_room_bookings_by_date(selected_date: str):
    cleanup_expired_bookings(); c = conn(); cur = c.cursor(); cur.execute("SELECT * FROM room_bookings WHERE booking_date=? ORDER BY booking_time ASC, room_no ASC", (selected_date,)); rows = [dict(r) for r in cur.fetchall()]; c.close(); return rows
