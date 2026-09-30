# main.py
import random, string, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from config import *
import database as db
import api
from keyboards import main_menu, admin_menu

# ---------- helpers ----------
def fmt_response(title, data):
    if isinstance(data, dict) and "error" in data:
        return f"❌ *{title}*\n\n`{data['error']}`"
    lines = [f"✨ *{title}* ✨\n"]
    if isinstance(data, dict):
        for k, v in data.items():
            lines.append(f"• *{k}:* `{v}`")
    else:
        lines.append(f"`{data}`")
    return "\n".join(lines)

# ---------- /start ----------
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    uname = update.effective_user.username or "NoUsername"
    user = db.get_user(uid)
    # referral
    if ctx.args and ctx.args[0].startswith("ref_"):
        try:
            ref_id = int(ctx.args[0][4:])
            if ref_id != uid:
                conn = __import__("sqlite3").connect("bot_data.db")
                c = conn.cursor()
                c.execute("SELECT referred_by FROM users WHERE user_id=?", (uid,))
                if c.fetchone()[0] == 0:
                    c.execute("UPDATE users SET referred_by=? WHERE user_id=?", (ref_id, uid))
                    c.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (REFERRAL_BONUS, ref_id))
                    conn.commit()
                    try:
                        await ctx.bot.send_message(ref_id, f"🎉 New referral! +{REFERRAL_BONUS} credits")
                    except: pass
                conn.close()
        except: pass

    text = (
        f"╔══════════════════════╗\n"
        f"   💎 *LUXURY OSINT BOT* 💎\n"
        f"╚══════════════════════╝\n\n"
        f"👋 Welcome, *{update.effective_user.first_name}*\n"
        f"🆔 `{uid}`\n"
        f"💰 Credits: *{user[2]}*\n\n"
        f"🔍 Select a service below:"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu())

# ---------- generic API handler ----------
async def run_api(update, ctx, api_type, query):
    uid = update.effective_user.id
    user = db.get_user(uid)
    if user[3]:  # banned
        return await update.message.reply_text("🚫 You are banned.")
    if user[4]:  # muted
        return await update.message.reply_text("🔇 You are muted.")
    if db.get_setting("maintenance", "off") == "on" and not db.is_admin(uid):
        return await update.message.reply_text("🛠️ Bot under maintenance. Try later.")

    price = PRICES[api_type]
    if user[2] < price:
        return await update.message.reply_text(
            f"❌ *Insufficient credits*\nNeed: `{price}` | You have: `{user[2]}`",
            parse_mode="Markdown"
        )

    msg = await update.message.reply_text("⏳ *Searching...*", parse_mode="Markdown")
    try:
        if api_type == "num":
            res = await api.num_lookup(query)
            title = "📱 NUMBER INFO"
        elif api_type == "aadhar":
            res = await api.aadhar_lookup(query)
            title = "🆔 LEAK INFO"
        elif api_type == "email":
            res = await api.email_lookup(query)
            title = "📧 EMAIL LEAK"
        else:
            res = await api.vehicle_lookup(query)
            title = "🚗 VEHICLE INFO"

        db.update_credits(uid, -price)
        db.log_search(uid, api_type, query, res)
        text = fmt_response(title, res)
        await msg.edit_text(text, parse_mode="Markdown")

        # log to channel
        if LOG_CHANNEL:
            try:
                await ctx.bot.send_message(
                    LOG_CHANNEL,
                    f"🔍 *{api_type}* by `{uid}`\nQuery: `{query}`\nCost: {price}"
                , parse_mode="Markdown")
            except: pass
    except Exception as e:
        await msg.edit_text(f"❌ Error: `{e}`", parse_mode="Markdown")

# ---------- commands ----------
async def cmd_num(update, ctx):
    if not ctx.args:
        return await update.message.reply_text("Usage: `/num 91XXXXXXXXXX`", parse_mode="Markdown")
    await run_api(update, ctx, "num", ctx.args[0])

async def cmd_aadhar(update, ctx):
    if not ctx.args:
        return await update.message.reply_text("Usage: `/aadhar 91XXXXXXXXXX`", parse_mode="Markdown")
    await run_api(update, ctx, "aadhar", ctx.args[0])

async def cmd_email(update, ctx):
    if not ctx.args:
        return await update.message.reply_text("Usage: `/email abc@mail.com`", parse_mode="Markdown")
    await run_api(update, ctx, "email", ctx.args[0])

async def cmd_vehicle(update, ctx):
    if not ctx.args:
        return await update.message.reply_text("Usage: `/vehicle DL01AB1234`", parse_mode="Markdown")
    await run_api(update, ctx, "vehicle", ctx.args[0])

async def cmd_balance(update, ctx):
    user = db.get_user(update.effective_user.id)
    await update.message.reply_text(f"💰 *Balance:* `{user[2]}` credits", parse_mode="Markdown")

