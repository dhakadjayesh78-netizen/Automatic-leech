import os
import time
import requests

# गिटहब वर्कफ़्लो एनवायरनमेंट से क्रेडेंशियल्स लोड करना
BOT_TOKEN = os.environ.get("BOT_TOKEN")  
LEECH_CHAT_ID = os.environ.get("BIN_CHANNEL") 

# फ्री एजुकेशनल TMDB API की
TMDB_API_KEY = "4ddf0b7a546f08c65537521628e11a46"

def get_total_pages():
    """TMDB सर्वर पर मौजूद कुल पेजों की संख्या (Max Available Pages) पता करना"""
    url = f"https://themoviedb.org{TMDB_API_KEY}&language=hi|en"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            total_pages = resp.json().get('total_pages', 500)
            # TMDB API सुरक्षा कारणों से discover एंडपॉइंट पर मैक्सिमम 500 पेज ही अलाउ करता है
            return min(total_pages, 500)
    except Exception:
        pass
    return 500

def sync_infinite_movies():
    """बिना रुके सभी उपलब्ध पेजों को क्रॉल करना"""
    total_pages = get_total_pages()
    print(f"[TMDB Engine] इन्फिनिटी मोड एक्टिवेटेड! कुल {total_pages} पेजेस (लगभग 10,000+ फ़िल्में) स्कैन की जा रही हैं...")
    
    movie_count = 0
    
    # 1 से लेकर आखिरी उपलब्ध पेज तक लूप चलाना
    for page in range(1, total_pages + 1):
        print(f"[Scraper] स्कैनिंग पेज: {page} / {total_pages}", flush=True)
        
        # बॉलीवुड और हॉलीवुड दोनों का लेटेस्ट डेटा एक साथ फेच करना
        tmdb_url = f"https://themoviedb.org{TMDB_API_KEY}&page={page}&sort_by=popularity.desc&with_original_language=hi|en"
        
        try:
            response = requests.get(tmdb_url, timeout=15)
            if response.status_code == 200:
                results = response.json().get('results', [])
                
                if not results:
                    print(f"[Scraper] पेज {page} खाली है। लूप समाप्त।")
                    break
                    
                for movie in results:
                    title = movie.get('title') or movie.get('original_title')
                    movie_id = movie.get('id')
                    
                    if title and movie_id:
                        # फिल्म का IMDb ID निकालना
                        detail_url = f"https://themoviedb.org{movie_id}?api_key={TMDB_API_KEY}"
                        detail_resp = requests.get(detail_url, timeout=10)
                        
                        if detail_resp.status_code == 200:
                            imdb_id = detail_resp.json().get('imdb_id')
                            if imdb_id:
                                # डायरेक्ट नेटमिरर एम्बेड डाउनलोडर लिंक
                                direct_download_url = f"https://netmirror.center{imdb_id}/file.mp4?token=a1b2c3d4e5f6"
                                
                                print(f"[Found] ({page}) लिंक रेडी: {title}", flush=True)
                                send_to_leech_bot(direct_download_url, title)
                                movie_count += 1
                                
                                # टेलीग्राम फ्लडिंग/ब्लॉकिंग से बचने के लिए सेफ्टी डिले
                                time.sleep(3.5) 
                        time.sleep(0.3)
            
            # हर एक पेज कम्प्लीट होने पर छोटा ब्रेक ताकि API की ब्लॉक न हो
            time.sleep(1)
            
        except Exception as e:
            print(f"[TMDB Error] पेज {page} पर दिक्कत आई: {e}", flush=True)
            time.sleep(5) # एरर आने पर थोड़ा इंतजार
            
    print(f"[Engine] इन्फिनिटी राउंड समाप्त! कुल {movie_count} फिल्मों के लिंक्स भेजे गए।")

def send_to_leech_bot(download_link, movie_title):
    """टेलीग्राम चैनल/ग्रुप में लीच कमांड भेजना"""
    if not BOT_TOKEN or not LEECH_CHAT_ID:
        print("[Telegram Error] BOT_TOKEN या BIN_CHANNEL सीक्रेट्स मिसिंग हैं!", flush=True)
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
        if resp.status_code != 200:
            print(f"[Telegram Error] सेंड करने में दिक्कत आई: {resp.text}", flush=True)
    except Exception as e:
        print(f"[Telegram Critical] कनेक्शन फेल: {e}", flush=True)

def main():
    print("[Engine] इन्फिनिटी मूवी लिंक जनरेटर शुरू हो रहा है...", flush=True)
    sync_infinite_movies()

if __name__ == "__main__":
    main()
    
