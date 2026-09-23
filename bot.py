import os
import time
import random
import sqlite3
from flask import Flask, request
from threading import Thread
import telebot
from telebot import types
import datetime

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8621376781:AAG8O-3R8Hj7CVex1AeQiC1KLiSVeq4b89M"
ADMIN_ID = 5547760831
CHANNEL_USERNAME = "@workerbd1"
CHANNEL_LINK = "https://t.me/workerbd1"
SUPPORT_USERNAME = "@ad_min_100"

ACTIVATION_FEE = 100.0
MIN_WITHDRAW = 100.0

REF_LEVEL1_BONUS = 50.0
REF_LEVEL2_BONUS = 20.0
PLAN_REF_COMMISSION_PCT = 0.10

PLANS = {
    "1": {"name": "VIP Plan 1", "price": 1000.0, "daily": 50.0},
    "2": {"name": "VIP Plan 2", "price": 2000.0, "daily": 110.0},
    "3": {"name": "VIP Plan 3", "price": 3000.0, "daily": 160.0},
    "4": {"name": "VIP Plan 4", "price": 5000.0, "daily": 300.0},
    "5": {"name": "VIP Plan 5", "price": 7000.0, "daily": 490.0},
}

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

# Webhook Route
WEBHOOK_PATH = f"/{BOT_TOKEN}/"

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

@app.route('/')
def home():
    return "Bot is Running smoothly!"

