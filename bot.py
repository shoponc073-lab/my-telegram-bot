import os
import time
import requests
from flask import Flask
from threading import Thread
import telebot
from telebot import types
import sqlite3
import random

# ================= CONFIGURATION =================
TOKEN = "7821617300:AAHQi-pGWD3zToiU468uC8c1bCYoI21yB5M"  # Replace with your Telegram Bot Token
ADMIN_ID = 5410884108
CHANNEL_USERNAME = "@earnmoneybd10"
SUPPORT_USERNAME = "bad_mon_100"
CHANNEL_LINK = "https://t.me/earnmoneybd10"

ACTIVATION_FEE = 100.0
MIN_WITHDRAW = 50.0
REF_LEVEL1_BONUS = 10.0
REF_LEVEL2_BONUS = 5.0
PLAN_REF_COMMISSION = 20.0

PLANS = {
    "1": {"name": "VIP Plan 1", "price": 1000.0, "daily": 50.0},
    "2": {"name": "VIP Plan 2", "price": 2000.0, "daily": 100.0},
    "3": {"name": "VIP Plan 3", "price": 5000.0, "daily": 300.0},
    "4": {"name": "VIP Plan 4", "price": 7000.0, "daily": 450.0},
}

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running smoothly!"

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
        balance REAL DEFAULT 0.5,
        is_active INTEGER DEFAULT 0,
        ref_by INTEGER DEFAULT 0,
        last_draw_time TEXT DEFAULT NULL,
        plan_id TEXT DEFAULT 'TEST DEFAULT NULL'
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS pending_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        req_type TEXT,
        amount REAL,
        trx_id TEXT
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

