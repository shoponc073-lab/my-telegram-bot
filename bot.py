import os
import requests
from flask import Flask
from threading import Thread
import telebot
from telebot import types
import sqlite3

# ================= CONFIGURATION =================
TOKEN = "8621376781:AAG8O-3R8Hj7CVex1AeQiC1KLiSVeq4b89M"  # আপনার বট টোকেন
ADMIN_ID = 5547760831                                   # আপনার এডমিন আইডি
CHANNEL_USERNAME = "@workerbd1"                      # আপনার অফিশিয়াল চ্যানেল ইউজারনেম
SUPPORT_USERNAME = "@ad_min_100"                         # আপনার সাপোর্ট ইউজারনেম
CHANNEL_LINK = "https://t.me/workerbd1"              # আপনার চ্যানেল লিংক

ACTIVATION_FEE = 100.0
MIN_WITHDRAW = 50.0

# রেফার বোনাস সেটিংস
REF_LEVEL1_BONUS = 40.0      # লেভেল ১ বোনাস (৳৪০)
REF_LEVEL2_BONUS = 20.0      # লেভেল ২ বোনাস (৳২০)
PLAN_REF_COMMISSION = 20.0   # প্ল্যান ক্রয়ের ২০% কমিশন

PLANS = {
    "1": {"name": "VIP Plan 1", "price": 1000.0, "daily": 50.0},
    "2": {"name": "VIP Plan 2", "price": 2000.0, "daily": 100.0},
    "3": {"name": "VIP Plan 3", "price": 5000.0, "daily": 300.0},
    "4": {"name": "VIP Plan 4", "price": 7000.0, "daily": 450.0},
    "5": {"name": "VIP Plan 5", "price": 10000.0, "daily": 700.0},
}

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

@app.route('/')
def home():
    return "Worker BD Bot is running 24/7!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS USERS (
        user_id INTEGER PRIMARY KEY,
        balance REAL DEFAULT 0.0,
        is_active INTEGER DEFAULT 0,
        ref_by INTEGER DEFAULT 0,
        plan_id TEXT DEFAULT 'None'
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS SETTINGS (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    cursor.execute("INSERT OR IGNORE INTO SETTINGS (key, value) VALUES ('nagad', '018XXXXXXXX')")
    cursor.execute("INSERT OR IGNORE INTO SETTINGS (key, value) VALUES ('bkash', '018XXXXXXXX')")
    conn.commit()
    conn.close()

init_db()

def db_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    data = None
    if fetchone:
        data = cursor.fetchone()
    if fetchall:
        data = cursor.fetchall()
    if commit:
        conn.commit()
    conn.close()
    return data

def get_setting(key):
    res = db_query("SELECT value FROM SETTINGS WHERE key=?", (key,), fetchone=True)
    return res['value'] if res else "018XXXXXXXX"

def is_channel_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return True

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("👤 My Account"),
        types.KeyboardButton("⚡ Active Account"),
        types.KeyboardButton("💎 VIP Plan"),
        types.KeyboardButton("💸 Withdraw"),
        types.KeyboardButton("🔗 Refer & Earn"),
        types.KeyboardButton("🎧 Support")
    )
    return markup

