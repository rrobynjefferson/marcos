import os
import json
import requests
import time
import re
import random
import warnings
import string
import pandas as pd
from datetime import datetime
from slugify import slugify
from io import BytesIO
from PIL import Image
from groq import Groq, APIError, RateLimitError
from pytrends.request import TrendReq

# --- SUPPRESS WARNINGS ---
warnings.filterwarnings("ignore", category=FutureWarning)

# ==========================================
# ⚙️ KONFIGURASI: WORLD ADVENTURE GUIDE
# ==========================================

GROQ_KEYS_RAW = os.environ.get("GROQ_API_KEY", "")
GROQ_API_KEYS = [k.strip() for k in GROQ_KEYS_RAW.split(",") if k.strip()]

WEBSITE_URL = "https://marcos.biz.id"
INDEXNOW_KEY = "e74819b68a0f40e98f6ec3dc24f610f0"

if not GROQ_API_KEYS:
    print("❌ FATAL ERROR: Groq API Key is missing! Set env var GROQ_API_KEY")
    exit(1)

# 🔥 PERSONA PENULIS (Spesialis Dunia)
AUTHOR_PROFILES = [
    "Leo 'The Ranger' Santoso (Senior Expedition Leader, 20+ Countries)",
    "Sarah Wilds (Adventure Travel Journalist & Logistics Expert)",
    "Mike Overland (4x4 & Overland Route Specialist)",
    "Dr. Forest Green (Eco-Tourism Guide & Conservationist)",
    "Elena Summit (High-Altitude Alpinist & Travel Writer)",
    "Reza Petualang (Indonesian Adventure Blogger & Trail Runner)",
    "Yuki Yamamoto (Asia Pacific Adventure Specialist)",
    "Marco Expeditions (Latin America & Patagonia Expert)",
    "Amara Trails (Africa & Middle East Adventure Guide)"
]

# 📂 KATEGORI DESTINASI
VALID_CATEGORIES = [
    # Berdasarkan Benua
    "Asia Adventures", "Europe Trekking", "Americas Exploration",
    "Africa Expeditions", "Oceania Wilderness", "Middle East Discovery",
    # Berdasarkan Jenis Adventure
    "Mountain Expeditions", "Tropical Jungles", "Desert Trekking",
    "Coastal & Diving", "River & Kayaking", "Wildlife Safari",
    "Volcano Trekking", "Cultural Heritage Trails", "Winter & Ice Adventures",
    # Berdasarkan Level
    "Beginner Friendly", "Extreme Adventures", "Family Adventures",
    # Umum
    "Global Destinations", "Travel Logistics", "Hidden Gems"
]

