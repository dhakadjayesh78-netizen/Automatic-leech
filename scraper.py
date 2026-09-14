import os
import time
import requests
import cloudscraper
import httpx
import re
from bs4 import BeautifulSoup

# गिटहब वर्कफ़्लो एनवायरनमेंट से क्रेडेंशियल्स लोड करना
TARGET_URL = os.environ.get("TARGET_SCRAPE_URL", "https://netmirror.center")
BOT_TOKEN = os.environ.get("BOT_TOKEN")  
LEECH_CHAT_ID = os.environ.get("BIN_CHANNEL") 

def get_html_via_proxy(url):
    """गिटहब के ब्लॉक आईपी से बचने के लिए ऑल-इन-वन प्रॉक्सी और स्क्रैपिंग बाईपास लेयर"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }

    # तरीका 1: पब्लिक अनब्लॉकर प्रॉक्सी इंजन का उपयोग करके रिक्वेस्ट रीडायरेक्ट करना
    # यह गिटहब के आईपी को छुपाकर एक साधारण यूजर के आईपी से रिक्वेस्ट भेजेगा
    proxy_gateways = [
        f"https://allorigins.win{requests.utils.quote(url)}",
        f"https://corsproxy.io?{requests.utils.quote(url)}"
    ]

    for gateway in proxy_gateways:
        print(f"[Engine] प्रॉक्सी टनल के जरिए कनेक्ट किया जा रहा है: {gateway[:50]}...")
        try:
            resp = requests.get(gateway, headers=headers, timeout=20)
            if resp.status_code == 200:
                response_data = resp.text
                # AllOrigins प्रॉक्सी JSON के अंदर HTML देती है, उसे पार्स करना
                if "contents" in response_data:
                    import json
                    return json.loads(response_data).get("contents", "")
                if len(response_data) > 500:
                    return response_data
        except Exception as e:
            print(f"[Proxy Warning] इस गेटवे पर एरर आया: {e}")

    # तरीका 2: अगर प्रॉक्सी फेल हो तो डायरेक्ट क्लाउडस्क्रेपर का आखिरी प्रयास
    try:
        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )
        resp = scraper.get(url, headers=headers, timeout=15)
        if resp.status_code == 200 and len(resp.text) > 1000:
            return resp.text
    except Exception:
        pass

    return None

def scrape_movies():
    """पेज से मूवी डेटा और उनकी आईडी निकालना"""
    urls_to_try = [
        TARGET_URL.rstrip('/'),
        f"{TARGET_URL.rstrip('/')}/movies",
        f"{TARGET_URL.rstrip('/')}/trending"
    ]
    
    found_movies = []

    for url in urls_to_try:
        html_content = get_html_via_proxy(url)
        
        if html_content:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # तरीका ए: एंकर टैग्स से आईडी ढूंढना
            for anchor in soup.find_all('a', href=True):
                href = anchor['href']
                title = anchor.get_text(strip=True) or anchor.get('title', '').strip()
                
                if any(x in href for x in ["/details/", "/movie/", "/watch/"]):
                    parts = [p for p in href.split('/') if p]
                    movie_id = parts[-1] if parts else None
                    if movie_id and movie_id.isdigit():
                        movie_data = {"id": movie_id, "title": title if title else f"Movie {movie_id}"}
                        if movie_data not in found_movies:
                            found_movies.append(movie_data)
            
            # तरीका बी: अगर एंकर टैग्स न मिलें तो पूरे पेज में से रेगुलर एक्सप्रेशन (Regex) से मूवी आईडी निकालना
            # नेटमिरर अक्सर जावास्क्रिप्ट ऑब्जेक्ट्स में आईडी रखता है
            ids = re.findall(r'(?:id|movie_id)["\']?\s*:\s*["\']?(\d+)', html_content)
            for m_id in ids:
                movie_data = {"id": m_id, "title": f"NetMirror Content (ID: {m_id})"}
                if movie_data not in [m for m in found_movies]:
                    found_movies.append(movie_data)
                    
    return found_movies

def send_to_leech_bot(download_link, movie_title):
    """टेलीग्राम पर लीच कमांड भेजना"""
    if not BOT_TOKEN or not LEECH_CHAT_ID:
        print("[Telegram Error] BOT_TOKEN या BIN_CHANNEL सीक्रेट्स मिसिंग हैं!")
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
        resp = requests.post(telegram_url, json=payload, timeout=10)
        if resp.status_code == 200:
            print(f"[Telegram] सफलतापूर्वक ग्रुप में सेंड किया गया: {movie_title}")
        else:
            print(f"[Telegram Error] सेंड करने में दिक्कत आई: {resp.text}")
    except Exception as e:
        print(f"[Telegram Critical] कनेक्शन फेल: {e}")

def main():
    print("[Engine] प्रॉक्सी-बाईपास नेटमिरर क्रॉलर रन हो रहा है...")
    
    try:
        movies = scrape_movies()
        
        if movies:
            print(f"[Engine] सफलता! प्रॉक्सी के जरिए कुल {len(movies)} मूवीज का डेटा मिल गया है।")
            for movie in movies:
                title = movie["title"]
                movie_id = movie["id"]
                
                # डायरेक्ट डाउनलोड यूआरएल स्ट्रक्चर
                direct_download_url = f"https://netmirror.center{movie_id}/file.mp4?token=a1b2c3d4e5f6"
                
                print(f"[Found] डायरेक्ट लिंक रेडी: {title} (ID: {movie_id})")
                send_to_leech_bot(direct_download_url, title)
                time.sleep(3)  # टेलीग्राम फ्लडिंग सेफ्टी डिले
        else:
            print("[Engine Fatal] प्रॉक्सी चैनल्स भी ब्लॉक हैं। नेटमिरर पूरी तरह प्रोटेक्टेड है।")
            
        print("[Engine] क्रॉलर का यह राउंड सफलतापूर्वक पूरा हुआ।")
    except Exception as e:
        print(f"[Engine Error] मेन फ़ंक्शन में खराबी आई: {e}")

if __name__ == "__main__":
    main()
                
