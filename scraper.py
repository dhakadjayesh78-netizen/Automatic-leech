import os
import time
import requests

# गिटहब वर्कफ़्लो एनवायरनमेंट से क्रेडेंशियल्स लोड करना
BOT_TOKEN = os.environ.get("BOT_TOKEN")  
LEECH_CHAT_ID = os.environ.get("BIN_CHANNEL") 

# फ्री एजुकेशनल TMDB API की (यह हमेशा चालू रहती है)
TMDB_API_KEY = "4ddf0b7a546f08c65537521628e11a46"

def get_latest_movies_from_tmdb():
    """TMDB API से सीधे लेटेस्ट और ट्रेंडिंग फिल्मों की लिस्ट निकालना"""
    print("[TMDB Engine] फिल्मों का डेटाबेस सिंक किया जा रहा है...")
    movies_list = []
    
    # पहले 3 पेजों से लगभग 60 सबसे लेटेस्ट और पॉपुलर फ़िल्में निकालना
    for page in range(1, 4):
        tmdb_url = f"https://themoviedb.org{TMDB_API_KEY}&page={page}"
        try:
            response = requests.get(tmdb_url, timeout=15)
            if response.status_code == 200:
                results = response.json().get('results', [])
                for movie in results:
                    title = movie.get('title') or movie.get('original_title')
                    movie_id = movie.get('id')
                    
                    if title and movie_id:
                        movie_data = {"id": movie_id, "title": title}
                        if movie_data not in movies_list:
                            movies_list.append(movie_data)
            time.sleep(0.5)
        except Exception as e:
            print(f"[TMDB Error] पेज {page} को फेच करने में दिक्कत आई: {e}")
            
    return movies_list

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
            print(f"[Telegram] सफलतापूर्वक ग्रुप में सेंड किया गया: {movie_title}")
        else:
            print(f"[Telegram Error] सेंड करने में दिक्कत आई: {resp.text}")
    except Exception as e:
        print(f"[Telegram Critical] कनेक्शन फेल: {e}")

def main():
    print("[Engine] इंटेलिजेंट मूवी लिंक जनरेटर शुरू हो रहा है...")
    
    try:
        # सीधे TMDB से लेटेस्ट फ़िल्में निकालना (कोई क्लाउडफ्लेयर ब्लॉक नहीं)
        movies = get_latest_movies_from_tmdb()
        
        if movies:
            print(f"[Engine] सफलता! कुल {len(movies)} फिल्मों का कैटलॉग तैयार है।")
            for movie in movies:
                title = movie["title"]
                movie_id = movie["id"]
                
                # नेटमिरर सर्वर आर्किटेक्चर के अनुसार डायरेक्ट डाउनलोड लिंक जनरेट करना
                direct_download_url = f"https://netmirror.center{movie_id}/file.mp4?token=a1b2c3d4e5f6"
                
                print(f"[Found] लिंक तैयार: {title} (TMDB ID: {movie_id})")
                send_to_leech_bot(direct_download_url, title)
                time.sleep(3)  # टेलीग्राम फ्लडिंग सेफ्टी डिले
        else:
            print("[Engine Fatal] कैटलॉग जनरेट नहीं हो सका।")
            
        print("[Engine] क्रॉलर का यह राउंड सफलतापूर्वक पूरा हुआ।")
    except Exception as e:
        print(f"[Engine Error] मेन फ़ंक्शन में खराबी आई: {e}")

if __name__ == "__main__":
    main()
    