async def cmd_profile(update, ctx):
    uid = update.effective_user.id
    u = db.get_user(uid)
    txt = (
        f"👤 *PROFILE*\n\n"
        f"🆔 ID: `{uid}`\n"
        f"💰 Credits: `{u[2]}`\n"
        f"🔎 Searches: `{u[5]}`\n"
        f"📅 Joined: `{u[6][:10]}`"
    )
    await update.message.reply_text(txt, parse_mode="Markdown")

async def cmd_history(update, ctx):
    rows = db.get_history(update.effective_user.id, 10)
    if not rows:
        return await update.message.reply_text("No history yet.")
    txt = "📜 *Last Searches*\n\n"
    for t, q, ts in rows:
        txt += f"• `{t}` → `{q}` ({ts[:10]})\n"
    await update.message.reply_text(txt, parse_mode="Markdown")

async def cmd_redeem(update, ctx):
    if not ctx.args:
        return await update.message.reply_text("Usage: `/redeem CODE`", parse_mode="Markdown")
    amt = db.redeem_code(ctx.args[0], update.effective_user.id)
    if amt is None:
        return await update.message.reply_text("❌ Invalid or used code.")
    await update.message.reply_text(f"✅ Redeemed! +{amt} credits")

async def cmd_refer(update, ctx):
    uid = update.effective_user.id
    link = f"https://t.me/{ctx.bot.username}?start=ref_{uid}"
    await update.message.reply_text(
        f"👥 *Referral Program*\n\nShare this link:\n`{link}`\n\n"
        f"Earn *{REFERRAL_BONUS}* credits per join!",
        parse_mode="Markdown"
    )

# ---------- ADMIN COMMANDS ----------
def admin_only(func):
    async def wrapper(update, ctx):
        if not db.is_admin(update.effective_user.id):
            return await update.message.reply_text("⛔ Admin only.")
        return await func(update, ctx)
    return wrapper

@admin_only
async def cmd_admin(update, ctx):
    await update.message.reply_text("👑 *ADMIN PANEL*", parse_mode="Markdown", reply_markup=admin_menu())

@admin_only
async def cmd_addcredits(update, ctx):
    if len(ctx.args) < 2:
        return await update.message.reply_text("Usage: `/addcredits <uid> <amt>`")
    uid, amt = int(ctx.args[0]), int(ctx.args[1])
    db.update_credits(uid, amt)
    await update.message.reply_text(f"✅ Added {amt} credits to `{uid}`", parse_mode="Markdown")

@admin_only
async def cmd_removecredits(update, ctx):
    if len(ctx.args) < 2:
        return await update.message.reply_text("Usage: `/removecredits <uid> <amt>`")
    uid, amt = int(ctx.args[0]), int(ctx.args[1])
    db.update_credits(uid, -amt)
    await update.message.reply_text(f"✅ Removed {amt} credits from `{uid}`", parse_mode="Markdown")

@admin_only
async def cmd_ban(update, ctx):
    uid = int(ctx.args[0])
    db.set_ban(uid, 1)
    await update.message.reply_text(f"🚫 Banned `{uid}`", parse_mode="Markdown")

@admin_only
async def cmd_unban(update, ctx):
    uid = int(ctx.args[0])
    db.set_ban(uid, 0)
    await update.message.reply_text(f"✅ Unbanned `{uid}`", parse_mode="Markdown")

@admin_only
async def cmd_mute(update, ctx):
    uid = int(ctx.args[0])
    db.set_mute(uid, 1)
    await update.message.reply_text(f"🔇 Muted `{uid}`", parse_mode="Markdown")

@admin_only
async def cmd_unmute(update, ctx):
    uid = int(ctx.args[0])
    db.set_mute(uid, 0)
    await update.message.reply_text(f"🔊 Unmuted `{uid}`", parse_mode="Markdown")

@admin_only
async def cmd_users(update, ctx):
    await update.message.reply_text(f"👥 Total users: `{db.count_users()}`", parse_mode="Markdown")

@admin_only
async def cmd_stats(update, ctx):
    total = db.count_users()
    txt = f"📊 *BOT STATS*\n\n👥 Users: `{total}`\n🛠️ Maintenance: `{db.get_setting('maintenance','off')}`"
    await update.message.reply_text(txt, parse_mode="Markdown")

@admin_only
async def cmd_broadcast(update, ctx):
    if not ctx.args:
        return await update.message.reply_text("Reply: `/broadcast <message>`")
    text = " ".join(ctx.args)
    sent = 0
    for uid in db.all_users():
        try:
            await ctx.bot.send_message(uid, f"📢 *Broadcast*\n\n{text}", parse_mode="Markdown")
            sent += 1
            await asyncio.sleep(0.05)
        except: pass
    await update.message.reply_text(f"✅ Sent to {sent} users.")

