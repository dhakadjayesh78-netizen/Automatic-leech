import os
import asyncio
import cloudscraper
import httpx
from bs4 import BeautifulSoup

# एनवायरनमेंट वेरिएबल से वेबसाइट लिंक उठाना (डिफ़ॉल्ट रूप से एक लीगल आर्काइव सेट है)
TARGET_URL = os.environ.get("TARGET_SCRAPE_URL", "https://archive.org")

def get_latest_links():
    links = []
    
    # 1. पहला सुरक्षा बाईपास प्रयास (Cloudscraper का उपयोग)
    try:
        # यह क्लाउडफ्लेयर एंटी-बोट प्रोटेक्शन को बाईपास करने की कोशिश करता है
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        response = scraper.get(TARGET_URL, timeout=20)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            for anchor in soup.find_all('a'):
                link = anchor.get('href')
                if link and (link.endswith('.mp4') or link.endswith('.mkv')):
                    if link.startswith('/'):
                        # लिंक को पूरा डोमेन यूआरएल देना
                        base_url = TARGET_URL.split('/details')[0] if '/details' in TARGET_URL else TARGET_URL
                        link = base_url + link
                    if link not in links:
                        links.append(link)
            if links:
                print(f"[Scraper] Cloudscraper के जरिए कुल {len(links)} लिंक्स मिले।")
                return links
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
                soup = BeautifulSoup(resp.text, 'lxml')
                for anchor in soup.find_all('a'):
                    link = anchor.get('href')
                    if link and (link.endswith('.mp4') or link.endswith('.mkv')):
                        if link.startswith('/'):
                            base_url = TARGET_URL.split('/details')[0] if '/details' in TARGET_URL else TARGET_URL
                            link = base_url + link
                        if link not in links:
                            links.append(link)
                print(f"[Scraper] HTTPX के जरिए कुल {len(links)} लिंक्स मिले।")
                return links
    except Exception as e:
        print(f"[Scraper Critical Error] सभी बाईपास तरीके फेल रहे: {e}")
    
    return links  # अगर सब फेल हो गया, तो खाली लिस्ट भेजेगा ताकि बोट क्रैश न हो
                      
