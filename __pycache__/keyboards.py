# keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    kb = [
        [InlineKeyboardButton("📱 Number Lookup", callback_data="api_num")],
        [InlineKeyboardButton("🆔 Aadhar/Leak", callback_data="api_aadhar"),
         InlineKeyboardButton("📧 Email Leak", callback_data="api_email")],
        [InlineKeyboardButton("🚗 Vehicle RC", callback_data="api_vehicle")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance"),
         InlineKeyboardButton("👤 Profile", callback_data="profile")],
        [InlineKeyboardButton("🎁 Redeem", callback_data="redeem"),
         InlineKeyboardButton("👥 Refer", callback_data="refer")],
        [InlineKeyboardButton("📜 History", callback_data="history"),
         InlineKeyboardButton("☎️ Support", callback_data="support")],
    ]
    return InlineKeyboardMarkup(kb)

def admin_menu():
    kb = [
        [InlineKeyboardButton("👥 Users", callback_data="a_users"),
         InlineKeyboardButton("📊 Stats", callback_data="a_stats")],
        [InlineKeyboardButton("💰 Add Credits", callback_data="a_addcred"),
         InlineKeyboardButton("➖ Remove Credits", callback_data="a_remcred")],
        [InlineKeyboardButton("🚫 Ban", callback_data="a_ban"),
         InlineKeyboardButton("✅ Unban", callback_data="a_unban")],
        [InlineKeyboardButton("🔇 Mute", callback_data="a_mute"),
         InlineKeyboardButton("🔊 Unmute", callback_data="a_unmute")],
        [InlineKeyboardButton("🎟️ Gen Codes", callback_data="a_gen"),
         InlineKeyboardButton("📋 List Codes", callback_data="a_listcodes")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="a_broadcast")],
        [InlineKeyboardButton("👤 User Info", callback_data="a_uinfo")],
        [InlineKeyboardButton("⚙️ Maintenance", callback_data="a_maint")],
        [InlineKeyboardButton("📜 Logs", callback_data="a_logs")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(kb)