# ================= HELPER FUNCTIONS =================
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
        markup.add(types.InlineKeyboardButton("✅ Verified & Continue", callback_data="check_join"))
        bot.send_message(user_id, "⚠️ **বট ব্যবহার করার জন্য প্রথমে আমাদের চ্যানেলে জয়েন করুন:**", reply_markup=markup)
        return

    bot.send_message(user_id, "<b>👋 স্বাগতম! আমাদের অফিসিয়াল Earning Bot-এ!</b>", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    text = message.text

    if not is_channel_member(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
        markup.add(types.InlineKeyboardButton("✅ Verified & Continue", callback_data="check_join"))
        bot.send_message(user_id, "⚠️ **বট ব্যবহার করার জন্য প্রথমে আমাদের চ্যানেলে জয়েন করুন:**", reply_markup=markup)
        return

    if text == "👤 My Account":
        user = db_query("SELECT * FROM USERS WHERE user_id=?", (user_id,), fetchone=True)
        bal = user['balance'] if user else 0.0
        status = "Active 🟢" if user and user['is_active'] == 1 else "Inactive 🔴"
        plan_id = user['plan_id'] if user and user['plan_id'] else "None"
        plan_name = PLANS[plan_id]['name'] if plan_id in PLANS else "None"
        
        msg = f"<b>👤 Account Details:</b>\n\n🆔 User ID: <code>{user_id}</code>\n💰 Balance: <b>{bal:.2f} BDT</b>\n⚡ Status: <b>{status}</b>\n💎 Active Plan: <b>{plan_name}</b>"
        bot.send_message(user_id, msg)

    elif text == "⚡ Active Account":
        bkash = get_setting('bkash')
        nagad = get_setting('nagad')
        msg = f"<b>⚡ Account Activation Process:</b>\n\nঅ্যাকাউন্ট অ্যাক্টিভেশন ফি: <b>{ACTIVATION_FEE} BDT</b>\n\nSend Money Number:\n📌 bKash: <code>{bkash}</code>\n📌 Nagad: <code>{nagad}</code>\n\nটাকা পাঠানোর পর নিচের বাটনে ক্লিক করে TrxID দিন।"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Submit TrxID", callback_data="submit_act_trx"))
        bot.send_message(user_id, msg, reply_markup=markup)

    elif text == "💎 VIP Plan":
        msg = "<b>💎 Available VIP Plans:</b>\n\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for pid, pinfo in PLANS.items():
            msg += f"🔹 <b>{pinfo['name']}</b>: Price <b>{pinfo['price']} BDT</b> | Daily: <b>{pinfo['daily']} BDT</b>\n"
            markup.add(types.InlineKeyboardButton(f"Buy {pinfo['name']} - {pinfo['price']} BDT", callback_data=f"buy_plan_{pid}"))
        
        bot.send_message(user_id, msg, reply_markup=markup)

    elif text == "💸 Withdraw":
        user = db_query("SELECT * FROM USERS WHERE user_id=?", (user_id,), fetchone=True)
        if not user or user['is_active'] == 0:
            bot.send_message(user_id, "⚠️ **মেসেজ:** আপনার অ্যাকাউন্টটি সক্রিয় নয়! অ্যাকাউন্ট অ্যাক্টিভ করুন।")
            return
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💵 Request Withdraw", callback_data="start_withdraw"))
        bot.send_message(user_id, f"💳 **Withdraw Funds:**\n\nমিনিমাম উইথড্র: <b>{MIN_WITHDRAW} BDT</b>\nআপনার ব্যালেন্স: <b>{user['balance']:.2f} BDT</b>", reply_markup=markup)

    elif text == "🔗 Refer & Earn":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        msg = f"<b>🔗 Refer & Earn:</b>\n\nআপনার রেফারেল লিংক:\n<code>{ref_link}</code>\n\nরেফারাল বোনাস:\n- Level 1: {REF_LEVEL1_BONUS} BDT\n- Level 2: {REF_LEVEL2_BONUS} BDT"
        bot.send_message(user_id, msg)

    elif text == "🎧 Support":
        bot.send_message(user_id, f"🎧 আমাদের সাপোর্ট টিমের সাথে যোগাযোগ করতে মেসেজ দিন: @{SUPPORT_USERNAME}")

# ================= CALLBACK QUERY HANDLER =================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    
    if call.data == "check_join":
        if is_channel_member(user_id):
            bot.answer_callback_query(call.id, "✅ ধন্যবাদ! আপনি জয়েন করেছেন।")
            bot.send_message(user_id, "<b>👋 স্বাগতম!</b>", reply_markup=get_main_keyboard())
        else:
            bot.answer_callback_query(call.id, "⚠️ আপনি এখনও চ্যানেলে জয়েন করেননি!", show_alert=True)

    elif call.data == "submit_act_trx":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(user_id, "📝 অনুগ্রহ করে আপনার Send Money-এর <b>Transaction ID (TrxID)</b> দিন:")
        bot.register_next_step_handler(msg, process_activation_trx)

    elif call.data.startswith("buy_plan_"):
        bot.answer_callback_query(call.id)
        plan_id = call.data.split("_")[2]
        pinfo = PLANS.get(plan_id)
        if pinfo:
            bkash = get_setting('bkash')
            nagad = get_setting('nagad')
            msg = f"<b>💎 {pinfo['name']} ক্রয় করুন:</b>\n\nদাম: <b>{pinfo['price']} BDT</b>\n\nSend Money Number:\n📌 bKash: <code>{bkash}</code>\n📌 Nagad: <code>{nagad}</code>\n\nটাকা পাঠিয়ে নিচের বাটনে ক্লিক করে TrxID সাবমিট করুন।"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📝 Submit TrxID", callback_data=f"submit_plan_trx_{plan_id}"))
            bot.send_message(user_id, msg, reply_markup=markup)

    elif call.data.startswith("submit_plan_trx_"):
        bot.answer_callback_query(call.id)
        plan_id = call.data.split("_")[3]
        msg = bot.send_message(user_id, "📝 প্ল্যান কেনার জন্য আপনার <b>Transaction ID (TrxID)</b> দিন:")
        bot.register_next_step_handler(msg, process_plan_trx, plan_id)

    elif call.data == "start_withdraw":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(user_id, f"💸 কত টাকা উইথড্র করতে চান লিখুন (মিনিমাম {MIN_WITHDRAW} BDT):")
        bot.register_next_step_handler(msg, process_withdraw_amount)

    # Admin Callback Actions
    elif call.data.startswith("act_approve_") or call.data.startswith("act_reject_"):
        bot.answer_callback_query(call.id)
        action, _, req_id = call.data.split("_")
        req = db_query("SELECT * FROM pending_requests WHERE id=?", (req_id,), fetchone=True)
        if req:
            target_user = req['user_id']
            if action == "act_approve":
                db_query("UPDATE USERS SET is_active=1 WHERE user_id=?", (target_user,), commit=True)
                db_query("DELETE FROM pending_requests WHERE id=?", (req_id,), commit=True)
                bot.send_message(target_user, "🎉 **আপনার অ্যাকাউন্টটি সফলভাবে অ্যাক্টিভ করা হয়েছে!**")
                bot.send_message(ADMIN_ID, f"✅ Request {req_id} Approved.")
            else:
                db_query("DELETE FROM pending_requests WHERE id=?", (req_id,), commit=True)
                bot.send_message(target_user, "❌ **আপনার অ্যাকাউন্ট অ্যাক্টিভেশন রিকোয়েস্ট বাতিল করা হয়েছে।**")
                bot.send_message(ADMIN_ID, f"❌ Request {req_id} Rejected.")

    elif call.data.startswith("plan_approve_") or call.data.startswith("plan_reject_"):
        bot.answer_callback_query(call.id)
        parts = call.data.split("_")
        action = parts[0]
        req_id = parts[2]
        req = db_query("SELECT * FROM pending_requests WHERE id=?", (req_id,), fetchone=True)
        if req:
            target_user = req['user_id']
            plan_id = req['trx_id']
            if action == "plan":
                db_query("UPDATE USERS SET plan_id=? WHERE user_id=?", (plan_id, target_user), commit=True)
                db_query("DELETE FROM pending_requests WHERE id=?", (req_id,), commit=True)
                bot.send_message(target_user, f"🎉 **আপনার {PLANS[plan_id]['name']} সফলভাবে চালু হয়েছে!**")
                bot.send_message(ADMIN_ID, f"✅ Plan Request {req_id} Approved.")
            else:
                db_query("DELETE FROM pending_requests WHERE id=?", (req_id,), commit=True)
                bot.send_message(target_user, "❌ **আপনার VIP Plan কেনার আবেদন বাতিল করা হয়েছে।**")
                bot.send_message(ADMIN_ID, f"❌ Plan Request {req_id} Rejected.")

# ================= STEP HANDLERS =================
def process_activation_trx(message):
    trx_id = message.text.strip()
    user_id = message.from_user.id
    db_query("INSERT INTO pending_requests (user_id, req_type, amount, trx_id) VALUES (?, 'act', ?, ?)",
             (user_id, ACTIVATION_FEE, trx_id), commit=True)
    req = db_query("SELECT id FROM pending_requests WHERE user_id=? AND req_type='act' ORDER BY id DESC LIMIT 1", (user_id,), fetchone=True)
    
    bot.send_message(user_id, "✅ আপনার TrxID জমা নেওয়া হয়েছে। এডমিন চেক করে অনুমোদন দেবেন।")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Approve ✅", callback_data=f"act_approve_{req['id']}"),
        types.InlineKeyboardButton("Reject ❌", callback_data=f"act_reject_{req['id']}")
    )
    bot.send_message(ADMIN_ID, f"📥 **New Activation Request:**\nUser ID: `{user_id}`\nTrxID: `{trx_id}`", reply_markup=markup)

def process_plan_trx(message, plan_id):
    trx_id = message.text.strip()
    user_id = message.from_user.id
    pinfo = PLANS[plan_id]
    db_query("INSERT INTO pending_requests (user_id, req_type, amount, trx_id) VALUES (?, 'plan', ?, ?)",
             (user_id, pinfo['price'], plan_id), commit=True)
    req = db_query("SELECT id FROM pending_requests WHERE user_id=? AND req_type='plan' ORDER BY id DESC LIMIT 1", (user_id,), fetchone=True)
    
    bot.send_message(user_id, "✅ আপনার অনুরোধটি জমা দেওয়া হয়েছে।")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Approve ✅", callback_data=f"plan_approve_{req['id']}"),
        types.InlineKeyboardButton("Reject ❌", callback_data=f"plan_reject_{req['id']}")
    )
    bot.send_message(ADMIN_ID, f"📥 **New Plan Purchase Request:**\nPlan: {pinfo['name']}\nUser ID: `{user_id}`\nTrxID: `{trx_id}`", reply_markup=markup)

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
        bot.send_message(user_id, "❌ সংখ্যায় সঠিক পরিমাণ লিখুন।")

def process_withdraw_number(message, amount):
    number = message.text.strip()
    user_id = message.from_user.id
    db_query("UPDATE USERS SET balance = balance - ? WHERE user_id=?", (amount, user_id), commit=True)
    bot.send_message(user_id, f"✅ **উইথড্র রিকোয়েস্ট জমা হয়েছে!**\nপরিমাণ: {amount} BDT\nনম্বর: {number}")
    bot.send_message(ADMIN_ID, f"💸 **Withdraw Request:**\nUser ID: `{user_id}`\nAmount: {amount} BDT\nNumber: `{number}`")

# Delete old webhook then start polling
requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=true")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    print("Bot Polling Started...")
    bot.infinity_polling()
        
