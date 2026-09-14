import os
import asyncio
import cloudscraper
import httpx
from bs4 import BeautifulSoup

# एनवायरनमेंट वेरिएबल से वेबसाइट लिंक उठाना (डिफ़ॉल्ट रूप से नेटमिरर सेट है)
TARGET_URL = os.environ.get("TARGET_SCRAPE_URL", "https://netmirror.center/")

def extract_netmirror_data(html_content, base_url):
    """HTML कंटेंट में से वीडियो प्लेयर और डाउनलोड लिंक्स निकालने का हेल्पर फंक्शन"""
    soup = BeautifulSoup(html_content, 'lxml')
    stream_links = []
    download_links = []

    # 1. वीडियो प्लेयर के लिंक्स ढूंढना (<video src="...">)
    for video in soup.find_all('video'):
        src = video.get('src')
        if src:
            if src.startswith('/'):
                src = base_url.rstrip('/') + src
            if src not in stream_links:
                stream_links.append(src)

    # 2. डाउनलोड लिंक्स ढूंढना (<a class="download-link" href="..."> या .mp4/.mkv लिंक्स)
    for anchor in soup.find_all('a'):
        link = anchor.get('href')
        link_class = anchor.get('class', [])
        
        if link:
            # अगर क्लास 'download-link' है या लिंक के अंत में वीडियो फॉर्मेट है
            if 'download-link' in link_class or link.endswith('.mp4') or link.endswith('.mkv') or '.mp4?' in link:
                if link.startswith('/'):
                    link = base_url.rstrip('/') + link
                if link not in download_links:
                    download_links.append(link)

    return {
        "stream_links": stream_links,
        "download_links": download_links
    }

def get_latest_links():
    # अब यह फंक्शन एक डिक्शनरी रिटर्न करेगा जिसमें दोनों लिस्ट होंगी
    result_data = {"stream_links": [], "download_links": []}
    
    # बेस यूआरएल सेट करना ताकि रिलेटिव पाथ (/details...) पूरे यूआरएल बन सकें
    base_url = TARGET_URL.split('/details')[0] if '/details' in TARGET_URL else TARGET_URL

    # 1. पहला सुरक्षा बाईपास प्रयास (Cloudscraper का उपयोग)
    try:
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        response = scraper.get(TARGET_URL, timeout=20)
        
        if response.status_code == 200:
            extracted = extract_netmirror_data(response.text, base_url)
            if extracted["stream_links"] or extracted["download_links"]:
                print(f"[Scraper] Cloudscraper के जरिए कुल {len(extracted['stream_links'])} प्लेयर और {len(extracted['download_links'])} डाउनलोड लिंक्स मिले।")
                return extracted
    except Exception as e:
        print(f"[Scraper Warning] Cloudscraper फेल हो गया, दूसरा तरीका आजमाया जा रहा है: {e}")

    # 2. दूसरा सुरक्षा बाईपास प्रयास (HTTPX विद एडवांस हेडर्स) - बैकअप प्लान
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive"
        }
        
        with httpx.Client(headers=headers, follow_redirects=True, timeout=20.0) as client:
            resp = client.get(TARGET_URL)
            if resp.status_code == 200:
                extracted = extract_netmirror_data(resp.text, base_url)
                print(f"[Scraper] HTTPX के जरिए कुल {len(extracted['stream_links'])} प्लेयर और {len(extracted['download_links'])} डाउनलोड लिंक्स मिले।")
                return extracted
    except Exception as e:
        print(f"[Scraper Critical Error] सभी बाईपास तरीके फेल रहे: {e}")
    
    return result_data  # अगर सब फेल हो गया, तो खाली लिस्ट्स भेजेगा ताकि बोट क्रैश न हो

if __name__ == "__main__":
    # टेस्ट करने के लिए रन करें
    data = get_latest_links()
    print("प्लेयर लिंक्स:", data["stream_links"])
    print("डाउनलोड लिंक्स:", data["download_links"])
        
