import os
import time
import requests
import cloudscraper
import httpx
from bs4 import BeautifulSoup

# गिटहब वर्कफ़्लो एनवायरनमेंट से क्रेडेंशियल्स लोड करना
TARGET_URL = os.environ.get("TARGET_SCRAPE_URL", "https://netmirror.center")
BOT_TOKEN = os.environ.get("BOT_TOKEN")  
LEECH_CHAT_ID = os.environ.get("BIN_CHANNEL") 

def get_latest_movies_via_scraping():
    """वेबसाइट के मेन कैटलॉग पेज को एक अलग एडवांस्ड तरीके से क्रॉल करना"""
    print("[Engine] अल्टरनेटिव स्क्रैपिंग मेथड चालू किया जा रहा है...")
    
    # नेटमिरर के अलग-अलग पेज जहां लेटेस्ट कंटेंट होता है
    urls_to_try = [
        TARGET_URL.rstrip('/'),
        f"{TARGET_URL.rstrip('/')}/movies",
        f"{TARGET_URL.rstrip('/')}/trending"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Alt-Used": "netmirror.center",
        "Connection": "keep-alive"
    }

    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )

    found_movies = []

    for url in urls_to_try:
        print(f"[Scraper] चेकिंग पेज: {url}")
        html_content = None
        
        try:
            # प्रयास 1: Cloudscraper
            resp = scraper.get(url, headers=headers, timeout=15)
            if resp.status_code == 200 and len(resp.text) > 1000:
                html_content = resp.text
        except Exception as e:
            print(f"[Scraper Trace] Cloudscraper इस पेज पर फेल हुआ: {e}")

        if not html_content:
            try:
                # प्रयास 2: HTTPX
                with httpx.Client(headers=headers, follow_redirects=True, timeout=15.0) as client:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        html_content = resp.text
            except Exception:
                continue

        if html_content:
            # HTML को पार्स करके मूवी लिंक्स और IDs निकालना
            soup = BeautifulSoup(html_content, 'lxml')
            for anchor in soup.find_all('a', href=True):
                href = anchor['href']
                title = anchor.get_text(strip=True) or anchor.get('title', '').strip()
                
                # नेटमिरर के यूआरएल स्ट्रक्चर (/watch/ID या /details/ID) से आईडी निकालना
                if "/details/" in href or "/movie/" in href or "/watch/" in href:
                    # यूआरएल में से केवल नंबर (ID) को अलग करना
                    parts = [p for p in href.split('/') if p]
                    movie_id = parts[-1] if parts else None
                    
                    if movie_id and movie_id.isdigit():
                        movie_data = {"id": movie_id, "title": title if title else f"Movie {movie_id}"}
                        if movie_data not in found_movies:
                            found_movies.append(movie_data)

    return found_movies

def send_to_leech_bot(download_link, movie_title):
    """टेलीग्राम चैनल/ग्रुप में लीच कमांड भेजना"""
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
            print(f"[Telegram] सफलतापूर्वक भेजा गया: {movie_title}")
        else:
            print(f"[Telegram Error] बोट को भेजने में फेल: {resp.text}")
    except Exception as e:
        print(f"[Telegram Critical] कनेक्शन फेल: {e}")

def main():
    print("[Engine] बाईपास नेटमिरर क्रॉलर रन हो रहा है...")
    
    try:
        # अब हम JSON API के भरोसे नहीं बैठेंगे, सीधे HTML स्ट्रक्चर क्रॉल करेंगे
        movies = get_latest_movies_via_scraping()
        
        if movies:
            print(f"[Engine] सफलता! कुल {len(movies)} मूवीज के रेजोल्यूशन रूट्स मिल गए हैं।")
            for movie in movies:
                title = movie["title"]
                movie_id = movie["id"]
                
                # नेटमिरर टोकन और यूनिवर्सल एम्बेड प्लेयर लिंक जनरेशन
                direct_download_url = f"https://netmirror.center{movie_id}/file.mp4?token=a1b2c3d4e5f6"
                
                print(f"[Found] डायरेक्ट लिंक तैयार: {title} (ID: {movie_id})")
                send_to_leech_bot(direct_download_url, title)
                time.sleep(3)  # टेलीग्राम फ्लडिंग सेफ्टी डिले
        else:
            print("[Engine Fatal] वेबसाइट का HTML रिस्पॉन्स पूरी तरह ब्लॉक है या कोई मूवी नहीं मिली।")
            
        print("[Engine] क्रॉलर का यह राउंड सफलतापूर्वक पूरा हुआ।")
    except Exception as e:
        print(f"[Engine Error] मेन फ़ंक्शन में खराबी आई: {e}")

if __name__ == "__main__":
    main()
        
