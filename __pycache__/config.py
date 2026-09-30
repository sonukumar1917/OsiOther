# config.py
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8926539620:AAG_g4-eIJA3_wJIsYuijfBN_-n7SjQnyG0")
API_KEY = "cocine"

# API Endpoints
NUM_API      = "https://api-wd7m.onrender.com/api?key=cocine&number={number}&type=mobile"
AADHAR_API   = "https://api-wd7m.onrender.com/api?key=cocine&number={number}&type=leak"
EMAIL_API    = "https://api-wd7m.onrender.com/api?key=cocine&number={email}&type=leak"
VEHICLE_API  = "https://api-wd7m.onrender.com/api?key=cocine&number={number}&type=vehicle"

# Credit Pricing
PRICES = {
    "num": 1,
    "aadhar": 2,
    "email": 2,
    "vehicle": 3,
}

# Owner ID (tumhara telegram user id)
OWNER_ID = 8770083428   # <-- Change this

# New user bonus
WELCOME_CREDITS = 5
REFERRAL_BONUS  = 3

# Force join channel (optional)
FORCE_JOIN = "https://t.me/+gG6uyrj7Vwc1Mjk1"   # set None to disable

# Log channel
LOG_CHANNEL = -1004375426224   # channel id for logs