# 🌍 SEED DESTINASI DUNIA (Komprehensif: 5 Benua)
SEED_KEYWORDS = [
    # === ASIA ===
    "Everest Base Camp Trek Nepal",
    "Annapurna Circuit Nepal",
    "K2 Base Camp Baltoro Glacier Pakistan",
    "Trekking Rinjani Lombok Indonesia",
    "Bromo Tengger Semeru East Java",
    "Raja Ampat Diving West Papua",
    "Komodo Island Dragon Trek",
    "Flores Island Land Route",
    "Mount Fuji Climbing Japan",
    "Japan Alps Traverse Kamikochi",
    "Tiger's Nest Monastery Bhutan Trek",
    "Snowman Trek Bhutan",
    "Inca Trail Sacred Valley Peru",
    "Yunnan Tiger Leaping Gorge China",
    "Ha Giang Loop Vietnam Motorbike",
    "Sapa Fansipan Trekking Vietnam",
    "Phong Nha Caves Expedition Vietnam",
    "Himachal Pradesh Spiti Valley India",
    "Ladakh Motorcycle Adventure India",
    "Western Ghats Jungle Trek India",
    "Sri Lanka Adam's Peak Pilgrimage",
    "Mulu Caves Borneo Malaysia",
    "Mount Kinabalu Summit Climb",
    "Kawah Ijen Sulfur Mining Trek Java",
    "Banda Islands Spice Route Indonesia",
    "Wae Rebo Traditional Village Flores",
    "Tengger Caldera Hiking East Java",
    "Nusa Penida Island Cliffs Bali",
    # === EROPA ===
    "Tour du Mont Blanc Alps",
    "Via Ferrata Dolomites Italy",
    "Camino de Santiago Spain",
    "Laugavegur Trail Iceland",
    "Trolltunga Hiking Norway",
    "Preikestolen Pulpit Rock Norway",
    "West Highland Way Scotland",
    "GR20 Corsica Trek France",
    "Haute Route Chamonix Zermatt",
    "Tatry Mountains Slovakia",
    "Faroe Islands Hiking Routes",
    "Swiss Alps Via Alpina",
    "Julian Alps Slovenia Trek",
    "Transylvania Carpathians Romania",
    "Alpe Adria Trail Austria",
    # === AMERICAS ===
    "Patagonia Torres del Paine Chile",
    "W Trek Patagonia Guide",
    "O Trek Torres del Paine",
    "Fitz Roy Trekking Argentina Patagonia",
    "Machu Picchu Inca Trail Peru",
    "Lares Trek Peru Alternative",
    "Quilotoa Loop Ecuador",
    "Cotopaxi Volcano Climb Ecuador",
    "Amazon Jungle Expedition Brazil",
    "Pantanal Wildlife Safari Brazil",
    "Roraima Tepui Venezuela",
    "Yosemite Half Dome Climb California",
    "Grand Canyon Rim to Rim",
    "Zion Narrows Hiking Utah",
    "Banff National Park Lake Louise",
    "Haida Gwaii Wilderness Canada",
    "Baja California Whale Watching Mexico",
    "Copper Canyon Mexico Trekking",
    # === AFRIKA ===
    "Kilimanjaro Summit Tanzania",
    "Mount Kenya Trekking Routes",
    "Rwenzori Mountains Uganda",
    "Virunga Gorilla Trekking Rwanda",
    "Simien Mountains Ethiopia",
    "Drakensberg Traverse South Africa",
    "Sahara Desert Trekking Morocco",
    "Atlas Mountains Trek Morocco",
    "Erg Chebbi Sand Dunes Morocco",
    "Namib Desert Namibia Adventure",
    "Fish River Canyon Namibia",
    "Okavango Delta Canoe Safari Botswana",
    "Masai Mara Safari Kenya",
    "Serengeti Great Migration Tanzania",
    "Mozambique Island Scuba Diving",
    # === OCEANIA ===
    "Milford Track New Zealand",
    "Routeburn Track NZ South Island",
    "Tongariro Alpine Crossing NZ",
    "Kokoda Track Papua New Guinea",
    "Overland Track Tasmania Australia",
    "Larapinta Trail Northern Territory Australia",
    "Uluru Kata Tjuta Cultural Walk",
    "Great Barrier Reef Diving Queensland",
    "Whitsunday Islands Sailing Australia",
    "Vanuatu Volcano Island Ambrym",
    # === TIMUR TENGAH & LAINNYA ===
    "Petra Lost City Trekking Jordan",
    "Wadi Rum Desert Jordan",
    "Oman Jebel Akhdar Mountain",
    "Hajar Mountains Oman Trekking",
    "Dead Sea Jordan Float Experience",
    "Musandam Fjords Oman Kayak",
    "Georgia Caucasus Mountains Trek",
    "Kazbegi National Park Georgia",
    "Armenia Khachkar Trails",
    # === KUTUB & EKSTRIM ===
    "Antarctica Expedition Cruise",
    "Arctic Svalbard Ice Trekking",
    "Greenland Ice Sheet Crossing",
    "Iceland Northern Lights Trek"
]

CONTENT_DIR = "content/articles"
IMAGE_DIR = "static/images"
DATA_DIR = "automation/data"
MEMORY_FILE = f"{DATA_DIR}/link_memory.json"

TARGET_ARTICLES = 1