@admin_only
async def cmd_gencode(update, ctx):
    if len(ctx.args) < 2:
        return await update.message.reply_text("Usage: `/gencode <amt> <qty>`")
    amt, qty = int(ctx.args[0]), int(ctx.args[1])
    codes = []
    for _ in range(qty):
        code = "LUX-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        db.gen_code(code, amt)
        codes.append(code)
    await update.message.reply_text("🎟️ *Generated Codes:*\n\n" + "\n".join(f"`{c}`" for c in codes), parse_mode="Markdown")

@admin_only
async def cmd_userinfo(update, ctx):
    uid = int(ctx.args[0])
    u = db.get_user(uid)
    txt = (
        f"👤 *USER INFO*\n\n"
        f"🆔 `{u[0]}`\n💰 Credits: `{u[2]}`\n"
        f"🚫 Banned: `{u[3]}`\n🔇 Muted: `{u[4]}`\n"
        f"🔎 Searches: `{u[5]}`\n📅 Joined: `{u[6][:10]}`"
    )
    await update.message.reply_text(txt, parse_mode="Markdown")

@admin_only
async def cmd_maintenance(update, ctx):
    if not ctx.args:
        return await update.message.reply_text("Usage: `/maintenance on|off`")
    val = ctx.args[0].lower()
    db.set_setting("maintenance", val)
    await update.message.reply_text(f"🛠️ Maintenance: `{val}`", parse_mode="Markdown")

@admin_only
async def cmd_addadmin(update, ctx):
    uid = int(ctx.args[0])
    db.add_admin(uid)
    await update.message.reply_text(f"👑 Promoted `{uid}` to admin", parse_mode="Markdown")

@admin_only
async def cmd_deladmin(update, ctx):
    uid = int(ctx.args[0])
    db.del_admin(uid)
    await update.message.reply_text(f"❌ Demoted `{uid}`", parse_mode="Markdown")

@admin_only
async def cmd_logs(update, ctx):
    await update.message.reply_text("📜 Logs are being sent to log channel.")

@admin_only
async def cmd_setprice(update, ctx):
    if len(ctx.args) < 2:
        return await update.message.reply_text("Usage: `/setprice num <amt>`")
    key, amt = ctx.args[0], int(ctx.args[1])
    PRICES[key] = amt
    await update.message.reply_text(f"✅ {key} price → {amt}")

@admin_only
async def cmd_resetuser(update, ctx):
    uid = int(ctx.args[0])
    db.set_ban(uid, 0); db.set_mute(uid, 0)
    db.update_credits(uid, -999999)  # will go to default
    await update.message.reply_text(f"♻️ Reset `{uid}`", parse_mode="Markdown")

# ---------- callback handler ----------
async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data == "balance":
        user = db.get_user(q.from_user.id)
        await q.message.reply_text(f"💰 Balance: `{user[2]}`", parse_mode="Markdown")
    elif data == "profile":
        u = db.get_user(q.from_user.id)
        await q.message.reply_text(
            f"👤 `{q.from_user.id}`\n💰 `{u[2]}`\n🔎 `{u[5]}`",
            parse_mode="Markdown"
        )
    elif data.startswith("api_"):
        api_type = data[4:]
        await q.message.reply_text(
            f"Send command:\n`/{api_type} <value>`",
            parse_mode="Markdown"
        )
    elif data == "back_main":
        await q.message.reply_text("🏠 Main Menu", reply_markup=main_menu())
    elif data.startswith("a_"):
        if not db.is_admin(q.from_user.id):
            return
        await q.message.reply_text("Use commands for admin actions.")

# ---------- run ----------
def main():
    db.init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    # user
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("num", cmd_num))
    app.add_handler(CommandHandler("aadhar", cmd_aadhar))
    app.add_handler(CommandHandler("email", cmd_email))
    app.add_handler(CommandHandler("vehicle", cmd_vehicle))
    app.add_handler(CommandHandler("balance", cmd_balance))
    app.add_handler(CommandHandler("profile", cmd_profile))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(CommandHandler("redeem", cmd_redeem))
    app.add_handler(CommandHandler("refer", cmd_refer))

    # admin
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("addcredits", cmd_addcredits))
    app.add_handler(CommandHandler("removecredits", cmd_removecredits))
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(CommandHandler("unban", cmd_unban))
    app.add_handler(CommandHandler("mute", cmd_mute))
    app.add_handler(CommandHandler("unmute", cmd_unmute))
    app.add_handler(CommandHandler("users", cmd_users))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CommandHandler("gencode", cmd_gencode))
    app.add_handler(CommandHandler("userinfo", cmd_userinfo))
    app.add_handler(CommandHandler("maintenance", cmd_maintenance))
    app.add_handler(CommandHandler("addadmin", cmd_addadmin))
    app.add_handler(CommandHandler("deladmin", cmd_deladmin))
    app.add_handler(CommandHandler("logs", cmd_logs))
    app.add_handler(CommandHandler("setprice", cmd_setprice))
    app.add_handler(CommandHandler("resetuser", cmd_resetuser))

    # callbacks
    app.add_handler(CallbackQueryHandler(on_button))

    print("🚀 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()