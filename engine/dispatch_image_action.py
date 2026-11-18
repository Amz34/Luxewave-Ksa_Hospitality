#!/usr/bin/env python3
"""Luxe Wave GitHub Actions Image Dispatcher."""
import os
import sys
import json
import time
import urllib.request
import urllib.parse
from PIL import Image, ImageDraw, ImageFont

TOKEN = os.environ.get("LUXEWAVE_PAGE_TOKEN")
PAGE_ID = os.environ.get("LUXEWAVE_PAGE_ID", "115792525")
TG_BOT = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID")
THEME = os.environ.get("THEME", "bedding").lower()

if not TOKEN:
    print("ERROR: Missing LUXEWAVE_PAGE_TOKEN")
    sys.exit(1)

OWNER = f"urn:li:organization:{PAGE_ID}"

THEMES = {
    "bedding": {
        "title": "Five-Star Bedding Collection",
        "subtitle": "400-Thread Count Egyptian Cotton Sheets & Duvets",
        "caption": "Your guests spend eight hours deciding whether to return.\n\nCrisp 400-thread count Egyptian cotton bedding, cloud-soft duvets, and hypoallergenic pillow suites engineered for heavy industrial laundering without losing structure.\n\nLuxe Wave Trading Est. (CR 7050248579) delivers verified hotel-grade bedding across Riyadh, Jeddah, Makkah, and Madinah.\n\nExplore our catalog:\nhttps://luxewave.store\n\n#LuxeWave #HotelSupplies #HospitalityKSA #SaudiHotels #RiyadhHotels",
        "comment": "Catalog and wholesale ordering: https://luxewave.store"
    },
    "mattress": {
        "title": "Oasis Commercial Mattress Series",
        "subtitle": "Engineered Pocket-Spring Durability for 300+ Stays",
        "caption": "Most properties do not lose guests in the lobby. They lose them on night two.\n\nA mattress engineered specifically for high commercial turnover: reinforced edge support, independent pocket coils, and breathable high-density comfort foam.\n\nLuxe Wave supplies the Oasis series to premier hotels across the Kingdom.\n\nhttps://luxewave.store\n\n#LuxeWave #HotelProcurement #CommercialBedding #SaudiHospitality",
        "comment": "Contract specs and wholesale pricing: https://luxewave.store"
    },
    "amenities": {
        "title": "Bespoke Guest Care Amenities",
        "subtitle": "Botanical In-Room Vanity Care & Zero-Plastic Packaging",
        "caption": "Turnkey guest amenities supplied directly to your housekeeping hub.\n\nEliminate multiple vendor friction with standardized packaging, eco-conscious botanical formulations, and guaranteed replenishment SLAs.\n\nhttps://luxewave.store\n\n#LuxeWave #HotelAmenities #HospitalitySupply #Procurement #Riyadh",
        "comment": "Direct inquiries and sample kits: https://luxewave.store"
    }
}

theme_data = THEMES.get(THEME, THEMES["bedding"])
out_img = "luxewave_social_card.jpg"

# Generate branded 4:5 visual card
W, H = 1080, 1350
img = Image.new("RGB", (W, H))
d = ImageDraw.Draw(img)

# Gradient background
top_c, bot_c = (8, 12, 18), (18, 24, 34)
for y in range(H):
    t = y / H
    d.line([(0, y), (W, y)], fill=(int(top_c[0]+(bot_c[0]-top_c[0])*t), int(top_c[1]+(bot_c[1]-top_c[1])*t), int(top_c[2]+(bot_c[2]-top_c[2])*t)))

GOLD = (201, 168, 76)
WHITE = (240, 244, 248)
MUTED = (148, 163, 184)

# Draw typography
d.text((W//2 - 140, 60), "LUXE  WAVE", fill=GOLD)
d.text((W//2 - 220, 110), "PREMIUM HOSPITALITY SUPPLY · SAUDI ARABIA", fill=MUTED)
d.text((W//2 - 180, 140), "CR: 7050248579 · HOTEL-GRADE ESSENTIALS", fill=GOLD)

# Center Box
d.rounded_rectangle([100, 200, 980, 820], radius=24, fill=(16, 22, 32), outline=GOLD, width=3)
d.text((W//2 - 160, 480), "HOTEL-GRADE AMENITIES", fill=WHITE)
d.text((W//2 - 130, 520), "OFFICIAL COLLECTION", fill=GOLD)

# Details
d.text((W//2 - 220, 880), theme_data["title"].upper(), fill=WHITE)
d.text((W//2 - 250, 930), theme_data["subtitle"], fill=MUTED)
d.rounded_rectangle([290, 1050, 790, 1120], radius=35, fill=GOLD)
d.text((340, 1068), "REQUEST CATALOG & SAMPLES", fill=(10, 14, 20))
d.text((W//2 - 160, 1180), "Portal: https://luxewave.store", fill=GOLD)

img.save(out_img, quality=95)
print(f"Generated card: {out_img}")

# LinkedIn Register & Upload
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "X-Restli-Protocol-Version": "2.0.0",
    "User-Agent": "luxewave-gh-publisher/1.0"
}

reg_body = {
    "registerUploadRequest": {
        "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
        "owner": OWNER,
        "serviceRelationships": [{"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}]
    }
}
req = urllib.request.Request("https://api.linkedin.com/v2/assets?action=registerUpload", data=json.dumps(reg_body).encode(), headers=headers)
with urllib.request.urlopen(req, timeout=30) as resp:
    res = json.loads(resp.read().decode())

val = res["value"]
asset = val["asset"]
upload_url = val["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]

up_req = urllib.request.Request(upload_url, data=open(out_img, "rb").read(), method="PUT", headers={"Content-Type": "image/jpeg"})
with urllib.request.urlopen(up_req, timeout=60) as up_res:
    print(f"Uploaded asset: {up_res.status}")

time.sleep(3)

# Publish UGC
post_body = {
    "author": OWNER,
    "lifecycleState": "PUBLISHED",
    "specificContent": {
        "com.linkedin.ugc.ShareContent": {
            "shareCommentary": {"text": theme_data["caption"]},
            "shareMediaCategory": "IMAGE",
            "media": [{
                "status": "READY",
                "description": {"text": theme_data["title"][:70]},
                "media": asset,
                "title": {"text": theme_data["title"][:70]}
            }]
        }
    },
    "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
}
p_req = urllib.request.Request("https://api.linkedin.com/v2/ugcPosts", data=json.dumps(post_body).encode(), headers=headers)
with urllib.request.urlopen(p_req, timeout=30) as p_res:
    p_data = json.loads(p_res.read().decode())

post_id = p_data["id"]
feed_url = f"https://www.linkedin.com/feed/update/{post_id}"
print(f"SUCCESS: LinkedIn Company Page Image Post Live -> {feed_url}")

# Telegram Notification
if TG_BOT and TG_CHAT:
    msg_url = f"https://api.telegram.org/bot{TG_BOT}/sendMessage"
    payload = json.dumps({
        "chat_id": TG_CHAT,
        "text": f"👑 <b>Luxe Wave GitHub Action Image Live!</b>\n\n🎨 <b>Theme:</b> {theme_data['title']}\n🏢 <b>LinkedIn:</b> <a href=\"{feed_url}\">View Post</a>\n🛡️ <i>Strict Isolation Enforced</i>",
        "parse_mode": "HTML"
    }).encode()
    urllib.request.urlopen(urllib.request.Request(msg_url, data=payload, headers={"Content-Type": "application/json"}), timeout=10)
    print("Telegram alert sent.")