# ==================== DATABASE PATH SETUP ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY, 
                        balance REAL DEFAULT 0.0, 
                        is_active INTEGER DEFAULT 0, 
                        referrer_id INTEGER DEFAULT NULL, 
                        plan_id TEXT DEFAULT NULL, 
                        last_ad_time INTEGER DEFAULT 0,
                        last_daily_payout TEXT DEFAULT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS pending_requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        user_id INTEGER, 
                        req_type TEXT, 
                        amount REAL, 
                        trx_id TEXT, 
                        extra_data TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY, 
                        value TEXT)''')
    
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('bkash', '01833084108')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('nagad', '01833084108')")
    conn.commit()
    conn.close()

init_db()

def db_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(query, params)
    data = None
    if fetchone: data = cursor.fetchone()
    elif fetchall: data = cursor.fetchall()
    if commit: conn.commit()
    conn.close()
    return data

def get_setting(key):
    row = db_query("SELECT value FROM settings WHERE key=?", (key,), fetchone=True)
    return row[0] if row else "01833084108"

def set_setting(key, value):
    db_query("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value), commit=True)

def is_channel_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return True

def get_main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("👤 My Account"), types.KeyboardButton("💎 VIP Plans"),
        types.KeyboardButton("⚡ Active Account"), types.KeyboardButton("💸 Withdraw"),
        types.KeyboardButton("🔗 Refer & Earn"), types.KeyboardButton("💬 Support")
    )
    return markup

# ==================== ADMIN COMMANDS ====================
@bot.message_handler(commands=['setbkash'])
def set_bkash_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) > 1:
        new_num = args[1].strip()
        set_setting("bkash", new_num)
        bot.send_message(ADMIN_ID, f"✅ বিকাশ নম্বর পরিবর্তন করে <code>{new_num}</code> করা হয়েছে।")

@bot.message_handler(commands=['setnagad'])
def set_nagad_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) > 1:
        new_num = args[1].strip()
        set_setting("nagad", new_num)
        bot.send_message(ADMIN_ID, f"✅ নগদ নম্বর পরিবর্তন করে <code>{new_num}</code> করা হয়েছে।")

# ==================== BACKGROUND WORKER ====================
def background_daily_profit_worker():
    while True:
        try:
            time.sleep(3600)
            current_date = datetime.date.today().isoformat()
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute("SELECT user_id, plan_id, last_daily_payout FROM users WHERE plan_id IS NOT NULL AND plan_id != ''")
            users = cursor.fetchall()
            
            for user in users:
                u_id, p_id, last_payout = user
                if p_id in PLANS:
                    if last_payout != current_date:
                        daily_amt = PLANS[p_id]["daily"]
                        cursor.execute("UPDATE users SET balance = balance + ?, last_daily_payout = ? WHERE user_id = ?", (daily_amt, current_date, u_id))
                        conn.commit()
                        try:
                            bot.send_message(u_id, f"🎉 আপনার VIP Plan থেকে দৈনিক প্রফিট <b>+{daily_amt} BDT</b> আপনার মূল ব্যালেন্সে স্বয়ংক্রিয়ভাবে যোগ হয়েছে!")
                        except:
                            pass
            conn.close()
        except Exception as e:
            print("Background Worker Error:", e)

# ==================== BOT HANDLERS ====================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].isdigit():
        ref_candidate = int(args[1])
        if ref_candidate != user_id: referrer_id = ref_candidate

    user = db_query("SELECT user_id FROM users WHERE user_id=?", (user_id,), fetchone=True)
    if not user: db_query("INSERT OR IGNORE INTO users (user_id, referrer_id) VALUES (?, ?)", (user_id, referrer_id), commit=True)

    if not is_channel_member(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
        markup.add(types.InlineKeyboardButton("✅ Verified & Continue", callback_data="check_join"))
        bot.send_message(user_id, "🔥 <b>Welcome to WorkerBD!</b> 🔥\nবটটি ব্যবহার করতে প্রথমে আমাদের চ্যানেলে জয়েন করুন:", reply_markup=markup)
        return
    send_welcome(user_id)

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    bot.answer_callback_query(call.id)
    if is_channel_member(call.from_user.id):
        try:
            bot.delete_message(call.from_user.id, call.message.message_id)
        except Exception:
            pass
        send_welcome(call.from_user.id)
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো চ্যানেলে জয়েন করেননি!", show_alert=True)

def send_welcome(user_id):
    welcome_text = "✨ <b>WorkerBD Official Earning Bot</b> ✨\n\nগ্যারান্টিযুক্ত পেমেন্ট এবং রেফার ও প্ল্যান কিনে আয় করুন।\nনিচের মেনু থেকে বাটন সিলেক্ট করুন 👇"
    bot.send_message(user_id, welcome_text, reply_markup=get_main_keyboard(user_id))

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    user_id = message.from_user.id
    text = message.text

    if not is_channel_member(user_id):
        start_cmd(message)
        return

    bkash_num = get_setting("bkash")
    nagad_num = get_setting("nagad")

    if text == "👤 My Account":
        row = db_query("SELECT balance, is_active, plan_id FROM users WHERE user_id=?", (user_id,), fetchone=True)
        if row:
            balance, is_active, plan_id = row[0], row[1], row[2]
            status = "✅ ACTIVE" if is_active else "❌ INACTIVE"
            plan_name = PLANS[plan_id]["name"] if plan_id and plan_id in PLANS else "None"
            bot.send_message(user_id, f"👤 <b>Account Details</b>\n\n🆔 <b>User ID:</b> <code>{user_id}</code>\n💰 <b>Balance:</b> {balance:.2f} BDT\n⚡ <b>Status:</b> {status}\n💎 <b>Current Plan:</b> {plan_name}")

    elif text == "⚡ Active Account":
        msg = f"⚡ <b>Account Activation Process</b>\nঅ্যাক্টিভেশন ফি: <b>{ACTIVATION_FEE} BDT</b>\n\n📲 <b>বিকাশ পার্সোনাল:</b> <code>{bkash_num}</code>\n📲 <b>নগদ পার্সোনাল:</b> <code>{nagad_num}</code>\n\nটাকা পাঠানোর পর TrxID জমা দিন:"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📥 Submit TrxID", callback_data="submit_act_trx"))
        bot.send_message(user_id, msg, reply_markup=markup)

    elif text == "💎 VIP Plans":
        msg = "💎 <b>Available VIP Plans</b> 💎\n\n"
        for pid, p in PLANS.items():
            msg += f"📌 <b>{p['name']}</b> | দাম: {p['price']} BDT | আয়: {p['daily']} BDT\n"
        msg += f"\n📲 <b>বিকাশ পার্সোনাল:</b> <code>{bkash_num}</code>\n📲 <b>নগদ পার্সোনাল:</b> <code>{nagad_num}</code>\n\nযেকোনো প্ল্যানে ক্লিক করুন:"
        markup = types.InlineKeyboardMarkup(row_width=2)
        btns = [types.InlineKeyboardButton(p["name"], callback_data=f"buy_plan_{pid}") for pid, p in PLANS.items()]
        markup.add(*btns)
        bot.send_message(user_id, msg, reply_markup=markup)

    elif text == "🔗 Refer & Earn":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        bot.send_message(user_id, f"🔗 <b>Referral Program</b>\n\nলিংক:\n<code>{ref_link}</code>\n\nLevel 1 Bonus: {REF_LEVEL1_BONUS} BDT\nLevel 2 Bonus: {REF_LEVEL2_BONUS} BDT\nPlan Commission: {PLAN_REF_COMMISSION_PCT*100}%")

    elif text == "💸 Withdraw":
        row = db_query("SELECT balance, is_active FROM users WHERE user_id=?", (user_id,), fetchone=True)
        balance, is_active = row[0], row[1] if row else (0.0, 0)
        if not is_active:
            bot.send_message(user_id, "❌ টাকা উত্তোলনের জন্য আগে অ্যাকাউন্ট একটিভ করুন।")
            return
        if balance < MIN_WITHDRAW:
            bot.send_message(user_id, f"❌ সর্বনিম্ন উইথড্র <b>{MIN_WITHDRAW} BDT</b>। ব্যালেন্স: {balance:.2f} BDT")
            return
        msg = bot.send_message(user_id, "💳 পেমেন্ট নেওয়ার জন্য <b>বিকাশ বা নগদ নম্বর</b> লিখুন:")
        bot.register_next_step_handler(msg, process_withdraw_number, balance)

    elif text == "💬 Support":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("👨‍💻 Admin Support", url=f"https://t.me/{SUPPORT_USERNAME.replace('@','')}" ))
        bot.send_message(user_id, "এডমিনকে মেসেজ দিন:", reply_markup=markup)

# ==================== STEP HANDLERS & CALLBACKS ====================
@bot.callback_query_handler(func=lambda call: call.data == "submit_act_trx")
def submit_act_trx_cb(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.from_user.id, "📝 পেমেন্ট ট্রানজেকশন আইডি (TrxID) লিখে পাঠান:")
    bot.register_next_step_handler(msg, process_act_trx)

def process_act_trx(message):
    trx_id = message.text.strip()
    user_id = message.from_user.id
    db_query("INSERT INTO pending_requests (user_id, req_type, amount, trx_id) VALUES (?, ?, ?, ?)", (user_id, "activation", ACTIVATION_FEE, trx_id), commit=True)
    bot.send_message(user_id, "✅ আপনার অ্যাক্টিভেশন TrxID জমা হয়েছে। এডমিন ভেরিফাই করে অনুমোদন করবে।")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Approve", callback_data=f"app_act_{user_id}"), types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_act_{user_id}"))
    bot.send_message(ADMIN_ID, f"📩 <b>Activation Request!</b>\nUser: <code>{user_id}</code>\nTrxID: <code>{trx_id}</code>", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_plan_"))
def buy_plan_cb(call):
    bot.answer_callback_query(call.id)
    plan_id = call.data.split("_")[2]
    plan = PLANS[plan_id]
    msg = bot.send_message(call.from_user.id, f"📝 <b>{plan['name']}</b> ({plan['price']} BDT) কিনতে টাকা পাঠিয়ে নিচে ট্রানজেকশন আইডি (TrxID) লিখে পাঠান:")
    bot.register_next_step_handler(msg, process_plan_trx, plan_id)

def process_plan_trx(message, plan_id):
    trx_id = message.text.strip()
    user_id = message.from_user.id
    plan = PLANS[plan_id]
    db_query("INSERT INTO pending_requests (user_id, req_type, amount, trx_id, extra_data) VALUES (?, ?, ?, ?, ?)", (user_id, "plan", plan["price"], trx_id, plan_id), commit=True)
    bot.send_message(user_id, f"✅ আপনার <b>{plan['name']}</b> ক্রয়ের TrxID জমা হয়েছে। এডমিন ভেরিফাই করে চালু করে দেবে।")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Approve", callback_data=f"app_plan_{user_id}_{plan_id}"), types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_plan_{user_id}"))
    bot.send_message(ADMIN_ID, f"📩 <b>Plan Request!</b>\nUser: <code>{user_id}</code>\nPlan: {plan['name']}\nTrxID: <code>{trx_id}</code>", reply_markup=markup)

def process_withdraw_number(message, balance):
    number = message.text.strip()
    user_id = message.from_user.id
    msg = bot.send_message(user_id, f"💸 কত টাকা উইথড্র করবেন? (ব্যালেন্স: {balance:.2f} BDT):")
    bot.register_next_step_handler(msg, process_withdraw_amount, number)

def process_withdraw_amount(message, number):
    user_id = message.from_user.id
    try: amount = float(message.text.strip())
    except ValueError:
        bot.send_message(user_id, "❌ অংক ভুল!")
        return
    row = db_query("SELECT balance FROM users WHERE user_id=?", (user_id,), fetchone=True)
    if amount < MIN_WITHDRAW or amount > row[0]:
        bot.send_message(user_id, "❌ অপর্যাপ্ত ব্যালেন্স!")
        return
    db_query("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, user_id), commit=True)
    bot.send_message(user_id, f"✅ {amount} BDT উইথড্র জমা হয়েছে।")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Paid", callback_data=f"app_wdr_{user_id}_{amount}"), types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_wdr_{user_id}_{amount}"))
    bot.send_message(ADMIN_ID, f"📩 <b>Withdraw Request!</b>\nUser: <code>{user_id}</code>\nNumber: <code>{number}</code>\nAmount: {amount} BDT", reply_markup=markup)

# ==================== ADMIN ACTIONS ====================
@bot.callback_query_handler(func=lambda call: call.data.startswith(("app_act_", "rej_act_", "app_plan_", "rej_plan_", "app_wdr_", "rej_wdr_")))
def admin_actions(call):
    bot.answer_callback_query(call.id)
    if call.from_user.id != ADMIN_ID: return
    data = call.data.split("_")
    action_type = data[0] + "_" + data[1]
    target_user_id = int(data[2])

    if action_type == "app_act":
        db_query("UPDATE users SET is_active=1 WHERE user_id=?", (target_user_id,), commit=True)
        bot.send_message(target_user_id, "🎉 আপনার অ্যাকাউন্ট অ্যাক্টিভ করা হয়েছে।")
        bot.edit_message_text(f"✅ Approved Activation User {target_user_id}", ADMIN_ID, call.message.message_id)

    elif action_type == "rej_act":
        bot.send_message(target_user_id, "❌ অ্যাকাউন্ট অ্যাক্টিভেশন বাতিল হয়েছে।")
        bot.edit_message_text(f"❌ Rejected User {target_user_id}", ADMIN_ID, call.message.message_id)

    elif action_type == "app_plan":
        plan_id = data[3]
        plan = PLANS[plan_id]
        db_query("UPDATE users SET plan_id=? WHERE user_id=?", (plan_id, target_user_id), commit=True)
        bot.send_message(target_user_id, f"🎉 {plan['name']} চালু করা হয়েছে।")
        bot.edit_message_text(f"✅ Approved Plan User {target_user_id}", ADMIN_ID, call.message.message_id)

    elif action_type == "rej_plan":
        bot.send_message(target_user_id, "❌ প্ল্যান ক্রয় বাতিল হয়েছে।")
        bot.edit_message_text(f"❌ Rejected Plan User {target_user_id}", ADMIN_ID, call.message.message_id)

    elif action_type == "app_wdr":
        bot.send_message(target_user_id, f"✅ উইথড্র সফলভাবে সম্পন্ন হয়েছে।")
        bot.edit_message_text(f"✅ Withdrawal Paid User {target_user_id}", ADMIN_ID, call.message.message_id)

    elif action_type == "rej_wdr":
        w_amount = float(data[3])
        db_query("UPDATE users SET balance = balance + ? WHERE user_id=?", (w_amount, target_user_id), commit=True)
        bot.send_message(target_user_id, f"❌ উইথড্র বাতিল এবং {w_amount} BDT ফেরত দেওয়া হয়েছে।")
        bot.edit_message_text(f"❌ Rejected Refunded User {target_user_id}", ADMIN_ID, call.message.message_id)

if __name__ == "__main__":
    Thread(target=background_daily_profit_worker, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    
