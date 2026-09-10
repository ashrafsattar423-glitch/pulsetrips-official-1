import os
import re
import json
import random
import requests
import google.generativeai as genai

# Configuration
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL") or os.getenv("WEBHOOK_URL")

genai.configure(api_key=GEMINI_API_KEY)

# Affiliate Links & Widgets Mapping with explicit keywords for Make.com Filters
AFFILIATE_DATA = {
    "flights": {
        "badge": "✈️ Flight Deals",
        "btn_text": "Book Cheap Flights Now",
        "link": "https://kiwi.tpk.ro/NsxwLSqE",
        "keyword": "flight flights airline airfare cheap tickets plane",
        "widget_html": """<script async src="https://tpscr.com/content?currency=usd&trs=570438&shmarker=773883&searchUrl=www.aviasales.com%2Fsearch&locale=en&powered_by=true&origin=LON&destination=BKK&period=year&promo_id=4041&campaign_id=100" charset="utf-8"></script>"""
    },
    "esim": {
        "badge": "📶 International Data eSIM",
        "btn_text": "Get Instant eSIM Plan",
        "link": "https://airalo.tpk.ro/WZs9mIjC",
        "keyword": "esim internet sim card mobile data roaming",
        "widget_html": """<div class="text-center py-6"><p class="text-slate-300 font-semibold mb-2">⚡ Stay Connected Worldwide with Airalo eSIM</p><p class="text-xs text-slate-400">Instant digital activation • No physical SIM needed • High-speed 4G/5G data</p></div>"""
    },
    "tours": {
        "badge": "🎟️ Tours & Experiences",
        "btn_text": "Book Activities & Tickets",
        "link": "https://klook.tpk.ro/TmmM5wxy",
        "keyword": "tour attraction museum entry pass ticket activities things to do",
        "widget_html": """<div class="text-center py-6"><p class="text-slate-300 font-semibold mb-2">🌟 Discover Top Attractions & Day Trips with Klook</p><p class="text-xs text-slate-400">Skip-the-line tickets • Instant confirmation • Verified reviews</p></div>"""
    },
    "transfers": {
        "badge": "🚕 Airport Rides & Taxis",
        "btn_text": "Book Private Airport Taxi",
        "link": "https://gettransfer.tpk.ro/sdoNOlXV",
        "keyword": "transfer taxi airport shuttle ride car rental drive",
        "widget_html": """<div class="text-center py-6"><p class="text-slate-300 font-semibold mb-2">🚘 Premium Airport Transfers with GetTransfer</p><p class="text-xs text-slate-400">Driver meets you at arrival • Fixed pricing • Clean & comfortable vehicles</p></div>"""
    },
    "airhelp": {
        "badge": "⚖️ Flight Compensation",
        "btn_text": "Claim Compensation (Up to $650)",
        "link": "https://airhelp.tpk.ro/GJreOSXw",
        "keyword": "compensation delayed flight canceled claim refund airhelp",
        "widget_html": """<div class="text-center py-6"><p class="text-slate-300 font-semibold mb-2">🛡️ Delayed or Canceled Flight?</p><p class="text-xs text-slate-400">Check if you are eligible for up to $650 compensation with AirHelp.</p></div>"""
    }
}

# 80% Priority Locations (US, UK, Europe Target)
WESTERN_DESTINATIONS = [
    "New York, USA", "London, UK", "Paris, France", "Rome, Italy", 
    "Barcelona, Spain", "Amsterdam, Netherlands", "Santorini, Greece", 
    "Prague, Czech Republic", "Zurich, Switzerland", "Vienna, Austria",
    "Los Angeles, USA", "Edinburgh, Scotland"
]

# 20% Global Locations
GLOBAL_DESTINATIONS = [
    "Tokyo, Japan", "Bali, Indonesia", "Dubai, UAE", 
    "Istanbul, Turkey", "Bangkok, Thailand", "Kyoto, Japan"
]

def clean_text(text):
    return re.sub(r'[*#_`]', '', text).strip()

def get_pexels_image(query):
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=1"
    try:
        res = requests.get(url, headers=headers).json()
        if res.get("photos"):
            return res["photos"][0]["src"]["large"]
    except Exception as e:
        print(f"Pexels error: {e}")
    return "https://images.pexels.com/photos/386009/pexels-photo-386009.jpeg"

def get_target_destination():
    # 80% chance Western, 20% Global
    if random.random() < 0.8:
        return random.choice(WESTERN_DESTINATIONS)
    return random.choice(GLOBAL_DESTINATIONS)

def generate_content(destination, topic):
    # Higher temperature (0.75 equivalent) via generation_config
    generation_config = genai.types.GenerationConfig(
        temperature=0.75,
        top_p=0.9
    )
    model = genai.GenerativeModel("models/gemini-1.5-flash", generation_config=generation_config)
    
    keyword_hint = AFFILIATE_DATA[topic]["keyword"]
    prompt = f"""Create a highly engaging Pinterest-optimized travel pin content focusing on '{topic}' for {destination}.
Make sure to naturally include relevant travel search keywords like: {keyword_hint}.
Target US/UK/EU tourists searching for trending travel tips and deals.
Return ONLY valid JSON with exact keys: 'title', 'description', 'slug'."""

    try:
        res = model.generate_content(prompt)
        text = res.text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            title = clean_text(data["title"])
            description = clean_text(data["description"])
            # Inject keyword in description to guarantee Make.com filter matching
            description += f" Best {topic} options and travel deals for {destination}."
            return title, description, data["slug"]
    except Exception as e:
        print(f"Gemini API Error: {e}")
    
    slug = f"{destination.lower().replace(',', '').replace(' ', '-')}-{topic}-{random.randint(100,999)}"
    title = f"Ultimate {destination} {topic.capitalize()} Guide"
    description = f"Discover exclusive deals and book your {topic} ({keyword_hint}) for {destination} today."
    return title, description, slug

