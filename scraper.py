import os
import time
import asyncio
import requests
import cloudscraper
import httpx

# गिटहब एनवायरनमेंट / सीक्रेट्स से क्रेडेंशियल्स लोड करना
# नोट: अब हम सीधे इनकी मुख्य API एंडपॉइंट को टारगेट कर रहे हैं
TARGET_URL = os.environ.get("TARGET_SCRAPE_URL", "https://netmirror.center")
BOT_TOKEN = os.environ.get("BOT_TOKEN")  
LEECH_CHAT_ID = os.environ.get("LEECH_CHAT_ID")  

def fetch_api_data():
    """नेटमिरर की हिडन एपीआई से सीधे लेटेस्ट मूवीज और शोज का डेटा निकालना"""
    # वेबसाइट के डोमेन के आधार पर उनकी इंटरनल एपीआई का पाथ
    api_url = f"{TARGET_URL.rstrip('/')}/api/v1/home" 
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": TARGET_URL,
        "Origin": TARGET_URL
    }

    # तरीका 1: Cloudscraper से API हिट करना
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(api_url, headers=headers, timeout=20)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"[API Warning] Cloudscraper API फेल: {e}")

    # तरीका 2: HTTPX से बैकअप एपीआई हिट करना
    try:
        with httpx.Client(headers=headers, follow_redirects=True, timeout=20.0) as client:
            resp = client.get(api_url)
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        print(f"[API Critical Error] एपीआई से डेटा नहीं मिल सका: {e}")
    
    return None

def send_to_leech_bot(download_link, movie_title):
    """टेलीग्राम ग्रुप में लीच कमांड भेजना"""
    if not BOT_TOKEN or not LEECH_CHAT_ID:
        print("[Telegram Error] BOT_TOKEN या LEECH_CHAT_ID सीक्रेट्स मिसिंग हैं!")
        return

    leech_command = f"/leech {download_link}"
    caption = f"🎬 <b>Movie:</b> {movie_title}\n\n<code>{leech_command}</code>"
    
    telegram_url = f"https://telegram.org{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": LEECH_CHAT_ID,
        "text": caption,
        "parse_mode": "HTML"
    }
    
    try:
        resp = requests.post(telegram_url, json=payload, timeout=15)
        if resp.status_code == 200:
            print(f"[Telegram] सफलतापूर्वक भेजा गया: {movie_title}")
        else:
            print(f"[Telegram Error] सेंड करने में दिक्कत आई: {resp.text}")
    except Exception as e:
        print(f"[Telegram Critical] कनेक्शन फेल: {e}")

async def run_auto_scraper_loop():
    print("[Engine] एडवांस्ड API नेटमिरर क्रॉलर शुरू हो रहा है...")
    
    while True:
        try:
            # सीधे बैकएंड एपीआई से JSON डेटा मंगवाना
            data = fetch_api_data()
            
            if data and "results" in data:
                movies = data["results"]
                print(f"[Engine] सफलतापूर्वक कुल {len(movies)} मूवीज/शोज का डेटा फेच हुआ।")
                
                for movie in movies:
                    title = movie.get("title") or movie.get("name")
                    movie_id = movie.get("id")
                    
                    if title and movie_id:
                        # नेटमिरर के स्टैंडर्ड डाउनलोड स्ट्रक्चर के अनुसार डायरेक्ट लिंक जनरेट करना
                        direct_download_url = f"https://netmirror.center{movie_id}/file.mp4?token=a1b2c3d4e5f6"
                        
                        print(f"[Found] लिंक जनरेट हुआ: {title}")
                        send_to_leech_bot(direct_download_url, title)
                        await asyncio.sleep(4)  # बोट फ्लडिंग सेफ्टी गैप
            else:
                # बैकअप लॉजिक: अगर एपीआई का स्ट्रक्चर थोड़ा अलग हो (जैसे डायरेक्ट लिस्ट)
                if isinstance(data, list) and len(data) > 0:
                    print(f"[Engine] कुल {len(data)} आइटम्स मिले।")
                else:
                    print("[Engine] कोई नया डेटा नहीं मिला। सर्वर रिपॉन्स खाली है या ब्लॉक है।")
            
            print("[Engine] राउंड पूरा हुआ। अब 2 घंटे का ब्रेक...")
            await asyncio.sleep(7200)  
        except Exception as e:
            print(f"[Engine Error] लूप क्रैश हुआ: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(run_auto_scraper_loop())
    
