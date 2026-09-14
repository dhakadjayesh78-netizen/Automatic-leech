import os
import time
import cloudscraper
import httpx
from bs4 import BeautifulSoup

# 1. कॉन्फ़िगरेशन (अपनी डिटेल्स यहाँ भरें या GitHub Secrets में सेट करें)
TARGET_URL = os.environ.get("TARGET_SCRAPE_URL", "https://netmirror.center")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")  # आपके टेलीग्राम बोट का टोकन
# आपका वो ग्रुप/चैनल ID या Leech Bot की Chat ID जहाँ लिंक भेजना है
LEECH_CHAT_ID = os.environ.get("LEECH_CHAT_ID", "YOUR_CHAT_ID_OR_GROUP_ID") 

def get_scraper_response(url):
    """सुरक्षित तरीके से वेबपेज का HTML लोड करने का फंक्शन (Anti-Bot बाईपास के साथ)"""
    try:
        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )
        response = scraper.get(url, timeout=20)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"[Scraper Warning] Cloudscraper फेल हुआ, बैकअप आजमाया जा रहा है: {e}")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        with httpx.Client(headers=headers, follow_redirects=True, timeout=20.0) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                return resp.text
    except Exception as e:
        print(f"[Critical Error] पेज लोड नहीं हो सका: {e}")
    return None

def send_to_leech_bot(download_link, movie_title):
    """टेलीग्राम बोट API के जरिए Leech Bot को डायरेक्ट डाउनलोड कमांड भेजना"""
    # अधिकांश Leech बोट्स /leech [Direct Link] कमांड लेते हैं
    leech_command = f"/leech {download_link}"
    
    # आप चाहें तो मैसेज को थोड़ा सुंदर भी बना सकते हैं ताकि ट्रैकिंग आसान हो
    caption = f"🎬 <b>Movie:</b> {movie_title}\n\n<code>{leech_command}</code>"
    
    telegram_url = f"https://telegram.org{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": LEECH_CHAT_ID,
        "text": caption,
        "parse_mode": "HTML"
    }
    
    try:
        resp = requests.post(telegram_url, json=payload)
        if resp.status_code == 200:
            print(f"[Telegram] सफलतापूर्वक भेजा गया: {movie_title}")
        else:
            print(f"[Telegram Error] बोट को मैसेज भेजने में दिक्कत आई: {resp.text}")
    except Exception as e:
        print(f"[Telegram Critical] कनेक्शन फेल: {e}")

def extract_movie_page_links(homepage_html, base_url):
    """होमपेज से सभी मूवी और वेब सीरीज के पेजों (Details Pages) के लिंक्स निकालना"""
    soup = BeautifulSoup(homepage_html, 'lxml')
    movie_pages = []
    
    # नेटमिरर पर मूवी कार्ड्स के लिंक्स आमतौर पर /details/ या /watch/ से शुरू होते हैं
    for anchor in soup.find_all('a', href=True):
        href = anchor['href']
        title = anchor.get_text(strip=True) or "Unknown Movie"
        
        if "/details/" in href or "/movie/" in href:
            if href.startswith('/'):
                href = base_url.rstrip('/') + href
            if href not in [m['url'] for m in movie_pages]:
                movie_pages.append({"url": href, "title": title})
                
    return movie_pages

def scrape_single_movie_direct_link(movie_url):
    """एक सिंगल मूवी पेज के अंदर जाकर उसका असली डाउनलोड लिंक ढूंढना"""
    html = get_scraper_response(movie_url)
    if not html:
        return None
        
    soup = BeautifulSoup(html, 'lxml')
    
    # <a class="download-link" href="..."> को खोजना
    for anchor in soup.find_all('a', href=True):
        link = anchor['href']
        link_class = anchor.get('class', [])
        
        if 'download-link' in link_class or link.endswith('.mp4') or link.endswith('.mkv') or '.mp4?' in link:
            if link.startswith('/'):
                # बेस यूआरएल निकालना
                base = TARGET_URL.split('/details')[0] if '/details' in TARGET_URL else TARGET_URL
                link = base.rstrip('/') + link
            return link # पहला वैलिड डायरेक्ट डाउनलोड लिंक मिलते ही रिटर्न करें
            
    return None

def start_crawler():
    print("[Engine] नेटमिरर क्रॉलर शुरू हो रहा है...")
    base_url = TARGET_URL.split('/details')[0] if '/details' in TARGET_URL else TARGET_URL
    
    # 1. होमपेज लोड करें
    homepage_html = get_scraper_response(TARGET_URL)
    if not homepage_html:
        print("[Error] होमपेज लोड नहीं हो सका। क्रॉलर बंद किया जा रहा है।")
        return
        
    # 2. सभी मूवीज की लिस्ट निकालें
    movie_list = extract_movie_page_links(homepage_html, base_url)
    print(f"[Engine] कुल {len(movie_list)} मूवीज/वेब सीरीज के पेजेस मिले।")
    
    # 3. हर मूवी पेज पर जाकर डायरेक्ट लिंक निकालें और लीच बोट को भेजें
    for movie in movie_list:
        print(f"[Scraper] प्रोसेसिंग: {movie['title']}")
        
        direct_download_url = scrape_single_movie_direct_link(movie['url'])
        
        if direct_download_url:
            print(f"[Found] डायरेक्ट लिंक मिला: {direct_download_url}")
            # लीच बोट को भेजें
            send_to_leech_bot(direct_download_url, movie['title'])
            # बोट ब्लॉक न हो और सर्वर पर लोड न पड़े इसलिए 3 सेकंड का गैप
            time.sleep(3) 
        else:
            print(f"[Skipped] {movie['title']} का डायरेक्ट डाउनलोड लिंक नहीं मिला (शायद हिडन जावास्क्रिप्ट हो)।")
            
        time.sleep(1) # हर पेज रिक्वेस्ट के बीच छोटा गैप

if __name__ == "__main__":
    import requests # टेलीग्राम पोस्ट के लिए इम्पोर्ट
    start_crawler()
    
