from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import json
import os
import random
import time

TOKEN = "8641217051:AAE2r_hCQ0KvnPfXoUt5MveCWd4JSzXTje8"
ADMIN_ID = 1043242158

USERS_FILE = "users.json"
CHANNELS_FILE = "channels.json"
REF_FILE = "refs.json"

last_used = {}

# ---------- JSON ----------
def load_json(file):
    if os.path.exists(file):
        with open(file,"r") as f:
            return json.load(f)
    return {}

def save_json(file,data):
    with open(file,"w") as f:
        json.dump(data,f)

# ---------- Anti Spam ----------
def anti_spam(user):
    now = time.time()
    if user in last_used:
        if now-last_used[user] < 2:
            return False
    last_used[user] = now
    return True

# ---------- Start ----------
async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)

    if not anti_spam(user_id):
        return

    users = load_json(USERS_FILE)
    refs = load_json(REF_FILE)

    if context.args:
        ref = context.args[0]
        if ref != user_id:
            refs[ref] = refs.get(ref,0)+1
            save_json(REF_FILE,refs)

    if user_id not in users:
        users[user_id] = {"points":0}
        save_json(USERS_FILE,users)

    channels = load_json(CHANNELS_FILE).get("channels",["@Courses_by_Professor_OmarHussein"])

    buttons = []

    for ch in channels:
        buttons.append([InlineKeyboardButton(f"📢 اشترك في {ch}",url=f"https://t.me/{ch.replace('@','')}")])

    buttons.append([InlineKeyboardButton("✅ تحقق من الاشتراك",callback_data="check")])

    keyboard = InlineKeyboardMarkup(buttons)

    a = random.randint(1,10)
    b = random.randint(1,10)

    context.user_data["captcha"] = a+b

    await update.message.reply_text(
        f"👋 أهلاً بك\n\nحل الكابتشا:\n{a}+{b}=?",
        reply_markup=keyboard
    )

# ---------- Captcha ----------
async def captcha(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if "captcha" not in context.user_data:
        return

    ans = context.user_data["captcha"]

    if update.message.text == str(ans):

        await update.message.reply_text("✅ تم حل الكابتشا")

        context.user_data.pop("captcha")

    else:

        await update.message.reply_text("❌ جواب خطأ")

# ---------- Check Join ----------
async def check(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = query.from_user.id

    channels = load_json(CHANNELS_FILE).get("channels",["@Courses_by_Professor_OmarHussein"])

    for ch in channels:

        member = await context.bot.get_chat_member(ch,user)

        if member.status in ["left","kicked"]:

            await query.answer("❌ اشترك بكل القنوات",show_alert=True)
            return

    await query.edit_message_text("🎉 تم التحقق\nادخل الكروب:\nhttps://t.me/Courses_OmarHussein")

# ---------- Invite ----------
async def invite(update:Update,context:ContextTypes.DEFAULT_TYPE):

    bot = context.bot.username
    user = update.effective_user.id

    link = f"https://t.me/{bot}?start={user}"

    await update.message.reply_text(f"🔗 رابط الدعوة:\n{link}")

# ---------- Refs ----------
async def refs(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user = str(update.effective_user.id)

    refs = load_json(REF_FILE)

    count = refs.get(user,0)

    await update.message.reply_text(f"👥 دعوت:\n{count}")

# ---------- Points ----------
async def points(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user = str(update.effective_user.id)

    users = load_json(USERS_FILE)

    p = users.get(user,{}).get("points",0)

    await update.message.reply_text(f"💰 نقاطك:\n{p}")

# ---------- Admin ----------
async def admin(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    buttons = [
    [InlineKeyboardButton("📊 احصائيات",callback_data="stats")],
    [InlineKeyboardButton("📢 برودكاست",callback_data="broadcast")],
  [InlineKeyboardButton("➕ اضافة قناة",callback_data="addch")]
    ]

    await update.message.reply_text("لوحة التحكم",reply_markup=InlineKeyboardMarkup(buttons))

# ---------- Admin Buttons ----------
async def admin_btn(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    data = query.data

    if data == "stats":

        users = load_json(USERS_FILE)

        await query.edit_message_text(f"👥 المستخدمين:\n{len(users)}")

    if data == "broadcast":

        context.user_data["bc"]=True

        await query.message.reply_text("ارسل الرسالة")

    if data == "addch":

        context.user_data["add"]=True

        await query.message.reply_text("ارسل @channel")

# ---------- Admin Messages ----------
async def admin_msg(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if context.user_data.get("bc"):

        users = load_json(USERS_FILE)

        for u in users:

            try:
                await context.bot.send_message(u,update.message.text)
            except:
                pass

        context.user_data["bc"]=False

        await update.message.reply_text("تم الارسال")

    elif context.user_data.get("add"):

        ch = update.message.text

        data = load_json(CHANNELS_FILE)

        channels = data.get("channels",[])

        channels.append(ch)

        data["channels"]=channels

        save_json(CHANNELS_FILE,data)

        context.user_data["add"]=False

        await update.message.reply_text("تمت الاضافة")

# ---------- Run ----------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("invite",invite))
app.add_handler(CommandHandler("refs",refs))
app.add_handler(CommandHandler("points",points))
app.add_handler(CommandHandler("admin",admin))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,captcha))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,admin_msg))

app.add_handler(CallbackQueryHandler(check,pattern="check"))
app.add_handler(CallbackQueryHandler(admin_btn))

print("Bot running...")
app.run_polling()