# ================= USER COMMANDS =================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    args = message.text.split()
    ref_by = 0
    if len(args) > 1 and args[1].isdigit():
        ref_by = int(args[1])
        if ref_by == user_id:
            ref_by = 0

    user = db_query("SELECT * FROM USERS WHERE user_id=?", (user_id,), fetchone=True)
    if not user:
        db_query("INSERT INTO USERS (user_id, ref_by) VALUES (?, ?)", (user_id, ref_by), commit=True)

    if not is_channel_member(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
        
        welcome_channel_msg = (
            "🔥 <b>Worker BD-এ আপনাকে স্বাগতম!</b> 🔥\n\n"
            "বটটি ব্যবহার করে প্রতিদিন ভালো পরিমাণ টাকা আয় করতে পারবেন ১০০% বিশ্বস্ততার সাথে! "
            "আমাদের কাজের আপডেট, পেমেন্ট প্রুফ এবং প্রয়োজনীয় সকল নোটিশ সবার আগে পেতে আমাদের অফিশিয়াল টেলিগ্রাম চ্যানেলে যুক্ত হওয়া বাধ্যতামূলক।\n\n"
            "👉 <b>নিচের বাটন চেপে চ্যানেলে জয়েন করুন এবং আবার স্টার্ট দিন!</b>"
        )
        bot.send_message(user_id, welcome_channel_msg, reply_markup=markup)
        return

    welcome_main_msg = (
        "<b>👋 স্বাগতম! Worker BD-এর অফিশিয়াল বটে!</b>\n\n"
        "এখানে আপনি অ্যাকাউন্ট অ্যাক্টিভ করে এবং VIP প্ল্যান নিয়ে দৈনিক ইনকাম করতে পারবেন। "
        "নিচের মেনু থেকে আপনার কাঙ্ক্ষিত অপশনটি বেছে নিন:"
    )
    bot.send_message(user_id, welcome_main_msg, reply_markup=get_main_keyboard())

# ================= ADMIN COMMANDS =================
@bot.message_handler(commands=['active'])
def admin_active_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        target_id = int(message.text.split()[1])
        user = db_query("SELECT * FROM USERS WHERE user_id=?", (target_id,), fetchone=True)
        
        if not user:
            bot.send_message(message.chat.id, "❌ এই ইউজারের কোনো আইডি ডাটাবেসে পাওয়া যায়নি।")
            return

        db_query("UPDATE USERS SET is_active=1 WHERE user_id=?", (target_id,), commit=True)
        bot.send_message(message.chat.id, f"✅ User <code>{target_id}</code> এর একাউন্ট সফলভাবে Active করা হয়েছে!")
        bot.send_message(target_id, "🎉 <b>অভিনন্দন! Worker BD-এ আপনার অ্যাকাউন্টটি সফলভাবে সক্রিয় (Active) করা হয়েছে!</b>")
        
        # Level 1 রেফারেল বোনাস (৳৪০)
        if user['ref_by'] and user['ref_by'] != 0:
            l1_id = user['ref_by']
            db_query("UPDATE USERS SET balance = balance + ? WHERE user_id=?", (REF_LEVEL1_BONUS, l1_id), commit=True)
            try:
                bot.send_message(l1_id, f"🎉 <b>রেফারেল বোনাস (Level 1)!</b>\nআপনার রেফার করা ইউজার (<code>{target_id}</code>) অ্যাকাউন্ট অ্যাক্টিভ করায় আপনি <b>{REF_LEVEL1_BONUS:.2f} BDT</b> বোনাস পেয়েছেন!")
            except Exception:
                pass

            # Level 2 রেফারেল বোনাস (৳২০)
            l1_user = db_query("SELECT ref_by FROM USERS WHERE user_id=?", (l1_id,), fetchone=True)
            if l1_user and l1_user['ref_by'] and l1_user['ref_by'] != 0:
                l2_id = l1_user['ref_by']
                db_query("UPDATE USERS SET balance = balance + ? WHERE user_id=?", (REF_LEVEL2_BONUS, l2_id), commit=True)
                try:
                    bot.send_message(l2_id, f"🎉 <b>রেফারেল বোনাস (Level 2)!</b>\nআপনার টিমের একজন ইউজার অ্যাকাউন্ট অ্যাক্টিভ করায় আপনি <b>{REF_LEVEL2_BONUS:.2f} BDT</b> বোনাস পেয়েছেন!")
                except Exception:
                    pass

    except Exception:
        bot.send_message(message.chat.id, "❌ নিয়ম: `/active <user_id>` (যেমন: `/active 123456789`)")

@bot.message_handler(commands=['plan'])
def admin_set_plan(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        args = message.text.split()
        target_id = int(args[1])
        plan_id = str(args[2])
        
        user = db_query("SELECT * FROM USERS WHERE user_id=?", (target_id,), fetchone=True)
        if not user:
            bot.send_message(message.chat.id, "❌ এই ইউজারের কোনো আইডি পাওয়া যায়নি।")
            return

        if plan_id in PLANS:
            pinfo = PLANS[plan_id]
            db_query("UPDATE USERS SET plan_id=? WHERE user_id=?", (plan_id, target_id), commit=True)
            bot.send_message(message.chat.id, f"✅ User <code>{target_id}</code> এর জন্য {pinfo['name']} এক্টিভ করা হয়েছে!")
            bot.send_message(target_id, f"💎 <b>অভিনন্দন! Worker BD-এ আপনার {pinfo['name']} সফলভাবে চালু করা হয়েছে!</b>")
            
            # প্ল্যান বিক্রির রেফার কমিশন (২০%)
            if user['ref_by'] and user['ref_by'] != 0:
                referrer_id = user['ref_by']
                commission = (pinfo['price'] * PLAN_REF_COMMISSION) / 100.0
                db_query("UPDATE USERS SET balance = balance + ? WHERE user_id=?", (commission, referrer_id), commit=True)
                try:
                    bot.send_message(referrer_id, f"🎉 <b>প্ল্যান রেফারেল কমিশন!</b>\nআপনার রেফার করা ইউজার (<code>{target_id}</code>) {pinfo['name']} কেনায় আপনি <b>{commission:.2f} BDT</b> (২০%) কমিশন পেয়েছেন!")
                except Exception:
                    pass
        else:
            bot.send_message(message.chat.id, "❌ ভুল Plan ID! ১, ২, ৩, ৪ অথবা ৫ দিন।")
    except Exception:
        bot.send_message(message.chat.id, "❌ নিয়ম: `/plan <user_id> <plan_id>` (যেমন: `/plan 123456789 5`)")

@bot.message_handler(commands=['setbkash'])
def set_bkash(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        num = message.text.split()[1]
        db_query("INSERT OR REPLACE INTO SETTINGS (key, value) VALUES ('bkash', ?)", (num,), commit=True)
        bot.send_message(message.chat.id, f"✅ বিকাশ পার্সোনাল নম্বর আপডেট হয়েছে: {num}")
    except Exception:
        bot.send_message(message.chat.id, "❌ নিয়ম: `/setbkash 017XXXXXXXX`")

@bot.message_handler(commands=['setnagad'])
def set_nagad(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        num = message.text.split()[1]
        db_query("INSERT OR REPLACE INTO SETTINGS (key, value) VALUES ('nagad', ?)", (num,), commit=True)
        bot.send_message(message.chat.id, f"✅ নগদ পার্সোনাল নম্বর আপডেট হয়েছে: {num}")
    except Exception:
        bot.send_message(message.chat.id, "❌ নিয়ম: `/setnagad 018XXXXXXXX`")

# ================= TEXT HANDLERS =================
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    text = message.text

    if text == "👤 My Account":
        user = db_query("SELECT * FROM USERS WHERE user_id=?", (user_id,), fetchone=True)
        bal = user['balance'] if user else 0.0
        status = "Active 🟢" if user and user['is_active'] == 1 else "Inactive 🔴"
        plan_id = str(user['plan_id']) if user and user['plan_id'] else "None"
        plan_name = PLANS[plan_id]['name'] if plan_id in PLANS else "None"
        
        msg = f"<b>👤 Worker BD Account Details:</b>\n\n🆔 User ID: <code>{user_id}</code>\n💰 Balance: <b>{bal:.2f} BDT</b>\n⚡ Status: <b>{status}</b>\n💎 Active Plan: <b>{plan_name}</b>"
        bot.send_message(user_id, msg)

    elif text == "⚡ Active Account":
        bkash = get_setting('bkash')
        nagad = get_setting('nagad')
        msg = f"<b>⚡ Account Activation Process (Worker BD):</b>\n\nঅ্যাকাউন্ট অ্যাক্টিভেশন ফি: <b>{ACTIVATION_FEE} BDT</b>\n\nSend Money Number:\n📌 bKash (Personal): <code>{bkash}</code>\n📌 Nagad (Personal): <code>{nagad}</code>\n\n⚠️ <b>টাকা পাঠানোর পর আপনার ইউজার আইডি (<code>{user_id}</code>) সহ এডমিনকে মেসেজ দিন।</b>\n\n🎧 Admin Username: @{SUPPORT_USERNAME}"
        bot.send_message(user_id, msg)

    elif text == "💎 VIP Plan":
        bkash = get_setting('bkash')
        nagad = get_setting('nagad')
        msg = "<b>💎 VIP Plans List (Worker BD):</b>\n\n"
        for pid, pinfo in PLANS.items():
            msg += f"🔹 <b>{pinfo['name']}</b> (ID: {pid}): দাম <b>{pinfo['price']} BDT</b> | দৈনিক: <b>{pinfo['daily']} BDT</b>\n"
        
        msg += f"\nSend Money Number:\n📌 bKash (Personal): <code>{bkash}</code>\n📌 Nagad (Personal): <code>{nagad}</code>\n\n⚠️ <b>প্ল্যান কিনতে টাকা পাঠিয়ে আপনার ইউজার আইডি (<code>{user_id}</code>) সহ এডমিনের সাথে যোগাযোগ করুন।</b>\n\n🎧 Admin: @{SUPPORT_USERNAME}"
        bot.send_message(user_id, msg)

    elif text == "💸 Withdraw":
        user = db_query("SELECT * FROM USERS WHERE user_id=?", (user_id,), fetchone=True)
        if not user or user['is_active'] == 0:
            bot.send_message(user_id, "⚠️ আপনার অ্যাকাউন্টটি সক্রিয় নয়! আগে অ্যাকাউন্ট অ্যাক্টিভ করুন।")
            return
        
        msg = bot.send_message(user_id, f"💳 <b>Withdraw Funds:</b>\n\nমিনিমাম উইথড্র: <b>{MIN_WITHDRAW} BDT</b>\nআপনার ব্যালেন্স: <b>{user['balance']:.2f} BDT</b>\n\nকত টাকা উইথড্র করতে চান লিখুন:")
        bot.register_next_step_handler(msg, process_withdraw_amount)

    elif text == "🔗 Refer & Earn":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        msg = f"<b>🔗 Refer & Earn (Worker BD):</b>\n\nআপনার রেফারেল লিংক:\n<code>{ref_link}</code>\n\nরেফারাল বোনাস:\n- Level 1 একাউন্ট এক্টিভ বোনাস: {REF_LEVEL1_BONUS} BDT\n- Level 2 একাউন্ট এক্টিভ বোনাস: {REF_LEVEL2_BONUS} BDT\n- প্ল্যান ক্রয়ের কমিশন: {PLAN_REF_COMMISSION}%"
        bot.send_message(user_id, msg)

    elif text == "🎧 Support":
        bot.send_message(user_id, f"🎧 Worker BD এডমিনের সাথে যোগাযোগ করতে মেসেজ দিন: @{SUPPORT_USERNAME}")

# ================= WITHDRAW PROCESS =================
def process_withdraw_amount(message):
    try:
        amount = float(message.text.strip())
        user_id = message.from_user.id
        user = db_query("SELECT balance FROM USERS WHERE user_id=?", (user_id,), fetchone=True)
        if amount < MIN_WITHDRAW or amount > user['balance']:
            bot.send_message(user_id, "❌ অপর্যাপ্ত ব্যালেন্স বা ভুল পরিমাণ!")
            return
        msg = bot.send_message(user_id, "📱 আপনার পেমেন্ট নম্বরটি (bKash/Nagad) লিখুন:")
        bot.register_next_step_handler(msg, process_withdraw_number, amount)
    except Exception:
        bot.send_message(user_id, "❌ সঠিক সংখ্যায় পরিমাণ লিখুন।")

def process_withdraw_number(message, amount):
    number = message.text.strip()
    user_id = message.from_user.id
    
    # ইউজারকে পেন্ডিং নোটিফিকেশন দেওয়া
    bot.send_message(user_id, f"⏳ <b>আপনার উইথড্র রিকোয়েস্টটি পেন্ডিং রয়েছে!</b>\n\nপরিমাণ: <b>{amount:.2f} BDT</b>\nনম্বর: <code>{number}</code>\n\nএডমিন রিভিউ করার পর আপনার পেমেন্ট সফল করা হবে।")
    
    # এডমিনকে এপ্রুভ ও রিজেক্ট বাটনের নোটিফিকেশন পাঠানো
    markup = types.InlineKeyboardMarkup()
    btn_approve = types.InlineKeyboardButton("✅ Approve", callback_data=f"wd_app_{user_id}_{amount}_{number}")
    btn_reject = types.InlineKeyboardButton("❌ Reject", callback_data=f"wd_rej_{user_id}_{amount}")
    markup.add(btn_approve, btn_reject)
    
    bot.send_message(
        ADMIN_ID, 
        f"💸 <b>নতুন Withdraw Request (Pending):</b>\n\nUser ID: <code>{user_id}</code>\nAmount: <b>{amount:.2f} BDT</b>\nNumber: <code>{number}</code>", 
        reply_markup=markup
    )

# ================= CALLBACK HANDLER (APPROVE/REJECT) =================
@bot.callback_query_handler(func=lambda call: call.data.startswith('wd_'))
def handle_withdraw_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "আপনি এডমিন নন!", show_alert=True)
        return

    data = call.data.split('_')
    action = data[1]
    target_id = int(data[2])
    amount = float(data[3])

    if action == "app":
        number = data[4]
        user = db_query("SELECT balance FROM USERS WHERE user_id=?", (target_id,), fetchone=True)
        
        if not user or user['balance'] < amount:
            bot.answer_callback_query(call.id, "ইউজারের পর্যাপ্ত ব্যালেন্স নেই!", show_alert=True)
            return

        # ব্যালেন্স কেটে নেওয়া
        db_query("UPDATE USERS SET balance = balance - ? WHERE user_id=?", (amount, target_id), commit=True)
        
        # ইউজারকে সাকসেস মেসেজ পাঠানো
        success_msg = (
            f"🎉 <b>কংগ্রাচুলেশন! আপনার উইথড্র সফল হয়েছে!</b>\n\n"
            f"💰 পরিমাণ: <b>{amount:.2f} BDT</b>\n"
            f"📱 নম্বর: <code>{number}</code>\n"
            f"✅ স্ট্যাটাস: <b>Withdraw Success / Confirmed</b>\n\n"
            f"Worker BD-এর সাথে থাকার জন্য ধন্যবাদ!"
        )
        try:
            bot.send_message(target_id, success_msg)
        except Exception:
            pass

        bot.edit_message_text(f"✅ <b>Withdraw Approved!</b>\nUser ID: <code>{target_id}</code>\nAmount: {amount} BDT", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "উইথড্র সফলভাবে এপ্রুভ করা হয়েছে!")

    elif action == "rej":
        # ইউজারকে বাতিল করার মেসেজ পাঠানো (ব্যালেন্স কাটা হবে না)
        reject_msg = (
            f"❌ <b>দুঃখিত! আপনার উইথড্র রিকোয়েস্টটি বাতিল করা হয়েছে।</b>\n\n"
            f"💰 পরিমাণ: <b>{amount:.2f} BDT</b>\n\n"
            f"দয়া করে সাপোর্ট আইডি বা এডমিনের সাথে যোগাযোগ করুন: @{SUPPORT_USERNAME}"
        )
        try:
            bot.send_message(target_id, reject_msg)
        except Exception:
            pass

        bot.edit_message_text(f"❌ <b>Withdraw Rejected!</b>\nUser ID: <code>{target_id}</code>\nAmount: {amount} BDT", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "উইথড্র রিজেক্ট করা হয়েছে!")

# Clear Webhook
requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=true")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.infinity_polling()
    