# ==========================================
# 🧠 HELPER FUNCTIONS
# ==========================================
def load_link_memory():
    if not os.path.exists(MEMORY_FILE): return {}
    try:
        with open(MEMORY_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_link_to_memory(title, slug):
    os.makedirs(DATA_DIR, exist_ok=True)
    memory = load_link_memory()
    memory[title] = f"/articles/{slug}/"
    if len(memory) > 500: memory = dict(list(memory.items())[-500:])
    with open(MEMORY_FILE, 'w') as f: json.dump(memory, f, indent=2)

def optimize_seo_slug(text, main_keyword=None):
    stop_words = [
        'a', 'an', 'the', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'guide', 'ultimate', 'complete', 'review', 'best', 'trip', 'tour', 'travel',
        'how', 'get', 'adventure', 'journey', 'is', 'are', 'was', 'your', 'my'
    ]
    source_text = main_keyword if main_keyword and len(main_keyword.split()) > 1 else text
    words = slugify(source_text).split('-')
    clean_words = [w for w in words if w not in stop_words]
    if not clean_words: clean_words = words
    final_slug = "-".join(clean_words[:5])
    return final_slug

def fetch_trending_topics(keywords, max_results=3):
    print(f"      ... Memilih destinasi dari database...")
    topics = []

    try:
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
        current_kw = random.choice(keywords)
        print(f"      🔍 Menganalisa Destinasi: '{current_kw}'")
        time.sleep(random.uniform(2, 5))
        pytrends.build_payload([current_kw], cat=0, timeframe='today 12-m', geo='', gprop='')
        related = pytrends.related_queries()

        if current_kw in related and related[current_kw]['top'] is not None:
            df_top = related[current_kw]['top']
            for index, row in df_top.iterrows():
                query = row['query']
                if any(x in query for x in ['guide', 'cost', 'route', 'how to', 'trek', 'hike', 'camp', 'itinerary', 'best time', 'permit', 'difficulty']):
                    topics.append(query.title())
                    if len(topics) >= max_results: break

            if len(topics) > 0:
                print(f"      ✅ Ditemukan {len(topics)} topik trending.")
                return topics

        print("      ⚠️ Menggunakan Seed Destination (Fallback).")
        return [f"{current_kw} Complete Travel Guide"]

    except Exception as e:
        print(f"      ⚠️ GTrends Fallback: {e}")
        chosen = random.choice(keywords)
        return [chosen]

def clean_markdown_body(text):
    if not text: return ""
    text = re.sub(r'^```[a-zA-Z]*\n', '', text)
    text = re.sub(r'\n```$', '', text)
    text = text.replace("```", "")
    patterns = [r'^#+\s*Introduction\s*$', r'^#+\s*Conclusion\s*$', r'^#+\s*Summary\s*$']
    for p in patterns:
        text = re.sub(p, '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'([^\n])\n(#{2,4}\s)', r'\1\n\n\2', text)
    return text.strip()

# ==========================================
# 📑 NAVIGASI & LINKS
# ==========================================
def generate_toc(content_body):
    headers = re.findall(r'^(#{2,3})\s+(.+)$', content_body, flags=re.MULTILINE)
    if not headers: return ""
    toc_lines = ["**📋 Table of Contents**\n"]
    for level, title in headers:
        anchor = slugify(title)
        indent = "  " if level == "###" else ""
        toc_lines.append(f"{indent}- [{title}](#{anchor})")
    return "\n".join(toc_lines) + "\n\n---\n\n"

def inject_smart_links(content_body, current_title):
    memory = load_link_memory()
    internal_links = []

    if memory:
        current_keywords = set(current_title.lower().split())
        for title, url in memory.items():
            title_words = set(title.lower().split())
            common = current_keywords.intersection(title_words)
            common = [w for w in common if len(w) > 3]
            if len(common) > 0:
                internal_links.append((title, url))

        if not internal_links:
            items = list(memory.items())
            internal_links = random.sample(items, min(3, len(items)))
        else:
            internal_links = internal_links[:3]

    # External authority links — Travel & Booking
    external_links = [
        ("Skyscanner — Cari Tiket Terbaik", "https://www.skyscanner.com/"),
        ("Booking.com — Akomodasi Dunia", "https://www.booking.com/"),
        ("Lonely Planet Guides", "https://www.lonelyplanet.com/"),
        ("Hostelworld — Budget Stays", "https://www.hostelworld.com/"),
        ("Viator — Tours & Activities", "https://www.viator.com/"),
        ("GetYourGuide — Local Guides", "https://www.getyourguide.com/"),
        ("iOverlander — Overlander Maps", "https://www.ioverlander.com/"),
        ("AllTrails — Trail Maps", "https://www.alltrails.com/")
    ]

    final_box = ""
    if internal_links:
        final_box += "\n\n> **🌏 Destinasi Terkait di WorldAdventure.Guide:**\n"
        for title, url in internal_links:
            final_box += f"> - [{title}]({url})\n"

    if len(internal_links) < 2:
        ext = random.choice(external_links)
        final_box += f"\n> **✈️ Resource Perjalanan:** [{ext[0]}]({ext[1]})\n"

    final_box += "\n"

    paragraphs = content_body.split('\n\n')
    if len(paragraphs) > 6:
        paragraphs.insert(5, final_box)
        return "\n\n".join(paragraphs)
    return content_body + final_box

# ==========================================
# 🚀 INDEXING
# ==========================================
def submit_to_indexnow(url):
    try:
        endpoint = "https://api.indexnow.org/indexnow"
        host = "marcos.biz.id"
        data = {
            "host": host,
            "key": INDEXNOW_KEY,
            "keyLocation": f"https://{host}/{INDEXNOW_KEY}.txt",
            "urlList": [url]
        }
        requests.post(endpoint, json=data, headers={'Content-Type': 'application/json'}, timeout=10)
        print(f"      🚀 IndexNow Submitted")
    except Exception: pass

# ==========================================
# 🎨 IMAGE GENERATOR (LANDSCAPE/LOCATION)
# ==========================================
def generate_outdoor_image(prompt, filename):
    output_path = f"{IMAGE_DIR}/{filename}"
    default_img = "/images/default-adventure.webp"

    forced_style = "travel photography, wide angle lens, national geographic style, dramatic golden hour light, cinematic composition, 8k resolution, photorealistic, award-winning landscape"
    clean_prompt = prompt.replace("Guide", "").replace("Review", "").replace("Trekking", "").strip()
    final_prompt = f"{clean_prompt} landscape, {forced_style}"

    print(f"      🎨 Generating Image: {clean_prompt[:35]}...")
    headers = {"User-Agent": "Mozilla/5.0"}

    # 1. HERCAI (Best for Landscape)
    try:
        hercai_url = f"https://hercai.onrender.com/v3/text2image?prompt={requests.utils.quote(final_prompt)}"
        resp = requests.get(hercai_url, headers=headers, timeout=45)
        if resp.status_code == 200:
            data = resp.json()
            if "url" in data:
                img_data = requests.get(data["url"], headers=headers, timeout=30).content
                if len(img_data) > 3000:
                    img = Image.open(BytesIO(img_data)).convert("RGB")
                    img.save(output_path, "WEBP", quality=90)
                    print("      ✅ Image Saved (Hercai AI)")
                    return f"/images/{filename}"
    except Exception: pass

    # 2. FLICKR LOC (Fallback - Real Location Photo)
    try:
        search_term = "+".join(clean_prompt.split()[:2])
        flickr_url = f"https://loremflickr.com/1280/720/{search_term},landscape,nature/all"
        resp = requests.get(flickr_url, headers=headers, timeout=30, allow_redirects=True)
        if resp.status_code == 200 and len(resp.content) > 3000:
            img = Image.open(BytesIO(resp.content)).convert("RGB")
            img.save(output_path, "WEBP", quality=90)
            print("      ✅ Image Saved (Flickr Stock)")
            return f"/images/{filename}"
    except Exception: pass

    return default_img

# ==========================================
# 🧠 AI ENGINE — WORLD ADVENTURE GUIDE
# ==========================================
def get_groq_article_markdown(keyword, author_name):
    current_time = datetime.now().strftime("%B %Y")

    # 🔥 MEGA PROMPT — PANDUAN LENGKAP DESTINASI DUNIA
    system_prompt = f"""
    You are {author_name}, a world-class Adventure Travel Expert and Logistics Specialist.
    Your readers are adventure travelers from Indonesia and around the world who SERIOUSLY want to visit this destination.
    Current Date: {current_time}.

    MISSION: Write the MOST COMPREHENSIVE and ACTIONABLE Adventure Guide for "{keyword}".
    This must be genuinely useful — real numbers, real places, real routes.

    ==============================================
    🗺️ MANDATORY ARTICLE STRUCTURE (FOLLOW EXACTLY):
    ==============================================

    ## 🌄 Why {keyword}? (Daya Tarik Utama)
    - Apa yang membuat destinasi ini UNIK dan WAJIB dikunjungi?
    - Pengalaman apa yang tidak bisa didapat di tempat lain?
    - Highlight visual/sensory (warna landscape, suara, bau, rasa)
    - Best reasons: spiritual, physical challenge, nature, culture, or all?

    ## ✈️ Cara Menuju ke {keyword} (Rute Perjalanan Lengkap)
    Sub-sections WAJIB:
    ### Dari Indonesia (via Jalur Udara)
    - Bandara Internasional asal terbaik (CGK, DPS, SUB, dll)
    - Maskapai rekomendasi + transit hub (misalnya via Singapura, Dubai, dll)
    - Estimasi harga tiket (range LOW-HIGH season)
    - App/website booking terbaik

    ### Dari Gateway City ke Lokasi (Last Mile)
    - Kota terdekat yang punya bandara internasional
    - Transportasi darat: bus, kereta, jeep, ojek, boat — dengan nama perusahaan
    - Durasi perjalanan REALISTIS (jangan underestimate!)
    - Titik transit dan checkpoint penting
    - Jika perlu penyeberangan ferry/boat: detail kapal dan pelabuhan

    ### Opsi Overland/Backpacker Route
    - Jalur darat alternatif untuk budget traveler
    - Border crossing jika lintas negara (nama pos perbatasan resmi)

    ## 🗓️ Waktu Terbaik Berkunjung
    - Peak season vs off-season (bulan spesifik)
    - Kondisi cuaca per musim
    - Festival/event lokal yang worth attending
    - WARNING: musim/cuaca buruk yang harus dihindari (banjir, badai salju, dll)

    ## 🥾 Aktivitas Adventure & Itinerary
    Berikan itinerary REALISTIS per hari:
    ### Hari 1 — [Nama Aktivitas]
    (detail route, landmark, jarak, elevasi jika relevant)
    ### Hari 2 — [Nama Aktivitas]
    ... dst sesuai trip length ideal

    Jenis aktivitas yang bisa dilakukan:
    - Trekking/Hiking (nama trail, panjang, difficulty level: Easy/Moderate/Hard/Extreme)
    - Climbing (nama peak, height, technical grade if any)
    - Diving/Snorkeling (dive sites, visibility, marine life)
    - Safari (animal species, best viewing spots)
    - Kayaking/Rafting (sungai/danau, difficulty class)
    - Cultural visits (nama suku, ritual, permission needed)
    - Photography spots (golden hour spots, coordinates if possible)

    ## 🏕️ Akomodasi & Basecamp
    - Budget option: camping/hostel (harga per malam)
    - Mid-range: guesthouse/lodge (harga + nama)
    - Premium: eco-lodge/resort (nama + estimasi harga)
    - Wild camping: legal or not? permit needed?
    - Nama-nama akomodasi NYATA di lokasi

    ## 💰 Budget & Biaya Perjalanan
    Breakdown detail (dalam USD, juga IDR jika relevan):
    - Tiket pesawat pulang-pergi
    - Akomodasi per malam (low/mid/high range)
    - Makan per hari
    - Transportasi lokal
    - Entry fees / permit fees (harga EXACT)
    - Guide fees (wajib atau opsional?)
    - Equipment rental jika perlu
    - TOTAL ESTIMASI 7-10 hari

    ## 🎒 Perlengkapan Wajib (Gear List)
    Spesifik untuk kondisi destinasi ini:
    - Pakaian (lapisan yang dibutuhkan, material)
    - Alas kaki (jenis boot/sandal)
    - Navigation tools
    - Safety equipment
    - Medical kit khusus (altitude sickness, tropical disease, dll)
    - Electronics (adapter, power bank, satellite communicator?)

    ## 📋 Visa, Permit & Regulasi
    - Visa requirements untuk WNI (perlu visa atau bebas visa?)
    - Izin masuk kawasan (nama permit, cara apply, harga, lead time)
    - Wajib pakai guide lokal? Ya/Tidak dan alasannya
    - Regulasi lingkungan (drone ban, campfire rules, dll)
    - Kontak embassy/konsulat terdekat

    ## ⚠️ Keselamatan & Risiko
    - Risiko utama di lokasi ini (altitude, wildlife, cuaca, dll)
    - Emergency contacts (SAR lokal, hospital terdekat, medical evac)
    - Travel insurance rekomendasi
    - Common mistakes yang harus dihindari
    - Solo travel: aman atau tidak?

    ## 🌱 Etika & Responsible Travel
    - Leave No Trace principles spesifik untuk lokasi ini
    - Bagaimana mendukung komunitas lokal (beli produk lokal, dll)
    - Musim ini: apakah perlu aklimatisasi khusus?

    ==============================================
    STYLE GUIDELINES:
    ==============================================
    - Gunakan BAHASA INGGRIS untuk artikel (SEO) — tapi boleh mix Bahasa Indonesia untuk tips khusus WNI
    - Use H2 (##) for main sections, H3 (###) for sub-steps
    - Use bullet points and numbered lists heavily
    - Include REAL numbers, REAL place names, REAL prices (estimate clearly)
    - Be SPECIFIC: "Bus from Kathmandu to Lukla" not just "take a bus"
    - Add emoji sparingly for readability
    - Minimum length: 2500 words. Target: 3000+ words.
    
    OUTPUT FORMAT: Start DIRECTLY with YAML frontmatter, no preamble.

    ---
    title: "Engaging, Keyword-Rich H1 Title Here (under 70 chars)"
    description: "Meta description: Complete travel guide including how to get there, itinerary, costs, and tips for [Location]. (under 160 chars)"
    category: "MOST RELEVANT CATEGORY"
    tags: ["adventure", "trekking", "destination", "travel-guide", "location-name"]
    main_keyword: "{keyword}"
    continent: "CONTINENT NAME"
    difficulty: "Easy/Moderate/Hard/Extreme"
    duration: "X-Y Days"
    best_season: "Month Range"
    ---

    [FULL ARTICLE CONTENT STARTS HERE]
    """

    user_prompt = f"""
    Write the complete adventure guide for: {keyword}
    
    IMPORTANT: 
    - Include specific real place names, actual transport options, and realistic cost ranges
    - Section "Cara Menuju" (How To Get There) must be VERY detailed with all transport legs
    - Must be genuinely useful for someone who has NEVER been there before
    - Include Indonesian traveler perspective (flights from Jakarta/Bali)
    - Minimum 2500 words
    """

    for api_key in GROQ_API_KEYS:
        client = Groq(api_key=api_key)
        try:
            print(f"      🤖 AI Writing Comprehensive Adventure Guide...")
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.65,
                max_tokens=8000,
            )
            return completion.choices[0].message.content
        except RateLimitError:
            print(f"      ⏳ Rate limit, waiting...")
            time.sleep(10)
        except Exception as e:
            print(f"      ❌ API Error: {e}")
    return None

def parse_ai_response(raw_text):
    try:
        match = re.search(r'---\n(.*?)\n---', raw_text, re.DOTALL)
        if match:
            yaml_text = match.group(1)
            data = {}
            for line in yaml_text.split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key == 'tags':
                        clean_tags = val.replace('[', '').replace(']', '').replace('"', '').replace("'", "")
                        data['tags'] = [t.strip() for t in clean_tags.split(',')]
                    else:
                        data[key] = val
            content_body = raw_text.split('---', 2)[-1].strip()
            return data, content_body
        else:
            return None, None
    except Exception:
        return None, None

# ==========================================
# 🏁 MAIN WORKFLOW
# ==========================================
def main():
    os.makedirs(CONTENT_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    print("🌍 WORLD ADVENTURE GUIDE ENGINE STARTED")
    print(f"   📍 Total Destinasi Database: {len(SEED_KEYWORDS)} locations")
    print(f"   🎯 Target Articles: {TARGET_ARTICLES}")

    trending_topics = fetch_trending_topics(SEED_KEYWORDS, max_results=TARGET_ARTICLES)

    processed_count = 0

    for topic in trending_topics:
        if processed_count >= TARGET_ARTICLES: break

        clean_topic = topic.strip().title()
        temp_slug_check = slugify(clean_topic)

        exists = False
        for f in os.listdir(CONTENT_DIR):
            if temp_slug_check in f: exists = True

        if exists:
            print(f"   ⏩ Skipped (exists): {clean_topic}")
            continue

        print(f"\n   🗺️  Generating Guide: {clean_topic}")

        author = random.choice(AUTHOR_PROFILES)
        print(f"   ✍️  Author: {author}")

        raw_output = get_groq_article_markdown(clean_topic, author)
        if not raw_output:
            print(f"   ❌ Failed to generate: {clean_topic}")
            continue

        meta_data, body_content = parse_ai_response(raw_output)
        if not meta_data or not body_content:
            print(f"   ❌ Failed to parse: {clean_topic}")
            continue

        title = meta_data.get('title', clean_topic)
        main_kw = meta_data.get('main_keyword', clean_topic)

        final_slug = optimize_seo_slug(title, main_keyword=main_kw)

        filename = f"{final_slug}.md"
        img_filename = f"{final_slug}.webp"

        img_path = generate_outdoor_image(main_kw, img_filename)
        clean_body = clean_markdown_body(body_content)
        final_body = generate_toc(clean_body) + inject_smart_links(clean_body, title)

        cat = meta_data.get('category', "Global Destinations")
        if cat not in VALID_CATEGORIES: cat = random.choice(VALID_CATEGORIES)

        # Extra metadata dari AI
        continent = meta_data.get('continent', '')
        difficulty = meta_data.get('difficulty', '')
        duration = meta_data.get('duration', '')
        best_season = meta_data.get('best_season', '')

        md = f"""---
title: "{title.replace('"', "'")}"
date: {datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00")}
author: "{author}"
categories: ["{cat}"]
tags: {json.dumps(meta_data.get('tags', []))}
featured_image: "{img_path}"
description: "{meta_data.get('description', '').replace('"', "'")}"
slug: "{final_slug}"
url: "/articles/{final_slug}/"
draft: false
weight: {random.randint(1, 10)}
continent: "{continent}"
difficulty: "{difficulty}"
duration: "{duration}"
best_season: "{best_season}"
---

{final_body}

---
*⚠️ Disclaimer: Informasi perjalanan dapat berubah sewaktu-waktu. Selalu cek kondisi terkini dengan konsulat, otoritas lokal, atau operator tour sebelum berangkat. Harga yang tercantum adalah estimasi dan dapat berubah.*

*Panduan ini dibuat oleh {author} berdasarkan riset lapangan dan data terkini per {datetime.now().strftime("%B %Y")}.*
"""
        with open(f"{CONTENT_DIR}/{filename}", "w", encoding="utf-8") as f:
            f.write(md)

        save_link_to_memory(title, final_slug)
        submit_to_indexnow(f"{WEBSITE_URL}/articles/{final_slug}/")

        word_count = len(final_body.split())
        print(f"      ✅ Published: {final_slug}")
        print(f"      📊 Words: {word_count} | Category: {cat}")
        processed_count += 1

        print("      💤 Cooling down 60s (rate limit)...")
        time.sleep(60)

    print(f"\n🏁 Done! Generated {processed_count} articles.")

if __name__ == "__main__":
    main()