def build_html_page(title, description, image_url, destination, slug, topic):
    os.makedirs("destinations", exist_ok=True)
    file_path = f"destinations/{slug}.html"
    
    topic_data = AFFILIATE_DATA.get(topic, AFFILIATE_DATA["flights"])
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - PulseTrips</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-slate-950 text-slate-100 font-sans min-h-screen flex flex-col justify-between">

    <!-- Header -->
    <header class="border-b border-slate-800 bg-slate-900/90 backdrop-blur-md sticky top-0 z-50">
        <div class="max-w-5xl mx-auto px-4 py-3.5 flex items-center justify-between">
            <a href="/" class="text-xl font-black text-blue-500 tracking-wide flex items-center gap-2">
                <i class="fa-solid fa-plane-departure text-blue-400"></i> PulseTrips
            </a>
            <span class="text-xs font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> Verified Deal
            </span>
        </div>
    </header>

    <!-- Main Section -->
    <main class="flex-grow flex items-center justify-center px-4 py-10">
        <div class="max-w-3xl w-full bg-slate-900/80 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl relative">
            
            <!-- Hero Image Banner -->
            <div class="relative h-64 md:h-80 w-full overflow-hidden">
                <img src="{image_url}" alt="{title}" class="w-full h-full object-cover">
                <div class="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/40 to-transparent"></div>
                
                <div class="absolute top-4 left-4">
                    <span class="bg-blue-600/90 text-white text-xs font-bold px-3 py-1.5 rounded-full shadow-lg backdrop-blur-md">
                        {topic_data['badge']}
                    </span>
                </div>
            </div>

            <!-- Content Area -->
            <div class="p-6 md:p-8">
                <h1 class="text-2xl md:text-4xl font-extrabold text-white mb-3 leading-tight">{title}</h1>
                <p class="text-slate-300 text-sm md:text-base mb-6 leading-relaxed">{description}</p>

                <!-- Live Topic Widget Box -->
                <div class="bg-slate-950/70 border border-slate-800 rounded-2xl p-4 md:p-6 mb-6 shadow-inner">
                    {topic_data['widget_html']}
                </div>

                <!-- Call to Action Button -->
                <a href="{topic_data['link']}" target="_blank" rel="noopener noreferrer" class="group flex items-center justify-center gap-3 w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold py-4 px-8 rounded-2xl transition-all duration-300 shadow-xl shadow-blue-600/20 text-lg text-center">
                    <span>{topic_data['btn_text']}</span>
                    <i class="fa-solid fa-arrow-right transition-transform group-hover:translate-x-1"></i>
                </a>

                <!-- Conversion Features / Trust Indicators -->
                <div class="mt-6 pt-6 border-t border-slate-800/80 grid grid-cols-3 gap-2 text-center">
                    <div>
                        <i class="fa-solid fa-shield-halved text-blue-400 text-sm mb-1"></i>
                        <p class="text-[11px] text-slate-400 font-medium">100% Secure</p>
                    </div>
                    <div>
                        <i class="fa-solid fa-bolt text-amber-400 text-sm mb-1"></i>
                        <p class="text-[11px] text-slate-400 font-medium">Instant Booking</p>
                    </div>
                    <div>
                        <i class="fa-solid fa-tag text-emerald-400 text-sm mb-1"></i>
                        <p class="text-[11px] text-slate-400 font-medium">Best Price Guarantee</p>
                    </div>
                </div>

            </div>

        </div>
    </main>

    <!-- Footer -->
    <footer class="border-t border-slate-800 bg-slate-900 py-4 text-center text-slate-500 text-xs">
        &copy; 2026 PulseTrips. Direct booking options provided by verified partners.
    </footer>

</body>
</html>
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    return f"https://pulsetrips.com/destinations/{slug}.html"

def send_to_make(title, description, image_url, page_url):
    if not MAKE_WEBHOOK_URL:
        print("Webhook URL missing, skipping Make.com call")
        return
    payload = {
        "title": title,
        "description": description,
        "image_url": image_url,
        "link": page_url
    }
    requests.post(MAKE_WEBHOOK_URL, json=payload)

def main():
    destination = get_target_destination()
    topic = random.choice(list(AFFILIATE_DATA.keys()))
    
    title, description, slug = generate_content(destination, topic)
    image_url = get_pexels_image(destination)
    
    page_url = build_html_page(title, description, image_url, destination, slug, topic)
    send_to_make(title, description, image_url, page_url)
    print(f"Successfully created {topic} page for {destination}: {page_url}")

if __name__ == "__main__":
    main()
