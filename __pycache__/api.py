# api.py
import aiohttp
from config import NUM_API, AADHAR_API, EMAIL_API, VEHICLE_API

async def fetch(url):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=45)) as r:
                if r.status != 200:
                    return {"error": f"HTTP {r.status}"}
                return await r.json()
    except Exception as e:
        return {"error": str(e)}

async def num_lookup(number):
    return await fetch(NUM_API.format(number=number))

async def aadhar_lookup(number):
    return await fetch(AADHAR_API.format(number=number))

async def email_lookup(email):
    return await fetch(EMAIL_API.format(email=email))

async def vehicle_lookup(number):
    return await fetch(VEHICLE_API.format(number=number))